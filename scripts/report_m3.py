"""Meeting 3 report: sweeps of img2img strength and IP-Adapter scale.

    python scripts/report_m3.py draft
    python scripts/report_m3.py validation   # lock the two choices (before test)
    python scripts/report_m3.py final        # add the chosen runs' test results

Writes the "# Meeting 3" section of EXPERIMENTS.md (earlier sections untouched).
Hand-written text is included from evidence/m3-*.md; closeness numbers come from
evidence/closeness.json (scripts/closeness.py).
"""

import argparse
import hashlib
import json
import statistics
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from report_m2 import (
    LABELS,
    METRICS,
    existing,
    mean,
    overview_plot,
    paired,
    pool_stats,
    read_run,
    seed_table,
    summary_table,
    tile,
    write_csv,
)

from synthdata.inputs import source_photo
from synthdata.pools import read_manifest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
BASELINES = ("m1-real", "m1-oversample", "m1-augment-strong", "m2-base")
SWEEPS = {
    "img2img": ("strength", [(f"m3-strength-{s}", s) for s in (0.3, 0.5, 0.7, 0.9)]),
    "ip-adapter": (
        "IP-Adapter scale",
        [(f"m3-ip-{s}", s) for s in (0.3, 0.5, 0.7, 1.0)],
    ),
}
POOLS = tuple(n for _, runs in SWEEPS.values() for n, _ in runs)
MARKER = "\n# Meeting 3"
EXAMPLE_INDICES = (1, 6, 10)  # image i starts from training photo i mod 15


def closeness():
    path = EVIDENCE / "closeness.json"
    return json.loads(path.read_text()) if path.exists() else {}


def pool_table(names, close):
    lines = [
        "| Pool | Mode | Strength / scale | Effective steps | Usable / attempts | "
        "Safety-blocked | s per image | Similarity to source | Similarity to "
        "nearest training photo | Pixel difference to source | Within-pool "
        "similarity |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in names:
        s = pool_stats(name)
        settings = json.loads((ROOT / "pools" / name / "pool.json").read_text())
        value = settings["strength"] or settings["ip_adapter_scale"]
        effective = (
            int(settings["steps"] * settings["strength"])
            if settings["mode"] == "img2img"
            else settings["steps"]
        )
        c = close.get(name, {})

        def fmt(key, c=c):
            return f"{c[key]:.3f}" if c.get(key) is not None else "–"

        lines.append(
            f"| `{name}` | {settings['mode']} | "
            f"{value if value is not None else '–'} | "
            f"{effective} | {s['usable']} / {s['attempts']} | {s['blocked']} | "
            f"{s['seconds']:.1f} | {fmt('sim_to_source')} | "
            f"{fmt('sim_to_nearest_train')} | {fmt('pixel_mad_to_source')} | "
            f"{fmt('within_pool_similarity')} |"
        )
    return "\n".join(lines)


def sweep_plot(val, base, path):
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), layout="constrained")
    styles = {
        "m1-real": ":",
        "m1-oversample": "--",
        "m1-augment-strong": "-.",
        "m2-base": "-",
    }
    for col, (mode, (xlabel, runs)) in enumerate(SWEEPS.items()):
        runs = [(n, x) for n, x in runs if n in val]
        xs = [x for _, x in runs]
        for row, metric in enumerate(METRICS):
            ax = axes[row][col]
            for seed in range(5):
                ax.plot(
                    xs,
                    [val[n][seed][metric] for n, _ in runs],
                    "o-",
                    alpha=0.55,
                    color=f"C{seed}",
                    label=f"seed {seed}" if (row, col) == (0, 0) else None,
                )
            ax.plot(
                xs,
                [mean(val[n], metric) for n, _ in runs],
                "kD-",
                ms=8,
                label="mean" if (row, col) == (0, 0) else None,
            )
            for name, style in styles.items():
                ax.axhline(
                    mean(base[name], metric),
                    color="C3" if name == "m2-base" else "grey",
                    ls=style,
                    lw=1.3,
                    label=f"{name} (mean)" if (row, col) == (0, 0) else None,
                )
            ax.set_xticks(xs)
            ax.set_xlabel(xlabel)
            ax.set_ylim((0.3, 1.0) if metric == METRICS[0] else (0.8, 0.95))
            ax.grid(axis="y", alpha=0.25)
            if col == 0:
                ax.set_ylabel(LABELS[metric])
            if row == 0:
                ax.set_title(mode)
    fig.legend(
        *axes[0][0].get_legend_handles_labels(),
        loc="outside lower center",
        ncol=5,
        fontsize=8,
    )
    fig.suptitle("Validation, all five seeds (red: Meeting 2 pool; grey: Meeting 1)")
    fig.savefig(path, dpi=150)
    plt.close(fig)


