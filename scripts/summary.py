"""Whole-project summary: cross-meeting tables and plots for SUMMARY.md.

    python scripts/summary.py

Every number comes from runs/*/results.json, runs/*/test-results.json,
runs/*/seed-*/(test-)metrics.json and evidence/closeness.json. The script
replaces the blocks between <!-- BEGIN:name --> and <!-- END:name --> in
SUMMARY.md and redraws evidence/summary-*.png; the hand-written text around the
blocks is left untouched. To add a later meeting, append its runs to RUNS.
"""

import json
import re
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
SUMMARY = ROOT / "SUMMARY.md"
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
MAU = BREEDS.index("Egyptian Mau")

# (meeting, run, short label, how the 55 extra Egyptian Mau examples are made)
RUNS = [
    (1, "m1-real", "real only", "none (15 Mau photos only)"),
    (1, "m1-oversample", "oversample", "exact repeats of the 15 photos"),
    (1, "m1-augment", "augment ±10°", "random flips/rotations/colour jitter of the 15"),
    (1, "m1-augment-strong", "augment ±25°", "as above, rotation up to ±25°"),
    (2, "m2-base", "T2I base", "SD 1.5 text-to-image, 4 prompts, 30 steps, g=7.5"),
    (2, "m2-guidance-2", "T2I guidance 2", "base with guidance 2"),
    (2, "m2-guidance-15", "T2I guidance 15", "base with guidance 15"),
    (2, "m2-steps-10", "T2I 10 steps", "base with 10 steps"),
    (2, "m2-prompt-simple", "T2I 1 prompt", "base with one simple prompt"),
    (
        3,
        "m3-strength-0.3",
        "img2img 0.3",
        "img2img from a training photo, strength 0.3",
    ),
    (3, "m3-strength-0.5", "img2img 0.5", "img2img, strength 0.5"),
    (3, "m3-strength-0.7", "img2img 0.7", "img2img, strength 0.7"),
    (3, "m3-strength-0.9", "img2img 0.9", "img2img, strength 0.9"),
    (3, "m3-ip-0.3", "IP-Adapter 0.3", "IP-Adapter with a training photo, scale 0.3"),
    (3, "m3-ip-0.5", "IP-Adapter 0.5", "IP-Adapter, scale 0.5"),
    (3, "m3-ip-0.7", "IP-Adapter 0.7", "IP-Adapter, scale 0.7"),
    (3, "m3-ip-1.0", "IP-Adapter 1.0", "IP-Adapter, scale 1.0"),
]
LABEL = {run: label for _, run, label, _ in RUNS}
COLOURS = {1: "#7f7f7f", 2: "#d62728", 3: "#1f77b4", 4: "#2ca02c", 5: "#9467bd"}


def seeds(run, split):
    name = "results.json" if split == "val" else "test-results.json"
    path = ROOT / "runs" / run / name
    if not path.exists():
        return None
    rows = json.loads(path.read_text())["seeds"]
    assert sorted(r["seed"] for r in rows) == list(range(5)), run
    return sorted(rows, key=lambda r: r["seed"])


def stat(rows, key):
    values = [r[key] for r in rows]
    return statistics.mean(values), statistics.stdev(values)


def confusions(run, split):
    prefix = "" if split == "val" else "test-"
    mats = [
        json.loads(
            (ROOT / "runs" / run / f"seed-{s}" / f"{prefix}metrics.json").read_text()
        )["confusion"]
        for s in range(5)
    ]
    row = [statistics.mean(m[MAU][j] for m in mats) for j in range(len(BREEDS))]
    false_mau = statistics.mean(
        sum(m[i][MAU] for i in range(len(BREEDS)) if i != MAU) for m in mats
    )
    return row, false_mau


def paired(a, b, key):
    d = [100 * (x[key] - y[key]) for x, y in zip(a, b, strict=True)]
    return (
        statistics.mean(d),
        sum(x > 0 for x in d),
        sum(x == 0 for x in d),
        sum(x < 0 for x in d),
    )


def fmt_pm(rows, key):
    m, s = stat(rows, key)
    return f"{m:.3f} ± {s:.3f}"


