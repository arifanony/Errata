# Base Model — Pseudocode

**Model:** Vendor Payment Fraud Triage Agent
**Purpose:** This is the *base model* — the example agent Errata will eventually evaluate. It is written and reasoned through first, on its own, before any Errata harness logic touches it.
**Prepared by:** Arif Hussain
**Drafted:** 16 August 2026 (planning pass, before Stage 1 work formally began on 17 August)
**Last cross-checked against actual code:** 21 August 2026, as part of a full reliability audit — confirmed to match `fraud_triage_simulation.py` exactly, including the reliability fix described in the decision record's §11.5.

---

## What this file is (and isn't)

This is pseudocode — the algorithmic skeleton of the agent's decision logic. It is not the reasoning, the worked numbers, or the corrections — all of that lives in `decision/probability-decision-record.md`. Read this file to see *the shape* of what the agent does, step by step; read the decision record to see *why* each number is what it is.

---

## 1. Inputs

```
INPUT:
    email                   # the incoming bank-account-change request
    known_supplier_domain   # supplier's real, on-file email domain
    known_supplier_phone    # supplier's real, on-file phone number
    account_history         # internal DB of previously used accounts
```

## 2. Hidden states and priors

```
STATES = [Genuine, Compromised, Impersonation, Insider, SomethingElse]

PRIOR = {
    Genuine:        0.85,
    Compromised:    0.06,
    Impersonation:  0.06,
    Insider:        0.02,
    SomethingElse:  0.01
}

ASSERT sum(PRIOR.values()) == 1.0
```

## 3. Evidence sources (each returns 1/0)

```
FUNCTION check_E1_new_account(email, account_history):
    RETURN 1 if requested account NOT IN account_history else 0

FUNCTION check_E2_domain_mismatch(email, known_supplier_domain):
    RETURN 1 if email.sender_domain != known_supplier_domain else 0

FUNCTION check_E3_phone_confirms(known_supplier_phone):
    # Cost: ~30 min analyst time. Only run if still uncertain after E1+E2.
    CALL known_supplier_phone  # NEVER a number from the email itself
    RETURN 1 if supplier confirms the request else 0
```

Each evidence source has its own **likelihood table** — P(observation | state) — for both its possible outcomes. These tables live in the decision record (§3); this file only references them, it doesn't restate the numbers, to avoid two places going out of sync.

```
LIKELIHOOD_E1[state][value]   # value ∈ {new, known}
LIKELIHOOD_E2[state][value]   # value ∈ {mismatch, match}
LIKELIHOOD_E3[state][value]   # value ∈ {confirms, denies}
```

## 4. Bayesian update (single reusable function)

```
FUNCTION bayes_update(prior, likelihood_table, observed_value):
    unnormalized = {}
    FOR EACH state IN STATES:
        likelihood = likelihood_table[state][observed_value]
        unnormalized[state] = prior[state] * likelihood

    total = SUM(unnormalized.values())

    posterior = {}
    FOR EACH state IN STATES:
        posterior[state] = unnormalized[state] / total

    RETURN posterior
```

## 5. Entropy and information gain (diagnostic, not decision-driving)

```
FUNCTION entropy(distribution):
    RETURN -SUM( p * log2(p) for p in distribution.values() if p > 0 )

FUNCTION expected_info_gain(prior, likelihood_table):
    h_prior = entropy(prior)
    h_conditional = 0
    FOR EACH outcome IN [0, 1]:
        p_outcome = SUM( prior[s] * likelihood_table[s][outcome] for s in STATES )
        posterior_given_outcome = bayes_update(prior, likelihood_table, outcome)
        h_conditional += p_outcome * entropy(posterior_given_outcome)
    RETURN h_prior - h_conditional
```

Used once, up front (decision record §6), to decide which evidence sources are worth running at all. This is a design-time comparison, not re-run per case in the main decision loop below.

## 6. Cost inputs

```
C_FP = 2,000         # wrongly holding/escalating a genuine payment
C_FN = 8,00,000      # wrongly paying an actual fraud
C_V  = 300           # cost of running the E3 phone-callback check
```

## 7. Decision thresholds — TWO separate thresholds, for TWO separate moments

```
# --- PRE-verification thresholds (decide: Pay / Verify / Escalate, using E1+E2 only) ---

r = weighted_average(
        LIKELIHOOD_E3[state][confirms]
        for state in [Compromised, Impersonation, Insider, SomethingElse],
        weights = PRIOR[state] / sum(PRIOR[fraud_states])
    )

P_LOW  = C_V / (C_FN * (1 - r))            # refined 3-action threshold (decision record §7.4)
P_HIGH = 0.90                              # policy choice, not yet cost-derived (§10 limitation)

# --- POST-verification threshold (decide: Pay / Escalate ONLY, once E3 already happened) ---

P_STAR = C_FP / (C_FP + C_FN)              # plain 2-action threshold (decision record §7.2,
                                            # REUSED for this different moment, not re-derived)
                                            # NOT the same as P_LOW -- P_LOW prices the RISK of
                                            # running verification before it happens; P_STAR is
                                            # used only after verification is already sunk.
```

## 8. Main decision loop — one case

