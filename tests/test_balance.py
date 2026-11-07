import random
from collections import Counter

import numpy as np
import pytest
import torch
from PIL import Image

from synthdata import balance


@pytest.mark.parametrize("budget", [0, 1, 14, 15, 16, 55, 100])
def test_oversample_balances_all_sources_and_preserves_input(budget):
    names = [f"photo-{i}" for i in range(15)]
    original = names.copy()
    result = balance.oversample(names, budget, random.Random(4))
    counts = Counter(result)
    assert len(result) == budget
    assert set(result) <= set(names)
    assert (
        max(counts[name] for name in names) - min(counts[name] for name in names) <= 1
    )
    assert names == original
    assert result == balance.oversample(names, budget, random.Random(4))


def test_55_extras_use_ten_sources_four_times_and_five_three_times():
    counts = Counter(
        balance.oversample(list(map(str, range(15))), 55, random.Random(0))
    )
    assert Counter(counts.values()) == {4: 10, 3: 5}


def test_invalid_sources_and_budget():
    assert balance.oversample([], 0, random.Random(0)) == []
    for names, budget in [([], 1), (["a"], -1), (["a", "a"], 2)]:
        with pytest.raises(ValueError):
            balance.oversample(names, budget, random.Random(0))


@pytest.mark.parametrize("variant", ["mild", "strong"])
def test_augment_preserves_input_shape_and_is_seeded(variant, monkeypatch):
    monkeypatch.setattr(balance, "AUGMENTATION", variant)
    pixels = np.random.default_rng(1).integers(0, 256, (80, 120, 3), dtype=np.uint8)
    source = Image.fromarray(pixels)
    torch.manual_seed(42)
    first = balance.augment(source)
    torch.manual_seed(42)
    second = balance.augment(source)
    assert first is not source
    assert first.mode == "RGB" and first.size == source.size
    assert np.array_equal(np.asarray(source), pixels)
    assert np.array_equal(np.asarray(first), np.asarray(second))
    assert not np.array_equal(np.asarray(first), pixels)
    assert not np.array_equal(np.asarray(balance.augment(source)), np.asarray(first))
