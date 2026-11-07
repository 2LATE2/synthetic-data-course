"""Meeting 2 report: tables, plots and image grids from measured files.

    python scripts/report_m2.py validation   # lock the pool choice (before test)
    python scripts/report_m2.py final        # add the chosen run's test results

The Meeting 2 section of EXPERIMENTS.md is everything from "# Meeting 2" on;
the Meeting 1 part above it is left untouched. Hand-written observations
(failure types, interpretation) live in evidence/m2-observations.md and are
included verbatim; example failure images are listed in evidence/m2-failures.json.
"""

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
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
BASELINES = ("m1-real", "m1-oversample", "m1-augment-strong")
POOLS = (
    "m2-base",
    "m2-guidance-2",
    "m2-guidance-15",
    "m2-steps-10",
    "m2-prompt-simple",
)
# Each comparison: changed setting, x-axis label, (run, x value) in order.
COMPARISONS = [
    (
        "guidance",
        "guidance scale",
        [("m2-guidance-2", 2), ("m2-base", 7.5), ("m2-guidance-15", 15)],
    ),
    ("steps", "denoising steps", [("m2-steps-10", 10), ("m2-base", 30)]),
    ("prompt", "prompt", [("m2-base", "4 varied"), ("m2-prompt-simple", "1 simple")]),
]
METRICS = ("egyptian_mau_recall", "macro_f1")
LABELS = {"egyptian_mau_recall": "Egyptian Mau recall", "macro_f1": "Macro-F1"}
BREEDS = [
    "Abyssinian",
    "Bengal",
    "Birman",
    "Bombay",
    "Egyptian Mau",
    "Ragdoll",
    "Russian Blue",
    "Siamese",
]
MAU, BENGAL = BREEDS.index("Egyptian Mau"), BREEDS.index("Bengal")
GRID_SEEDS = (1000, 1001, 1004, 1009)
MARKER = "\n# Meeting 2"


def existing(names, filename="results.json"):
    return [n for n in names if (ROOT / "runs" / n / filename).exists()]


def read_run(name, split="val"):
    filename = "results.json" if split == "val" else "test-results.json"
    result = json.loads((ROOT / "runs" / name / filename).read_text())
    assert result["split"] == split
    assert sorted(row["seed"] for row in result["seeds"]) == list(range(5)), name
    return sorted(result["seeds"], key=lambda row: row["seed"])


def mean(rows, key):
    return statistics.mean(row[key] for row in rows)


def sd(rows, key):
    return statistics.stdev(row[key] for row in rows)


def confusion(name, split="val"):
    """Mean per seed: Mau photos called Bengal, other photos called Mau."""
    prefix = "" if split == "val" else "test-"
    to_bengal, false_mau = [], []
    for seed in range(5):
        path = ROOT / "runs" / name / f"seed-{seed}" / f"{prefix}metrics.json"
        matrix = json.loads(path.read_text())["confusion"]
        to_bengal.append(matrix[MAU][BENGAL])
        false_mau.append(sum(matrix[i][MAU] for i in range(len(BREEDS)) if i != MAU))
    return statistics.mean(to_bengal), statistics.mean(false_mau)


def pool_stats(name):
    pool = ROOT / "pools" / name
    records = {}
    for line in (pool / "manifest.jsonl").read_text().splitlines():
        if line:
            record = json.loads(line)
            records[record["sample_id"]] = record
    rows = list(records.values())
    settings = json.loads((pool / "pool.json").read_text())
    ok = [r for r in rows if r["status"] == "ok"]
    return {
        "attempts": len(rows),
        "usable": len(ok),
        "blocked": sum(r["status"] == "safety_blocked" for r in rows),
        "seconds": statistics.mean(r["seconds"] for r in rows),
        "vram": max((r["peak_vram_mb"] or 0) for r in rows),
        "model": settings["model"],
        "steps": settings["steps"],
        "guidance": settings["guidance"],
        "scheduler": settings["scheduler"],
        "prompts": len(settings["prompts"]),
    }


