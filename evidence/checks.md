# Implementation verification

Executed locally before training:

- `python -m pytest`: **27 passed** (10.52 seconds).
- `python -m ruff check src tests scripts`: **All checks passed**.

The tests include the starter's split counts, role disjointness, metric and
checkpoint checks, plus 11 new parameterized cases for balancing and augmentation.
No validation/test result is used by these checks to tune the implementation.

Additional checks:

- `synth-data` verified that all 905 prescribed images are available, with the
  required class counts in each role.
- SHA-256 image audit: 905 unique files; zero duplicate groups or cross-role
  exact duplicates (`leakage-check.json`). Near-duplicates are not checked.
- ImageNet-pretrained EfficientNet-B0 GPU forward pass: output shape `(1, 8)`.
- Visual inspection of the training-only augmentation sheet: cats remain
  recognisable in both variants; stronger rotation has more visible black corners.
