"""Lesson 21: compare precision and recall across TEM thresholds."""

from pathlib import Path

import numpy as np
from PIL import Image

from lesson_18 import disagreement_masks
from lesson_19 import pixel_precision
from lesson_20 import pixel_recall


def main():
    thresholds = [120, 140, 160]  # Experiment: change only 160 to 180.
    project = Path(__file__).resolve().parent
    data = project / "data" / "public_tem"

    # Pillow reads PNG pixels without Matplotlib's automatic 0-to-1 rescaling.
    with Image.open(data / "L1-1-D.png") as source:
        image = np.array(source)
    with Image.open(data / "L1-1-D_mask.png") as source:
        reference_image = np.array(source)
    if image.ndim != 2 or image.dtype != np.uint8:
        raise ValueError("This lesson expects a two-dimensional uint8 image.")
    if image.shape != reference_image.shape:
        raise ValueError("The image and reference must have matching dimensions.")
    if not np.all(np.isin(reference_image, [0, 255])):
        raise ValueError("The source reference must contain only 0 and 255.")

    # Identical original coordinates keep the image and annotation aligned.
    # This fixed crop avoids the bottom scale bar and image-edge markings.
    roi = image[300:1100, 300:1100]
    reference = reference_image[300:1100, 300:1100] > 0
    print("Same TEM crop and reference; only the threshold changes")
    print(f"{'Threshold':>9} {'Selected':>10} {'Extra':>10} {'Missed':>10} {'Precision':>11} {'Recall':>10}")
    for threshold in thresholds:
        candidate = roi < threshold
        extra, missed = disagreement_masks(reference, candidate)
        selected = np.count_nonzero(candidate)
        # An empty selection has undefined precision, not perfect precision.
        precision = pixel_precision(reference, candidate) if selected else np.nan
        recall = pixel_recall(reference, candidate)
        print(f"{threshold:9d} {selected:10d} {np.count_nonzero(extra):10d} "
              f"{np.count_nonzero(missed):10d} {precision:11.2%} {recall:10.2%}")
    print("nan means undefined precision when no pixels are selected.")
    print("These are pixel comparisons on one crop, not an independently validated optimum.")


if __name__ == "__main__":
    main()
