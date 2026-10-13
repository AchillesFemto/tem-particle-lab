"""Lesson 5: represent identical RGB components as one grayscale plane."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

import matplotlib.pyplot as plt
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
    same_components = np.array_equal(red, green) and np.array_equal(red, blue)
    print("All RGB components identical:", same_components)
    if not same_components:
        raise ValueError("This ROI contains unequal RGB values; stop and inspect it.")

    component = 1  # Experiment: change only this to 1 (green).
    gray = roi[:, :, component].copy()
    print("Selected RGB component:", component)
    print("RGB ROI shape:", roi.shape)
    print("Grayscale shape, ndim, dtype:", gray.shape, gray.ndim, gray.dtype)
    print("First RGB pixel:", roi[0, 0])
    print("First grayscale pixel:", gray[0, 0])
    print("Grayscale equals red plane:", np.array_equal(gray, red))

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].imshow(roi, origin="upper", interpolation="nearest")
    axes[0].set_title("RGB ROI: three values per pixel")
    # Fixed display limits match this uint8 RGB image's 0–255 display range.
    axes[1].imshow(gray, cmap="gray", vmin=0, vmax=255,
                   origin="upper", interpolation="nearest")
    axes[1].set_title("Grayscale: one value per pixel")
    for ax in axes:
        ax.set_xlabel("Column within ROI (pixels)")
        ax.set_ylabel("Row within ROI (pixels)")
    fig.tight_layout()
    output_path = Path(__file__).resolve().parent / "lesson_05.png"
    fig.savefig(output_path, dpi=150)
    print("Saved comparison:", output_path)
    plt.show()


if __name__ == "__main__":
    main()
