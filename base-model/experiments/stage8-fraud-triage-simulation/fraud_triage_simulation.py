"""
Vendor Payment Fraud Triage Agent — Stage 8 Simulation (v2, reliability-audited)
================================================================================
Errata project — Arif Hussain

CHANGE LOG (21 August 2026, reliability audit):
  - v1 used Python's shared GLOBAL `random` module for every draw. This meant
    the exact reported batch numbers were only reproducible if the 3 verbose
    demo cases ran BEFORE the main batch (since both drew from the same
    global stream). Removing/reordering the demo section would have silently
    changed the "same seed=42" results with no warning.
  - FIX: every batch now uses its OWN dedicated `random.Random(seed)`
    instance, completely isolated from the demo section and from every
    other batch. Verified: running unrelated random calls before a batch, or
    skipping the demo section entirely, no longer changes that batch's
    results at all. Reproducibility is now a real, structural guarantee,
    not an artifact of call order.
  - One consequence, disclosed honestly: because the isolation changes
    exactly how many random numbers the main batch consumes internally, its
    reported numbers shift slightly from the original run (e.g. FP moves
    from 122 to 124 out of 1000 -- well within normal sampling noise, not a
    sign either run was wrong). The MATH and DECISION LOGIC are unchanged;
    only the random draw sequence differs.

WHAT THIS SCRIPT DOES (unchanged from v1):
Generates N synthetic cases, draws a hidden true state per case, generates
evidence from the document's own likelihood tables, runs a real Bayesian
update, applies the two-phase cost policy (P_LOW/P_HIGH pre-verification,
P_STAR post-verification), grades the result against ground truth, and
reports a confusion matrix + Total Expected Cost. Then runs the five §11.4
stress-test scenarios.
"""

# ---------------------------------------------------------------------------
# 1. CORE DATA — copied directly from probability-decision-record.md
# ---------------------------------------------------------------------------
import random

STATES = ["Genuine", "Compromised", "Impersonation", "Insider", "Something else"]

PRIORS = {
    "Genuine": 0.85, "Compromised": 0.06, "Impersonation": 0.06,
    "Insider": 0.02, "Something else": 0.01,
}
assert abs(sum(PRIORS.values()) - 1.0) < 1e-9, "Priors must sum to 1.0"

E1_TABLE = {"Genuine": 0.05, "Compromised": 0.90, "Impersonation": 0.90,
            "Insider": 0.90, "Something else": 0.50}
E2_TABLE = {"Genuine": 0.00, "Compromised": 0.00, "Impersonation": 0.90,
            "Insider": 0.50, "Something else": 0.50}
E3_TABLE = {"Genuine": 0.90, "Compromised": 0.05, "Impersonation": 0.00,
            "Insider": 0.00, "Something else": 0.50}

C_FP = 2_000
C_FN = 800_000
C_V = 300

P_LOW = 0.000396      # refined 3-action threshold, decision record §7.4
P_HIGH = 0.90         # policy choice, decision record §7.3 / §10
P_STAR = C_FP / (C_FP + C_FN)   # plain 2-action threshold, §7.2

print("Core data loaded.")
print(f"Priors sum to: {sum(PRIORS.values()):.4f}")
print(f"P_LOW  (pre-verify,  §7.4, 3-action) = {P_LOW*100:.4f}%")
print(f"P_HIGH (pre-verify,  §7.3, 3-action) = {P_HIGH*100:.1f}%")
print(f"P_STAR (post-verify, §7.2, 2-action) = {P_STAR*100:.4f}%")


# ---------------------------------------------------------------------------
# 2. CORE MECHANICS — all functions take an explicit rng, never use the
#    global `random` module. This is the reliability fix: every batch owns
#    its own isolated random stream.
# ---------------------------------------------------------------------------

def draw_true_state(rng, priors):
    states = list(priors.keys())
    weights = list(priors.values())
    return rng.choices(states, weights=weights, k=1)[0]


def draw_evidence(rng, true_state, likelihood_table):
    p_fires = likelihood_table[true_state]
    return 1 if rng.random() < p_fires else 0


def likelihood_row_for_value(table, value):
    if value == 1:
        return dict(table)
    return {state: 1.0 - p for state, p in table.items()}


def bayes_update(prior, table, observed_value):
    likelihood = likelihood_row_for_value(table, observed_value)
    unnormalized = {s: prior[s] * likelihood[s] for s in prior}
    total = sum(unnormalized.values())
    posterior = {s: v / total for s, v in unnormalized.items()}
    return posterior, unnormalized, total


print("\nCore mechanics defined (all functions take an explicit rng argument).")

