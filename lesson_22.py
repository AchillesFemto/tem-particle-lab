"""Lesson 22: distance to background inside a TEM foreground mask."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import ndimage


def foreground_distance(mask):
    """Return Euclidean distances to background pixel centres, in pixels."""
    if mask.ndim != 2 or mask.dtype != bool:
        raise ValueError("Use a two-dimensional Boolean mask.")
    if not np.any(mask) or np.all(mask):
        raise ValueError("This lesson requires both foreground and background pixels.")
    return ndimage.distance_transform_edt(mask)


def main():
    threshold = 140  # Experiment: change only this to 160.
    project = Path(__file__).resolve().parent
    image_path = project / "data" / "public_tem" / "L1-1-D.png"
    with Image.open(image_path) as source:
        image = np.array(source)
    if image.ndim != 2 or image.dtype != np.uint8:
        raise ValueError("This lesson expects a two-dimensional uint8 image.")

    # Keep our established crop, away from the scale bar and edge markings.
    roi = image[300:1100, 300:1100]
    candidate = roi < threshold
    distance = foreground_distance(candidate)
    print("Threshold:", threshold)
    print("Selected pixels:", np.count_nonzero(candidate))
    print("Distance-map shape:", distance.shape, "dtype:", distance.dtype)
    print(f"Largest distance to background: {distance.max():.2f} pixels")
    print("Distances describe the threshold mask; they are not calibrated particle radii.")

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), layout="constrained")
    axes[0].imshow(roi, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
    axes[0].set_title("TEM intensity crop")
    axes[1].imshow(candidate, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
    axes[1].set_title(f"Foreground: intensity < {threshold}")
    # Fixed colour limits make parameter changes visually comparable.
    display = axes[2].imshow(distance, cmap="viridis", vmin=0, vmax=80,
                             interpolation="nearest")
    axes[2].set_title("Distance to background")
    fig.colorbar(display, ax=axes[2], label="Distance (pixels)", extend="max")
    for ax in axes:
        ax.set_xlabel("Column within crop (pixels)")
        ax.set_ylabel("Row within crop (pixels)")
    output_path = project / "lesson_22.png"
    fig.savefig(output_path, dpi=150)
    print("Saved figure:", output_path)
    plt.show()


if __name__ == "__main__":
    main()
