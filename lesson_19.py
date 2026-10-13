"""Lesson 19: measure pixel precision against a manual TEM reference."""

from pathlib import Path

import numpy as np
from PIL import Image

from lesson_18 import disagreement_masks


def pixel_precision(reference, candidate):
    """Return shared foreground / selected foreground for aligned Boolean masks."""
    # Reuse Lesson 18's input checks and definition of extra pixels.
    extra, _ = disagreement_masks(reference, candidate)
    selected_count = np.count_nonzero(candidate)
    if selected_count == 0:
        raise ValueError("Precision is undefined when no pixels are selected.")
    shared_count = selected_count - np.count_nonzero(extra)
    return shared_count / selected_count


def main():
    threshold = 140  # Experiment: change only this to 160.
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
    candidate = roi < threshold

    extra, missed = disagreement_masks(reference, candidate)
    shared_count = np.count_nonzero(np.logical_and(reference, candidate))
    selected_count = np.count_nonzero(candidate)
    precision = pixel_precision(reference, candidate)
    print("Pixel precision relative to the manual reference")
    print("Threshold:", threshold)
    print("Selected pixels:", selected_count)
    print("Shared foreground pixels:", shared_count)
    print("Extra pixels:", np.count_nonzero(extra))
    print("Missed pixels (not in the precision formula):", np.count_nonzero(missed))
    print(f"Precision = {shared_count} / {selected_count} = {precision:.4f}")
    print(f"{precision:.2%} of selected pixels are also selected by the reference.")
    print("This is a pixel metric, not particle-count accuracy or repeatability.")


if __name__ == "__main__":
    main()
