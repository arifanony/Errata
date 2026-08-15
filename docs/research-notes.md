# Errata — Research Notes

**An Evaluation Harness for AI Classifiers and Agents**

*The corrected record your model's accuracy score doesn't show you — what I looked into before deciding to build this, written the way I'd explain it out loud.*

Arif Hussain · 11 August 2026

---

## What Am I Actually Trying to Build?

Not a spam filter. Not a fraud detector. Those are just the examples I use to explain the idea — they aren't the actual deliverable.

What I'm building is something that sits on top of any of those models and checks whether the model's own "score" can actually be trusted. Almost every AI project I've come across — including the ones I've built myself — ends with one number: "my model is 94% accurate." That number sounds like an answer, but it almost never tells you the thing you actually need to know, which is: accurate at what, and what happens on the 6% it gets wrong?

So the project is an evaluation tool. Hand it a model and a test set, and instead of one number, it hands back a proper report: which specific mistakes the model is making, how expensive each kind of mistake actually is, whether the model only looks good because the dangerous case is rare, whether its confidence can be trusted, and whether it can be tricked. Think of it less like a student taking an exam and more like the person standing at the door afterward, checking whether the exam actually proved anything.

## Why I Named It Errata

An errata is the corrected record a publisher attaches to a book after it's out — not a star rating, not "this book is good," but an itemised list: page 45 says X, it should say Y. A book can look complete and be "published" while still carrying specific, identifiable mistakes that only show up once someone actually checks the details.

That's the exact parallel to this project. A model can be "94% accurate" and still have never once caught the one dangerous case it existed to catch — the accuracy paradox that's the whole reason this project exists. Just like an errata, this tool doesn't hand back a single verdict; it hands back the itemised record: this case was missed, this one was a false alarm, this one was answered at 90% confidence but was wrong, and here's how far off each guess was on the category tree. It's a correction record, checked against a known-correct answer after the fact — exactly the "hide the answer, let the model commit, then compare" structure this harness runs on.

One honest caveat: the metaphor isn't a perfect one-to-one match. A real errata is usually a static list written once by a human proofreader — it doesn't stress-test the book against tricky or adversarial readers, and it doesn't get re-run under different conditions. This project's adversarial testing and base-rate simulation go further than a literal errata sheet would. The name captures the core spirit — reject one clean verdict, insist on the itemised truth — rather than describing every single feature literally.

## How I Even Landed on This Problem

It started from a simple annoyance: I kept seeing "accuracy: 92%" used as if it settles the argument — in demos, in dashboards, everywhere. The more I sat with it, the more I realised that number can be almost meaningless on its own, and I wanted to actually prove that to myself with real numbers instead of just having a feeling about it.

Here's the example I used to convince myself. Say a company gets 100 emails a day and wants a filter to catch the dangerous ones. Only 8 of those 100 are actually dangerous — the other 92 are normal, boring email. Now imagine the laziest possible filter: one that just says "safe" to everything, every single day, without reading a word.

That filter would be right 92 times out of 100. Its accuracy would be 92%. And it would have caught exactly zero of the dangerous emails — every single attack would get straight through, every single time. The 92% isn't lying about the arithmetic. It's lying about what it implies. "92% correct" quietly gets heard as "this thing is doing its job well," when the honest sentence is "this thing is right most of the time because most days are boring, and it has never once caught the thing it was actually built for."

> **Something that made this click properly**
>
> An industry write-up on fraud models put this failure mode in words that stuck with me: a fraud model hit 99.2% accuracy in testing, got shipped on a Friday, and by Monday it had waved through every fraudulent transaction in the queue — because saying "legitimate" every single time is exactly how you score 99.2% when fraud only shows up once in two hundred cases. The model didn't fail. The metric did.

Once I saw that clearly, I couldn't unsee it, and I started noticing the same shape everywhere — a rare-disease test that's 99.9% accurate by saying "healthy" to everyone, a factory camera that's excellent right up until the one cracked bottle reaches a customer. Different situations, same underlying trick: when the bad case is rare, a model can look great while doing nothing useful.

That's the itch this whole project scratches. Not "let me build a better email filter," but "let me build the thing that would have caught this problem before anyone shipped it."

## What I Checked Before Starting to Build Anything

Before writing a single line of code, I wanted to answer one question honestly: does something like this already exist, and if it does, why would I bother building it again? I went looking piece by piece, because the idea actually breaks into a few separate problems, not one.

