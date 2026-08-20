# Probability Decision Record

**Project:** Vendor Payment Fraud Triage Agent (evaluated using Errata)
**Prepared by:** Arif Hussain
**Created:** 20 August 2026
**Last verified/corrected:** 22 August 2026 — see the note at the end of this document. All calculations in this file were independently recomputed from scratch; two numeric errors were found and corrected below, and are marked where they occurred rather than silently fixed.

**Work timeline (by stage):**

| Stage | Content | Date worked |
|---|---|---|
| 1–4 | Problem statement, hidden states/priors, evidence/likelihood tables, worked Bayes update | 17 August 2026 |
| 5 | Entropy (before/after evidence) | 18 August 2026 |
| 6 | Information gain — comparing evidence sources | 19 August 2026 |
| 7 | Cost-based decision policy and thresholds (incl. 20 Aug threshold refinement) | 20 August 2026 |
| 8 | Policy evaluation design AND executed simulation (see §11.6 — simulation was run, not just designed) | 20–21 August 2026 |
| — | Recheck of §7.4 refinement, §11, and a reliability audit of the simulation script (bug found and fixed — see §11.6) | 21 August 2026 |
| — | Independent full recomputation / correction pass (original Stages 1–7 content) | 22 August 2026 |

---

## 1. Problem Statement
*Stage 1 — 17 August 2026*

> The agent observes the email requesting a bank-account change — sender address, SPF/DKIM result, message content, and whether this account has been used before. It must select **pay / verify by calling the supplier / hold and escalate to a human** because whether this request genuinely came from the real supplier or from an attacker is not known.

This is a real, current, well-documented problem. The FBI's IC3 reported **$3.05 billion in verified Business Email Compromise (BEC) losses in 2025 alone** (24,768 complaints, ~$123,000 average loss per incident), and **60% of all BEC scams specifically impersonate vendors/suppliers** — the exact scenario modeled here. Real, named cases include Google and Facebook losing a combined $121 million to a fake-vendor scheme, and the City of Baltimore losing $1.52 million when an attacker inserted new bank details into an active, trusted email thread.

---

## 2. The Belief-State Table
*Stage 2 — 17 August 2026*

### 2.1 Hidden States and Priors

| Hidden state | Prior | Source |
|---|---|---|
| Genuine | 0.85 | Assumption — most vendor correspondence is legitimate; exact company-level BEC rates are not public |
| Compromised (real mailbox hacked) | 0.06 | Assumption, informed by BEC literature naming this as a top attack mechanism |
| Impersonation (lookalike domain) | 0.06 | Assumption, informed by BEC literature naming this as a top attack mechanism |
| Insider / malicious collusion | 0.02 | Assumption — rarer mechanism in named case reporting (e.g. Google/Facebook, Baltimore were both external) |
| Something else (residual) | 0.01 | Residual state — covers cases not on this list (e.g. a genuine new vendor with no prior history) |

**Sum: 0.85 + 0.06 + 0.06 + 0.02 + 0.01 = 1.00 ✅** *(independently reconfirmed 22 Aug 2026)*

All numbers above are **hypothetical / assumed**, not measured from real company data, and are labeled as such per course requirements.

---

## 3. Evidence Sources and Likelihood Tables
*Stage 3 — 17 August 2026*

Three evidence sources were compared. For each, the likelihood table states: *"if this hidden state were true, how often would this evidence appear?"*

### Evidence 1 — Is the requested bank account new (never used before)?

| Hidden state | P(new account) | P(known account) |
|---|---|---|
| Genuine | 0.05 | 0.95 |
| Compromised | 0.90 | 0.10 |
| Impersonation | 0.90 | 0.10 |
| Insider | 0.90 | 0.10 |
| Something else | 0.50 | 0.50 |

*Reasoning: genuine bank changes are rare and typically go through predefined approval/verbal channels rather than appearing as a brand-new account via email alone — revised from an initial estimate of 0.25 to 0.05 after reconsidering how strict real account-manager verification processes typically are. All three fraud mechanisms redirect money to an account the attacker controls, so a new account appears in the large majority of fraud cases.*

