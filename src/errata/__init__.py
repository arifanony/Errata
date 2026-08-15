"""
Errata — an evaluation harness for AI classifiers and agents.

This package is the actual implementation, built to follow the pseudocode
in docs/pseudocode.md step by step:

    1. Build the hidden test set
    2. Model predicts, blind
    3. Adapter layer (standardise the model's raw output)
    4. Reveal the real answers
    5. Compare guess vs. real answer
    6. Score it four ways — flat, tree-distance, cost, calibration
    7. Adversarial cases, mixed in
    8. Base-rate simulation
    9. One consolidated errata report

Nothing is implemented yet — this file is a placeholder so the folder
structure is tracked in Git from day one.
"""

__version__ = "0.0.1"
