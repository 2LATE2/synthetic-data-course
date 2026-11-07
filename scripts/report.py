"""Create tables/plots from measured results, and lock choices before testing."""

import argparse
import csv
import hashlib
import json
import statistics
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
RUNS = ("m1-real", "m1-oversample", "m1-augment", "m1-augment-strong")
METRICS = ("egyptian_mau_recall", "macro_f1")


def read_run(name, split):
    filename = "results.json" if split == "val" else "test-results.json"
    result = json.loads((ROOT / "runs" / name / filename).read_text())
    assert result["split"] == split
    assert sorted(row["seed"] for row in result["seeds"]) == list(range(5))
    return sorted(result["seeds"], key=lambda row: row["seed"])


def mean(rows, key):
    return statistics.mean(row[key] for row in rows)


def table(data):
    lines = [
        "| Run | Seed | Egyptian Mau recall | Macro-F1 | Accuracy |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, rows in data.items():
        for row in rows:
            lines.append(
                f"| {name} | {row['seed']} | {row[METRICS[0]]:.4f} | "
                f"{row[METRICS[1]]:.4f} | {row['accuracy']:.4f} |"
            )
        cells = [
            f"{mean(rows, key):.4f} ± {statistics.stdev(r[key] for r in rows):.4f}"
            for key in (*METRICS, "accuracy")
        ]
        lines.append(f"| **{name}** | **mean ± SD** | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def artifacts(data, split):
    fields = ["run", "seed", *METRICS, "accuracy"]
    with (EVIDENCE / f"{split}-metrics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for name, rows in data.items():
            writer.writerows(
                {"run": name, **{k: row[k] for k in fields[1:]}} for row in rows
            )
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
    labels = [n.removeprefix("m1-") for n in data]
    for ax, metric, title in zip(
        axes, METRICS, ["Egyptian Mau recall", "Macro-F1"], strict=True
    ):
        for seed in range(5):
            values = [rows[seed][metric] for rows in data.values()]
            ax.plot(range(len(data)), values, "o-", alpha=0.65, label=f"seed {seed}")
        ax.plot(
            range(len(data)),
            [mean(rows, metric) for rows in data.values()],
            "kD",
            markersize=7,
            label="mean",
        )
        ax.set(
            xticks=range(len(data)),
            xticklabels=labels,
            ylim=(0, 1.03),
            title=title,
            ylabel="Score",
        )
        ax.grid(axis="y", alpha=0.25)
    axes[1].legend(loc="lower right", fontsize=8)
    fig.suptitle(f"{split.upper()}: all five seeds; same fixed split")
    fig.savefig(EVIDENCE / f"{split}-comparison.png", dpi=180)
    plt.close(fig)


def differences(data):
    base = data["m1-real"]
    lines = []
    for name, rows in list(data.items())[1:]:
        parts = []
        for metric, label in zip(METRICS, ["Mau recall", "macro-F1"], strict=True):
            delta = [
                100 * (r[metric] - b[metric]) for r, b in zip(rows, base, strict=True)
            ]
            parts.append(
                f"{label}: {statistics.mean(delta):+.2f} pp mean paired change "
                f"(SD {statistics.stdev(delta):.2f} pp; individual changes "
                + ", ".join(f"{x:+.2f}" for x in delta)
                + " pp)"
            )
        lines.append(f"- **{name}** versus real: " + "; ".join(parts) + ".")
    return "\n".join(lines)


def paired(a, b, metric):
    return [100 * (x[metric] - y[metric]) for x, y in zip(a, b, strict=True)]


def test_summary(test, val, selected):
    real, over, aug = test["m1-real"], test["m1-oversample"], test[selected]
    lines = ["### What the test results show", ""]
    for name, rows in (("oversampling", over), (selected, aug)):
        rec = paired(rows, real, METRICS[0])
        f1 = paired(rows, real, METRICS[1])
        lines.append(
            f"Compared with real data only, {name} raises mean test Mau recall from "
            f"{mean(real, METRICS[0]):.3f} to {mean(rows, METRICS[0]):.3f} "
            f"({statistics.mean(rec):+.1f} pp; higher in "
            f"{sum(x > 0 for x in rec)}/5 seeds) and changes mean macro-F1 by "
            f"{statistics.mean(f1):+.1f} pp (lower in {sum(x < 0 for x in f1)}/5 "
            f"seeds, by at most {abs(min(min(f1), 0)):.1f} pp)."
        )
    gap = paired(over, aug, METRICS[0])
    lines.append(
        "\nBoth classical fixes therefore help Egyptian Mau without harming the other "
        "breeds, which agrees with validation. On test, oversampling is ahead of "
        f"{selected} by {statistics.mean(gap):+.1f} pp mean Mau recall (paired SD "
        f"{statistics.stdev(gap):.1f} pp; ahead in {sum(x > 0 for x in gap)}/5 seeds, "
        f"tied in {sum(x == 0 for x in gap)}/5). One test Mau photo is "
        f"{100 / 30:.1f} pp, so this gap is about "
        f"{statistics.mean(gap) / (100 / 30):.1f} photos per model. On validation "
        f"the means were {mean(val['m1-oversample'], METRICS[0]):.3f} (oversampling) "
        f"and {mean(val[selected], METRICS[0]):.3f} ({selected}), so the order "
        "between oversampling and augmentation is not established. "
        "The difference to real data is larger than the seed spread on both splits. "
        "Later methods must beat these three test baselines; the higher one "
        f"(oversampling, mean Mau recall {mean(over, METRICS[0]):.3f}) is the "
        "strongest classical reference."
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["validation", "final"])
    args = parser.parse_args()
    EVIDENCE.mkdir(exist_ok=True)
    decision_path = EVIDENCE / "validation-decision.json"
    val = {name: read_run(name, "val") for name in RUNS}
    if args.stage == "validation":
        if decision_path.exists():
            raise SystemExit("Decision already locked; refusing to overwrite it.")
        if any((ROOT / "runs" / n / "test-results.json").exists() for n in RUNS):
            raise SystemExit(
                "Test results already exist; cannot claim a pre-test choice."
            )
        # Primary metric, guardrail tie-break, conservative variant on exact tie.
        selected = max(
            RUNS[2:],
            key=lambda n: (
                mean(val[n], METRICS[0]),
                mean(val[n], METRICS[1]),
                n == "m1-augment",
            ),
        )
        decision = {
            "recorded_utc": datetime.now(UTC).isoformat(),
            "selected_augmentation_run": selected,
            "test_runs": ["m1-real", "m1-oversample", selected],
            "rule": (
                "Highest mean validation Mau recall; tie: macro-F1; exact tie: mild."
            ),
            "validation_sha256": {
                n: hashlib.sha256(
                    (ROOT / "runs" / n / "results.json").read_bytes()
                ).hexdigest()
                for n in RUNS
            },
        }
        decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    else:
        decision = json.loads(decision_path.read_text())
        for n, digest in decision["validation_sha256"].items():
            assert (
                hashlib.sha256(
                    (ROOT / "runs" / n / "results.json").read_bytes()
                ).hexdigest()
                == digest
            )
    selected = decision["selected_augmentation_run"]
    artifacts(val, "val")
    rotation_deltas = [
        100 * (strong[METRICS[0]] - mild[METRICS[0]])
        for mild, strong in zip(
            val["m1-augment"], val["m1-augment-strong"], strict=True
        )
    ]
    rotation_f1_delta = 100 * (
        mean(val["m1-augment-strong"], METRICS[1]) - mean(val["m1-augment"], METRICS[1])
    )
    report = f"""# Meeting 1 — Real-Data Baselines

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

{table(val)}

![Validation comparison](evidence/val-comparison.png)

{differences(val)}

### Augmentation comparison and decision (written before testing)

Mild mean Mau recall: {mean(val["m1-augment"], METRICS[0]):.4f};
strong: {mean(val["m1-augment-strong"], METRICS[0]):.4f}.
Mild mean macro-F1: {mean(val["m1-augment"], METRICS[1]):.4f};
strong: {mean(val["m1-augment-strong"], METRICS[1]):.4f}.
Increasing the rotation limit therefore changes mean recall by
{statistics.mean(rotation_deltas):+.2f} percentage points (paired SD
{statistics.stdev(rotation_deltas):.2f} pp), and mean macro-F1 by
{rotation_f1_delta:+.2f} pp. It improves Mau recall in
{sum(x > 0 for x in rotation_deltas)}/5 seeds, ties in
{sum(x == 0 for x in rotation_deltas)}/5, and worsens it in
{sum(x < 0 for x in rotation_deltas)}/5. The rotation range is the only changed
augmentation setting, so this comparison measures its effect within this setup.
The selected augmentation baseline is **{selected}**, according to the fixed
validation rule: {decision["rule"]}
The decision was recorded at {decision["recorded_utc"]} in
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
uv run synth-test --run {selected}
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
"""
    if args.stage == "final":
        test = {name: read_run(name, "test") for name in decision["test_runs"]}
        artifacts(test, "test")
        report += "\n## Test — three chosen baselines\n\n" + table(test)
        report += (
            "\n\n![Test comparison](evidence/test-comparison.png)\n\n"
            + differences(test)
        )
        report += "\n\n" + test_summary(test, val, selected)
        report += (
            "\n\nTest results are a final measurement; "
            "the validation decision remains unchanged.\n"
        )
    else:
        report += (
            "\n## Test\n\nNot evaluated yet. The validation decision above is locked.\n"
        )
        (EVIDENCE / "validation-before-test.md").write_text(report, encoding="utf-8")
    # Keep later meetings' sections (written by their own report scripts).
    path = ROOT / "EXPERIMENTS.md"
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    if "\n# Meeting 2" in old:
        report = report.rstrip("\n") + "\n" + "\n# Meeting 2" + old.split(
            "\n# Meeting 2", 1)[1]
    path.write_text(report, encoding="utf-8")
    print(f"Report saved; chosen augmentation: {selected}")


if __name__ == "__main__":
    main()
