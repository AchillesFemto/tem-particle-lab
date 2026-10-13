"""Lesson 18: locate extra and missed foreground pixels relative to a reference."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from lesson_17 import mask_iou


def disagreement_masks(reference, candidate):
    """Return extra and missed pixels for aligned Boolean masks."""
    if reference.shape != candidate.shape:
        raise ValueError("Masks must have identical shapes and aligned coordinates.")
    if reference.dtype != bool or candidate.dtype != bool:
        raise ValueError("Both masks must contain Boolean selections.")
    extra = np.logical_and(candidate, np.logical_not(reference))
    missed = np.logical_and(reference, np.logical_not(candidate))
    return extra, missed


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
    extra_count = np.count_nonzero(extra)
    missed_count = np.count_nonzero(missed)
    score = mask_iou(reference, candidate)
    print("Pixel disagreements relative to the manual reference")
    print("Threshold:", threshold)
    print("Shared foreground pixels:", shared_count)
    print("Extra pixels (false positives):", extra_count)
    print("Missed pixels (false negatives):", missed_count)
    print(f"IoU = shared / (shared + extra + missed) = {score:.3f}")

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
    panels = (roi, extra, missed)
    titles = ("Original TEM crop", f"Extra pixels: {extra_count:,}",
              f"Missed pixels: {missed_count:,}")
    for ax, panel, title in zip(axes, panels, titles):
        upper = 255 if panel is roi else 1
        ax.imshow(panel, cmap="gray", vmin=0, vmax=upper,
                  interpolation="nearest", origin="upper")
        ax.set_title(title)
        ax.set_xlabel("Column within crop (pixels)")
        ax.set_ylabel("Row within crop (pixels)")
    fig.suptitle(f"Disagreement with manual reference; threshold = {threshold}")
    fig.tight_layout()
    output_path = project / "lesson_18.png"
    fig.savefig(output_path, dpi=150)
    print("Saved comparison:", output_path)
    plt.show()


if __name__ == "__main__":
    main()