# Sanity check against §4's worked example — uses its own throwaway rng,
# doesn't touch anything else's random state.
_check_posterior, _check_unnorm, _check_total = bayes_update(PRIORS, E1_TABLE, 1)
print("\nSanity check against §4's worked example (E1 = new account observed):")
print(f"  {'State':<16} {'Doc posterior':>14} {'Script posterior':>18}")
_doc_values = {"Genuine": 0.245, "Compromised": 0.311, "Impersonation": 0.311,
               "Insider": 0.104, "Something else": 0.029}
for s in STATES:
    print(f"  {s:<16} {_doc_values[s]:>14.3f} {_check_posterior[s]:>18.3f}")
print(f"  Denominator (§4 says 0.1735): script computed {_check_total:.4f}")


# ---------------------------------------------------------------------------
# 3. SINGLE-CASE SIMULATION — verbose trace, using its OWN isolated rng
#    (seed fixed separately from the main batch, so the demo section can be
#    edited/removed freely without affecting batch reproducibility at all).
# ---------------------------------------------------------------------------

def fmt_posterior(post):
    return ", ".join(f"{s}={post[s]:.3f}" for s in STATES)


def simulate_one_case(rng, case_id, verbose=False):
    if verbose:
        print(f"\n{'='*78}\nCASE #{case_id}\n{'='*78}")

    true_state = draw_true_state(rng, PRIORS)
    if verbose:
        print(f"[Step 1] TRUE hidden state drawn (hidden from agent): {true_state}")

    e1 = draw_evidence(rng, true_state, E1_TABLE)
    post_e1, _, tot_e1 = bayes_update(PRIORS, E1_TABLE, e1)
    if verbose:
        print(f"[Step 2] Evidence 1 (new account?) generated: {e1} "
              f"({'NEW' if e1 else 'known'} account)")
        print(f"[Step 3] Posterior after E1: {fmt_posterior(post_e1)}  "
              f"(denominator={tot_e1:.4f})")

    e2 = draw_evidence(rng, true_state, E2_TABLE)
    post_e1e2, _, tot_e2 = bayes_update(post_e1, E2_TABLE, e2)
    if verbose:
        print(f"[Step 3] Evidence 2 (domain mismatch?) generated: {e2} "
              f"({'MISMATCH' if e2 else 'exact match'})")
        print(f"         Posterior after E1+E2: {fmt_posterior(post_e1e2)}  "
              f"(denominator={tot_e2:.4f})")

    fraud_prob_e1e2 = 1.0 - post_e1e2["Genuine"]
    if verbose:
        print(f"         Combined fraud probability = {fraud_prob_e1e2*100:.3f}%")

    verification_used = False
    final_posterior = post_e1e2
    final_fraud_prob = fraud_prob_e1e2

    if fraud_prob_e1e2 < P_LOW:
        action = "Pay"
        if verbose:
            print(f"[Step 4] {fraud_prob_e1e2*100:.3f}% < P_LOW -> PAY")
    elif fraud_prob_e1e2 >= P_HIGH:
        action = "Escalate"
        if verbose:
            print(f"[Step 4] {fraud_prob_e1e2*100:.3f}% >= P_HIGH -> ESCALATE")
    else:
        verification_used = True
        if verbose:
            print(f"[Step 4] {fraud_prob_e1e2*100:.3f}% between thresholds -> "
                  f"VERIFY (incur Rs {C_V})")
        e3 = draw_evidence(rng, true_state, E3_TABLE)
        final_posterior, _, _ = bayes_update(post_e1e2, E3_TABLE, e3)
        final_fraud_prob = 1.0 - final_posterior["Genuine"]
        if verbose:
            print(f"         Evidence 3 generated: {e3} "
                  f"({'CONFIRMS genuine' if e3 else 'DENIES/cannot confirm'})")
            print(f"         Final fraud probability = {final_fraud_prob*100:.3f}%")

        if final_fraud_prob < P_STAR:
            action = "Pay"
            if verbose:
                print(f"[Step 4] Post-verification: {final_fraud_prob*100:.3f}% "
                      f"< P_STAR ({P_STAR*100:.2f}%) -> PAY")
        else:
            action = "Escalate"
            if verbose:
                print(f"[Step 4] Post-verification: {final_fraud_prob*100:.3f}% "
                      f">= P_STAR ({P_STAR*100:.2f}%) -> ESCALATE")

    is_fraud = true_state != "Genuine"
    cost = C_V if verification_used else 0
    if action == "Pay":
        outcome = "FN" if is_fraud else "TN"
        cost += C_FN if is_fraud else 0
    else:
        outcome = "TP" if is_fraud else "FP"
        cost += C_FP if not is_fraud else 0

    if verbose:
        print(f"[Step 5] TRUE state = {true_state} | Action = {action} | "
              f"Outcome = {outcome} | Cost = Rs {cost:,}")

    return {"true_state": true_state, "is_fraud": is_fraud, "action": action,
            "outcome": outcome, "cost": cost}


