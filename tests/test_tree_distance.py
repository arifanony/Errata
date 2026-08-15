"""
Placeholder test file for the tree_distance() function described in
docs/pseudocode.md, Step 6b.

Once src/errata/scoring.py (or similar) implements tree_distance(),
these tests should be filled in to check things like:

    - tree_distance("phishing", "phishing") == 0
    - tree_distance("phishing", "malware") is small (same branch)
    - tree_distance("phishing", "safe") is bigger (different branch)
    - tree_distance("safe", "suspicious") is smaller than tree_distance("safe", "dangerous")

Nothing is implemented yet — this file exists so the test structure
is in place from day one, and so `pytest` has something to discover.
"""

import pytest


@pytest.mark.skip(reason="tree_distance() not implemented yet — see docs/pseudocode.md Step 6b")
def test_tree_distance_placeholder():
    assert True
