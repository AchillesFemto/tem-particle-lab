"""Lesson 17: compare a TEM threshold mask with a manual reference."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def mask_iou(reference, candidate):
    """Return intersection-over-union for aligned Boolean masks."""
    if reference.shape != candidate.shape:
        raise ValueError("Masks must have the same shape and aligned coordinates.")
    if reference.dtype != bool or candidate.dtype != bool:
        raise ValueError("Use Boolean masks, not grayscale values or region IDs.")
    intersection = np.count_nonzero(np.logical_and(reference, candidate))
    union = np.count_nonzero(np.logical_or(reference, candidate))
    if union == 0:
        raise ValueError("Both masks are empty; IoU is undefined in this lesson.")
    return intersection / union


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

    overlap = np.logical_and(reference, candidate)
    combined = np.logical_or(reference, candidate)
    score = mask_iou(reference, candidate)
    print("Experimental TEM crop: original rows/columns 300 through 1099")
    print("ROI shape:", roi.shape, "dtype:", roi.dtype)
    print("Threshold:", threshold)
    print("Reference selected pixels:", np.count_nonzero(reference))
    print("Candidate selected pixels:", np.count_nonzero(candidate))
    print("Intersection pixels:", np.count_nonzero(overlap))
    print("Union pixels:", np.count_nonzero(combined))
    print(f"Intersection over union (IoU): {score:.3f}")
    print("IoU measures foreground agreement, not particle-count accuracy.")

    fig, axes = plt.subplots(2, 2, figsize=(9, 9))
    panels = (roi, reference, candidate, overlap)
    titles = ("TEM intensities", "Manual reference", 
              f"Threshold selection: intensity < {threshold}", "Intersection: selected by both")
    for ax, panel, title in zip(axes.flat, panels, titles):
        upper = 255 if panel is roi else 1
        ax.imshow(panel, cmap="gray", vmin=0, vmax=upper,
                  interpolation="nearest", origin="upper")
        ax.set_title(title)
        ax.set_xlabel("Column within crop (pixels)")
        ax.set_ylabel("Row within crop (pixels)")
    fig.suptitle(f"TEM foreground agreement: IoU = {score:.3f}")
    fig.tight_layout()
    output_path = project / "lesson_17.png"
    fig.savefig(output_path, dpi=150)
    print("Saved comparison:", output_path)
    plt.show()


if __name__ == "__main__":
    main()
