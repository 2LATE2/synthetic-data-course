# Meeting 2 protocol — fixed before generating any image

Author: Mikołaj Zwiefka

Question: which text-to-image generation settings produce Egyptian Mau images
that help the classifier, compared with the Meeting 1 baselines?

## Fixed for every pool

- `synth-generate`, text-to-image mode, 110 images per pool, seeds 1000–1109
  (image *i* uses seed 1000 + *i*), the starter's default negative prompt.
- Base pool `m2-base`: Stable Diffusion 1.5, 30 steps, guidance 7.5, DPM-Solver
  scheduler, and four varied prompts used in turn:
  1. `a photo of an Egyptian Mau cat sitting indoors, silver coat with random black spots, green eyes, natural light`
  2. `close-up photo of an Egyptian Mau cat lying on a sofa, spotted silver tabby coat, gooseberry green eyes`
  3. `full body photo of an Egyptian Mau cat standing on the floor, short spotted coat, banded tail, home interior`
  4. `candid photo of an Egyptian Mau cat outdoors in a garden, bronze spotted coat, green eyes`

  The prompts describe the breed's real features (random spots, not stripes;
  green eyes; banded tail; silver/bronze colours) and vary pose, framing and
  setting, because the Oxford-IIIT Pet photos are ordinary pet snapshots.
- Classifier training is the unchanged Meeting 1 setup: `synth-train --method
  synthetic --pool <pool>`, 5 seeds (0–4), 55 random images from the pool per seed.
- Same environment as Meeting 1 (Python 3.13.2, torch 2.14.1+cu130, RTX 4060
  Laptop GPU), plus diffusers 0.40.0 / transformers 5.22.2 for generation.

## One setting changed per pool (everything else as in `m2-base`)

| Pool | Changed setting | Value |
| --- | --- | --- |
| `m2-guidance-2` | guidance | 2 |
| `m2-guidance-15` | guidance | 15 |
| `m2-steps-10` | steps | 10 |
| `m2-prompt-simple` | prompt | one prompt: `a photo of an Egyptian Mau cat` |

Three settings are changed (guidance with two values, steps, prompt), which is
what the assignment asks for ("at least three of"). An SDXL-Turbo pool was in the
first draft of this plan but was dropped before any classifier was trained or
any SDXL image was generated, only to avoid a 7 GB model download.

Each run is tagged with the changed setting (`--tag guidance=15`, etc.).
No pool or image is deleted; failed and safety-blocked attempts stay in the manifest.

## Decision rule (validation only)

- Primary measure: mean validation Egyptian Mau recall over 5 seeds.
  Guardrail: macro-F1 over all eight breeds; any macro-F1 loss is reported.
- The pool taken forward is the one with the highest mean validation Mau recall;
  ties are broken by mean macro-F1, then by preferring `m2-base` (fewest changes).
- The choice, its reasoning, and the contact-sheet observations are written down
  before `synth-test` is run. Only the chosen run is tested and compared with the
  Meeting 1 test baselines (`m1-real`, `m1-oversample`, `m1-augment-strong`).
- Five seeds measure training randomness only; one validation Mau photo is
  5 percentage points of recall. No significance claims from five seeds.
