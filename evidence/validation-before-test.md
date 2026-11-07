# Meeting 1 — Real-Data Baselines

Author: **Mikołaj Zwiefka**

## Question and protocol

Do 55 repeated or transformed minority observations improve Egyptian Mau recognition?
The starter's unchanged `data/split.csv` contains 505 training images (15 Mau,
70 per other breed), 160 validation images (20 per breed), and 240 test images
(30 per breed). Added observations come exclusively from the 15 training Mau photos.
See [protocol.md](protocol.md) for fixed settings and the predeclared decision rule.

## Implementation and checks

`oversample()` shuffles complete rounds of the source list and truncates the last
round. For 55 additions, ten photos are used four times and five three times.
It uses the supplied `random.Random`, leaves the input unchanged, and rejects
invalid budgets or duplicate source names. The source schedule matches the
starter's augmentation schedule for each seed.

`augment()` returns a new PIL image, with horizontal flip (p=0.5), random rotation
within ±10°, and brightness/contrast/saturation jitter of 0.1. No vertical flip,
large crop, or hue shift is added. The variant changes **only rotation to ±25°**.
Both versions are retained behind `--augmentation` for reproducibility.
The starter applies its own crop/flip/colour training transform to **all** methods,
including `real` and `oversample`; our augmentation is an additional transform on
the 55 minority copies, refreshed on every load. Oversampled source pixels are
identical before that common training transform.

Automated tests cover the exact budget, balanced source counts, reproducibility,
input immutability, PIL output shape, changing augmentations, and split disjointness.
The contact sheet in `evidence/augmentation-examples.jpg` shows training photos only.
Visual inspection of those examples confirms that the cats remain recognisable;
the strong variant has more visible black corners and edge cropping. The SHA-256
leakage audit found 905 unique image files and no byte-identical duplicates across
roles (see `evidence/leakage-check.json`). This audit does not detect near-duplicates.

## Validation — measured results, all seeds

| Run | Seed | Egyptian Mau recall | Macro-F1 | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| m1-real | 0 | 0.4500 | 0.8609 | 0.8688 |
| m1-real | 1 | 0.5000 | 0.8570 | 0.8625 |
| m1-real | 2 | 0.4500 | 0.8554 | 0.8625 |
| m1-real | 3 | 0.4000 | 0.8403 | 0.8500 |
| m1-real | 4 | 0.6000 | 0.8715 | 0.8750 |
| **m1-real** | **mean ± SD** | 0.4800 ± 0.0758 | 0.8570 ± 0.0112 | 0.8638 ± 0.0093 |
| m1-oversample | 0 | 0.6500 | 0.8912 | 0.8938 |
| m1-oversample | 1 | 0.6000 | 0.8596 | 0.8625 |
| m1-oversample | 2 | 0.6500 | 0.8730 | 0.8750 |
| m1-oversample | 3 | 0.7500 | 0.8934 | 0.8938 |
| m1-oversample | 4 | 0.7000 | 0.8984 | 0.9000 |
| **m1-oversample** | **mean ± SD** | 0.6700 ± 0.0570 | 0.8831 ± 0.0163 | 0.8850 ± 0.0157 |
| m1-augment | 0 | 0.6000 | 0.8836 | 0.8875 |
| m1-augment | 1 | 0.6000 | 0.8718 | 0.8750 |
| m1-augment | 2 | 0.6500 | 0.8715 | 0.8750 |
| m1-augment | 3 | 0.7500 | 0.9057 | 0.9062 |
| m1-augment | 4 | 0.7500 | 0.8989 | 0.9000 |
| **m1-augment** | **mean ± SD** | 0.6700 ± 0.0758 | 0.8863 ± 0.0156 | 0.8888 ± 0.0143 |
| m1-augment-strong | 0 | 0.6000 | 0.8899 | 0.8938 |
| m1-augment-strong | 1 | 0.6000 | 0.8718 | 0.8750 |
| m1-augment-strong | 2 | 0.6500 | 0.8778 | 0.8812 |
| m1-augment-strong | 3 | 0.7500 | 0.8920 | 0.8938 |
| m1-augment-strong | 4 | 0.8000 | 0.9055 | 0.9062 |
| **m1-augment-strong** | **mean ± SD** | 0.6800 ± 0.0908 | 0.8874 ± 0.0131 | 0.8900 ± 0.0122 |

