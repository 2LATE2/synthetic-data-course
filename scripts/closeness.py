"""How close is every pool image to the real training photos? (descriptive only)

    python scripts/closeness.py m2-base m3-strength-0.3 ...

For every usable image: cosine similarity of ImageNet-pretrained EfficientNet-B0
features (torchvision weights; not a trained course model) to its source photo
and to the nearest of the 15 Egyptian Mau training photos, plus the mean absolute
pixel difference to the source at 128×128 (0 = identical, 1 = maximal).
Reference: each training photo against its nearest *other* training photo.
Writes evidence/closeness.csv (per image) and evidence/closeness.json (per pool).
"""

import csv
import json
import statistics
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

from synthdata.data import minority_training_photos
from synthdata.inputs import source_photo
from synthdata.pools import usable

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"


def main():
    names = sys.argv[1:]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    weights = EfficientNet_B0_Weights.DEFAULT
    model = efficientnet_b0(weights=weights).eval().to(device)
    prep = weights.transforms()

    @torch.no_grad()
    def embed(images):
        out = []
        for i in range(0, len(images), 32):
            batch = torch.stack([prep(im) for im in images[i : i + 32]]).to(device)
            feats = model.avgpool(model.features(batch)).flatten(1)
            out.append(torch.nn.functional.normalize(feats, dim=1).cpu())
        return torch.cat(out)

    def small(image):
        return (
            np.asarray(
                image.resize((128, 128), Image.Resampling.BILINEAR), dtype=np.float32
            )
            / 255
        )

    train = minority_training_photos()
    photos = {name: source_photo(name) for name in train}
    train_feats = embed([photos[n] for n in train])
    sims = train_feats @ train_feats.T
    within_train = float(
        (sims.sum() - sims.diagonal().sum()) / (len(train) * (len(train) - 1))
    )
    sims.fill_diagonal_(-1)
    reference = sims.max(dim=1).values.tolist()

    rows, summary = (
        [],
        {
            "_reference_nearest_other_training_photo": {
                "mean": statistics.mean(reference),
                "min": min(reference),
                "max": max(reference),
            },
            "_reference_within_training_photos": within_train,
        },
    )
    for name in names:
        pool = ROOT / "pools" / name
        records = usable(pool)
        images = [Image.open(pool / r["file"]).convert("RGB") for r in records]
        feats = embed(images)
        nearest = (feats @ train_feats.T).max(dim=1).values.tolist()
        to_source, pixel = [], []
        for record, image, feat in zip(records, images, feats, strict=True):
            src = record.get("source")
            if src:
                to_source.append(float(feat @ train_feats[train.index(src)]))
                pixel.append(float(np.abs(small(image) - small(photos[src])).mean()))
            else:
                to_source.append(None)
                pixel.append(None)
        for record, a, b, c in zip(records, to_source, nearest, pixel, strict=True):
            rows.append(
                {
                    "pool": name,
                    "sample_id": record["sample_id"],
                    "source": record.get("source") or "",
                    "sim_to_source": a,
                    "sim_to_nearest_train": b,
                    "pixel_mad_to_source": c,
                }
            )
        valid = [x for x in to_source if x is not None]
        pairwise = feats @ feats.T
        n = len(records)
        within = float((pairwise.sum() - pairwise.diagonal().sum()) / (n * (n - 1)))
        summary[name] = {
            "images": len(records),
            "within_pool_similarity": within,
            "sim_to_source": statistics.mean(valid) if valid else None,
            "sim_to_nearest_train": statistics.mean(nearest),
            "pixel_mad_to_source": (
                statistics.mean(p for p in pixel if p is not None) if valid else None
            ),
        }
        print(
            name,
            {
                k: round(v, 3) if isinstance(v, float) else v
                for k, v in summary[name].items()
            },
            flush=True,
        )
    with (EVIDENCE / "closeness.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (EVIDENCE / "closeness.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        "reference (nearest other training photo):",
        round(summary["_reference_nearest_other_training_photo"]["mean"], 3),
    )


if __name__ == "__main__":
    main()
