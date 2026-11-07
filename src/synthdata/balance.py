"""Meeting 1: balanced repetition and conservative image augmentation."""

import random

from PIL import Image
from torchvision import transforms

AUGMENTATION = "mild"
AUGMENTATIONS = {
    name: transforms.Compose(
        [
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(
                degrees, interpolation=transforms.InterpolationMode.BILINEAR
            ),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
        ]
    )
    for name, degrees in (("mild", 10), ("strong", 25))
}


def oversample(
    minority_photos: list[str], budget: int, rng: random.Random
) -> list[str]:
    """Choose which Egyptian Mau training photos to repeat.

    Return a list of exactly `budget` names taken from `minority_photos`; names
    may repeat. Repeat the photos as evenly as possible and use `rng` for every
    random choice, so a run can be reproduced from its seed.
    """
    if budget < 0:
        raise ValueError("budget must be non-negative")
    if not minority_photos:
        if budget == 0:
            return []
        raise ValueError("a positive budget requires source photos")
    if len(set(minority_photos)) != len(minority_photos):
        raise ValueError("source photo names must be unique")
    # Full shuffled rounds plus a partial round: any two counts differ by <= 1.
    order = list(minority_photos)
    chosen = []
    while len(chosen) < budget:
        rng.shuffle(order)
        chosen.extend(order)
    return chosen[:budget]


def augment(image: Image.Image) -> Image.Image:
    """Return a randomly transformed copy of one Egyptian Mau training photo.

    The training script calls this every time an added copy is loaded, so each
    epoch sees a new variant. Typical choices are crops, flips, rotations, and
    colour changes from `torchvision.transforms`. Keep the cat recognisable.
    """
    return AUGMENTATIONS[AUGMENTATION](image.copy())
