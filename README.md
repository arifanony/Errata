## Errata

**An evaluation harness that audits AI classifiers and agents — catching the mistakes a plain accuracy score hides.**

Most AI projects end with one number: *"my model is 94% accurate."* That number sounds like an answer, but it rarely tells you the thing you actually need to know — accurate at what, and what happens on the 6% it gets wrong?

Errata is not another classifier. It's the tool that sits on top of any classifier or agent and checks whether its score can actually be trusted. Hand it a model and a test set, and instead of one number, it hands back an itemised record: which specific mistakes the model made, how far off each one was, what it would actually cost, whether the model's confidence can be trusted, and whether it can be tricked.

Think of it less like a student taking an exam, and more like the person standing at the door afterward, checking whether the exam actually proved anything.

### Why "Errata"?

An errata is the corrected record a publisher attaches to a book after it's already printed — not a star rating, but an itemised list of exactly what's wrong and where. This project does the same thing for a model's predictions: instead of one clean verdict, it hands back the itemised correction record. See [docs/research-notes.md](docs/research-notes.md) for the full reasoning, including the honest caveat on where that metaphor doesn't perfectly apply.

### How it works

[Errata flow diagram](assets/errata-flow-diagram.png)

The short version:
- Start with a test set where the right answers are already known — but keep them hidden from the model while it makes its guesses.
- Let the model predict, blind. Whatever it hands back (a label, a score, a number, or free text) gets standardised by a small adapter layer before anything else touches it.
- Only after every guess is locked in, reveal the real answers and compare.
- Score the result several different ways at once: a plain flat accuracy score, how far off the guess was on the category tree, what it would cost in rupees, and whether the model's stated confidence matched how often it was actually right.
- Mix in a handful of deliberately adversarial test cases, and separately re-run the whole thing while dialling the rare-case rate up or down.
- Put it all together into one report — not one number pretending to speak for everything.

Full step-by-step pseudocode for the harness itself is in [docs/pseudocode.md](docs/pseudocode.md).

### Two separate things live in this repo — read this before going further

This repo actually holds **two different projects at two different stages**, and it's easy to mix them up if you don't know that going in:

| | **Errata itself** (the harness) | **The base model** (the agent being evaluated) |
|---|---|---|
| **What it is** | The evaluation tool — plain logic, no ML, the "auditor" | A vendor-payment fraud triage agent — the first real subject Errata will eventually evaluate |
| **Status** | Research, design, pseudocode, and a proven dry run — done. Real Python implementation — not started. | Bayesian reasoning, decision policy, and a working Stage 8 simulation — done and executed. |
| **Where it lives** | `docs/`, `src/errata/`, `dry_run_demo.py` | `base-model/` |
| **Read this first** | [docs/research-notes.md](docs/research-notes.md) | [base-model/decision/probability-decision-record.md](base-model/decision/probability-decision-record.md) |

**Why the base model exists at all:** Errata needs something real to evaluate once it's built — a model or agent with actual decisions, actual probabilities, actual mistakes to catch. Rather than wait until Errata's code is finished to pick that subject, the fraud triage agent was built and reasoned through first, so there's a concrete, already-tested agent ready and waiting the moment Errata's own scoring logic is implemented.

### What's actually new here (Errata itself)