def closeness_plot(val, close, path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout="constrained")
    ref = close["_reference_nearest_other_training_photo"]["mean"]
    names = [n for n in ("m2-base", *POOLS) if n in val and n in close]
    offsets = {"m3-ip-0.5": (5, 6), "m3-ip-0.7": (5, -10)}
    for ax, metric in zip(axes, METRICS, strict=True):
        for n in names:
            x = close[n]["sim_to_nearest_train"]
            y = mean(val[n], metric)
            colour = "C3" if n == "m2-base" else "C0" if "strength" in n else "C2"
            ax.errorbar(
                x,
                y,
                yerr=statistics.stdev(r[metric] for r in val[n]),
                fmt="o",
                color=colour,
                capsize=3,
            )
            ax.annotate(
                n.removeprefix("m3-").removeprefix("m2-"),
                (x, y),
                textcoords="offset points",
                xytext=offsets.get(n, (5, 4)),
                fontsize=8,
            )
        ax.axvline(ref, color="grey", ls="--", lw=1)
        ax.text(
            ref,
            ax.get_ylim()[0],
            " nearest other\n real Mau photo",
            fontsize=7,
            color="grey",
            va="bottom",
        )
        ax.set_xlabel("mean feature similarity to the nearest training Mau photo")
        ax.set_ylabel(f"validation {LABELS[metric]} (mean ± SD)")
        ax.grid(alpha=0.25)
    fig.suptitle(
        "How close to the real photos? (blue: img2img, green: IP-Adapter, "
        "red: Meeting 2 text-only)"
    )
    fig.savefig(path, dpi=150)
    plt.close(fig)


def example_sheet(path, size=180):
    """Per example photo: one img2img row and one IP-Adapter row."""
    columns = 5
    rows = []
    for index in EXAMPLE_INDICES:
        for mode, (_, runs) in SWEEPS.items():
            rows.append((index, mode, runs))
    sheet = Image.new("RGB", (columns * size, len(rows) * (size + 18)), "white")
    draw = ImageDraw.Draw(sheet)
    for r, (index, mode, runs) in enumerate(rows):
        y = r * (size + 18)
        first = runs[0][0]
        records = {
            rec["sample_id"]: rec for rec in read_manifest(ROOT / "pools" / first)
        }
        source = records[f"{first}-{index:04d}"]["source"]
        photo = source_photo(source).resize((size, size))
        sheet.paste(photo, (0, y + 18))
        draw.text((4, y + 3), f"training photo ({source})", fill="black")
        for c, (name, value) in enumerate(runs, start=1):
            file = ROOT / "pools" / name / "images" / f"{name}-{index:04d}.png"
            sheet.paste(tile(file, size), (c * size, y + 18))
            label = "img2img" if mode == "img2img" else "IP-Adapter"
            draw.text((c * size + 4, y + 3), f"{label} {value}", fill="black")
    sheet.save(path, quality=90)


def write_section(text):
    path = ROOT / "EXPERIMENTS.md"
    head = path.read_text(encoding="utf-8").split(MARKER)[0].rstrip("\n")
    path.write_text(head + "\n" + text, encoding="utf-8")


