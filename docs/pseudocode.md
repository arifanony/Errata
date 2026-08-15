# Errata — Pseudocode

**An Evaluation Harness for AI Classifiers and Agents**

*This is pseudocode, not real code — it shows how each step should think, matching the flow diagram exactly, so the actual Python later just follows this shape.*

Arif Hussain · 13 August 2026

---

## STEP 1 -- BUILD THE HIDDEN TEST SET

```
    DEFINE test_set as a list of cases

    FOR each case:
        case.input           = the thing being judged (an email, a message, etc.)
        case.true_label      = the real answer (e.g. "phishing")  -- KEPT HIDDEN
        case.true_label_path = full path in the tree (root -> dangerous -> phishing)

    # Nothing here is shown to the model yet.
    # This whole list is locked away until Step 4.
```

## STEP 2 -- MODEL PREDICTS, BLIND

```
    DEFINE raw_predictions as an empty list

    FOR each case IN test_set:
        raw_output = model.predict(case.input)   # model never sees true_label
        raw_predictions.append({
            case_id:     case.id,
            raw_output:  raw_output    # could be a label, a score, a number,
        })                             # or free text -- not yet standardised

    # At this point the model has committed. No going back and changing
    # a guess after seeing an answer -- that would make the test meaningless.
    #
    # NOTE: what the model actually returns here depends on what kind of
    # model is being tested. That is exactly why Step 3 exists.
```

## STEP 3 -- ADAPTER LAYER   (sits between the model and the harness)

```
    # Errata only ever wants ONE standard shape to work with:
    # a predicted_label, plus an optional confidence number if the
    # model gave one. This step is the only place that has to know
    # or care what kind of model produced raw_output.

    FUNCTION standardise(raw_output):
        IF raw_output is already a clean category label:
            RETURN { predicted_label: raw_output, confidence: null }

        IF raw_output is a probability or risk score (e.g. 0.83):
            predicted_label = "dangerous" IF raw_output >= threshold ELSE "safe"
            RETURN { predicted_label: predicted_label, confidence: raw_output }

        IF raw_output is a plain number, not a probability (e.g. an amount):
            # no label exists in this case -- handled separately,
            # compared directly as numbers rather than forced into a tree
            RETURN { predicted_label: null, predicted_value: raw_output }

        IF raw_output is free text:
            # the model should have been prompted to reply in a fixed
            # format in the first place (label + confidence) --
            # this branch is the fallback if that didn't happen
            predicted_label, confidence = extract_label_and_confidence(raw_output)
            RETURN { predicted_label: predicted_label, confidence: confidence }

    DEFINE predictions as an empty list
    FOR each raw IN raw_predictions:
        standard = standardise(raw.raw_output)
        predictions.append({
            case_id:          raw.case_id,
            predicted_label:  standard.predicted_label,
            confidence:       standard.confidence     # may be null
        })

    # Everything from here on only ever deals with predictions,
    # never with raw_predictions again.
```

## STEP 4 -- REVEAL THE REAL ANSWERS

```
    FOR each prediction IN predictions:
        matching_case = find case in test_set where case.id == prediction.case_id
        prediction.true_label = matching_case.true_label     # unlocked, only now
```

## STEP 5 -- COMPARE GUESS VS. REAL ANSWER

```
    FOR each prediction IN predictions:
        p = prediction.predicted_label
        t = prediction.true_label

        IF p == "dangerous" AND t == "dangerous":  result = "caught it"          # true positive
        IF p == "safe"      AND t == "dangerous":  result = "missed it"          # false negative
        IF p == "dangerous" AND t == "safe":       result = "false alarm"        # false positive
        IF p == "safe"      AND t == "safe":       result = "correctly ignored"  # true negative
        # "suspicious" predictions or true labels are handled the same way --
        # compared exactly, and scored for "how far off" in Step 6b below

        prediction.result = result

    confusion_counts = count(predictions grouped by result)
```

## STEP 6a -- FLAT SCORE

```
    total   = count(predictions)
    correct = count(predictions where predicted_label == true_label)

    flat_accuracy = correct / total

    # nothing new here -- this is the plain, standard number, kept only
    # so it can be compared side by side with 6b, 6c and 6d
```

## STEP 6b -- TREE-DISTANCE SCORE   (no existing library does this)

