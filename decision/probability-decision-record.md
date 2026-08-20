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
| 8 | Policy evaluation, simulation design, and failure analysis | 20 August 2026 |
| — | Independent full recomputation / correction pass | 22 August 2026 |

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

> **Update, 20 August 2026.** The p_low derivation in §7.2 above is not silently changed — it is kept as originally written, and this section adds a more precise refinement next to it, for the same reason the 22 Aug corrections elsewhere in this file are marked rather than edited away: so the reasoning trail stays auditable.

**The problem with the §7.2 formula.** $$p^* = \frac{C_{FP}}{C_{FP}+C_{FN}}$$ is the correct break-even formula **only when there are exactly two actions** being compared (here: Pay vs. an alternative that is treated as fully protective). It silently assumes that stepping off the "Pay" path removes all fraud risk. But this agent has **three** actions — Pay / Verify / Escalate — and Verify is not free and not perfect: Evidence 3's own likelihood table (§3) already states that a phone callback still gets fooled **5% of the time when the true state is Compromised**, and is uninformative (50/50) under "Something else." §7.3 even names this residual risk in words ("~5% false-confirm rate under Compromised") without actually folding it into the threshold arithmetic. That gap is fixed here.

**Step 1 — the correct three-action comparison for the Pay/Verify boundary.**

$$EC(\text{Pay}) = p \cdot L$$
$$EC(\text{Verify}) = C_V + p \cdot r \cdot L$$

where $$p$$ = posterior probability of fraud, $$L$$ = ₹8,00,000 (fraud loss if paid), $$C_V$$ = ₹300 (verification cost), and $$r$$ = the probability that verification still fails to catch a fraud that is actually present (a "false-confirm").

**Step 2 — deriving $$r$$ from the Evidence 3 table (§3), weighted by how the three fraud mechanisms actually split the 15% prior fraud mass:**

| Fraud state | Share of prior fraud (state prior ÷ 0.15) | P(verify wrongly confirms \| this state) |
|---|---|---|
| Compromised | 0.06 ÷ 0.15 = 0.400 | 0.05 |
| Impersonation | 0.06 ÷ 0.15 = 0.400 | 0.00 |
| Insider | 0.02 ÷ 0.15 = 0.133 | 0.00 |
| Something else | 0.01 ÷ 0.15 = 0.067 | 0.50 |

$$r = (0.400)(0.05) + (0.400)(0.00) + (0.133)(0.00) + (0.067)(0.50) = 0.020 + 0 + 0 + 0.033 = 0.0533 \approx 5.33\%$$

In words: averaged across the actual mix of fraud mechanisms this agent expects to see, the phone callback fails to catch real fraud about **5.33%** of the time — driven almost entirely by the "Something else" residual state (uninformative check) and, to a smaller extent, Compromised (attacker answers convincingly 5% of the time). Impersonation and Insider are caught with certainty by this check (0.00 confirm rate), consistent with §3's finding that E3 cannot be fooled by those two mechanisms.

**Step 3 — solve for the refined threshold.** Setting $$EC(\text{Pay}) = EC(\text{Verify})$$:

$$p \cdot L = C_V + p \cdot r \cdot L$$
$$p \cdot L (1-r) = C_V$$
$$p_{low}^{\,refined} = \frac{C_V}{L(1-r)} = \frac{300}{8{,}00{,}000 \times (1-0.0533)} = \frac{300}{7{,}57{,}360} = 0.000396 \approx 0.040\%$$

**Verification of the crossover** (both actions cost the same at this p): $$EC(\text{Pay}) = 0.000396 \times 800{,}000 = ₹316.90$$; $$EC(\text{Verify}) = 300 + (0.000396 \times 0.0533 \times 800{,}000) = 300 + ₹16.90 = ₹316.90$$ ✅

**Step 4 — why the refined number moves, and which direction.**

| | §7.2 (original, two-action) | §7.4 (refined, three-action) |
|---|---|---|
| p_low | 0.25% | **0.04%** |
| Formula basis | $$C_{FP}/(C_{FP}+C_{FN})$$ — treats the alternative to Pay as fully protective and priced at the ₹2,000 FP cost | $$C_V/(L(1-r))$$ — treats Verify as its own action, priced at its real ₹300 cost, discounted for its real 5.33% miss rate |
| What it's really comparing | Pay vs. an idealized single audit | Pay vs. the actual phone-callback step |