### The confusion-matrix part — already solved, nothing to add here

The basic idea of sorting predictions into "caught it / missed it / false alarm / correctly ignored" — what's formally called a confusion matrix — is old and well built out. There are solid, popular libraries (pycm, mlxtend, scikit-learn's own tools) that already do this correctly for straightforward, flat categories. I didn't need to reinvent this part, and I'm not going to — I'll reuse the same basic logic, just extend what it's capable of.

### The part that's actually rare — evaluation that understands a hierarchy of mistakes

Here's where it got interesting. Most real categories aren't flat — they're a tree. Something isn't just "safe" or "dangerous," there's usually a middle ground too (a "suspicious" case that isn't clearly either), and the dangerous branch itself splits into specific types — phishing, malware, fraud. A model that mistakes phishing for malware got the wrong sub-type, but it still correctly realised something was wrong. A model that mistakes phishing for safe made a completely different, much worse kind of mistake — it let the actual harm straight through. And mistaking safe for suspicious is a smaller, more forgivable error than mistaking safe for dangerous outright.

A standard confusion matrix can't tell any of these mistakes apart in degree — it just scores everything as "one wrong answer," full stop. That felt like a real gap, so I went digging to see if anyone had already solved it properly.

Turns out, yes — Apple's own machine learning research team published a paper on exactly this in 2022 (it won a best paper award at CHI, a major human-computer-interaction conference). They noticed their own engineers struggling with this same blind spot and built an internal tool called Neo to fix it. A few academic papers since then have formalised the same idea mathematically — basically, walk up the category tree from the guess and from the real answer until you hit a point where they meet, and however many steps that took is how "big" the mistake was.

The catch: none of this research comes with anything you can actually install and use. Apple never released Neo as public code. The academic papers describe the math but don't ship a ready-to-use tool either — one of them even says a code release is "planned," which tells me this genuinely isn't a solved, packaged problem yet, even though the idea itself is sound and already proven out by serious people. So this became the one piece I'd actually have to build myself from the description of the idea, rather than being able to import it.

### The cost part — well understood, but almost nobody combines it with the tree idea above

Separately, there's a whole area of machine learning called cost-sensitive learning, and its core idea is simple: not all mistakes cost the same, so stop treating them as if they do. A missed fraud case and an annoying false alarm are not the same size of problem, and if you build that difference into how you score a model, you get a much more honest picture of whether it's actually worth using. This is old, well-established, and there's good practical writing on it — and a recent comparison study that tested different fixes for this across thousands of experiments found that simply adjusting the decision threshold (how confident the model needs to be before it commits to "dangerous") works better than most people expect.

What I didn't find anywhere was this cost idea combined with the tree idea from above. People who think about cost usually assume a flat yes/no. People who think about hierarchy usually just use the tree distance itself as a stand-in for cost, rather than letting you plug in a real number. Putting both of these together — a cost that can depend on both how severe the mistake was and how far off the guess was — is the part of this project that isn't really "out there" as one thing yet.

### The part I almost missed — whether the model's confidence can actually be trusted

This one only occurred to me after I'd already sketched out the rest of the project, and it came from a good question about where the "belief" actually lives. The agent being tested doesn't usually just blurt out a final answer — it typically builds up a belief across the possible truths as it looks at evidence (something like "70% safe, 20% suspicious, 10% dangerous") before a decision policy turns that into one final action. My first version of this project only ever looked at that final action — right or wrong — and threw away the confidence number entirely.

The agent only ever sees the evidence in front of it — the email's content, the sender, the patterns — it never gets to directly observe the actual hidden truth. It has to reason about which of the possible truths is most likely, and hold onto that uncertainty honestly, rather than collapsing to a guess too early:

