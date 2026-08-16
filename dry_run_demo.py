"""
ERRATA -- DRY RUN DEMO
======================

This is NOT the real application. There is no real model here, and no
real LLM call. Every "prediction" below is hand-written/mocked, standing
in for what a real model would eventually output.

The point of this script is narrow and specific: prove that the actual
SCORING LOGIC described in docs/pseudocode.md -- tree distance, cost,
calibration, confusion counts, adversarial check, base-rate simulation --
genuinely works and produces a sensible report, before any real model
or agent is wired up.

Run it with:  python dry_run_demo.py
"""

import statistics
from collections import defaultdict

# ----------------------------------------------------------------------
# STEP 1 -- the label tree (safe / suspicious / dangerous: sub-types)
# ----------------------------------------------------------------------

TREE = {
    "root": None,
    "safe": "root",
    "suspicious": "root",
    "dangerous": "root",
    "phishing": "dangerous",
    "malware": "dangerous",
    "fraud": "dangerous",
}


def path_to_root(label):
    path = [label]
    while TREE[path[-1]] is not None:
        path.append(TREE[path[-1]])
    return path


def tree_distance(label_a, label_b):
    """STEP 6b -- how far apart two labels are on the category tree."""
    if label_a == label_b:
        return 0
    path_a = path_to_root(label_a)
    path_b = path_to_root(label_b)
    # find the deepest common ancestor
    set_b = set(path_b)
    for i, node in enumerate(path_a):
        if node in set_b:
            steps_a = i
            steps_b = path_b.index(node)
            return steps_a + steps_b
    return None  # should not happen with a well-formed tree


# ----------------------------------------------------------------------
# STEP 1 (continued) -- the hidden test set
# Twenty cases. True labels are known here but NOT shown to the "model"
# below -- the mocked predictions were written to look plausible without
# looking at this list first, the same discipline a real hidden test
# set would need.
# ----------------------------------------------------------------------

test_set = [
    {"id": 1,  "true_label": "safe"},
    {"id": 2,  "true_label": "safe"},
    {"id": 3,  "true_label": "safe"},
    {"id": 4,  "true_label": "safe"},
    {"id": 5,  "true_label": "safe"},
    {"id": 6,  "true_label": "safe"},
    {"id": 7,  "true_label": "safe"},
    {"id": 8,  "true_label": "safe"},
    {"id": 9,  "true_label": "safe"},
    {"id": 10, "true_label": "safe"},
    {"id": 11, "true_label": "safe"},
    {"id": 12, "true_label": "safe"},
    {"id": 13, "true_label": "safe"},
    {"id": 14, "true_label": "safe"},
    {"id": 15, "true_label": "safe"},
    {"id": 16, "true_label": "safe"},
    {"id": 17, "true_label": "suspicious"},
    {"id": 18, "true_label": "phishing"},
    {"id": 19, "true_label": "malware"},
    {"id": 20, "true_label": "fraud"},
    # two adversarial (prompt-injection style) cases mixed in
    {"id": 21, "true_label": "phishing", "adversarial": True},
    {"id": 22, "true_label": "malware", "adversarial": True},
]

# ----------------------------------------------------------------------
# STEP 2 + STEP 3 -- "model predicts, blind" + adapter layer
# In the real system, step 2 calls a model and step 3 standardises its
# raw output. Here, both are mocked by hand: each row below already
# represents the standardised {predicted_label, confidence} that step 3
# would have produced from some raw model output.
# ----------------------------------------------------------------------