The refined threshold is roughly **6x lower** than originally stated. This is not a small rounding difference — it is a genuine correction to the policy's logic, and it moves in the direction of caution: because verification is cheap (₹300) relative to the loss it is protecting against (₹8,00,000), and it is mostly — though not perfectly — effective (94.67% catch rate overall), the agent should stop paying outright at a **much lower** fraud probability than 0.25% suggested. The original §7.2 number was not "wrong" as a two-action formula, but it was the wrong formula for a three-action policy — it happened to still land in a sensible place only because 0.25% and 0.04% are both very small in absolute terms and neither changes the Section 9 decision (75.5% posterior sits deep in the "Verify" zone either way).

**What is deliberately left unresolved — p_high.** The same refinement cannot yet be applied to the Verify/Escalate boundary (§7.3's 90%), because that would require an explicit operational cost for "hold and escalate to a human" (analogous to $$C_V$$ for Verify), and this document does not currently state one. Until that cost is estimated, p_high = 90% remains a **risk-tolerance policy choice**, not a cost-derived value — this is now recorded as an open item rather than silently assumed to be equivalent in rigor to p_low. See the added limitation in §10.

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
| **Policy** | Three-zone threshold policy — p_low = 0.25% (§7.2, two-action formula) / **0.040%** (§7.4, refined three-action formula, 20 Aug); p_high = 90% (policy choice, not yet cost-derived — see §7.4, §10) |
| **Decision** | Combined fraud belief (75.5%) falls in the "uncertain" zone under **both** versions of p_low → **Verify** (phone callback). The §7.4 refinement does not change this specific decision, since 75.5% is far above either threshold. |
| **Audit data** | Prepared as part of Week 1/2 AI-Native deliverable; all numbers hypothetical/assumed and labeled as such; policy version 1.2 (threshold refined 20 Aug, see §7.4) |

---

## 10. Limitations, Stated Honestly

- All priors and costs are **hypothetical assumptions**, not measured from real company data.
- The phone-callback likelihood table assumes only the email channel is compromised, never the phone channel — a real, sophisticated attacker who also compromises the phone line would defeat this check. This is a stated, intentional simplification.
- Evidence 1 and Evidence 3 are both weak at distinguishing *which* fraud mechanism is occurring (Compromised vs. Impersonation vs. Insider) — they are good at "genuine vs. not," but not at classifying the specific fraud type.
- The base rates (priors) are not sourced from this company's actual historical data; a real deployment would require this to be measured, not assumed.
- **p_high (90%) is not yet cost-derived** (added 20 Aug, see §7.4). Unlike the refined p_low, it has not been recomputed from an expected-cost equality between Verify and Escalate, because this document does not state an explicit operational cost for escalation. It should be treated as a risk-tolerance policy choice until that cost is estimated and the same three-action method used in §7.4 is applied to it.
- **The refined r (5.33%) in §7.4 is a prior-weighted average**, not a case-specific one — it assumes the population-level mix of fraud mechanisms (40% Compromised / 40% Impersonation / 13% Insider / 7% Something-else) holds generally. In any single case where the posterior fraud-type mix has already shifted (e.g. after Evidence 1, per §4, where Compromised and Impersonation posteriors are equal at 31.1% each, not 40/40 of a smaller base), a case-specific r would be more accurate, but the fixed, prior-weighted r is used here because a *policy* threshold needs to be set once, in advance, not recomputed per case.
- **Stage 8's test scenarios (§11) are a design, not executed results.** No synthetic transaction data has actually been generated and run through this policy yet — that is the explicitly planned next step (see §11.6).

---

## 11. Stage 8 — Policy Evaluation, Simulation Design, and Failure Analysis
*Stage 8 — 20 August 2026*

Stages 1–7 built the reasoning chain: prior → evidence → posterior → entropy/information gain → expected-cost thresholds → a single decision. Stage 8 asks a different question: **does this policy actually perform well across many realistic cases, not just the one worked example in Section 9?** A policy can be internally consistent (every formula correct) and still fail in deployment if its underlying assumptions — the priors, the likelihoods, the costs, or the verification effectiveness — don't hold up outside the one scenario it was designed and checked against.

### 11.1 Why accuracy alone is the wrong metric here

Fraud is a rare-event problem: this agent's own prior puts fraud at only 15% of cases (§2.1), and real-world BEC rates are almost certainly far lower than that once averaged across *all* vendor email, not just flagged ones (§1's cited BEC loss figures represent a small fraction of total vendor traffic). This creates the classic **accuracy paradox**: a policy that simply approved every payment would still score a high raw "accuracy," because the base rate of genuine payments is so high, while providing **zero actual fraud protection**. Accuracy is silent about *which* cases were wrong.