```mermaid
flowchart TD
    E[Visible Evidence] --> A[Agent]
    A -. Cannot directly observe .-> H[Hidden True State]
    H --> H1[Safe]
    H --> H2[Suspicious]
    H --> H3[Dangerous: Phishing]
    H --> H4[Dangerous: Malware]
    H --> H5[Dangerous: Fraud]

That's a real gap, because a model can have excellent accuracy and still be dangerously overconfident — saying "95% sure" and being wrong half the time is a different, arguably worse problem than just being wrong, since nobody double-checks a confident answer. The proper name for this is calibration: grouping predictions by how confident the model claimed to be, then checking whether it was actually right that often. A well-calibrated model that says 90% sure is right about 90% of the time; a badly-calibrated one might say 90% sure and only be right half the time, which is a confidently wrong model wearing a trustworthy mask.

This only works, though, if the model actually gives back a confidence number in the first place — which ties directly into the next thing I had to think through.

### The part I hadn't planned for — what happens when the model's answer isn't a clean label

Everything above quietly assumes the model says something like "phishing" or "safe." Real models don't always answer that way. Some give back a raw score (0.83), some give back a plain number that isn't a probability at all (an estimated rupee amount, say), and an LLM-based agent left to its own devices will often just reply in a full sentence.

Rather than rebuild the whole harness differently for each of those, the fix is to add one small adapter step right at the boundary between the model and the harness — it takes whatever the model handed back and turns it into the one standard shape everything else already expects (a label, plus a confidence number if there is one). A label gets used as-is, a score gets turned into a label with a threshold, a plain number gets compared directly instead of forced into a category tree, and free text gets parsed back into a label and confidence — though the better fix there is just prompting the model to always reply in a fixed format to begin with, so that fallback rarely gets used. Everything after that one step — tree distance, cost, calibration, adversarial testing, base-rate simulation — stays exactly the same no matter which kind of model is being tested. That's actually what makes this a general-purpose harness rather than something tied to one narrow kind of model.

### The AI-agent-safety-testing part — close, but not quite the same target

I also looked for anyone doing something similar specifically for LLM-based agents, since that's the direction a lot of real systems are heading now. I found one recent, small, genuinely well-done project called AgentSentinel — it wraps any agent and checks it for whether it stays truthful, whether it can be tricked by a poisoned prompt, and whether a new version accidentally breaks something that used to work. It's a good project and honestly close in spirit to what I want to build. But its scoring is still flat — pass or fail — with no idea of "how costly," "how structurally wrong," or "how well-calibrated" a failure was. That gap is exactly where mine would sit differently.

On the "can it be tricked" side specifically, there's a well-known, actively maintained list called the OWASP Top 10 for LLM Applications, and the number-one risk on that list, three years running now, is prompt injection — basically, hiding an instruction inside content the model reads, so it does something it shouldn't. That gave me a proper, credible source to build a small set of "try to fool it" test cases from, instead of just making them up myself.

### A quick reality check on "fraud detection dashboard" as the demo

My first instinct for the example to demo this on was fraud detection — it's the classic case people reach for. So I went and looked at what already exists in that exact space, and it's genuinely crowded. I found several near-identical portfolio projects: same public credit-card dataset, RandomForest or XGBoost, a Streamlit dashboard, accuracy/precision/recall at the end. Nothing wrong with any of them individually, but if I built one more, it would blend straight into that pile and prove nothing new about me.

That's when I decided the demo classifier should be something with a natural hierarchy of its own — which is why I landed on a small security/content-moderation style example (safe / suspicious / dangerous: phishing, malware, fraud) instead of fraud. It's not a saturated space the same way, it lines up naturally with the tree-distance idea, and it connects cleanly with the prompt-injection testing piece too.

### What I'm keeping out of this, on purpose

This project has nothing to do with the ICAS work or with the Prescription Safety Assistant project — they're separate on purpose, even though a couple of the underlying ideas (cost of a missed case vs. a false alarm, for instance) happen to show up in both. I'm also not chasing medical data or anything that needs a license or a gated dataset. Everything here will be built on data I generate myself, specifically so I never have to worry about licensing the way the Prescription project had to when it found the drug-interaction API had quietly been shut down.

## So, What Does That Leave Me to Actually Build?

Stripping all of the above down to a plain checklist — what's genuinely mine to build versus what I'm standing on top of:

| Piece | Already Exists — I'll Reuse It | Doesn't Really Exist Yet — I Build It |
|---|---|---|
| Basic right/wrong scoring | Yes — confusion matrix logic from standard libraries | — |
| "How wrong" scoring for a tree of categories | Idea is published (Apple's Neo, academic papers) | Yes — no usable code exists, so I write the tree-walking function myself |
| Turning mistakes into a real cost | The theory and general approach is well documented | Yes — combining it with tree-distance hasn't been done together anywhere I found |
| Checking whether the model's confidence can be trusted | Calibration as a concept is well known in ML evaluation | Yes — combining it with the same cost-and-hierarchy report as everything else is the new part |
| Testing whether the model can be fooled | OWASP's list gives me credible attack patterns to draw from | Yes — wiring those into the same hidden-answer test loop as everything else |
| Showing how the score changes as the rare case gets rarer or more common | The underlying concept (base rate) is well known | Yes — a live, adjustable version tied to a real model doesn't seem to exist anywhere I found |
| Handling models that don't answer in a clean category | — | Yes — the small adapter step that standardises a label, score, number, or free text before scoring |

## How I Think This Should Actually Work

This is the flow I've settled on — one evaluation run, start to finish:

- Start with a test set where I already know the right answers — but keep those answers hidden from the model while it's making its guesses. Nobody grades their own exam while still writing it.
- Let the model guess on every case, one at a time, with no peeking. Whatever it hands back — a label, a score, a number, or free text — gets standardised by a small adapter step before anything else touches it.
- Only after every guess is locked in, reveal the real answers and compare.
- Sort every result into a confusion matrix — then look at that same result several different ways at once: the plain flat score, how far off the guess was on the category tree, what it would actually cost in rupees, and whether the model's stated confidence actually matched how often it was right.
- A handful of deliberately tricky, adversarial cases were mixed into the test set from the start — check whether those got caught too.
- Separately, rerun the same comparison while dialling the rare/dangerous case up or down, to see how much of the score depends on the world being calm rather than the model being good.
- Put all of it together into one report, instead of one number pretending to speak for everything.

The full diagram of this flow lives at [`../assets/errata-flow-diagram.png`](../assets/errata-flow-diagram.png). The step-by-step pseudocode is in [`pseudocode.md`](pseudocode.md).

## What I'm Still Not Sure About

- How strict the tree-distance penalty should feel in practice — I'll probably need to build a small version first and actually look at the numbers before I trust my own instinct on this.
- The ₹ cost figures I'll use at first are just reasonable guesses to make the maths concrete, not real researched numbers — worth being upfront about that rather than pretending they're precise.
- Whether "suspicious" needs its own sub-types the way "dangerous" does, or whether it's fine as a single middle branch — I'm starting with the simpler version and only adding more depth if the demo actually needs it.
- I'm keeping the classifier being tested deliberately simple. The temptation will be to spend time making it smarter, but the actual point of this project is the report it produces, not the model itself — so I need to resist polishing the wrong part.

## Where I'm Actually Starting

Next concrete thing: design the small category tree (safe / suspicious / dangerous: phishing, malware, fraud) and write the little function that walks up that tree to measure how far apart two labels are. That's the one piece with no shortcut available, so it makes sense to get it right first, before anything else gets built on top of it.

## Sources I Actually Leaned On

Not a formal bibliography — just the specific things I read that shaped the decisions above, in case I want to go back to any of them.

- [Accuracy paradox](https://en.wikipedia.org/wiki/Accuracy_paradox) — the Wikipedia page has a genuinely good worked example with the numbers laid out.
- [Base rate fallacy](https://en.wikipedia.org/wiki/Base_rate_fallacy) — the general statistics idea behind why this trick works on people, not just on models.
- [Cost-sensitive machine learning](https://en.wikipedia.org/wiki/Cost-sensitive_machine_learning), general overview.
- [A clear, practical walkthrough of cost-sensitive learning for imbalanced classification](https://machinelearningmastery.com/cost-sensitive-learning-for-imbalanced-classification/).
- [A 2024 paper comparing fixes for imbalanced data](https://arxiv.org/html/2409.19751v1) across thousands of experiments — found threshold-tuning held up best.
- [Apple's Neo paper](https://machinelearning.apple.com/research/generalizing-confusion-matrix) — the CHI 2022 best-paper-award research on hierarchical confusion matrices.
- [A 2024 AISTATS paper formalising tree-distance scoring](https://proceedings.mlr.press/v238/cao24a.html) for hierarchical classification.
- [A paper arguing pass/fail scoring is misleading](https://arxiv.org/pdf/2508.04489), proposing tree-based partial credit; notes a code release is planned but not yet out.
- [AgentSentinel](https://github.com/Shree-2004/Agentsentinel) — the closest existing project I found to this idea, for LLM agents specifically.
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf) — where prompt injection sits as the #1 risk, with real examples.
- [A few near-identical fraud-detection portfolio projects](https://github.com/ominirao/Fraud-Detection-Dashboard) I checked, confirming that space is crowded.
- [TrustLens on PyPI](https://pypi.org/project/trustlens/) — checked while naming this project; an existing, active package doing very similar accuracy-beyond-accuracy auditing, which is why that name was ruled out.