![Validation comparison](evidence/val-comparison.png)

- **m1-oversample** versus real: Mau recall: +19.00 pp mean paired change (SD 10.25 pp; individual changes +20.00, +10.00, +20.00, +35.00, +10.00 pp); macro-F1: +2.61 pp mean paired change (SD 1.85 pp; individual changes +3.03, +0.26, +1.76, +5.30, +2.68 pp).
- **m1-augment** versus real: Mau recall: +19.00 pp mean paired change (SD 9.62 pp; individual changes +15.00, +10.00, +20.00, +35.00, +15.00 pp); macro-F1: +2.93 pp mean paired change (SD 2.08 pp; individual changes +2.27, +1.48, +1.61, +6.53, +2.73 pp).
- **m1-augment-strong** versus real: Mau recall: +20.00 pp mean paired change (SD 9.35 pp; individual changes +15.00, +10.00, +20.00, +35.00, +20.00 pp); macro-F1: +3.04 pp mean paired change (SD 1.39 pp; individual changes +2.90, +1.48, +2.24, +5.17, +3.40 pp).

### Augmentation comparison and decision (written before testing)

Mild mean Mau recall: 0.6700;
strong: 0.6800.
Mild mean macro-F1: 0.8863;
strong: 0.8874.
Increasing the rotation limit therefore changes mean recall by
+1.00 percentage points (paired SD
2.24 pp), and mean macro-F1 by
+0.11 pp. It improves Mau recall in
1/5 seeds, ties in
4/5, and worsens it in
0/5. The rotation range is the only changed
augmentation setting, so this comparison measures its effect within this setup.
The selected augmentation baseline is **m1-augment-strong**, according to the fixed
validation rule: Highest mean validation Mau recall; tie: macro-F1; exact tie: mild.
The decision was recorded at 2026-10-24T08:03:13.965621+00:00 in
`evidence/validation-decision.json`, together with hashes of the validation files.

Five seeds measure training randomness on one fixed split, not uncertainty across
new populations or new data splits. With only 20 validation Mau photos, one photo
changes recall by 5 percentage points. Mean differences must be interpreted
alongside their paired spread; these runs alone do not establish statistical
significance. Stronger rotation may add useful pose variation, but may also
introduce black corners and remove edge content; any observed effect is specific
to this split and training setup.

## Reproduction

```bash
uv sync --locked
uv run synth-data
uv run pytest
uv run synth-train --name m1-real --method real
uv run synth-train --name m1-oversample --method oversample
uv run synth-train --name m1-augment --method augment --augmentation mild
uv run synth-train --name m1-augment-strong --method augment --augmentation strong
uv run python scripts/preview.py
uv run python scripts/report.py validation
uv run synth-test --run m1-real
uv run synth-test --run m1-oversample
uv run synth-test --run m1-augment-strong
uv run python scripts/report.py final
```

The validation report refuses to overwrite an existing decision. To repeat the
whole experiment, use a fresh checkout/output directory rather than mixing runs.
The JSON files contain unrounded values, per-seed predictions, settings, hardware,
and runtime. CSV tables and plots are generated directly from those JSON files.
The local measurements used the installed CUDA 13.0 runtime and main package
versions in `requirements-runtime.txt`, rather than the template's `uv.lock`.
See `protocol.md`. CPU thread limits were `OMP_NUM_THREADS=4` and
`MKL_NUM_THREADS=4` for every training run.

## Test

Not evaluated yet. The validation decision above is locked.