print("\nRunning 3 fully verbose example cases (own isolated rng, seed=1):")
demo_rng = random.Random(1)      # <-- ISOLATED seed, independent of batch seed
for i in range(1, 4):
    simulate_one_case(demo_rng, i, verbose=True)


# ---------------------------------------------------------------------------
# 4. FULL BATCH RUN — each call gets its OWN isolated rng (reliability fix)
# ---------------------------------------------------------------------------

def run_batch(n, seed=42, priors=PRIORS, e1_table=E1_TABLE, e2_table=E2_TABLE,
              e3_table=E3_TABLE, c_fp=C_FP, c_fn=C_FN, c_v=C_V,
              p_low=P_LOW, p_high=P_HIGH, p_star=None, label=""):
    if p_star is None:
        p_star = c_fp / (c_fp + c_fn)

    rng = random.Random(seed)    # <-- dedicated, isolated per batch
    results = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    total_cost = 0
    verify_count = 0
    true_state_counts = {s: 0 for s in STATES}
    e1_fires_given_genuine = 0
    genuine_count = 0

    for i in range(n):
        true_state = draw_true_state(rng, priors)
        true_state_counts[true_state] += 1
        is_fraud = true_state != "Genuine"

        e1 = draw_evidence(rng, true_state, e1_table)
        if true_state == "Genuine":
            genuine_count += 1
            if e1 == 1:
                e1_fires_given_genuine += 1

        post_e1, _, _ = bayes_update(priors, e1_table, e1)
        e2 = draw_evidence(rng, true_state, e2_table)
        post_e1e2, _, _ = bayes_update(post_e1, e2_table, e2)
        fraud_prob = 1.0 - post_e1e2["Genuine"]

        case_cost = 0
        if fraud_prob < p_low:
            action = "Pay"
        elif fraud_prob >= p_high:
            action = "Escalate"
        else:
            verify_count += 1
            case_cost += c_v
            e3 = draw_evidence(rng, true_state, e3_table)
            post_final, _, _ = bayes_update(post_e1e2, e3_table, e3)
            final_fraud_prob = 1.0 - post_final["Genuine"]
            action = "Pay" if final_fraud_prob < p_star else "Escalate"

        if action == "Pay":
            if is_fraud:
                results["FN"] += 1
                case_cost += c_fn
            else:
                results["TN"] += 1
        else:
            if is_fraud:
                results["TP"] += 1
            else:
                results["FP"] += 1
                case_cost += c_fp

        total_cost += case_cost

    tp, fp, fn, tn = results["TP"], results["FP"], results["FN"], results["TN"]
    recall = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
    precision = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
    accuracy = (tp + tn) / n

    print(f"\n{'-'*78}")
    print(f"BATCH RESULTS — {label} (n={n}, seed={seed})" if label else f"BATCH RESULTS (n={n}, seed={seed})")
    print(f"{'-'*78}")
    print(f"True state distribution: " +
          ", ".join(f"{s}={true_state_counts[s]}" for s in STATES))
    print(f"Expected Genuine count (prior×n = {priors['Genuine']}×{n}): "
          f"{priors['Genuine']*n:.0f}  |  Actual: {true_state_counts['Genuine']}")
    if genuine_count > 0:
        expected_e1_fire = genuine_count * e1_table["Genuine"]
        print(f"Of {genuine_count} Genuine cases, E1 fired 'new account' by chance: "
              f"{e1_fires_given_genuine}  (expected ≈ {expected_e1_fire:.1f})")
    print(f"\nConfusion matrix (Positive = Fraud):")
    print(f"                    Predicted Fraud    Predicted Genuine")
    print(f"  Actually Fraud    TP={tp:<14}  FN={fn}")
    print(f"  Actually Genuine  FP={fp:<14}  TN={tn}")
    print(f"\nRecall    = {tp}/{tp+fn} = {recall*100:.2f}%")
    print(f"Precision = {tp}/{tp+fp} = {precision*100:.2f}%")
    print(f"Accuracy (misleading, §11.1) = {accuracy*100:.2f}%")
    print(f"Verification used in {verify_count}/{n} cases ({verify_count/n*100:.1f}%)")
    print(f"TOTAL EXPECTED COST = Rs {total_cost:,}")
    print(f"Average cost/case   = Rs {total_cost/n:,.2f}")

    return {"n": n, "results": results, "total_cost": total_cost,
            "recall": recall, "precision": precision, "accuracy": accuracy,
            "verify_count": verify_count}


