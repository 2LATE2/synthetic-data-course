"""Training-only examples for visual inspection of both augmentation variants."""

from pathlib import Path

import torch
from PIL import Image, ImageDraw, ImageOps

from synthdata import balance
from synthdata.data import image_path, minority_training_photos, open_rgb


def main():
    names = minority_training_photos()[:5]
    sheet = Image.new("RGB", (5 * 220, len(names) * 245), "white")
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(names):
        source = open_rgb(image_path(name))
        images = [("original", source)]
        for variant in ("mild", "strong"):
            balance.AUGMENTATION = variant
            for seed in (0, 1):
                torch.manual_seed(seed)
                images.append((f"{variant}, seed {seed}", balance.augment(source)))
        for col, (label, image) in enumerate(images):
            x, y = col * 220, row * 245
            sheet.paste(ImageOps.contain(image, (216, 216)), (x, y + 27))
            draw.text((x + 2, y), f"{name}\n{label}", fill="black")
    dest = (
        Path(__file__).resolve().parents[1] / "evidence" / "augmentation-examples.jpg"
    )
    dest.parent.mkdir(exist_ok=True)
    sheet.save(dest, quality=92)
    print(dest)


if __name__ == "__main__":
    main()