def seed_table(data):
    lines = [
        "| Run | Seed | Egyptian Mau recall | Macro-F1 | Accuracy |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, rows in data.items():
        for row in rows:
            lines.append(
                f"| {name} | {row['seed']} | {row['egyptian_mau_recall']:.4f} | "
                f"{row['macro_f1']:.4f} | {row['accuracy']:.4f} |"
            )
        cells = [
            f"{mean(rows, k):.4f} ± {sd(rows, k):.4f}" for k in (*METRICS, "accuracy")
        ]
        lines.append(f"| **{name}** | **mean ± SD** | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def paired(rows, base, key):
    return [100 * (r[key] - b[key]) for r, b in zip(rows, base, strict=True)]


def summary_table(data, split="val"):
    base = data.get("m2-base")
    if base is None or split == "test":
        lines = [
            "| Run | Mau recall (mean ± SD) | Macro-F1 (mean ± SD) | "
            "Mau→Bengal per model | Other breeds→Mau per model |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for name, rows in data.items():
            to_bengal, false_mau = confusion(name, split)
            lines.append(
                f"| {name} | {mean(rows, METRICS[0]):.3f} ± "
                f"{sd(rows, METRICS[0]):.3f} | {mean(rows, METRICS[1]):.3f} ± "
                f"{sd(rows, METRICS[1]):.3f} | {to_bengal:.1f} | {false_mau:.1f} |"
            )
        return "\n".join(lines)
    lines = [
        "| Run | Mau recall (mean ± SD) | Macro-F1 (mean ± SD) | Δ Mau recall vs "
        "m2-base, pp (paired SD; seeds +/=/−) | Δ macro-F1 vs m2-base, pp | "
        "Mau→Bengal per model | Other breeds→Mau per model |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, rows in data.items():
        if name.startswith(("m2-", "m3-")) and name != "m2-base":
            d = paired(rows, base, METRICS[0])
            f = paired(rows, base, METRICS[1])
            delta = (
                f"{statistics.mean(d):+.1f} ({statistics.stdev(d):.1f}; "
                f"{sum(x > 0 for x in d)}/{sum(x == 0 for x in d)}/"
                f"{sum(x < 0 for x in d)})"
            )
            fdelta = f"{statistics.mean(f):+.2f}"
        else:
            delta = fdelta = "–"
        to_bengal, false_mau = confusion(name, split)
        lines.append(
            f"| {name} | {mean(rows, METRICS[0]):.3f} ± {sd(rows, METRICS[0]):.3f} | "
            f"{mean(rows, METRICS[1]):.3f} ± {sd(rows, METRICS[1]):.3f} | {delta} | "
            f"{fdelta} | {to_bengal:.1f} | {false_mau:.1f} |"
        )
    return "\n".join(lines)


def pool_table(names):
    lines = [
        "| Pool | Model | Steps | Guidance | Scheduler | Prompts | Usable / attempts "
        "| Safety-blocked | s per image | Peak VRAM, MB |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in names:
        s = pool_stats(name)
        lines.append(
            f"| `{name}` | {s['model']} | {s['steps']} | {s['guidance']:g} | "
            f"{s['scheduler']} | {s['prompts']} | {s['usable']} / {s['attempts']} | "
            f"{s['blocked']} | {s['seconds']:.1f} | {s['vram']} |"
        )
    return "\n".join(lines)


def write_csv(data, path):
    fields = ["run", "seed", *METRICS, "accuracy"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for name, rows in data.items():
            writer.writerows(
                {"run": name, **{k: r[k] for k in fields[1:]}} for r in rows
            )


def comparison_plot(val, base_val, path):
    comps = [c for c in COMPARISONS if all(n in val for n, _ in c[2])]
    fig, axes = plt.subplots(
        2,
        len(comps),
        figsize=(4.2 * len(comps), 8),
        layout="constrained",
        squeeze=False,
    )
    styles = {"m1-real": ":", "m1-oversample": "--", "m1-augment-strong": "-."}
    for col, (setting, xlabel, runs) in enumerate(comps):
        for row, metric in enumerate(METRICS):
            ax = axes[row][col]
            xs = list(range(len(runs)))
            for seed in range(5):
                ax.plot(
                    xs,
                    [val[n][seed][metric] for n, _ in runs],
                    "o-",
                    alpha=0.55,
                    color=f"C{seed}",
                    label=f"seed {seed}" if col == 0 else None,
                )
            ax.plot(
                xs,
                [mean(val[n], metric) for n, _ in runs],
                "kD",
                ms=8,
                label="mean" if col == 0 else None,
            )
            for name, style in styles.items():
                ax.axhline(
                    mean(base_val[name], metric),
                    color="grey",
                    ls=style,
                    lw=1.2,
                    label=f"{name} (mean)" if col == 0 else None,
                )
            ax.set_xticks(xs, [str(x) for _, x in runs])
            ax.set_xlim(-0.4, len(runs) - 0.6)
            ax.set_xlabel(xlabel)
            ax.set_ylim((0.3, 1.0) if metric == METRICS[0] else (0.8, 0.95))
            ax.grid(axis="y", alpha=0.25)
            if col == 0:
                ax.set_ylabel(LABELS[metric])
            if row == 0:
                ax.set_title(f"changed: {setting}")
    fig.legend(
        *axes[0][0].get_legend_handles_labels(),
        loc="outside lower center",
        ncol=9,
        fontsize=8,
    )
    fig.suptitle(
        "Validation, all five seeds; one setting changed per pool "
        "(grey lines: Meeting 1 baselines)"
    )
    fig.savefig(path, dpi=150)
    plt.close(fig)


def overview_plot(data, path, split):
    names = list(data)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), layout="constrained")
    for ax, metric in zip(axes, METRICS, strict=True):
        for i, name in enumerate(names):
            values = [r[metric] for r in data[name]]
            colour = "C7" if name.startswith("m1-") else "C0"
            ax.scatter([i] * 5, values, color=colour, alpha=0.5, s=25)
            ax.errorbar(
                i,
                statistics.mean(values),
                yerr=statistics.stdev(values),
                fmt="kD",
                capsize=4,
                ms=6,
            )
        ax.set_xticks(
            range(len(names)),
            [n.removeprefix("m1-").removeprefix("m2-") for n in names],
            rotation=35,
            ha="right",
        )
        ax.set_title(LABELS[metric])
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(
        f"{split.upper()}: every seed (dots), mean ± SD (diamonds); "
        "grey = Meeting 1 baselines"
    )
    fig.savefig(path, dpi=150)
    plt.close(fig)


def tile(path, size=200):
    return ImageOps.fit(Image.open(path).convert("RGB"), (size, size))


def seed_grid(names, path, size=200, label_w=170):
    """Rows: pools; columns: the same seeds, i.e. the same starting noise."""
    sheet = Image.new(
        "RGB", (label_w + size * len(GRID_SEEDS), 22 + size * len(names)), "white"
    )
    draw = ImageDraw.Draw(sheet)
    for c, seed in enumerate(GRID_SEEDS):
        draw.text((label_w + c * size + 6, 5), f"seed {seed}", fill="black")
    for r, name in enumerate(names):
        y = 22 + r * size
        draw.text((6, y + size // 2 - 6), name, fill="black")
        for c, seed in enumerate(GRID_SEEDS):
            file = ROOT / "pools" / name / "images" / f"{name}-{seed - 1000:04d}.png"
            sheet.paste(tile(file, size), (label_w + c * size, y))
    sheet.save(path, quality=90)


def failure_sheet(items, path, size=210, columns=5):
    rows = -(-len(items) // columns)
    sheet = Image.new("RGB", (columns * size, rows * (size + 34)), "white")
    draw = ImageDraw.Draw(sheet)
    for i, item in enumerate(items):
        x, y = (i % columns) * size, (i // columns) * (size + 34)
        file = (
            ROOT
            / "pools"
            / item["pool"]
            / "images"
            / f"{item['pool']}-{item['index']:04d}.png"
        )
        sheet.paste(tile(file, size), (x, y))
        draw.text((x + 4, y + size + 3), item["label"], fill="black")
        draw.text(
            (x + 4, y + size + 18), f"{item['pool']} #{item['index']}", fill="grey"
        )
    sheet.save(path, quality=90)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["draft", "validation", "final"])
    args = parser.parse_args()
    decision_path = EVIDENCE / "m2-decision.json"
    names = existing(POOLS)
    val = {n: read_run(n) for n in names}
    base_val = {n: read_run(n) for n in BASELINES}

    if args.stage == "validation":
        if decision_path.exists():
            raise SystemExit(
                "Meeting 2 decision already locked; refusing to overwrite."
            )
        missing = [n for n in POOLS if n not in val]
        if missing:
            raise SystemExit(f"runs missing: {missing}")
        if existing(POOLS, "test-results.json"):
            raise SystemExit("A Meeting 2 run was already tested.")
        chosen = max(
            POOLS,
            key=lambda n: (
                mean(val[n], METRICS[0]),
                mean(val[n], METRICS[1]),
                n == "m2-base",
            ),
        )
        decision = {
            "recorded_utc": datetime.now(UTC).isoformat(),
            "chosen_pool": chosen,
            "rule": "Highest mean validation Mau recall; tie: macro-F1; then m2-base.",
            "validation_sha256": {
                n: hashlib.sha256(
                    (ROOT / "runs" / n / "results.json").read_bytes()
                ).hexdigest()
                for n in POOLS
            },
        }
        decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    elif args.stage == "final":
        decision = json.loads(decision_path.read_text())
        for n, digest in decision["validation_sha256"].items():
            actual = hashlib.sha256((ROOT / "runs" / n / "results.json").read_bytes())
            assert actual.hexdigest() == digest, f"{n} changed after the decision"
    else:
        decision = None

    write_csv({**base_val, **val}, EVIDENCE / "m2-val-metrics.csv")
    comparison_plot(val, base_val, EVIDENCE / "m2-val-comparisons.png")
    overview_plot({**base_val, **val}, EVIDENCE / "m2-val-overview.png", "val")
    seed_grid(names, EVIDENCE / "m2-seed-grid.jpg")
    failures_file = EVIDENCE / "m2-failures.json"
    if failures_file.exists():
        failure_sheet(
            json.loads(failures_file.read_text(encoding="utf-8")),
            EVIDENCE / "m2-failures.jpg",
        )
    observations = EVIDENCE / "m2-observations.md"
    notes = observations.read_text(encoding="utf-8") if observations.exists() else ""
    interp_file = EVIDENCE / "m2-val-interpretation.md"
    interpretation = (
        interp_file.read_text(encoding="utf-8") if interp_file.exists() else ""
    )

    text = f"""
# Meeting 2 — Text-to-Image Generation

Plan, prompts and decision rule were fixed before generating:
[protocol-m2.md](protocol-m2.md). Every pool was made with `synth-generate`
(110 attempts, seeds 1000–1109) and every run with `synth-train --method synthetic`
(5 seeds; each seed draws a different random 55 images from the pool).
Commands: [scripts/run_m2.py](scripts/run_m2.py).

## Pools

{pool_table(names)}

Contact sheets (first 24 attempts, failed ones included): {
        ", ".join(f"[{n}](pools/{n}/contact-sheet.jpg)" for n in names)
    }.
Same starting noise in every pool (columns = seeds, rows = pools):

![Same seeds across pools](evidence/m2-seed-grid.jpg)

{notes}

## Validation — every seed

{seed_table(val)}

Meeting 1 baselines on the same validation photos, for reference:

{seed_table(base_val)}

### Summary

{summary_table({**base_val, **val})}

"Mau→Bengal" is the mean number of the 20 validation Egyptian Mau photos that a
model calls Bengal; "other breeds→Mau" is the mean number of the 140 other photos
it calls Egyptian Mau (the price of a higher Mau recall).

![All runs](evidence/m2-val-overview.png)

![One plot per changed setting](evidence/m2-val-comparisons.png)

{interpretation}
"""
    if decision:
        text += f"""
### Pool taken forward (written before testing)

By the fixed rule ({decision["rule"]}) the pool taken forward is
**{decision["chosen_pool"]}**. The decision was recorded at
{decision["recorded_utc"]} in `evidence/m2-decision.json` together with hashes of
every Meeting 2 validation file.
"""
    if args.stage == "final":
        chosen = decision["chosen_pool"]
        test = {n: read_run(n, "test") for n in (*BASELINES, chosen)}
        write_csv(test, EVIDENCE / "m2-test-metrics.csv")
        overview_plot(test, EVIDENCE / "m2-test-overview.png", "test")
        lines = []
        for b in BASELINES:
            d = paired(test[chosen], test[b], METRICS[0])
            f = paired(test[chosen], test[b], METRICS[1])
            lines.append(
                f"- **{chosen}** versus **{b}**: Mau recall "
                f"{statistics.mean(d):+.1f} pp (paired SD {statistics.stdev(d):.1f}; "
                f"higher/equal/lower in {sum(x > 0 for x in d)}/"
                f"{sum(x == 0 for x in d)}/{sum(x < 0 for x in d)} seeds); "
                f"macro-F1 {statistics.mean(f):+.2f} pp "
                f"(lower in {sum(x < 0 for x in f)}/5 seeds)."
            )
        test_notes = EVIDENCE / "m2-test-observations.md"
        text += f"""
## Test — chosen run against the Meeting 1 baselines

{seed_table(test)}

{summary_table(test, "test")}

![Test](evidence/m2-test-overview.png)

Paired by training seed (one test Mau photo = 3.3 pp):

{chr(10).join(lines)}

{test_notes.read_text(encoding="utf-8") if test_notes.exists() else ""}
Test results are a final measurement; the validation decision remains unchanged.
"""
    report_path = ROOT / "EXPERIMENTS.md"
    old = report_path.read_text(encoding="utf-8")
    head = old.split(MARKER)[0].rstrip("\n")
    later = "\n# Meeting 3"  # keep sections written by later meetings' scripts
    tail = later + old.split(later, 1)[1] if later in old else ""
    report_path.write_text(
        head + "\n" + text.rstrip("\n") + "\n" + tail, encoding="utf-8"
    )
    print(f"Meeting 2 report written ({args.stage}); runs: {', '.join(names)}")


if __name__ == "__main__":
    main()