print("\n" + "=" * 78)
print("STAGE 8 — MAIN SIMULATION: n = 1,000, seed=42, document's own numbers")
print("=" * 78)
main_batch = run_batch(1000, seed=42, label="Baseline")

# Reliability proof: re-run the SAME batch after burning unrelated global
# random calls, to demonstrate isolation actually holds now.
_ = [random.random() for _ in range(500)]   # unrelated noise on the GLOBAL random
proof_batch = run_batch(1000, seed=42, label="Same seed, AFTER 500 unrelated global random.random() calls")
identical = (main_batch["results"] == proof_batch["results"] and
             main_batch["total_cost"] == proof_batch["total_cost"])
print(f"\n*** RELIABILITY CHECK: identical results despite unrelated noise? "
      f"{'YES -- fix confirmed working' if identical else 'NO -- still fragile!'} ***")


# ---------------------------------------------------------------------------
# 5. STAGE 8 STRESS-TEST SCENARIOS (§11.4) — each uses its own isolated seed
# ---------------------------------------------------------------------------

def weighted_r(priors, e3_table):
    fraud_states = [s for s in priors if s != "Genuine"]
    fraud_total = sum(priors[s] for s in fraud_states)
    return sum((priors[s] / fraud_total) * e3_table[s] for s in fraud_states)


print("\n" + "=" * 78)
print("STAGE 8 — STRESS-TEST SCENARIOS (§11.4)")
print("=" * 78)

# --- Scenario 1: Base-rate sensitivity ---
print("\n### Scenario 1: Base-rate sensitivity ###")
fraud_shape = {"Compromised": 0.4, "Impersonation": 0.4,
               "Insider": 0.1333, "Something else": 0.0667}

def make_priors(genuine_share):
    fraud_share = 1 - genuine_share
    p = {"Genuine": genuine_share}
    for s, share in fraud_shape.items():
        p[s] = fraud_share * share
    total = sum(p.values())
    return {s: v / total for s, v in p.items()}

for genuine_share, tag, seed in [(0.98, "rare fraud, 2%", 101),
                                   (0.85, "baseline, 15%", 102),
                                   (0.60, "high fraud, 40%", 103)]:
    p = make_priors(genuine_share)
    r = weighted_r(p, E3_TABLE)
    p_low = C_V / (C_FN * (1 - r))
    run_batch(1000, seed=seed, priors=p, p_low=p_low, p_high=P_HIGH,
              label=f"Scenario 1 — {tag} (r={r*100:.2f}%, p_low={p_low*100:.4f}%)")

# --- Scenario 2: Cost-structure sensitivity ---
print("\n### Scenario 2: Cost-structure sensitivity ###")
r_baseline = weighted_r(PRIORS, E3_TABLE)
for c_fn_test, c_v_test, tag, seed in [
        (800_000, 300, "baseline: L=Rs 8,00,000, C_V=Rs 300", 201),
        (80_000, 300, "smaller payment: L=Rs 80,000", 202),
        (800_000, 1500, "expensive verification: C_V=Rs 1,500", 203)]:
    p_low_test = c_v_test / (c_fn_test * (1 - r_baseline))
    p_star_test = C_FP / (C_FP + c_fn_test)
    run_batch(1000, seed=seed, c_fn=c_fn_test, c_v=c_v_test,
              p_low=p_low_test, p_high=P_HIGH, p_star=p_star_test,
              label=f"Scenario 2 — {tag} (p_low={p_low_test*100:.4f}%, "
                    f"p_star={p_star_test*100:.4f}%)")

# --- Scenario 3: Verification-effectiveness sensitivity ---
print("\n### Scenario 3: Verification-effectiveness sensitivity ###")
for miss_rate, tag, seed in [(0.05, "baseline: 5% miss under Compromised", 301),
                               (0.20, "unreliable: 20% miss", 302),
                               (0.01, "very reliable: 1% miss", 303)]:
    e3_test = dict(E3_TABLE)
    e3_test["Compromised"] = miss_rate
    r_test = weighted_r(PRIORS, e3_test)
    p_low_test = C_V / (C_FN * (1 - r_test))
    run_batch(1000, seed=seed, e3_table=e3_test, p_low=p_low_test, p_high=P_HIGH,
              label=f"Scenario 3 — {tag} (r={r_test*100:.2f}%, "
                    f"p_low={p_low_test*100:.4f}%)")

