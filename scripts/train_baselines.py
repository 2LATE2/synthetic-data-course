"""Run all four validation experiments with the unchanged course hyperparameters."""

from synthdata.train import main

if __name__ == "__main__":
    for name, method, variant in (
        ("m1-real", "real", "mild"),
        ("m1-oversample", "oversample", "mild"),
        ("m1-augment", "augment", "mild"),
        ("m1-augment-strong", "augment", "strong"),
    ):
        main(["--name", name, "--method", method, "--augmentation", variant])