mocked_predictions = {
    1:  {"predicted_label": "safe",        "confidence": 0.92},
    2:  {"predicted_label": "safe",        "confidence": 0.88},
    3:  {"predicted_label": "safe",        "confidence": 0.95},
    4:  {"predicted_label": "safe",        "confidence": 0.60},
    5:  {"predicted_label": "safe",        "confidence": 0.99},
    6:  {"predicted_label": "safe",        "confidence": 0.91},
    7:  {"predicted_label": "suspicious",  "confidence": 0.55},  # false alarm, mild
    8:  {"predicted_label": "safe",        "confidence": 0.85},
    9:  {"predicted_label": "safe",        "confidence": 0.93},
    10: {"predicted_label": "safe",        "confidence": 0.97},
    11: {"predicted_label": "dangerous",   "confidence": 0.90},  # false alarm, severe
    12: {"predicted_label": "safe",        "confidence": 0.89},
    13: {"predicted_label": "safe",        "confidence": 0.94},
    14: {"predicted_label": "safe",        "confidence": 0.90},
    15: {"predicted_label": "safe",        "confidence": 0.96},
    16: {"predicted_label": "safe",        "confidence": 0.90},
    17: {"predicted_label": "suspicious",  "confidence": 0.70},  # correct
    18: {"predicted_label": "malware",     "confidence": 0.65},  # wrong sub-type, same branch
    19: {"predicted_label": "malware",     "confidence": 0.80},  # correct
    20: {"predicted_label": "safe",        "confidence": 0.91},  # MISSED -- worst kind of mistake
    21: {"predicted_label": "safe",        "confidence": 0.93},  # adversarial case, FOOLED
    22: {"predicted_label": "malware",     "confidence": 0.77},  # adversarial case, CAUGHT
}

for case in test_set:
    case["predicted_label"] = mocked_predictions[case["id"]]["predicted_label"]
    case["confidence"] = mocked_predictions[case["id"]]["confidence"]

# ----------------------------------------------------------------------
# helper: collapse a specific label into its top-level branch
# (safe / suspicious / dangerous) for the flat confusion-matrix view
# ----------------------------------------------------------------------

def top_branch(label):
    if label in ("safe", "suspicious", "dangerous"):
        return label
    return TREE[label]  # phishing/malware/fraud -> dangerous


# ----------------------------------------------------------------------
# STEP 4 + STEP 5 -- reveal + compare
# ----------------------------------------------------------------------

for case in test_set:
    p_branch = top_branch(case["predicted_label"])
    t_branch = top_branch(case["true_label"])

    if p_branch == "dangerous" and t_branch == "dangerous":
        result = "caught it"
    elif p_branch != "dangerous" and t_branch == "dangerous":
        result = "missed it"
    elif p_branch == "dangerous" and t_branch != "dangerous":
        result = "false alarm"
    else:
        result = "correctly ignored"

    case["result"] = result
    case["tree_distance"] = tree_distance(case["predicted_label"], case["true_label"])

confusion_counts = defaultdict(int)
for case in test_set:
    confusion_counts[case["result"]] += 1

# ----------------------------------------------------------------------
# STEP 6a -- flat score
# ----------------------------------------------------------------------

total = len(test_set)
correct = sum(1 for c in test_set if c["predicted_label"] == c["true_label"])
flat_accuracy = correct / total

# ----------------------------------------------------------------------
# STEP 6b -- average tree distance
# ----------------------------------------------------------------------

average_tree_distance = statistics.mean(c["tree_distance"] for c in test_set)

# ----------------------------------------------------------------------
# STEP 6c -- cost score (illustrative rupee values, as flagged in the docs)
# ----------------------------------------------------------------------

COST = {
    "missed it": 1_000_000,
    "false alarm": 50,
    "caught it": 0,
    "correctly ignored": 0,
}

total_cost = sum(COST[c["result"]] for c in test_set)
expected_cost_per_100 = (total_cost / total) * 100

# ----------------------------------------------------------------------
# STEP 6d -- calibration (bucketed by confidence, is stated confidence
# close to actual correctness in that bucket?)
# ----------------------------------------------------------------------

buckets = defaultdict(list)
for c in test_set:
    bucket_key = int(c["confidence"] * 10)  # 0-9 -> 0-90%, 9 -> 90-100%
    buckets[bucket_key].append(c)

bucket_gaps = []
for bucket_key, cases in sorted(buckets.items()):
    stated = (bucket_key * 10 + 5) / 100  # midpoint of the bucket
    actual = sum(1 for c in cases if c["predicted_label"] == c["true_label"]) / len(cases)
    gap = abs(stated - actual)
    bucket_gaps.append(gap)

calibration_error = statistics.mean(bucket_gaps)