print("\n*** GENUINE FINDING (independently re-verified, not a bug) ***")
print("At either a 40% fraud base rate (Scenario 1) OR a 20% verification")
print("miss rate (Scenario 3), even a GENUINE case with the BEST possible")
print("evidence (known account + matching domain + supplier confirms)")
print("computes a final fraud probability ABOVE P_STAR's fixed 0.2494%")
print("threshold -- because P_STAR is a fixed cost-ratio number that does")
print("NOT adapt to base rate or evidence quality, unlike P_LOW (which §7.4")
print("already adjusts via r). Independently hand-verified:")
print("  Scenario 1 (40% fraud): best-case genuine -> 0.7996% final fraud prob")
print("  Scenario 3 (20% miss):  best-case genuine -> 0.3360% final fraud prob")
print("  Both exceed P_STAR (0.2494%) -> both get wrongly escalated.")

# --- Scenario 4: Threshold-boundary robustness ---
print("\n### Scenario 4: Threshold-boundary robustness ###")
def decide_at(fraud_prob, p_low=P_LOW, p_high=P_HIGH):
    if fraud_prob < p_low: return "Pay"
    if fraud_prob >= p_high: return "Escalate"
    return "Verify"

print(f"Around P_LOW ({P_LOW*100:.4f}%):")
for p in [P_LOW-0.00001, P_LOW, P_LOW+0.00001]:
    print(f"  fraud_prob={p*100:.5f}%  ->  {decide_at(p)}")
print(f"Around P_HIGH ({P_HIGH*100:.1f}%):")
for p in [P_HIGH-0.001, P_HIGH, P_HIGH+0.001]:
    print(f"  fraud_prob={p*100:.3f}%  ->  {decide_at(p)}")
print("Result: clean transitions at both boundaries, no discontinuity bugs.")

# --- Scenario 5: Adversarial gaming ---
print("\n### Scenario 5: Adversarial / gaming behavior ###")

def run_gaming_batch(n, seed=401, priors=PRIORS, c_fp=C_FP, c_fn=C_FN, c_v=C_V,
                      p_low=P_LOW, p_high=P_HIGH, p_star=None):
    if p_star is None:
        p_star = c_fp / (c_fp + c_fn)
    rng = random.Random(seed)
    results = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    total_cost = 0
    for i in range(n):
        true_state = draw_true_state(rng, priors)
        is_fraud = true_state != "Genuine"
        if is_fraud:
            e1, e2 = 0, 0   # attacker forces known account + matching domain
        else:
            e1 = draw_evidence(rng, true_state, E1_TABLE)
            e2 = draw_evidence(rng, true_state, E2_TABLE)
        post_e1, _, _ = bayes_update(priors, E1_TABLE, e1)
        post_e1e2, _, _ = bayes_update(post_e1, E2_TABLE, e2)
        fraud_prob = 1.0 - post_e1e2["Genuine"]
        case_cost = 0
        if fraud_prob < p_low:
            action = "Pay"
        elif fraud_prob >= p_high:
            action = "Escalate"
        else:
            case_cost += c_v
            e3 = draw_evidence(rng, true_state, E3_TABLE)
            post_final, _, _ = bayes_update(post_e1e2, E3_TABLE, e3)
            final_fraud_prob = 1.0 - post_final["Genuine"]
            action = "Pay" if final_fraud_prob < p_star else "Escalate"
        if action == "Pay":
            if is_fraud: results["FN"] += 1; case_cost += c_fn
            else: results["TN"] += 1
        else:
            if is_fraud: results["TP"] += 1
            else: results["FP"] += 1; case_cost += c_fp
        total_cost += case_cost
    return results, total_cost

gaming_results, gaming_cost = run_gaming_batch(1000, seed=401)
tp, fp, fn, tn = gaming_results["TP"], gaming_results["FP"], gaming_results["FN"], gaming_results["TN"]
gaming_recall = tp/(tp+fn) if (tp+fn) > 0 else float("nan")
print(f"Attacker always defeats E1+E2:")
print(f"  Confusion matrix: TP={tp} FP={fp} FN={fn} TN={tn}")
print(f"  Recall = {gaming_recall*100:.2f}%  (baseline recall was {main_batch['recall']*100:.2f}%)")
print(f"  Total Expected Cost = Rs {gaming_cost:,}  "
      f"(baseline was Rs {main_batch['total_cost']:,})")

print("\n" + "=" * 78)
print("ALL SCENARIOS COMPLETE.")
print("=" * 78)