The confusion-matrix framing that matters instead (Positive = Fraud, the class this agent exists to catch):

| | Predicted Fraud (Verify/Escalate) | Predicted Genuine (Pay) |
|---|---|---|
| **Actually Fraud** | True Positive (TP) — caught | False Negative (FN) — missed, full loss |
| **Actually Genuine** | False Positive (FP) — unnecessarily delayed | True Negative (TN) — correctly paid |

$$\text{Recall (fraud catch rate)} = \frac{TP}{TP+FN} \qquad \text{Precision} = \frac{TP}{TP+FP}$$

For this agent specifically, **recall matters more than precision**, because the FN/FP cost ratio is 400:1 (§7.1) — a missed fraud is roughly 400x more expensive than an unnecessarily delayed genuine payment. A policy that trades a large drop in precision for a small gain in recall is very likely still worth it here; that trade-off is exactly what the expected-cost thresholds in §7 already encode, so Stage 8's job is to confirm that behavior holds up under stress, not to re-derive it.

### 11.2 The metric that actually decides between policies: Total Expected Cost

$$\text{Total Expected Cost} = \sum_{\text{cases}} \big[\, \mathbb{1}(\text{FN}) \cdot C_{FN} \;+\; \mathbb{1}(\text{FP}) \cdot C_{FP} \;+\; \text{action cost incurred (}C_V\text{ if Verify chosen)} \,\big]$$

This is the same per-case expected-cost logic from §7, simply summed across a batch of simulated or historical cases instead of evaluated once. Two policies with very different recall/precision profiles should be ranked by this single number, not by accuracy, and not by recall or precision in isolation — a policy that catches more fraud but at disproportionate verification cost is not automatically better, and vice versa.

### 11.3 Simulation design — what has *not* yet been run

To actually evaluate this policy the way §11.1–11.2 describe, the next step (not yet done — see §11.6) is to generate a batch of synthetic cases (e.g. n = 1,000) by sampling from the §2.1 priors, applying the §3 likelihood tables to generate evidence for each case, running the §4 Bayes update, and applying the §7 decision policy (using the refined p_low from §7.4) to each one — then tallying TP/FP/FN/TN and Total Expected Cost across the batch. That would produce this agent's actual recall, precision, and total expected cost under its own current assumptions, rather than the assumptions being checked only against a single hand-worked case.

### 11.4 Stress-test scenarios to run once simulation exists

| # | Scenario | What it checks | Why it matters for *this* agent specifically |
|---|---|---|---|
| 1 | **Base-rate sensitivity** — vary true fraud prevalence (e.g. 2% / 15% / 40%) | Whether the policy collapses toward "approve everything" when fraud is rarer than the assumed 15% prior, or over-escalates when it's more common | The §2.1 priors are explicitly labeled hypothetical (§10) — real vendor fraud incidence for this company is unknown and could be far from 15% |
| 2 | **Cost-structure sensitivity** — vary $$C_{FN}$$, $$C_{FP}$$, $$C_V$$ | Whether p_low and p_high shift sensibly as payment size or verification cost change | A ₹8,00,000 payment and a ₹80,000 payment should not share the same threshold — §7.4's formula already predicts p_low should scale with $$1/L$$ |
| 3 | **Verification-effectiveness sensitivity** — vary the phone-callback miss rate $$r$$ | Whether the policy still holds up if $$r$$ is worse than the assumed 5.33% (e.g. if analysts are less thorough than assumed, or an attacker is more convincing) | §7.4's refined p_low is directly proportional to $$1/(1-r)$$ — if real-world $$r$$ turns out closer to 20%, p_low roughly doubles |
| 4 | **Threshold-boundary robustness** — test posteriors just above/below p_low (0.04%) and p_high (90%) | Whether the policy behaves sensibly at the exact crossover points, with no implementation discontinuities | Protects against *the agent's own* arithmetic or code bugs, not against an adversary |
| 5 | **Adversarial / gaming behavior** — simulate an attacker who has learned the policy's thresholds and evidence checks | Whether a sophisticated attacker can deliberately shape a request (e.g. reuse an old bank account to defeat Evidence 1, or spoof a domain closely enough to reduce Evidence 2's signal) to keep the posterior under p_low | This is the risk category most specific to fraud (vs. e.g. a spam filter): the "positive" class here has direct financial incentive to reverse-engineer and defeat the exact checks in §3 |

### 11.5 Defenses against scenario 5 (gaming), for future hardening