```
    DEFINE label_tree:
        root
         |-- safe
         |-- suspicious
         `-- dangerous
              |-- phishing
              |-- malware
              `-- fraud

    FUNCTION tree_distance(label_a, label_b):
        IF label_a == label_b:
            RETURN 0
        path_a = path from root to label_a     # e.g. [root, dangerous, phishing]
        path_b = path from root to label_b
        common_ancestor = deepest node that appears in both path_a AND path_b
        steps_a = distance from label_a up to common_ancestor
        steps_b = distance from label_b up to common_ancestor
        RETURN steps_a + steps_b

    FOR each prediction IN predictions:
        prediction.tree_distance = tree_distance(prediction.predicted_label,
                                                   prediction.true_label)

    average_tree_distance = mean(all prediction.tree_distance values)

    # mistaking "phishing" for "malware"   -> small number  (2)
    # mistaking "safe" for "suspicious"    -> small number  (2)
    # mistaking "phishing" for "safe"      -> bigger number (3)
    # exact right answer                   -> always 0
```

## STEP 6c -- COST SCORE

```
    DEFINE cost_matrix:
        cost["missed it"]         = 1000000   # false negative -- illustrative value
        cost["false alarm"]       = 50        # false positive -- illustrative value
        cost["caught it"]         = 0
        cost["correctly ignored"] = 0

    total_cost = 0
    FOR each prediction IN predictions:
        total_cost = total_cost + cost[prediction.result]

    expected_cost_per_100 = (total_cost / total) * 100

    # this is the number that tells you what the model's mistakes would
    # actually cost, not just how many mistakes there were
```

## STEP 6d -- CALIBRATION SCORE

```
    # Only meaningful for predictions that came with a confidence number
    # (Step 3 sets confidence = null when there wasn't one -- skip those)

    calibratable = filter predictions where confidence IS NOT null

    # Group predictions into confidence "buckets" -- e.g. everything the
    # model said it was 80-90% sure about, everything it said 90-100%, etc.
    FOR each bucket IN [0-10%, 10-20%, ... , 90-100%]:
        predictions_in_bucket   = filter calibratable where confidence falls in bucket
        stated_confidence       = midpoint of the bucket (e.g. 85% for the 80-90% bucket)
        actual_accuracy         = count(correct) / count(predictions_in_bucket)
        bucket.gap              = stated_confidence - actual_accuracy

    calibration_error = mean(absolute value of bucket.gap, across all buckets)

    # a model that says "90% sure" and is actually right ~90% of the time
    # has a calibration_error near 0 -- well-calibrated
    #
    # a model that says "90% sure" but is only right 50% of the time
    # has a large calibration_error -- confidently wrong, a real risk
    # that flat_accuracy alone would never reveal
```

## STEP 7 -- ADVERSARIAL CASES, MIXED IN

```
    DEFINE adversarial_cases as a small hand-built list, e.g.:
        - an email with a hidden instruction telling the model to say "safe"
        - a message that tries to override the system prompt
        (patterns based on OWASP's prompt-injection category)

    # these get added into test_set BEFORE step 2, mixed in with normal
    # cases, so the model doesn't know which ones are the "trick" ones

    adversarial_predictions = filter predictions where case_id IN adversarial_cases
    adversarial_pass_rate   = count(correct) / count(adversarial_predictions)

    # if this is much worse than the overall flat_accuracy, that is a
    # real, specific weakness worth flagging on its own
```

## STEP 8 -- BASE-RATE SIMULATION

```
    FOR rare_rate IN [0.01, 0.05, 0.10, 0.20, 0.50]:
        simulated_set = build a test set where "dangerous" cases make up
                        rare_rate of the total
        # the model itself does NOT change -- only the test-set mix changes

        simulated_predictions = run steps 2-5 on simulated_set
        simulated_accuracy    = flat_accuracy of simulated_predictions

        record (rare_rate, simulated_accuracy)

    # plot rare_rate against simulated_accuracy -- shows how much of the
    # model's score depends on the world being calm, not on the model
    # actually being good
```

## STEP 9 -- ONE CONSOLIDATED ERRATA REPORT

```
    errata_report = {
        flat_accuracy:          from step 6a,
        average_tree_distance:  from step 6b,
        expected_cost_per_100:  from step 6c,
        calibration_error:      from step 6d,
        confusion_counts:       from step 5,
        adversarial_pass_rate:  from step 7,
        base_rate_curve:        from step 8
    }

    PRINT errata_report as one combined summary

    # no single number is allowed to represent the whole thing on its own --
    # this report is the itemised correction record, not a single grade
```