def include(name):
    path = EVIDENCE / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["draft", "validation", "final"])
    args = parser.parse_args()
    decision_path = EVIDENCE / "m3-decision.json"
    names = existing(POOLS)
    val = {n: read_run(n) for n in names}
    base = {n: read_run(n) for n in BASELINES}
    close = closeness()

    if args.stage == "validation":
        if decision_path.exists():
            raise SystemExit(
                "Meeting 3 decision already locked; refusing to overwrite."
            )
        if set(names) != set(POOLS):
            raise SystemExit(f"runs missing: {set(POOLS) - set(names)}")
        if existing(POOLS, "test-results.json"):
            raise SystemExit("A Meeting 3 run was already tested.")
        chosen = {}
        for mode, (_, runs) in SWEEPS.items():
            chosen[mode] = max(
                (n for n, _ in runs),
                key=lambda n: (
                    mean(val[n], METRICS[0]),
                    mean(val[n], METRICS[1]),
                    n.endswith("-0.5"),
                ),
            )
        decision = {
            "recorded_utc": datetime.now(UTC).isoformat(),
            "chosen": chosen,
            "rule": "Per mode: highest mean validation Mau recall; tie: macro-F1; "
            "then the 0.5 pool.",
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

    write_csv({**base, **val}, EVIDENCE / "m3-val-metrics.csv")
    sweep_plot(val, base, EVIDENCE / "m3-val-sweeps.png")
    overview_plot({**base, **val}, EVIDENCE / "m3-val-overview.png", "val")
    if close and all(n in close for n in names):
        closeness_plot({**base, **val}, close, EVIDENCE / "m3-closeness.png")
    if set(names) == set(POOLS):
        example_sheet(EVIDENCE / "m3-examples.jpg")
    ref = close.get("_reference_nearest_other_training_photo", {}).get("mean")

    text = f"""
# Meeting 3 — Generating from Training Photos

Plan, prompt and decision rule were fixed before generating:
[protocol-m3.md](protocol-m3.md). Commands: [scripts/run_m3.py](scripts/run_m3.py).
All pools use the four `m2-base` prompts and only the 15 Egyptian Mau
**training** photos as sources; image *i* of every pool starts from the same
photo (*i* mod 15) and the same seed, so pools are directly comparable.

## Pools

{pool_table(["m2-base", *names], close)}

Similarities are cosine similarities of ImageNet EfficientNet-B0 features
(1 = identical); pixel difference is the mean absolute difference at 128×128;
within-pool similarity is the mean similarity between two images of the same
pool (lower = more diverse). For reference, a real training photo has similarity
{f"{ref:.3f}" if ref else "–"} to its nearest *other* real training photo, and
two of the 15 training photos have mean similarity
{close.get("_reference_within_training_photos", float("nan")):.3f}.
Contact sheets (source photo next to each of the first 24 images):
{", ".join(f"[{n}](pools/{n}/contact-sheet.jpg)" for n in names)}.

Each pair of rows starts from the same training photo:

![Examples](evidence/m3-examples.jpg)

{include("m3-observations.md")}

## Validation — every seed

{seed_table(val)}

### Summary (Δ against the Meeting 2 pool `m2-base`)

{summary_table({**base, **val})}

![Sweeps](evidence/m3-val-sweeps.png)

![Closeness against recall](evidence/m3-closeness.png)

![All runs](evidence/m3-val-overview.png)

{include("m3-val-interpretation.md")}
"""
    if decision:
        text += f"""
### Pools taken forward (written before testing)

By the fixed rule ({decision["rule"]}): **{decision["chosen"]["img2img"]}** for
image-to-image and **{decision["chosen"]["ip-adapter"]}** for IP-Adapter, recorded
at {decision["recorded_utc"]} in `evidence/m3-decision.json` with hashes of every
Meeting 3 validation file.
"""
    if args.stage == "final":
        chosen = list(decision["chosen"].values())
        test = {n: read_run(n, "test") for n in (*BASELINES, *chosen)}
        write_csv(test, EVIDENCE / "m3-test-metrics.csv")
        overview_plot(test, EVIDENCE / "m3-test-overview.png", "test")
        lines = []
        for c in chosen:
            for b in ("m1-oversample", "m2-base"):
                d = paired(test[c], test[b], METRICS[0])
                f = paired(test[c], test[b], METRICS[1])
                lines.append(
                    f"- **{c}** versus **{b}**: Mau recall "
                    f"{statistics.mean(d):+.1f} pp "
                    f"(paired SD {statistics.stdev(d):.1f}; higher/equal/lower in "
                    f"{sum(x > 0 for x in d)}/{sum(x == 0 for x in d)}/"
                    f"{sum(x < 0 for x in d)} seeds); macro-F1 "
                    f"{statistics.mean(f):+.2f} pp."
                )
        text += f"""
## Test — chosen runs against Meetings 1 and 2

{seed_table(test)}

{summary_table(test, "test")}

![Test](evidence/m3-test-overview.png)

Paired by training seed (one test Mau photo = 3.3 pp):

{chr(10).join(lines)}

{include("m3-test-observations.md")}
Test results are a final measurement; the validation decisions remain unchanged.
"""
    write_section(text)
    print(f"Meeting 3 report written ({args.stage}); runs: {', '.join(names)}")


if __name__ == "__main__":
    main()