Two pieces of this don't exist anywhere as a ready-to-use tool, as far as the research in this repo could find:
- **Tree-distance scoring** — treating "mistook phishing for malware" as a smaller error than "mistook phishing for safe." The underlying idea is published research (Apple's *Neo*, CHI 2022), but no open, installable implementation of it exists — this repo builds it from scratch.
- **Cost + hierarchy + calibration combined in one report** — most tools do one of these in isolation. Combining "how severe," "how expensive," and "was the confidence honest" into a single evaluation is the actual contribution here.

Full literature review and gap analysis: [docs/research-notes.md](docs/research-notes.md).

### Project status

<table>
<tr><th>Piece</th><th>Status</th></tr>
<tr><td>Problem research & prior-art check (Errata)</td><td>Done — see docs/research-notes.md</td></tr>
<tr><td>Tools & architecture decisions (Errata)</td><td>Done — see docs/tools-and-approach.md</td></tr>
<tr><td>Full pseudocode, 9 steps (Errata)</td><td>Done — see docs/pseudocode.md</td></tr>
<tr><td>Flow diagram (Errata)</td><td>Done — see assets/errata-flow-diagram.png</td></tr>
<tr><td>Dry run proving the scoring logic works (Errata)</td><td>Done — see docs/dry-run-walkthrough.md</td></tr>
<tr><td>Actual Python implementation (Errata)</td><td>Not started</td></tr>
<tr><td>Base model — priors, evidence, Bayesian update</td><td>Done — see base-model/decision/probability-decision-record.md</td></tr>
<tr><td>Base model — cost-based decision policy & thresholds</td><td>Done — see base-model/decision/probability-decision-record.md §7</td></tr>
<tr><td>Base model — pseudocode</td><td>Done — see base-model/pseudocode.md</td></tr>
<tr><td>Base model — Stage 8 simulation (executed, not just designed)</td><td>Done — see base-model/experiments/stage8-fraud-triage-simulation/</td></tr>
<tr><td>Social Media Discussion</td><td>Ongoing — <code>reddit.com/r/learnmachinelearning/s/3QpeJ4lR3p</code>, <code>reddit.com/r/AI_Agents/s/d5597YtN3n</code></td></tr>
</table>

### Repo structure

```
errata/
├── README.md                          ← you are here
├── LICENSE
├── requirements.txt
├── .gitignore
├── .env.example
├── dry_run_demo.py                     ← proves Errata's scoring logic works, no real model needed
│
├── base-model/                         ← the AGENT being evaluated (not Errata itself)
│   ├── pseudocode.md                   ← this agent's own decision-logic pseudocode
│   ├── decision/
│   │   └── probability-decision-record.md   ← priors, evidence, Bayes update, cost thresholds
│   └── experiments/
│       └── stage8-fraud-triage-simulation/
│           ├── fraud_triage_simulation.py    ← runs the simulation + 5 stress-test scenarios
│           └── results/
│               ├── summary.md                ← analysed results, findings, verdict
│               └── raw-output.txt             ← unprocessed console output
│
├── docs/                               ← ERRATA'S OWN docs (the harness, not the base model)
│   ├── research-notes.md               ← the "why" behind Errata, prior-art check
│   ├── tools-and-approach.md           ← tools, decisions, and reasoning
│   ├── pseudocode.md                   ← Errata's own step-by-step logic, all 9 steps
│   └── dry-run-walkthrough.md          ← one case traced by hand + full batch output
│
├── assets/
│   └── errata-flow-diagram.png
│
├── src/
│   └── errata/                         ← Errata's actual implementation goes here (not started yet)
│
└── tests/                              ← tests for Errata's own scoring logic
```

**Quick rule of thumb:** if you're looking for *the harness* — how Errata scores things, what makes it novel, its own design — go to `docs/` or `src/errata/`. If you're looking for *the agent being evaluated* — its priors, its Bayesian reasoning, its decision policy, or the simulation proving that policy works — go to `base-model/`.

### Try the dry run (Errata's own scoring logic)

No real model or setup needed — this proves Errata's scoring logic itself works, using hand-mocked predictions:

```
python dry_run_demo.py
```

See [docs/dry-run-walkthrough.md](docs/dry-run-walkthrough.md) for the full trace and what the output actually proves.

### Try the base-model simulation

No setup beyond the standard library — this runs the fraud-triage agent's decision policy across 1,000 synthetic cases plus five stress-test scenarios:

```
cd base-model/experiments/stage8-fraud-triage-simulation
python fraud_triage_simulation.py
```

See [base-model/experiments/stage8-fraud-triage-simulation/results/summary.md](base-model/experiments/stage8-fraud-triage-simulation/results/summary.md) for the analysed findings, or the decision record's §11 for the full reasoning behind the test design.

### Getting started (once Errata's own code lands)

```
git clone https://github.com/<your-username>/errata.git
cd errata
python -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in any local settings (e.g. your LiteLLM/Ollama endpoint) before running anything that needs a model.

### License

MIT — see [LICENSE](LICENSE).

Built by Arif Hussain as a personal project to demonstrate evaluation rigor for AI systems — not just building a model, but proving whether one is actually safe to trust.
