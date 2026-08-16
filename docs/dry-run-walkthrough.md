# Errata — Dry Run Walkthrough

**Before writing the real application, this is proof that the actual idea works.**

*One case traced by hand, then a small batch run through the real scoring logic — with actual computed numbers, not hypothetical ones.*

Arif Hussain · 16 August 2026

---

## What a "dry run" actually means here

Before building the real thing (a working LLM agent + a full application around it), I wanted to prove the *idea itself* holds up — that the scoring logic described in `docs/pseudocode.md` actually produces something useful, using real math on real (if hand-picked) data.

There is **no real model anywhere in this dry run.** Every "prediction" below is mocked by hand — standing in for what a real classifier or LLM agent would eventually output. What's real is everything *after* that: the tree-distance function, the cost calculation, the calibration check, the confusion-matrix sorting. All of that is the actual logic from the pseudocode, not a placeholder.

## Part 1 — One case, traced by hand

Take **case #20** from the test set. Here's exactly what happens to it, step by step, matching the pseudocode:

| Step | What happens to this one case |
|---|---|
| **1. Hidden test set** | True label: `fraud`. This is known to the test harness, but hidden from the model. |
| **2. Model predicts, blind** | The model looks at the email content and predicts: `safe`, with 91% confidence. |
| **3. Adapter layer** | The model already returned a clean label + confidence, so nothing needs converting — it passes straight through as `{predicted_label: "safe", confidence: 0.91}`. |
| **4. Reveal the real answer** | The true label (`fraud`) is now unlocked and attached to this case for comparison. |
| **5. Compare** | Predicted branch: `safe`. True branch: `dangerous` (fraud sits under the dangerous branch). Since the model said safe but the truth was dangerous, this is scored as **"missed it"** — a false negative. |
| **6a. Flat score** | This one case counts as one wrong answer, same as any other wrong answer — no severity information yet. |
| **6b. Tree distance** | Walking from `fraud` up to the common ancestor with `safe`: `fraud → dangerous → root`, `safe → root`. Distance = 3. This is the *worst possible kind of mistake* — a rare dangerous case slipping all the way through to "safe." |
| **6c. Cost** | A "missed it" result carries the illustrative cost of ₹10,00,000 in this dry run's cost matrix. One case alone adds ₹10,00,000 to the total. |
| **6d. Calibration** | The model was 91% confident **and wrong.** This case pulls down the calibration score for the 90–100% confidence bucket — a textbook example of "confidently wrong." |

That's the entire pipeline, on one case. Now scale that same logic across a full batch.

## Part 2 — The full batch, run through the real code

The batch: 22 cases total — 16 safe, 1 suspicious, 3 specific dangerous types (phishing/malware/fraud), and 2 of those dangerous cases deliberately marked as **adversarial** test cases. All predictions are hand-mocked (see `dry_run_demo.py` in this repo for the exact code and data).

### Case-by-case trace (actual script output)

```
 id  true label   predicted     conf  result             tree dist
------------------------------------------------------------------------
  1  safe         safe         0.92  correctly ignored  0
  2  safe         safe         0.88  correctly ignored  0
  3  safe         safe         0.95  correctly ignored  0
  4  safe         safe         0.60  correctly ignored  0
  5  safe         safe         0.99  correctly ignored  0
  6  safe         safe         0.91  correctly ignored  0
  7  safe         suspicious   0.55  correctly ignored  2
  8  safe         safe         0.85  correctly ignored  0
  9  safe         safe         0.93  correctly ignored  0
 10  safe         safe         0.97  correctly ignored  0
 11  safe         dangerous    0.90  false alarm        2
 12  safe         safe         0.89  correctly ignored  0
 13  safe         safe         0.94  correctly ignored  0
 14  safe         safe         0.90  correctly ignored  0
 15  safe         safe         0.96  correctly ignored  0
 16  safe         safe         0.90  correctly ignored  0
 17  suspicious   suspicious   0.70  correctly ignored  0
 18  phishing     malware      0.65  caught it          2
 19  malware      malware      0.80  caught it          0
 20  fraud        safe         0.91  missed it          3
 21  phishing     safe         0.93  missed it          3 [ADV]
 22  malware      malware      0.77  caught it          0 [ADV]
```

### The final Errata report (Step 9 output)

```
Flat accuracy:            77.3%
Average tree distance:    0.545
Expected cost per 100:    Rs. 9,091,136.36
Calibration error:        0.256
Adversarial pass rate:    50.0%

Confusion counts:
    correctly ignored    16
    false alarm          1
    caught it            3
    missed it            2

Base-rate simulation (if dangerous cases made up X% of the traffic):
        1% dangerous  ->  87.8% flat accuracy
        5% dangerous  ->  85.8% flat accuracy
       10% dangerous  ->  83.4% flat accuracy
       20% dangerous  ->  78.6% flat accuracy
       50% dangerous  ->  64.1% flat accuracy
```

## Part 3 — What this actually proves

**77.3% flat accuracy** on its own sounds mediocre but not alarming — the kind of number that might pass a quick review. The Errata report underneath it tells a very different story:

- **Two "missed it" cases** — including a real fraud case slipping through as "safe" at 91% confidence. That single mistake alone accounts for the bulk of the ₹90,91,136-per-100 expected cost figure. A flat accuracy score would never single this out.
- **Calibration error of 0.256** — meaningful evidence the model's stated confidence can't be fully trusted; it was 90%+ confident on both of the cases it got wrong.
- **Adversarial pass rate of only 50%** — one of the two deliberately tricky test cases fooled the model completely. A normal test set wouldn't have caught this at all, since these two cases were specifically designed to probe for exactly this weakness.
- **The base-rate curve** shows how much of any future "improvement" in accuracy could just be the world getting calmer (fewer dangerous cases showing up) rather than the model actually getting better — from 87.8% down to 64.1% accuracy on the exact same model, just by changing how common the dangerous case is.

None of this is visible from "77.3% accurate" alone. That's the entire point of the project.

## How to run this yourself

```bash
python dry_run_demo.py
```

No dependencies beyond the Python standard library — nothing to install, nothing to configure. The script is intentionally short and readable end to end; every section is labeled with which pseudocode step it implements.

## What comes next

This dry run only proves the *scoring logic* is sound. It does not yet include:
- A real model or LLM agent generating predictions (currently hand-mocked)
- The actual adapter layer handling real raw model output (currently bypassed, since the mocked data is already clean)
- A visual report (matplotlib charts) instead of console text

Those are the next real build steps, now that the underlying logic has been proven to work correctly on paper — and in code — before any of the harder integration work begins.