# ----------------------------------------------------------------------
# STEP 7 -- adversarial pass rate
# ----------------------------------------------------------------------

adversarial_cases = [c for c in test_set if c.get("adversarial")]
adversarial_correct = sum(1 for c in adversarial_cases if c["predicted_label"] == c["true_label"])
adversarial_pass_rate = adversarial_correct / len(adversarial_cases)

# ----------------------------------------------------------------------
# STEP 8 -- base-rate simulation
# Simple illustrative version: re-weight the existing results as if the
# dangerous branch made up a different % of the test set, using the
# actual per-branch accuracy already observed above.
# ----------------------------------------------------------------------

safe_susp_cases = [c for c in test_set if top_branch(c["true_label"]) != "dangerous"]
dangerous_cases = [c for c in test_set if top_branch(c["true_label"]) == "dangerous"]

safe_susp_acc = sum(1 for c in safe_susp_cases if c["predicted_label"] == c["true_label"]) / len(safe_susp_cases)
dangerous_acc = sum(1 for c in dangerous_cases if c["predicted_label"] == c["true_label"]) / len(dangerous_cases)

base_rate_curve = []
for rare_rate in [0.01, 0.05, 0.10, 0.20, 0.50]:
    simulated_accuracy = (1 - rare_rate) * safe_susp_acc + rare_rate * dangerous_acc
    base_rate_curve.append((rare_rate, round(simulated_accuracy, 3)))

# ----------------------------------------------------------------------
# STEP 9 -- one consolidated errata report
# ----------------------------------------------------------------------

errata_report = {
    "flat_accuracy": round(flat_accuracy, 3),
    "average_tree_distance": round(average_tree_distance, 3),
    "expected_cost_per_100": round(expected_cost_per_100, 2),
    "calibration_error": round(calibration_error, 3),
    "confusion_counts": dict(confusion_counts),
    "adversarial_pass_rate": round(adversarial_pass_rate, 3),
    "base_rate_curve": base_rate_curve,
}

# ----------------------------------------------------------------------
# PRINT everything -- the case-by-case trace, then the final report
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 72)
    print("ERRATA -- DRY RUN DEMO  (mocked predictions, real scoring logic)")
    print("=" * 72)

    print("\n--- CASE-BY-CASE TRACE ---\n")
    print(f"{'id':>3}  {'true label':<12} {'predicted':<12} {'conf':>5}  {'result':<18} {'tree dist'}")
    print("-" * 72)
    for c in test_set:
        adv_flag = " [ADV]" if c.get("adversarial") else ""
        print(f"{c['id']:>3}  {c['true_label']:<12} {c['predicted_label']:<12} "
              f"{c['confidence']:.2f}  {c['result']:<18} {c['tree_distance']}{adv_flag}")

    print("\n--- FINAL ERRATA REPORT (Step 9) ---\n")
    print(f"Flat accuracy:            {errata_report['flat_accuracy'] * 100:.1f}%")
    print(f"Average tree distance:    {errata_report['average_tree_distance']}")
    print(f"Expected cost per 100:    Rs. {errata_report['expected_cost_per_100']:,.2f}")
    print(f"Calibration error:        {errata_report['calibration_error']}")
    print(f"Adversarial pass rate:    {errata_report['adversarial_pass_rate'] * 100:.1f}%")
    print("\nConfusion counts:")
    for k, v in errata_report["confusion_counts"].items():
        print(f"    {k:<20} {v}")
    print("\nBase-rate simulation (if dangerous cases made up X% of the traffic):")
    for rate, acc in errata_report["base_rate_curve"]:
        print(f"    {rate*100:>5.0f}% dangerous  ->  {acc*100:.1f}% flat accuracy")

    print("\n" + "=" * 72)
    print("NOTE: flat_accuracy alone looks fine here, but the report shows")
    print("EXACTLY where the real risk is hiding -- case 20 was a missed")
    print("fraud case (worst possible mistake), and case 21 shows the model")
    print("can be fooled by an adversarial input. Neither of those would")
    print("show up if this only reported the flat accuracy number.")
    print("=" * 72)