**Cost: ~₹0 (internal database lookup). Time: milliseconds.**
**Known failure mode: a genuine but rare backup-account switch would also appear "new," producing a false alarm.**

### Evidence 2 — Does the sender's domain mismatch the real supplier's known domain?

| Hidden state | P(mismatch) | P(exact match) |
|---|---|---|
| Genuine | 0.00 | 1.00 |
| Compromised | 0.00 | 1.00 |
| Impersonation | 0.90 | 0.10 |
| Insider | 0.50 | 0.50 |
| Something else | 0.50 | 0.50 |

*Correction, 22 Aug 2026: this table originally omitted the "Something else" row entirely — only four of the five hidden states had a stated likelihood. It has been added here (0.50/0.50, consistent with how "Something else" is treated as an uninformative unknown in the other two evidence tables) so the full-precision recomputation below is well-defined and reproducible.*

*Reasoning: Compromised means the attacker is genuinely inside the real mailbox, so the domain is, by definition, the real domain — this check structurally cannot catch a mailbox compromise. This matches documented industry findings that "BEC attacks often pass SPF/DKIM/DMARC checks because those protocols validate sending infrastructure, not human intent." Insider is split 50/50 because two distinct sub-mechanisms exist: the insider may email from their own (matching) company domain, or may route through a colluding external ("phantom vendor") entity, which would mismatch.*

**Cost: ~₹0 (automated string comparison). Time: milliseconds.**
**Known failure mode: cannot detect mailbox compromise at all (0.00 likelihood) — this is a structural blind spot, not a tuning issue.**

### Evidence 3 — Does the supplier confirm the request by phone (calling the number already on file, not the number in the email)?

| Hidden state | P(confirms) | P(denies) |
|---|---|---|
| Genuine | 0.90 | 0.10 |
| Compromised | 0.05 | 0.95 |
| Impersonation | 0.00 | 1.00 |
| Insider | 0.00 | 1.00 |
| Something else | 0.50 | 0.50 |

*Reasoning: calling the number already on file (not any number in the suspicious email) reaches the real, legitimate supplier in every non-genuine case, since only the email channel — not the phone channel — is assumed compromised in this model. A stated limitation: a sufficiently sophisticated attacker who also compromises the phone channel would defeat this check; that scenario is explicitly out of scope here to keep the hidden-state list simple.*

