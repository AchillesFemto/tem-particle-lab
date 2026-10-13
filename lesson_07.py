"""Lesson 7: select dark pixels with an explicitly chosen threshold."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import tifffile


def main():
    image_path = teaching_tiff_path()
    with tifffile.TiffFile(image_path) as tif:
        image = tif.series[0].asarray()
    roi = image[100:300, 100:400, :].copy()
    red = roi[:, :, 0]
    green = roi[:, :, 1]
    blue = roi[:, :, 2]
    if not (np.array_equal(red, green) and np.array_equal(red, blue)):
        raise ValueError("Unequal RGB components: inspect the ROI before proceeding.")
    gray = green.copy()

    threshold = 100  # Teaching choice, not a validated particle threshold. Try 100.
    mask = gray < threshold
    selected_pixels = np.count_nonzero(mask)
    selected_percent = 100 * selected_pixels / gray.size
    print("Threshold (strictly less than):", threshold)
    print("Mask shape and dtype:", mask.shape, mask.dtype)
    print("Selected pixels:", selected_pixels, "out of", gray.size)
    print(f"Selected pixel percentage: {selected_percent:.2f}%")

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    axes[0].imshow(gray, cmap="gray", vmin=0, vmax=255,
                   origin="upper", interpolation="nearest")
    axes[0].set_title("Original grayscale ROI")
    axes[1].imshow(mask, cmap="gray", vmin=0, vmax=1,
                   origin="upper", interpolation="nearest")
    axes[1].set_title(f"Intensity < {threshold}: white = selected")
    axes[2].imshow(gray, cmap="gray", vmin=0, vmax=255,
                   origin="upper", interpolation="nearest")
    # RGBA display colors: transparent for False, translucent red for True.
    overlay_colors = ListedColormap([(0, 0, 0, 0), (1, 0, 0, 0.5)])
    axes[2].imshow(mask, cmap=overlay_colors, vmin=0, vmax=1,
                   origin="upper", interpolation="nearest")
    axes[2].set_title("Selected pixels overlaid in red")
    for ax in axes:
        ax.set_xlabel("Column within ROI (pixels)")
        ax.set_ylabel("Row within ROI (pixels)")
    fig.tight_layout()
    output_path = Path(__file__).resolve().parent / "lesson_07.png"
    fig.savefig(output_path, dpi=150)
    print("Saved display:", output_path)
    plt.show()


if __name__ == "__main__":
    main()
