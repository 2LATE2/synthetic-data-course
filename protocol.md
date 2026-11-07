# Protocol fixed before training

Author: Mikołaj Zwiefka

This implementation follows `as1.pdf` and the supplied course template, rather
than the newer version of the course website.

- Use `data/split.csv` unchanged: train 70 per majority breed / 15 Egyptian Mau,
  validation 20 per breed, test 30 per breed. No new split is drawn.
- Add exactly 55 training Egyptian Mau observations for oversampling/augmentation.
- EfficientNet-B0 with ImageNet weights; fine-tune all parameters for 8 epochs,
  batch size 64, AdamW lr 0.0003, weight decay 0.01, cosine LR schedule.
- Retain the starter's common training transforms for every condition.
- Seeds 0, 1, 2, 3, 4, same training settings and hardware for all four runs.
- Mild extra augmentation: horizontal flip p=0.5, rotation ±10 degrees,
  brightness/contrast/saturation jitter 0.1. Variant: only rotation becomes ±25.
- Primary measure: Egyptian Mau recall. Guardrail: macro-F1 over all eight breeds.
  Report accuracy as an additional descriptive measure.
- Select the augmentation variant with higher mean validation Mau recall;
  break ties by mean macro-F1, then prefer mild on exact ties. Explicitly report
  any macro-F1 loss. Do not claim significance based solely on five seeds.
- Record the choice and validation interpretation before evaluating test data.
  Test real, oversampling, and the chosen augmentation variant only, all 5 seeds.
- Save individual seed metrics, means, sample SD (ddof=1), paired changes versus
  real, plots, predictions, and a training-only augmentation contact sheet.
- Test observations never enter augmentation, training, or model selection.

## Execution environment

The local execution reuses the installed CUDA-enabled PyTorch through an isolated
Python 3.13 virtual environment with `--system-site-packages`. The supplied
`uv.lock` is retained, but was **not** the environment used for these measurements.
Exact package versions are recorded in `evidence/runtime-versions.json`; hardware
and Python/PyTorch versions are also saved in each seed's `run.json`.
The same environment is used for every condition. The module commands
`python -m synthdata.data`, `python -m synthdata.train`, and `python -m synthdata.test`
are equivalent to the template's installed `synth-*` entry points.
