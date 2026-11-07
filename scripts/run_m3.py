"""Meeting 3: generate every pool fixed in protocol-m3.md, then train on each.

    python scripts/run_m3.py            # generate + train everything missing
    python scripts/run_m3.py --only-generate

Same prompts as m2-base (imported from run_m2.py). Finished images and trained
runs are skipped on reruns.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from run_m2 import PROMPTS

ROOT = Path(__file__).resolve().parents[1]
STRENGTHS = (0.3, 0.5, 0.7, 0.9)
SCALES = (0.3, 0.5, 0.7, 1.0)

# name: (extra synth-generate options, tags)
POOLS = {
    **{
        f"m3-strength-{s}": (
            ["--mode", "img2img", "--strength", str(s)],
            {"mode": "img2img", "strength": s},
        )
        for s in STRENGTHS
    },
    **{
        f"m3-ip-{s}": (
            ["--mode", "ip-adapter", "--ip-adapter-scale", str(s)],
            {"mode": "ip-adapter", "scale": s},
        )
        for s in SCALES
    },
}


def run(*args):
    print(">>", " ".join(args), flush=True)
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-generate", action="store_true")
    parser.add_argument("--pools", nargs="+", default=list(POOLS))
    args = parser.parse_args()
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("MKL_NUM_THREADS", "4")
    prompt_args = [part for p in PROMPTS for part in ("--prompt", p)]
    for name in args.pools:
        run("-m", "synthdata.generate", "--name", name, *prompt_args, *POOLS[name][0])
    if args.only_generate:
        return
    for name in args.pools:
        if (ROOT / "runs" / name / "results.json").exists():
            print(f"{name}: already trained", flush=True)
            continue
        tags = [
            part for k, v in POOLS[name][1].items() for part in ("--tag", f"{k}={v}")
        ]
        run(
            "-m",
            "synthdata.train",
            "--name",
            name,
            "--method",
            "synthetic",
            "--pool",
            name,
            *tags,
        )


if __name__ == "__main__":
    main()
