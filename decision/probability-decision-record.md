# Probability Decision Record

**Project:** Vendor Payment Fraud Triage Agent (evaluated using Errata)
**Prepared by:** Arif Hussain
**Created:** 20 August 2026
**Last verified/corrected:** 22 August 2026 — see the note at the end of this document. All calculations in this file were independently recomputed from scratch; two numeric errors were found and corrected below, and are marked where they occurred rather than silently fixed.

---

## 1. Problem Statement

> The agent observes the email requesting a bank-account change — sender address, SPF/DKIM result, message content, and whether this account has been used before. It must select **pay / verify by calling the supplier / hold and escalate to a human** because whether this request genuinely came from the real supplier or from an attacker is not known.

This is a real, current, well-documented problem. The FBI's IC3 reported **$3.05 billion in verified Business Email Compromise (BEC) losses in 2025 alone** (24,768 complaints, ~$123,000 average loss per incident), and **60% of all BEC scams specifically impersonate vendors/suppliers** — the exact scenario modeled here. Real, named cases include Google and Facebook losing a combined $121 million to a fake-vendor scheme, and the City of Baltimore losing $1.52 million when an attacker inserted new bank details into an active, trusted email thread.

---

## 2. The Belief-State Table

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

$$H = -\sum p_i \log_2(p_i)$$

- **Entropy before evidence (prior):** 0.866 bits
- **Entropy after evidence (posterior):** 2.032 bits

*(Both values independently recomputed 22 Aug 2026 — confirmed correct to three decimal places.)*

**Finding — confusion increased, not decreased.** This runs counter to the common assumption that evidence always reduces uncertainty. Here, the evidence invalidated the dominant hypothesis (Genuine) without clearly favoring any single alternative — Genuine, Compromised, and Impersonation ended up nearly tied (24.5% / 31.1% / 31.1%). This is a genuine, non-trivial finding: the agent went from "confident" to "confused but alert," which is itself valuable information, even though the raw entropy number went up.

---

## 6. Information Selection — Comparing the Three Evidence Sources

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
| **Policy** | Three-zone threshold policy (p_low = 0.25%, p_high = 90%) |
| **Decision** | Combined fraud belief (75.5%) falls in the "uncertain" zone → **Verify** (phone callback) |
| **Audit data** | Prepared as part of Week 1/2 AI-Native deliverable; all numbers hypothetical/assumed and labeled as such; policy version 1.1 (corrected) |

---

## 10. Limitations, Stated Honestly

- All priors and costs are **hypothetical assumptions**, not measured from real company data.
- The phone-callback likelihood table assumes only the email channel is compromised, never the phone channel — a real, sophisticated attacker who also compromises the phone line would defeat this check. This is a stated, intentional simplification.
- Evidence 1 and Evidence 3 are both weak at distinguishing *which* fraud mechanism is occurring (Compromised vs. Impersonation vs. Insider) — they are good at "genuine vs. not," but not at classifying the specific fraud type.
- The base rates (priors) are not sourced from this company's actual historical data; a real deployment would require this to be measured, not assumed.

---

## Verification Note — 22 August 2026

This document was first prepared on 20 August 2026. On 22 August 2026, every calculation in this file was independently recomputed from first principles (not just re-read) to check the reasoning was sound. Two genuine numeric errors were found and are corrected in place above, not silently edited:

1. **Evidence 2's expected information gain was wrong** (stated as 0.611 bits; the correct value is 0.304 bits), and the accompanying claim that "E2 carries the most information of the three" was consequently also wrong — E1 and E3 are actually tied as the strongest checks. The root cause was reusing an entropy value computed for a different evidence source's outcome instead of computing E2's own "exact match" outcome fresh.
2. **The combined posterior fraud probability was mis-added** (stated as 65.5%; the correct sum of the four non-Genuine posteriors is 75.5%).

Neither error changes the final decision reached in Section 9 (Verify), but both were real errors in the stated numbers and needed correcting rather than left as-is. One documentation gap was also fixed: Evidence 2's likelihood table was missing its "Something else" row, now added. Everything else in this document — the Bayes update in Section 4, the entropy values in Section 5, the threshold derivation in Section 7, and the umbrella problem in Section 8 — was independently reconfirmed as correct.
