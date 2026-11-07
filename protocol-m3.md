# Meeting 3 protocol — fixed before generating any image

Author: Mikołaj Zwiefka

Question: how close to the 15 real Egyptian Mau training photos should the
synthetic images be to help the classifier most?

## Fixed for every pool

- `synth-generate` with SD 1.5 defaults (30 steps, guidance 7.5, DPM-Solver),
  110 images per pool, seeds 1000–1109. Image *i* starts from training photo
  *i* mod 15 (all 15 training Mau photos, the starter's order) and seed 1000 + *i*,
  so image *i* of every pool has the same source photo and the same noise.
- Only the 15 **training** photos are used as sources (the starter enforces this).
- Prompt: the four prompts of `m2-base` (the pool taken forward from Meeting 2),
  used in turn, identical in every pool, so that only strength or scale changes
  within a sweep and the difference to `m2-base` is the photo conditioning.
- Classifier training unchanged: `synth-train --method synthetic`, 5 seeds,
  55 images drawn per seed (the starter spreads them evenly over source photos).

## Sweeps (one setting changed at a time)

| Pool | Mode | Setting |
| --- | --- | --- |
| `m3-strength-0.3` | img2img | strength 0.3 (9 effective steps) |
| `m3-strength-0.5` | img2img | strength 0.5 (15 effective steps) |
| `m3-strength-0.7` | img2img | strength 0.7 (21 effective steps) |
| `m3-strength-0.9` | img2img | strength 0.9 (27 effective steps) |
| `m3-ip-0.3` | IP-Adapter | scale 0.3 |
| `m3-ip-0.5` | IP-Adapter | scale 0.5 |
| `m3-ip-0.7` | IP-Adapter | scale 0.7 |
| `m3-ip-1.0` | IP-Adapter | scale 1.0 |

Runs are tagged `--tag mode=img2img --tag strength=0.5` or
`--tag mode=ip-adapter --tag scale=0.5`. No pool or image is deleted.

## Closeness measure (descriptive only, not used for choosing)

For every usable image: cosine similarity between ImageNet-pretrained
EfficientNet-B0 features (torchvision weights, not a trained course classifier)
of the image and of its source photo, and the similarity to the *nearest* of
the 15 training Mau photos (also computed for `m2-base`, which has no source).
A pixel-level distance (mean absolute difference at 128×128) to the source photo
is reported as well. These numbers place every pool on one "closeness" axis.

## Decision rule (validation only)

- For each mode separately, the pool taken forward has the highest mean
  validation Egyptian Mau recall; ties: mean macro-F1; then the 0.5 pool.
- Each chosen pool is compared on validation with `m2-base` and the Meeting 1
  baselines. Choices and interpretation are written before `synth-test`.
- Only the two chosen runs are tested and compared with the test results of
  Meetings 1 and 2 (`m1-real`, `m1-oversample`, `m1-augment-strong`, `m2-base`).
- Five seeds measure training randomness only; no significance claims.