def table_tested(data):
    real, over = data["m1-real"]["test"], data["m1-oversample"]["test"]
    lines = [
        "| Meeting | Method | Test Mau recall | Test macro-F1 | Δ recall vs real, pp "
        "(seeds +/=/−) | Δ recall vs oversample, pp (seeds +/=/−) | Mau→Bengal | "
        "Mau→Russian Blue | Other breeds→Mau |",
        "| :-: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for meeting, run, label, _ in RUNS:
        test = data[run]["test"]
        if test is None:
            continue
        row, false_mau = confusions(run, "test")
        cells = []
        for ref in (real, over):
            if test is ref:
                cells.append("–")
            else:
                d, up, eq, down = paired(test, ref, "egyptian_mau_recall")
                cells.append(f"{d:+.1f} ({up}/{eq}/{down})")
        lines.append(
            f"| {meeting} | {label} (`{run}`) | "
            f"{fmt_pm(test, 'egyptian_mau_recall')} | "
            f"{fmt_pm(test, 'macro_f1')} | {cells[0]} | {cells[1]} | "
            f"{row[BREEDS.index('Bengal')]:.1f} | "
            f"{row[BREEDS.index('Russian Blue')]:.1f} | {false_mau:.1f} |"
        )
    return "\n".join(lines)


def table_all(data, close):
    lines = [
        "| Meeting | Method | How the 55 extra Mau examples are made | Val Mau recall "
        "| Val macro-F1 | Similarity to nearest training Mau photo | Tested |",
        "| :-: | --- | --- | ---: | ---: | ---: | :-: |",
    ]
    for meeting, run, label, how in RUNS:
        val = data[run]["val"]
        sim = close.get(run, {}).get("sim_to_nearest_train")
        lines.append(
            f"| {meeting} | {label} | {how} | {fmt_pm(val, 'egyptian_mau_recall')} | "
            f"{fmt_pm(val, 'macro_f1')} | {f'{sim:.2f}' if sim else '–'} | "
            f"{'✔' if data[run]['test'] else ''} |"
        )
    return "\n".join(lines)


def table_breeds(data):
    tested = [run for _, run, _, _ in RUNS if data[run]["test"]]
    lines = [
        "| Breed | " + " | ".join(LABEL[r] for r in tested) + " |",
        "| --- |" + " ---: |" * len(tested),
    ]
    for breed in BREEDS:
        cells = [
            statistics.mean(r["recall"][breed] for r in data[run]["test"])
            for run in tested
        ]
        best = max(cells)
        lines.append(
            f"| {breed} | "
            + " | ".join(f"**{c:.3f}**" if c == best else f"{c:.3f}" for c in cells)
            + " |"
        )
    return "\n".join(lines)


def table_val_test(data):
    lines = [
        "| Method | Val Mau recall | Test Mau recall | Test − val, pp | "
        "Val macro-F1 | Test macro-F1 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, run, label, _ in RUNS:
        val, test = data[run]["val"], data[run]["test"]
        if test is None:
            continue
        v, t = stat(val, "egyptian_mau_recall")[0], stat(test, "egyptian_mau_recall")[0]
        lines.append(
            f"| {label} | {v:.3f} | {t:.3f} | {100 * (t - v):+.1f} | "
            f"{stat(val, 'macro_f1')[0]:.3f} | {stat(test, 'macro_f1')[0]:.3f} |"
        )
    return "\n".join(lines)


def dot_plot(data, split, path, title):
    runs = [(m, r) for m, r, _, _ in RUNS if data[r][split]]
    fig, axes = plt.subplots(
        1, 2, figsize=(13, 0.42 * len(runs) + 1.6), layout="constrained", sharey=True
    )
    for ax, key, name in zip(
        axes,
        ("egyptian_mau_recall", "macro_f1"),
        ("Egyptian Mau recall", "Macro-F1"),
        strict=True,
    ):
        for y, (meeting, run) in enumerate(runs):
            values = [r[key] for r in data[run][split]]
            ax.scatter(values, [y] * 5, color=COLOURS[meeting], alpha=0.45, s=22)
            ax.errorbar(
                statistics.mean(values),
                y,
                xerr=statistics.stdev(values),
                fmt="D",
                color=COLOURS[meeting],
                mec="black",
                ms=7,
                capsize=3,
            )
        for ref, style in (("m1-real", ":"), ("m1-oversample", "--")):
            ax.axvline(
                stat(data[ref][split], key)[0],
                color="grey",
                ls=style,
                lw=1,
                label=f"{LABEL[ref]} (mean)",
            )
        ax.set_yticks(range(len(runs)), [f"M{m}  {LABEL[r]}" for m, r in runs])
        ax.invert_yaxis()
        ax.set_xlabel(name)
        ax.grid(axis="x", alpha=0.25)
    axes[0].legend(loc="lower right", fontsize=8)
    fig.suptitle(title)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def val_test_plot(data, path):
    fig, ax = plt.subplots(figsize=(6, 5.4), layout="constrained")
    for meeting, run, label, _ in RUNS:
        if not data[run]["test"]:
            continue
        v = stat(data[run]["val"], "egyptian_mau_recall")[0]
        t = stat(data[run]["test"], "egyptian_mau_recall")[0]
        ax.scatter(v, t, color=COLOURS[meeting], s=60, edgecolor="black", zorder=3)
        ax.annotate(
            label, (v, t), textcoords="offset points", xytext=(6, -3), fontsize=8
        )
    lims = (0.45, 0.85)
    ax.plot(lims, lims, color="grey", ls="--", lw=1, label="test = validation")
    ax.set(
        xlim=lims,
        ylim=lims,
        xlabel="validation Mau recall (mean of 5 seeds)",
        ylabel="test Mau recall (mean of 5 seeds)",
        title="Chosen runs: validation vs test",
    )
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", fontsize=8)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def replace_block(text, name, content):
    pattern = re.compile(rf"(<!-- BEGIN:{name} -->).*?(<!-- END:{name} -->)", re.DOTALL)
    assert pattern.search(text), f"block {name} missing in SUMMARY.md"
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(2)}", text)


def main():
    data = {
        run: {"val": seeds(run, "val"), "test": seeds(run, "test")}
        for _, run, _, _ in RUNS
    }
    missing = [r for r, d in data.items() if d["val"] is None]
    assert not missing, f"runs without results.json: {missing}"
    close_path = EVIDENCE / "closeness.json"
    close = json.loads(close_path.read_text()) if close_path.exists() else {}

    dot_plot(
        data,
        "test",
        EVIDENCE / "summary-test.png",
        "TEST: every chosen run, all five seeds (dots) and mean ± SD "
        "(grey M1, red M2, blue M3)",
    )
    dot_plot(
        data,
        "val",
        EVIDENCE / "summary-val.png",
        "VALIDATION: every run of the project, all five seeds and mean ± SD",
    )
    val_test_plot(data, EVIDENCE / "summary-val-vs-test.png")

    text = SUMMARY.read_text(encoding="utf-8")
    for name, content in (
        ("tested", table_tested(data)),
        ("all", table_all(data, close)),
        ("breeds", table_breeds(data)),
        ("valtest", table_val_test(data)),
    ):
        text = replace_block(text, name, content)
    SUMMARY.write_text(text, encoding="utf-8")
    print("SUMMARY.md tables and evidence/summary-*.png updated")


if __name__ == "__main__":
    main()