**Cost: ~₹300 (estimated analyst time, not a telecom charge — roughly 30 minutes of a finance analyst's paid time, an opportunity cost). Time: ~30 minutes.**
**Known failure mode: unreachable supplier, or (rarely) a compromised phone channel not modeled here.**

---

## 4. One Full Worked Bayes Update (Evidence 1: "new account" observed)
*Stage 4 — 17 August 2026*

### Step 1 — Prior × Likelihood

| State | Prior | Likelihood (new) | Prior × Likelihood |
|---|---|---|---|
| Genuine | 0.85 | 0.05 | 0.0425 |
| Compromised | 0.06 | 0.90 | 0.0540 |
| Impersonation | 0.06 | 0.90 | 0.0540 |
| Insider | 0.02 | 0.90 | 0.0180 |
| Something else | 0.01 | 0.50 | 0.0050 |

### Step 2 — Total (denominator)

$$P(\text{new account}) = 0.0425 + 0.0540 + 0.0540 + 0.0180 + 0.0050 = 0.1735$$

### Step 3 — Posterior (divide each row by the total)

| State | Posterior |
|---|---|
| Genuine | 0.0425 ÷ 0.1735 = **0.245** |
| Compromised | 0.0540 ÷ 0.1735 = **0.311** |
| Impersonation | 0.0540 ÷ 0.1735 = **0.311** |
| Insider | 0.0180 ÷ 0.1735 = **0.104** |
| Something else | 0.0050 ÷ 0.1735 = **0.029** |

**Check: 0.245 + 0.311 + 0.311 + 0.104 + 0.029 = 1.000 ✅** *(independently reconfirmed 22 Aug 2026 — exact: 0.99999... ≈ 1)*

**Interpretation:** a single piece of evidence — an unfamiliar bank account — was enough to flip belief from confidently genuine (85%) to genuinely uncertain (combined fraud probability rising from 15% to **75.5%**).

> **Correction, 22 Aug 2026:** this figure was originally stated as 65.5%. Recomputing directly from the posteriors above — 0.311 + 0.311 + 0.104 + 0.029 = 0.755 — the correct combined fraud probability is **75.5%**, not 65.5%. This was a simple arithmetic slip when this section was first written; it does not change the eventual decision (75.5% still falls in the "verify" zone defined in Section 7, well below the 90% escalation threshold), but the number itself needed correcting.

---

## 5. Entropy Before and After
*Stage 5 — 18 August 2026*

$$H = -\sum p_i \log_2(p_i)$$

- **Entropy before evidence (prior):** 0.866 bits
- **Entropy after evidence (posterior):** 2.032 bits

*(Both values independently recomputed 22 Aug 2026 — confirmed correct to three decimal places.)*

**Finding — confusion increased, not decreased.** This runs counter to the common assumption that evidence always reduces uncertainty. Here, the evidence invalidated the dominant hypothesis (Genuine) without clearly favoring any single alternative — Genuine, Compromised, and Impersonation ended up nearly tied (24.5% / 31.1% / 31.1%). This is a genuine, non-trivial finding: the agent went from "confident" to "confused but alert," which is itself valuable information, even though the raw entropy number went up.

---

## 6. Information Selection — Comparing the Three Evidence Sources
*Stage 6 — 19 August 2026*

For each evidence source, expected information gain was computed as $$IG = H(\text{prior}) - H(S|E)$$, where $$H(S|E)$$ is the probability-weighted average entropy across both possible outcomes of that evidence source (the "honest average" — not the entropy of just one outcome).

| Evidence | Expected Info Gain | Cost | Time | Notes |
|---|---|---|---|---|
| E1: Bank account new? | 0.347 bits | ~₹0 | ms | Cannot distinguish which fraud type |
| E2: Domain mismatch? | 0.304 bits | ~₹0 | ms | Cannot detect mailbox compromise at all |
| E3: Phone callback | 0.347 bits | ₹300 | ~30 min | Strongest single check tied with E1, but not free |

> **Correction, 22 Aug 2026:** E2's expected information gain was originally stated as 0.611 bits, with the accompanying claim that "E2 carries the most information of the three." Both were wrong. When independently recomputed — properly weighting *both* outcomes (mismatch **and** exact-match), the same way E1 and E3 were computed — the correct value is **0.304 bits**, making E2 the *weakest* of the three, not the strongest. The error traced back to the "exact match" outcome's entropy having been copied over from Evidence 1's corresponding calculation instead of computed fresh from Evidence 2's own likelihood table — the two evidence sources have different likelihoods, so their entropies are genuinely different (0.532 bits for E2's match outcome, not 0.202 bits). The full recomputation: P(mismatch) = 0.069, H(posterior|mismatch) = 0.955 bits; P(match) = 0.931, H(posterior|match) = 0.532 bits; H(S|E2) = (0.069×0.955)+(0.931×0.532) = 0.562 bits; IG2 = 0.866 − 0.562 = 0.304 bits.

**What this table actually shows, corrected:** E1 and E2 are both free and should always be run regardless of their relative information value. **E1 and E3 are tied as the strongest single checks (0.347 bits each)** — not E2. E2, despite structurally being unable to catch mailbox compromise at all (0.00 likelihood for Compromised), still carries real information because it's highly diagnostic for Impersonation specifically — just less, overall, than the other two. E3 is the only check capable of directly asking the real supplier, making it the appropriate second-stage check when E1/E2 leave belief in the uncertain middle zone.

**Policy implication:** run E1 and E2 first (free, instant, and complementary — E1 catches most fraud types, E2 specifically strengthens the Impersonation signal). Only pay for E3 if the resulting belief still sits between the two decision thresholds derived below.

---

## 7. Decision Policy and Thresholds
*Stage 7 — 20 August 2026 (threshold refined same day, see §7.4)*

### 7.1 Costs

| Error type | Cost | Reasoning |
|---|---|---|
| False Positive (wrongly hold/verify a genuine request) | ₹2,000 | Delay, supplier annoyance, staff time — illustrative, consistent with course brief's own worked example |
| False Negative (wrongly pay an actual fraud) | ₹8,00,000 | The payment, mostly unrecoverable — illustrative, consistent with course brief's own worked example |

### 7.2 Derived Threshold ($$p_{low}$$)

$$p^* = \frac{C_{FP}}{C_{FP} + C_{FN}} = \frac{2{,}000}{2{,}000 + 8{,}00{,}000} = 0.00249 \approx 0.25\%$$

*(Independently recomputed 22 Aug 2026: exact value is 0.2494%, which rounds to 0.25% as originally stated — confirmed correct.)*

This is markedly lower than an intuitive round number like 50% or 80% — a direct consequence of the 400x cost asymmetry between the two error types.

### 7.3 Three-Zone Policy

| Zone | Belief range | Action |
|---|---|---|
| Low risk | 0% – 0.25% | **Pay** automatically — risk too small to justify the ₹300 verification cost |
| Uncertain | 0.25% – 90% | **Verify** — call the supplier on the number already on file |
| High risk | Above 90% | **Hold and escalate** to a human — risk too high to rely on any single check, even the phone callback (which itself carries a residual ~5% false-confirm rate under Compromised) |

**Stop rule:** the agent stops gathering further evidence and acts as soon as (a) no remaining check could change the action, (b) the belief has moved outside the uncertain zone, or (c) the next-best evidence's cost exceeds its expected benefit.

### 7.4 Threshold Refinement — Accounting for Imperfect Verification

> **Update, 20 August 2026.** The p_low derivation in §7.2 above is not silently changed — it is kept as originally written, and this section adds a more precise refinement next to it, so the reasoning trail stays auditable.

**The problem with the §7.2 formula.** $$p^* = \frac{C_{FP}}{C_{FP}+C_{FN}}$$ is the correct break-even formula **only when there are exactly two actions** being compared. It silently assumes that stepping off the "Pay" path removes all fraud risk. But this agent has **three** actions — Pay / Verify / Escalate — and Verify is not free and not perfect: Evidence 3's own likelihood table (§3) already states a phone callback still gets fooled **5% of the time when the true state is Compromised**, and is uninformative (50/50) under "Something else."

**Step 1 — the correct three-action comparison for the Pay/Verify boundary.**

$$EC(\text{Pay}) = p \cdot L \qquad EC(\text{Verify}) = C_V + p \cdot r \cdot L$$

where $$r$$ = the probability that verification still fails to catch a fraud that is actually present.

**Step 2 — deriving $$r$$**, weighted by how the fraud mechanisms split the 15% prior fraud mass:

| Fraud state | Share of prior fraud | P(verify wrongly confirms \| state) |
|---|---|---|
| Compromised | 0.06÷0.15 = 0.400 | 0.05 |
| Impersonation | 0.06÷0.15 = 0.400 | 0.00 |
| Insider | 0.02÷0.15 = 0.133 | 0.00 |
| Something else | 0.01÷0.15 = 0.067 | 0.50 |

$$r = 0.400(0.05)+0.400(0.00)+0.133(0.00)+0.067(0.50) = 0.0533 \approx 5.33\%$$

**Step 3 — solve for the refined threshold:**

$$p_{low}^{\,refined} = \frac{C_V}{L(1-r)} = \frac{300}{8{,}00{,}000 \times 0.9467} = 0.000396 \approx 0.040\%$$

**Verification of the crossover:** $$EC(\text{Pay}) = 0.000396 \times 800{,}000 = ₹316.90$$; $$EC(\text{Verify}) = 300 + (0.000396 \times 0.0533 \times 800{,}000) = ₹316.90$$ ✅ *(independently reconfirmed 21 Aug 2026 — see the Verification Note below)*

**Step 4 — comparison table:**

| | §7.2 (original, two-action) | §7.4 (refined, three-action) |
|---|---|---|
| p_low | 0.25% | **0.04%** (≈6.3x lower) |
| Formula basis | $$C_{FP}/(C_{FP}+C_{FN})$$ | $$C_V/(L(1-r))$$ |

The refined threshold moves in the direction of caution: because verification is cheap relative to the loss it protects against, the agent should stop paying outright at a much lower fraud probability than 0.25% suggested. Neither number changes the Section 9 decision (75.5% sits deep in "Verify" either way).

**What is deliberately left unresolved — p_high.** p_high = 90% remains a **risk-tolerance policy choice**, not a cost-derived value, because no explicit escalation cost is stated in this document. See the limitation in §10.

**A second threshold this refinement makes necessary — P_STAR.** Once Verify has already happened (E3 collected), Verify is no longer an available action and its cost is sunk. The remaining choice is a plain **two-action** comparison (Pay vs. Escalate), which is exactly what §7.2's original, unrefined formula was built for:

$$P_{STAR} = \frac{C_{FP}}{C_{FP}+C_{FN}} = 0.2494\% \quad (\text{same value as §7.2 — reused for a different moment, not re-derived})$$

$$\text{final fraud probability} < P_{STAR} \Rightarrow \text{Pay} \qquad \text{final fraud probability} \geq P_{STAR} \Rightarrow \text{Escalate}$$

This distinction — P_LOW (§7.4) governs the pre-verification Pay/Verify/Escalate choice; P_STAR (§7.2, reused) governs the post-verification Pay/Escalate choice once Verify's cost is sunk — was a genuine correction made during Stage 8 simulation development. An earlier draft of the simulation code mistakenly reused P_LOW for the post-verification decision too; this was caught via a verbose single-case trace before it could distort batch results (see §11.6).

---

## 8. The Umbrella Problem (Section 16, mandatory)

A 35% chance of rain tomorrow. Should an umbrella be carried?

| | Case A: normal walk | Case B: important wedding |
|---|---|---|
| Cost of carrying, no rain | ₹20 | ₹20 |
| Cost of carrying, rain | ₹20 | ₹20 |
| Cost of not carrying, no rain | ₹0 | ₹0 |
| Cost of not carrying, rain | ₹200 | ₹1,000 |
| **Break-even rain probability** | 20 ÷ 200 = **10%** | 20 ÷ 1,000 = **2%** |
| **Decision at 35% rain** | Carry | Carry (far more decisively) |

*(Both break-even values independently reconfirmed 22 Aug 2026.)*

**The point:** the forecast (35%) never changed between the two cases — only the cost ratio did. This is the exact same equation as the fraud threshold above: $$p^* = \frac{\text{cost of caution}}{\text{cost of caution} + \text{cost of harm}}$$. A wedding outfit costing 5x more than a soaked walk pushes the break-even point from 10% down to 2%, precisely mirroring how a fraud payment costing 400x more than a delayed genuine payment pushes the agent's threshold down to 0.25%.

---

## 9. Selected Case — Full Decision Record

| Item | Information |
|---|---|
| **Evidence** | Bank account requested is new (never used before) |
| **Hidden states** | Genuine, Compromised, Impersonation, Insider, Something else |
| **Beliefs (prior)** | 0.85 / 0.06 / 0.06 / 0.02 / 0.01 |
| **Beliefs (posterior)** | 0.245 / 0.311 / 0.311 / 0.104 / 0.029 |
| **Event of interest** | Combined fraud probability (not-Genuine) — **75.5%** *(corrected from 65.5%, see Section 4)* |
| **Actions available** | Pay / Verify (phone callback) / Hold and escalate |
| **Costs** | False positive ₹2,000; false negative ₹8,00,000 |
| **Policy** | Three-zone threshold policy — p_low = 0.25% (§7.2, two-action) / **0.040%** (§7.4, refined three-action); p_high = 90% (policy choice); **P_STAR = 0.2494%** (§7.4, post-verification Pay-vs-Escalate) |
| **Decision** | Combined fraud belief (75.5%) falls in the "uncertain" zone under both versions of p_low → **Verify** (phone callback). The §7.4 refinement does not change this specific decision. |
| **Audit data** | Prepared as part of Week 1/2 AI-Native deliverable; all numbers hypothetical/assumed and labeled as such; policy version 1.3 (threshold refined + simulation executed + reliability-audited, see §7.4, §11) |

---

## 10. Limitations, Stated Honestly

- All priors and costs are **hypothetical assumptions**, not measured from real company data.
- The phone-callback likelihood table assumes only the email channel is compromised, never the phone channel — a real, sophisticated attacker who also compromises the phone line would defeat this check. This is a stated, intentional simplification.
- Evidence 1 and Evidence 3 are both weak at distinguishing *which* fraud mechanism is occurring (Compromised vs. Impersonation vs. Insider) — they are good at "genuine vs. not," but not at classifying the specific fraud type.
- The base rates (priors) are not sourced from this company's actual historical data; a real deployment would require this to be measured, not assumed.
- **p_high (90%) is not yet cost-derived** (added 20 Aug, see §7.4). It should be treated as a risk-tolerance policy choice until an explicit escalation cost is estimated.
- **P_STAR (§7.4) is a fixed cost-ratio number** that does not adapt to base rate or verification quality. The Stage 8 simulation (§11) found this concretely: at a 40% fraud base rate, or at a 20% verification miss rate, even a genuine case with the best possible evidence still computes a final fraud probability above P_STAR's fixed threshold, causing near-universal false-positive escalation in those regimes. This is a genuine, simulation-confirmed limitation, not a hypothetical one — see §11.4.

---

## 11. Stage 8 — Policy Evaluation, Simulation, and Failure Analysis
*Stage 8 — 20 August 2026 (designed) → 21 August 2026 (executed and reliability-audited)*

### 11.1 Why accuracy alone is the wrong metric here

Fraud is a rare-event problem (15% prior, §2.1). A policy that simply approved every payment would score high raw accuracy while providing zero fraud protection — the classic **accuracy paradox**. The confusion-matrix framing that matters instead (Positive = Fraud):

$$\text{Recall} = \frac{TP}{TP+FN} \qquad \text{Precision} = \frac{TP}{TP+FP}$$

Recall matters more than precision here, given the 400:1 cost ratio between a missed fraud and a wrongly-delayed genuine payment (§7.1).

### 11.2 Total Expected Cost — the metric that actually decides between policies

$$\text{Total Expected Cost} = \sum_{\text{cases}} \big[\, \mathbb{1}(\text{FN}) C_{FN} + \mathbb{1}(\text{FP}) C_{FP} + \text{action cost incurred} \,\big]$$

### 11.3 The simulation

A synthetic-case engine was built (`fraud_triage_simulation.py`): for each case, a true hidden state is drawn from the §2.1 priors, evidence is drawn from the §3 likelihood tables conditioned on that true state, a real Bayesian update is run (Section 4's exact method), the §7.4/§7.2 policy is applied, and the resulting action is graded against the (only-now-revealed) true state to tally a confusion matrix and Total Expected Cost.

**n = 1,000 baseline result:** TP=148, FN=1, FP=124, TN=727 → Recall 99.33%, Precision 54.41%, Total Expected Cost ₹13,28,500.

### 11.4 Stress-test scenarios — executed, not just designed

| # | Scenario | Result |
|---|---|---|
| 1 | Base-rate sensitivity (2% / 15% / 40% fraud) | At 40% fraud, precision collapses to ~40% — confirmed by hand: a best-case genuine evidence combination still computes final fraud probability ≈0.80%, above P_STAR's fixed 0.2494% |
| 2 | Cost-structure sensitivity (payment size, verification cost) | Both P_LOW and P_STAR scale correctly with cost inputs, as §7.4's formulas predict |
| 3 | Verification-effectiveness sensitivity (5%/20%/1% miss rate) | At 20% miss rate, precision collapses to ~13% — confirmed by hand: best-case genuine evidence still computes final fraud probability ≈0.336%, above P_STAR |
| 4 | Threshold-boundary robustness | Clean transitions at both P_LOW and P_HIGH, no discontinuity bugs |
| 5 | Adversarial gaming (attacker defeats E1+E2) | Recall drops from 99.33% to a measurably lower value; Total Expected Cost rises substantially — confirms evidence diversity matters, not just threshold math |

**Genuine finding, not a bug (independently hand-verified twice — once during initial development, once during a later reliability audit):** Scenarios 1 and 3 both expose the same underlying gap from different angles — P_STAR is a fixed cost-ratio number that does not adapt to base rate or evidence quality, unlike P_LOW (refined in §7.4 via `r`). This is now recorded as a limitation in §10.

### 11.5 A real reliability bug found and fixed during this stage (21 August 2026)

Two genuine issues were caught and corrected while building and then auditing this simulation — recorded here rather than silently fixed, per this document's own convention:

1. **Threshold bug (caught during initial development, 20 Aug):** the post-verification Pay-vs-Escalate decision was initially coded to reuse P_LOW (the pre-verification, three-action threshold) instead of P_STAR (the correct post-verification, two-action threshold). This was caught via a verbose single-case trace before it could distort batch results — see §7.4's explanation of why these are different thresholds for different moments.
2. **Random-state fragility (caught during a later reliability audit, 21 Aug):** the simulation initially drew all random numbers from Python's shared *global* `random` module. This meant the exact reported batch numbers were only reproducible if the verbose demo cases ran before the main batch (both drew from the same shared stream) — an undocumented, fragile coupling. **Fix:** every batch now uses its own dedicated `random.Random(seed)` instance, verified immune to unrelated random calls elsewhere in the script. This changed the exact reported counts slightly (e.g. FP moved from 122 to 124 out of 1,000) — a shift in which specific random numbers get drawn, not a change to the underlying math or policy, and well within normal sampling variation.

### 11.6 Status

The Stage 8 simulation has been **built and executed**, not merely designed. Full console output and the isolated-RNG-fixed script are kept alongside this document (see `experiments/stage8-fraud-triage-simulation/` in the repo). Re-running with a different seed will shift individual counts slightly; the proportions and the two genuine findings in §11.4 reproduce consistently at n=1,000.

---

## Verification Note — 21 August 2026

A full reliability audit was run on the 20 Aug additions (§7.4, §11) and the accompanying simulation script:

- **§7.4's numbers were independently re-derived from scratch** (not just re-read): r=5.33%, P_LOW=0.0396%, and the crossover verification (EC(Pay)=EC(Verify)=₹316.90 at p_low_refined) all recomputed correctly.
- **Every entropy/information-gain figure and the §7.2 threshold were independently recomputed** using fresh code, cross-checked against the document's stated values — all passed exactly.
- **Two real issues were found in the simulation script and fixed** (see §11.5 for full detail): a threshold bug (P_LOW wrongly reused post-verification instead of P_STAR) and a random-state fragility bug (batches depended on unrelated code running first). Both are now corrected; the fixed script's numbers are what's reported in §11.3–11.4.
- **§11.6's status was found stale and corrected**: an earlier version of this section stated the simulation "has not yet been executed," written when §11 was first drafted as a design. By 21 Aug the simulation had, in fact, been built and run — that stale claim has been corrected here rather than left standing.

---

## Verification Note — 22 August 2026

This document was first prepared on 20 August 2026. On 22 August 2026, every calculation in this file was independently recomputed from first principles (not just re-read) to check the reasoning was sound. Two genuine numeric errors were found and are corrected in place above, not silently edited:

1. **Evidence 2's expected information gain was wrong** (stated as 0.611 bits; the correct value is 0.304 bits), and the accompanying claim that "E2 carries the most information of the three" was consequently also wrong — E1 and E3 are actually tied as the strongest checks. The root cause was reusing an entropy value computed for a different evidence source's outcome instead of computing E2's own "exact match" outcome fresh.
2. **The combined posterior fraud probability was mis-added** (stated as 65.5%; the correct sum of the four non-Genuine posteriors is 75.5%).

Neither error changes the final decision reached in Section 9 (Verify), but both were real errors in the stated numbers and needed correcting rather than left as-is. One documentation gap was also fixed: Evidence 2's likelihood table was missing its "Something else" row, now added. Everything else in this document — the Bayes update in Section 4, the entropy values in Section 5, the threshold derivation in Section 7, and the umbrella problem in Section 8 — was independently reconfirmed as correct.
