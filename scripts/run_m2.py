"""Meeting 2: generate every pool fixed in protocol-m2.md, then train on each.

    python scripts/run_m2.py            # generate + train everything missing
    python scripts/run_m2.py --only-generate

Commands are the starter's `synth-generate` / `synth-train` (as modules), run
with the same interpreter. Finished images and seeds are skipped on reruns.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROMPTS = [
    "a photo of an Egyptian Mau cat sitting indoors, silver coat with random black "
    "spots, green eyes, natural light",
    "close-up photo of an Egyptian Mau cat lying on a sofa, spotted silver tabby "
    "coat, gooseberry green eyes",
    "full body photo of an Egyptian Mau cat standing on the floor, short spotted "
    "coat, banded tail, home interior",
    "candid photo of an Egyptian Mau cat outdoors in a garden, bronze spotted coat, "
    "green eyes",
]
SIMPLE = ["a photo of an Egyptian Mau cat"]

# name: (prompts, extra synth-generate options, tags)
POOLS = {
    "m2-base": (PROMPTS, [], {"setting": "base"}),
    "m2-guidance-2": (
        PROMPTS,
        ["--guidance", "2"],
        {"setting": "guidance", "guidance": 2},
    ),
    "m2-guidance-15": (
        PROMPTS,
        ["--guidance", "15"],
        {"setting": "guidance", "guidance": 15},
    ),
    "m2-steps-10": (PROMPTS, ["--steps", "10"], {"setting": "steps", "steps": 10}),
    "m2-prompt-simple": (SIMPLE, [], {"setting": "prompt", "prompt": "simple"}),
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
    for name in args.pools:
        prompts, options, _ = POOLS[name]
        prompt_args = [part for p in prompts for part in ("--prompt", p)]
        run("-m", "synthdata.generate", "--name", name, *prompt_args, *options)
    if args.only_generate:
        return
    for name in args.pools:
        tags = [
            part for k, v in POOLS[name][2].items() for part in ("--tag", f"{k}={v}")
        ]
        if (ROOT / "runs" / name / "results.json").exists():
            print(f"{name}: already trained", flush=True)
            continue
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
