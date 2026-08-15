# Errata — Tools, Components & Approach

**What I'm Building Errata With, the Different Ways I Could Do It, and Which One I'm Picking**

*A separate note from the main research log — this one is only about the actual tools and the decision on how to put them together.*

Arif Hussain · 14 August 2026

---

## First, the Three Things I Keep Mixing Up in My Head

Before listing tools, it's worth being clear about what's actually "machine learning" here and what isn't, because these are three separate pieces, not one:

- **The thing being tested** — a small classifier or agent that guesses safe/dangerous. This is the only piece that involves any ML or LLM at all.
- **Errata itself** — the actual evaluation harness. This is plain logic and arithmetic — comparisons, tree walks, sums. No training, no model, nothing "learned." It's the auditor, not the student.
- **The plumbing** — loading data, storing predictions in a table, running the numbers. Just data-handling tools, not ML by itself.

The tools below map cleanly onto these three, and that mapping is the main thing this document is trying to make obvious.

## The Tools and Components

Everything I'm planning to actually use, listed against which of the three pieces above it belongs to.

| Tool | Belongs To | What It's Actually For |
|---|---|---|
| Python 3.11 | All three | The language everything is written in — nothing here needs anything else. |
| pandas | Plumbing | Holding the test set and the predictions as a table, so I can filter/group/count results easily (e.g. "show me every 'missed it' row"). |
| numpy | Plumbing | Plain number-crunching — averaging tree-distances, generating a synthetic dataset with a controlled rare-case rate. |
| scikit-learn | Thing being tested (optional path) | Only if I train a small classic-ML classifier (e.g. logistic regression) as one of the subjects Errata evaluates. |
| LiteLLM + Ollama (already set up) | Thing being tested (chosen path) | Routes a prompt to a local model so an LLM agent can do the actual safe/dangerous classifying — reusing my existing local setup, no new paid API. |
| Plain Python (no library) | Errata itself | The confusion matrix sorting, the `tree_distance()` function, the cost matrix, the adversarial check, the base-rate loop — all hand-written, because no ready-made tool does this combination. |
| matplotlib | Reporting | Drawing the base-rate curve and the confusion-matrix visual for the final errata report. |
| pytest | Quality check | Basic tests so I know the `tree_distance()` function and the cost math are actually correct before trusting any report it produces. |
| Git + GitHub | All three | Version control and where the finished project lives — already learning this step by step separately. |
| Docker (optional, later) | Packaging | Wrapping the finished harness so it can run anywhere without "works on my machine" problems — a later polish step, not needed to get it working. |

## The Different Ways I Could Actually Build This

There isn't one obvious way to put this together — a few real decisions had to be made. Here's each one, with the options actually on the table.

### Decision 1 — What is the "thing being tested"?

- **Option A — Classic ML only.** Train a small scikit-learn model (logistic regression / decision tree) on the synthetic data and point Errata at that.
- **Option B — LLM agent only.** Prompt a local model through my existing LiteLLM → Ollama setup to do the classifying, and point Errata at that instead.
- **Option C — Both, side by side.** Run the same test set through both subjects and let Errata produce a report for each, so the two can be compared.

### Decision 2 — How do I build Errata's core logic?

- **Option A — Hand-write everything from scratch.** Write every piece — confusion matrix, tree distance, cost matrix — myself in plain Python, using the pseudocode as the exact blueprint.
- **Option B — Reuse an existing library for the basic part, hand-write only the new part.** Use scikit-learn's or pycm's confusion-matrix tools for the flat scoring, and only hand-write the tree-distance and cost layers, since those are the pieces nothing existing actually covers.
- **Option C — Build a full plugin-style framework.** Design it like a proper testing framework (the way pytest itself is built) where new scoring "plugins" can be dropped in later.

### Decision 3 — What should the demo classifier actually classify?

- **Option A — Fraud / spam.** The classic, instantly recognisable example — but confirmed to be a crowded, done-many-times-before portfolio space.
- **Option B — Security / content-moderation triage.** safe → suspicious → dangerous: phishing / malware / fraud — naturally hierarchical, and lines up with the OWASP prompt-injection test cases too.
- **Option C — Something entirely different (e.g. product-review moderation).** Would still need a hierarchy to be worth using, and doesn't add anything Option B doesn't already give.

## Which Way I'm Choosing, and Why

### On Decision 1 — going with Option C, starting with the LLM agent (Option B) first

I'm not locking myself into just one subject. I'll build the LLM-agent path first, since it reuses tools I already have working (LiteLLM, Ollama) and makes a better demo story — "I ran Errata against a real LLM agent," not "I scored a spreadsheet model." Once that's working, adding the scikit-learn classifier as a second subject is a natural stretch goal, and it directly proves Errata isn't hard-wired to one kind of model, which is the entire point of building a general evaluation tool rather than a one-off script.

### On Decision 2 — going with Option A, hand-write everything

