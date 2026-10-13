"""Lesson 10: inspect the benefits and costs of Gaussian smoothing."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter
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

    # Preserve fractional averages without rescaling the stored intensity range.
    gray_float = gray.astype(np.float64)
    sigma_pixels = 2.0  # Experiment: change only this to 2.0.
    smoothed = gaussian_filter(gray_float, sigma=sigma_pixels,
                               mode="reflect", truncate=4.0)

    print("Smoothing sigma (pixels):", sigma_pixels)
    print("Original shape and dtype:", gray.shape, gray.dtype)
    print("Smoothed shape and dtype:", smoothed.shape, smoothed.dtype)
    print("Original values unchanged:", np.array_equal(gray, green))
    print(f"Original intensity SD: {np.std(gray, ddof=0):.2f}")
    print(f"Smoothed intensity SD: {np.std(smoothed, ddof=0):.2f}")
    print("Lower intensity SD is not proof that only noise was removed.")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].imshow(gray, cmap="gray", vmin=0, vmax=255,
                   origin="upper", interpolation="nearest")
    axes[0].set_title("Original grayscale ROI")
    axes[1].imshow(smoothed, cmap="gray", vmin=0, vmax=255,
                   origin="upper", interpolation="nearest")
    axes[1].set_title(f"Gaussian smoothing: sigma = {sigma_pixels} pixels")
    for ax in axes:
        ax.set_xlabel("Column within ROI (pixels)")
        ax.set_ylabel("Row within ROI (pixels)")
    fig.tight_layout()
    output_path = Path(__file__).resolve().parent / "lesson_10.png"
    fig.savefig(output_path, dpi=150)
    print("Saved comparison:", output_path)
    plt.show()


if __name__ == "__main__":
    main()