- **Randomized micro-verification below p_low** — occasionally verify a small, random fraction of "Pay" cases anyway, so an attacker can never be certain that staying under the threshold guarantees approval.
- **Non-static, periodically recalculated thresholds** — since §7.4 shows p_low is a function of $$C_V$$, $$L$$, and $$r$$, recomputing it as costs or verification performance change (rather than hard-coding 0.04% indefinitely) makes it harder to reverse-engineer from observed approval patterns.
- **Evidence diversity** — §6 already found that E1 and E2 are complementary (E1 catches most mechanisms, E2 is specifically strong on Impersonation); a fraudster who defeats one evidence source does not automatically defeat the posterior, because the other still contributes.
- **Drift monitoring** — flag if posteriors start clustering suspiciously just below p_low across many cases; that pattern is itself evidence of an adversary probing the threshold, rather than of many independently low-risk cases.

### 11.6 Explicit status

No synthetic data has been generated and no simulation has been executed yet — §11.3–11.5 are the **evaluation design**, prepared so that running it next is a matter of executing the described procedure, not re-deriving it. This is recorded honestly rather than presented as completed results.

---

## Update Note — 20 August 2026

Stage dates were added throughout this document (Stages 1–4: 17 Aug; Stage 5: 18 Aug; Stage 6: 19 Aug; Stages 7–8: 20 Aug — see the timeline table at the top). Two substantive additions were made on 20 Aug, alongside the dating pass:

1. **§7.4 — Threshold Refinement.** The original §7.2 two-action formula ($$p^*=C_{FP}/(C_{FP}+C_{FN})$$, giving p_low = 0.25%) implicitly treats "not paying" as a single, fully protective action. It does not account for Verify being a distinct, imperfect action with its own ₹300 cost and a real ~5.33% chance of failing to catch fraud (derived from §3's Evidence 3 table, weighted by the §2.1 prior mix of fraud mechanisms). Redoing the Pay-vs-Verify break-even with the correct three-action expected-cost equations gives a refined **p_low ≈ 0.040%** — about 6x lower than originally stated. Both values are kept in the document (§7.2 as originally derived, §7.4 as the refinement) rather than overwriting one with the other, consistent with how the 22 Aug corrections below are also marked rather than silently edited. p_high (90%) was **not** similarly refined, because no explicit escalation cost is stated in this document to derive it from — this is now recorded as an open item in §10.
2. **§11 — Stage 8 (Policy Evaluation, Simulation Design, and Failure Analysis).** New section covering why accuracy is misleading for a rare-event problem like this one, the Total Expected Cost metric that should actually be used to compare policies, five stress-test scenario categories (base rate, cost structure, verification effectiveness, threshold-boundary robustness, and adversarial gaming — the last being the risk category most specific to fraud versus other classification problems), and defenses against gaming. This is recorded explicitly as an **evaluation design**, not as executed simulation results — no synthetic data has been generated or run yet.

---

## Verification Note — 22 August 2026

This document was first prepared on 20 August 2026. On 22 August 2026, every calculation in this file was independently recomputed from first principles (not just re-read) to check the reasoning was sound. Two genuine numeric errors were found and are corrected in place above, not silently edited:

1. **Evidence 2's expected information gain was wrong** (stated as 0.611 bits; the correct value is 0.304 bits), and the accompanying claim that "E2 carries the most information of the three" was consequently also wrong — E1 and E3 are actually tied as the strongest checks. The root cause was reusing an entropy value computed for a different evidence source's outcome instead of computing E2's own "exact match" outcome fresh.
2. **The combined posterior fraud probability was mis-added** (stated as 65.5%; the correct sum of the four non-Genuine posteriors is 75.5%).

Neither error changes the final decision reached in Section 9 (Verify), but both were real errors in the stated numbers and needed correcting rather than left as-is. One documentation gap was also fixed: Evidence 2's likelihood table was missing its "Something else" row, now added. Everything else in this document — the Bayes update in Section 4, the entropy values in Section 5, the threshold derivation in Section 7, and the umbrella problem in Section 8 — was independently reconfirmed as correct.

The 20 Aug additions (see Update Note above) were also checked as part of this pass: the weighted verification miss rate $$r = 0.4(0.05)+0.4(0.00)+0.133(0.00)+0.067(0.50) = 0.0533$$ and the refined threshold $$p_{low}=300/(800{,}000 \times 0.9467)=0.000396\approx0.040\%$$ in §7.4 were independently recomputed and confirmed correct.
