"""Lesson 20: measure pixel recall against a manual TEM reference."""

from pathlib import Path

import numpy as np
from PIL import Image

from lesson_18 import disagreement_masks


def pixel_recall(reference, candidate):
    """Return shared foreground / reference foreground for aligned Boolean masks."""
    # Reuse the Boolean-mask checks and missed-pixel definition from Lesson 18.
    _, missed = disagreement_masks(reference, candidate)
    reference_count = np.count_nonzero(reference)
    if reference_count == 0:
        raise ValueError("Recall is undefined when the reference has no foreground.")
    shared_count = reference_count - np.count_nonzero(missed)
    return shared_count / reference_count


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
    reference_count = np.count_nonzero(reference)
    shared_count = np.count_nonzero(np.logical_and(reference, candidate))
    recall = pixel_recall(reference, candidate)
    print("Pixel recall relative to the manual reference")
    print("Threshold:", threshold)
    print("Reference foreground pixels:", reference_count)
    print("Shared foreground pixels:", shared_count)
    print("Missed pixels:", np.count_nonzero(missed))
    print("Extra pixels (not in the recall formula):", np.count_nonzero(extra))
    print(f"Recall = {shared_count} / {reference_count} = {recall:.4f}")
    print(f"{recall:.2%} of reference foreground pixels are selected by our method.")
    print("This does not measure the fraction of whole particles detected.")


if __name__ == "__main__":
    main()
