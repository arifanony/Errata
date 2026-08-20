# Stage 8 Simulation — Results Summary (Reliability-Audited Run)

**Project:** Vendor Payment Fraud Triage Agent (Errata base model)
**Script:** `fraud_triage_simulation.py` (v2 — reliability-audited, isolated-RNG version)
**Run date:** 21 August 2026
**Seed:** each batch uses its own dedicated, isolated seed (42 for baseline; 101–103, 201–203, 301–303, 401 for the stress-test scenarios) — see script header for the reliability fix that makes this isolation real, not just labeled.

---

## What changed from the first run

An earlier version of this script drew all randomness from Python's shared *global* `random` module. That meant the exact reported numbers only reproduced correctly if the verbose demo cases ran **before** the main batch — an undocumented, fragile dependency. This was caught during a reliability audit (21 Aug) and fixed: every batch now uses its own `random.Random(seed)` instance, verified immune to unrelated random calls elsewhere in the script. The batch counts below shifted slightly from the first run as a result (e.g. baseline FP moved from 122 → 124) — this is a change in *which* random numbers got drawn, not a change to the underlying math, policy, or thresholds. Full detail in the decision record's §11.5.

---

## 1. Sanity check

The Bayes-update engine was checked against the decision record's own §4 worked example before any batch was trusted:

| State | Document's posterior | Script's posterior |
|---|---|---|
| Genuine | 0.245 | 0.245 |
| Compromised | 0.311 | 0.311 |
| Impersonation | 0.311 | 0.311 |
| Insider | 0.104 | 0.104 |
| Something else | 0.029 | 0.029 |

Exact match. Core mechanics confirmed correct before trusting any random simulation logic.

---

## 2. Main batch — n = 1,000, document's actual numbers

| Metric | Value |
|---|---|
| True state distribution | Genuine=851, Compromised=62, Impersonation=59, Insider=18, Something else=10 |
| Expected Genuine (0.85×1000) | 850 — actual 851 ✅ |
| E1 fired on Genuine cases (5% expected) | 47 actual vs. 42.6 expected ✅ |
| **Confusion matrix** | TP=148, FN=1, FP=124, TN=727 |
| **Recall** | 99.33% |
| **Precision** | 54.41% |
| **Accuracy** (flagged misleading, §11.1) | 87.50% |
| Verification used | 935/1000 (93.5%) |
| **Total Expected Cost** | **₹13,28,500** |

**Reliability proof included in this run:** the same batch (seed=42) was re-run immediately after deliberately burning 500 unrelated global `random.random()` calls. Result: **identical** confusion matrix and cost — confirming the isolation fix genuinely holds, not just in theory.

---

## 3. Stress-test scenarios (§11.4)

### Scenario 1 — Base-rate sensitivity

| Fraud rate | Recall | Precision | Total Cost |
|---|---|---|---|
| 2% (rare) | 100.00% | 8.97% | ₹5,82,200 |
| 15% (baseline) | 98.09% | 58.56% | ₹28,99,100 |
| 40% (high) | 100.00% | **42.00%** | ₹14,03,900 |

**Genuine finding, independently hand-verified twice:** at 40% fraud, every single Genuine case in this batch (580/580) was escalated — confirmed by hand that even a best-case genuine evidence combination (known account, matching domain, supplier confirms) computes a final fraud probability of ≈0.80%, above P_STAR's fixed 0.2494% threshold.

### Scenario 2 — Cost-structure sensitivity

| Scenario | p_low | p_star | Recall | Precision | Total Cost |
|---|---|---|---|---|---|
| Baseline (L=₹8,00,000, C_V=₹300) | 0.0396% | 0.2494% | 99.36% | 58.43% | ₹13,02,200 |
| Smaller payment (L=₹80,000) | 0.3961% | 2.4390% | 98.61% | 51.82% | ₹7,01,200 |
| Expensive verification (C_V=₹1,500) | 0.1981% | 0.2494% | 98.67% | 55.22% | ₹32,48,500 |

Both thresholds scale correctly with the cost inputs — a smaller payment loosens both thresholds, expensive verification raises p_low while p_star (which doesn't depend on C_V) stays fixed.

### Scenario 3 — Verification-effectiveness sensitivity

| Compromised miss rate | r (weighted) | p_low | Recall | Precision | Total Cost |
|---|---|---|---|---|---|
| 5% (baseline) | 5.33% | 0.0396% | 100.00% | 50.00% | ₹5,51,400 |
| 20% (unreliable) | 11.33% | 0.0423% | 100.00% | **13.50%** | ₹20,09,900 |
| 1% (very reliable) | 3.73% | 0.0390% | 99.37% | 56.03% | ₹13,27,000 |

**Genuine finding, independently hand-verified twice:** at 20% Compromised miss rate, all 865 Genuine cases in this batch were escalated (TN=0). Confirmed by hand that a best-case genuine evidence combination still computes ≈0.336% final fraud probability — above the fixed 0.2494% P_STAR.

**Same underlying gap, two different triggers:** Scenarios 1 and 3 independently expose that **P_STAR is a fixed cost-ratio number that does not adapt to base rate or evidence quality** — unlike P_LOW, which §7.4 already adjusts via `r`. This is now recorded as a limitation in the decision record's §10.

### Scenario 4 — Threshold-boundary robustness

```
Around P_LOW (0.0396%):
  0.03860% → Pay
  0.03960% → Verify
  0.04060% → Verify
Around P_HIGH (90.0%):
  89.900% → Verify
  90.000% → Escalate
  90.100% → Escalate
```
Clean transitions at both boundaries — no implementation bugs at the crossover points.

### Scenario 5 — Adversarial gaming

| | Baseline (no gaming) | Gaming (attacker defeats E1+E2) |
|---|---|---|
| Recall | 99.33% | **95.14%** |
| Total Cost | ₹13,28,500 | ₹61,36,000 |

A fraudster deliberately using an already-known account and a domain-matching setup to defeat E1 and E2 measurably reduces recall and roughly **4.6x's** the Total Expected Cost — confirming evidence diversity and drift-monitoring matter (§11.5 of the decision record), not just the threshold math alone.

---

## 4. Overall assessment

**✅ Reliable:**
- Bayes engine independently matches the decision record's own hand-worked example exactly.
- Batch proportions match expected values within normal sampling variation.
- **Deterministic and now genuinely isolated** — proven immune to unrelated code execution order, unlike the first version of this script.
- Threshold-boundary test shows no implementation bugs at exact crossover points.

**🔍 Two genuine findings, confirmed twice independently:**
- P_STAR (a fixed cost-ratio threshold) does not adapt to base rate or evidence quality shifts, unlike P_LOW. Both Scenario 1 (base-rate) and Scenario 3 (verification effectiveness) expose this same gap from different angles — this is a real, useful discovery, not a coincidence or a bug.

**⚠️ Known limitation, stated honestly:**
- Individual batch numbers carry normal sampling noise between runs (e.g. Scenario 2's baseline shows FN=1 while Scenario 3's baseline shows FN=0, despite both being "baseline" 15%-fraud draws) — each is an independent 1,000-case sample from the same underlying policy, not a sign of inconsistency in the policy itself. Averaging across multiple seeds would produce tighter, more defensible numbers if pursued further — noted as optional future work.