```
FUNCTION decide(email):

    posterior = PRIOR

    e1 = check_E1_new_account(email, account_history)
    posterior = bayes_update(posterior, LIKELIHOOD_E1, e1)

    e2 = check_E2_domain_mismatch(email, known_supplier_domain)
    posterior = bayes_update(posterior, LIKELIHOOD_E2, e2)

    fraud_prob = 1 - posterior[Genuine]

    IF fraud_prob < P_LOW:
        RETURN action = Pay, evidence_used = [E1, E2]

    IF fraud_prob >= P_HIGH:
        RETURN action = Escalate, evidence_used = [E1, E2]

    # Uncertain zone -- Verify (E3 is not free, incur C_V)
    e3 = check_E3_phone_confirms(known_supplier_phone)
    posterior = bayes_update(posterior, LIKELIHOOD_E3, e3)
    final_fraud_prob = 1 - posterior[Genuine]

    # Verify already spent, C_V is sunk. Only Pay vs Escalate remain --
    # use P_STAR, NOT P_LOW again.
    IF final_fraud_prob < P_STAR:
        RETURN action = Pay, evidence_used = [E1, E2, E3]
    ELSE:
        RETURN action = Escalate, evidence_used = [E1, E2, E3]
```

## 9. Grading a decision (only possible in simulation, where ground truth is known)

```
FUNCTION grade(true_state, action):
    is_fraud = (true_state != Genuine)

    IF action == Pay AND is_fraud:          RETURN "FN", cost = C_FN
    IF action == Pay AND NOT is_fraud:      RETURN "TN", cost = 0
    IF action == Escalate AND is_fraud:     RETURN "TP", cost = 0
    IF action == Escalate AND NOT is_fraud: RETURN "FP", cost = C_FP
```

## 10. Stage 8 simulation — generating one synthetic case

```
FUNCTION simulate_one_case(rng):
    # NOTE (added 21 Aug, reliability audit): rng must be a DEDICATED,
    # isolated random generator passed explicitly into this function --
    # never draw from a shared/global random source. An earlier version
    # of the real implementation used a global random module, which made
    # batch reproducibility silently depend on unrelated code (like demo
    # cases) running first. See decision record §11.5 for the full story.

    true_state = weighted_random_choice(rng, STATES, weights = PRIOR)

    e1 = weighted_random_choice(rng, [new, known], weights = LIKELIHOOD_E1[true_state])
    e2 = weighted_random_choice(rng, [mismatch, match], weights = LIKELIHOOD_E2[true_state])

    posterior = bayes_update(PRIOR, LIKELIHOOD_E1, e1)
    posterior = bayes_update(posterior, LIKELIHOOD_E2, e2)
    fraud_prob = 1 - posterior[Genuine]

    IF fraud_prob < P_LOW:
        action = Pay
    ELSE IF fraud_prob >= P_HIGH:
        action = Escalate
    ELSE:
        e3 = weighted_random_choice(rng, [confirms, denies], weights = LIKELIHOOD_E3[true_state])
        posterior = bayes_update(posterior, LIKELIHOOD_E3, e3)
        final_fraud_prob = 1 - posterior[Genuine]
        action = Pay if final_fraud_prob < P_STAR else Escalate

    outcome, cost = grade(true_state, action)
    RETURN {true_state, action, outcome, cost}
```

## 11. Stage 8 simulation — full batch

```
FUNCTION run_batch(n, seed):
    rng = new_isolated_random_generator(seed)   # dedicated per batch -- see note in §10
    confusion_matrix = {TP: 0, FP: 0, FN: 0, TN: 0}
    total_cost = 0

    REPEAT n TIMES:
        result = simulate_one_case(rng)
        confusion_matrix[result.outcome] += 1
        total_cost += result.cost

    recall    = TP / (TP + FN)
    precision = TP / (TP + FP)
    RETURN confusion_matrix, recall, precision, total_cost
```

## 12. Stress-test scenarios (executed — decision record §11.4 has full results)

```
run_batch(n, seed=101..103, priors = shifted_base_rate)          # Scenario 1: base-rate sensitivity
run_batch(n, seed=201..203, C_FN = X, C_V = Y)                    # Scenario 2: cost-structure sensitivity
run_batch(n, seed=301..303, LIKELIHOOD_E3 = degraded_table)       # Scenario 3: verification effectiveness
test_decide_at(P_LOW - ε, P_LOW, P_LOW + ε)                       # Scenario 4: threshold-boundary robustness
run_batch(n, seed=401, force e1=known, e2=match FOR fraud cases)  # Scenario 5: adversarial gaming
```

---

## Notes on scope

- This pseudocode describes the **base model only** — the fraud-triage agent's own decision logic. It says nothing about how Errata will later score or audit this agent's behavior; that harness-level logic belongs in Errata's own `docs/pseudocode.md`, not here.
- Every threshold and cost value referenced here is defined and justified in `decision/probability-decision-record.md` — this file intentionally does not restate those numbers, so corrections only ever need to happen in one place.
- The two-threshold design (`P_LOW`/`P_HIGH` before verification, `P_STAR` after) and the isolated-rng requirement in §10 were both genuine corrections made during Stage 7/8 development and a later reliability audit — both mistakes, and why they were wrong, are documented in the decision record's §7.4 and §11.5.