Option B (reuse a library for the flat part) sounds efficient, but it actually adds a dependency and a second mental model to keep track of, for a piece of logic that's maybe ten lines of code anyway. Since I'm building this to actually understand every part of it — not just glue libraries together — hand-writing the flat confusion matrix myself alongside the tree-distance and cost logic keeps the whole thing consistent and fully explainable, end to end, in one style. Option C (a full plugin framework) is solving a problem I don't have — that's the kind of over-engineering that's easy to justify later but wastes time now, for a portfolio-scale project with one harness and one report.

### On Decision 3 — going with Option B, security/content-moderation triage

This was already settled during the earlier research pass: fraud/spam is a saturated space, and I don't want the demo classifier itself to be mistaken for the point of the project. The safe/suspicious/dangerous tree gives the tree-distance scoring something real to chew on, and the adversarial testing step has an obvious, credible source to draw test cases from — OWASP's prompt-injection category — instead of me inventing attack examples out of thin air.

> **The short version**
>
> LLM agent (via LiteLLM/Ollama) as the first subject being tested, classic-ML classifier added later as a stretch goal — Errata's logic fully hand-written in plain Python, no external confusion-matrix library — demo built on a safe/suspicious/dangerous security-style tree instead of fraud.

## What Kind of Model Output Errata Actually Works On

Everything described so far quietly assumes the model being tested gives back a clean category — "phishing," "safe," "malware." That's true for the demo I'm building, but it's worth being clear that real models don't always answer that way, and Errata needs to handle that honestly rather than pretend every model works like the demo one.

### If the model outputs a clean category (the demo case)

This is the simplest case and the one everything so far was built around. The prediction and the true answer are both labels, they either match or they don't, and the tree-distance function can walk straight up the category tree between them. No changes needed — this is the default.

### If the model outputs a probability or a risk score (the most common case in real systems)

Very few production models just say "dangerous." Most give back something like a risk score of 0.83, and a threshold decides what that number means — "anything above 0.5 counts as dangerous." The comparison step just needs one small addition: pick a threshold, turn the score into a label using that threshold, and everything downstream (confusion matrix, tree distance, cost) runs exactly as before.

This case actually opens up something useful rather than just adding a complication: the threshold itself becomes something worth testing. Instead of running the report once, I can slide the threshold from strict to loose and watch cost and recall trade off against each other — more false alarms at a low threshold, more missed cases at a high one. It's a small addition to the existing steps, not a rebuild.

This is also the only case where the calibration check actually means anything — asking "when it said 90% sure, was it right about 90% of the time" only makes sense if the model gives a real probability in the first place, not a flat label.

### If the model outputs a number that isn't a probability (a regression-style answer)

Example: instead of a category, the model predicts something like an estimated fraud amount in rupees, or days until something fails. There's no label here at all, so the confusion matrix and tree-distance logic don't apply in their current form — comparing two numbers needs a different, simpler kind of scoring, like how far off the guess was on average.

The cost-matrix idea still holds up well here, and arguably gets more useful — the cost doesn't have to be a fixed number per mistake type anymore, it can scale directly with how far off the guess was. Guessing ₹500 of fraud when it was actually ₹5,00,000 is a much worse miss than guessing ₹4,00,000 for the same case, and that difference can be built straight into the cost formula.

### If the model's output is open-ended text (a raw LLM response)

This is the case that actually matters most for the LLM-agent path I've chosen, since a model talking to LiteLLM/Ollama doesn't naturally reply in a clean category unless it's told to. There's no straightforward way to compare two full sentences for an exact match, so there are two real options:

- **Force the structure at the source.** Prompt the model to always answer in a fixed shape — e.g. "respond only with one of: safe / suspicious / dangerous, plus a confidence number" — so its raw text gets converted back into the clean-category or probability case above before it ever reaches Errata. This is what most real agent systems already do, and it's the option I'm going with, since it means Errata itself never has to change.
- **Score the free text directly.** Genuinely harder — checking whether an explanation is faithful to the verdict it gave, the way the AgentSentinel project does. A legitimate stretch goal later, not something worth building first.

> **The actual takeaway**
>
> Errata only needs one small adapter step at the comparison stage that turns whatever the model outputs — a label, a probability, a number, or free text — into the same standard format. Everything after that — tree distance, cost, calibration, adversarial testing, base-rate simulation — stays exactly the same, regardless of what kind of model is being tested. That's also what makes this a general-purpose harness and not a tool tied to one narrow kind of model.

## What This Actually Looks Like Once Built

- Synthetic data generator (pandas + numpy) creates the test set with a controlled rare-case rate.
- The LLM agent (LiteLLM → Ollama) predicts on each case, blind to the true label, in a forced, fixed answer format.
- Errata's hand-written core (plain Python, following the pseudocode exactly) scores the results — flat, tree-distance, and cost, all three.
- A small adversarial set (OWASP-inspired) and the base-rate simulator run on top of the same setup.
- matplotlib turns the numbers into the final errata report; pytest checks the scoring logic is actually correct.
- Everything lives in a Git repo I'm building and understanding one command at a time.
