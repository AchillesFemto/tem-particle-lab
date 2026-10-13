"""Lesson 6: count grayscale pixels in intensity bins."""

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
    if not same_components:
        raise ValueError("Unequal RGB components: inspect the ROI before proceeding.")
    gray = green.copy()

    number_of_bins = 8  # Experiment: change only this to 16.
    # Cover every possible uint8 value; 256 is an edge, not a pixel value.
    counts, edges = np.histogram(gray, bins=number_of_bins, range=(0, 256))
    print("Grayscale shape:", gray.shape)
    print("Number of pixels:", gray.size)
    print("Observed minimum and maximum:", gray.min(), gray.max())
    print("Number of bins:", number_of_bins)
    print("Bin width:", edges[1] - edges[0])
    print("Counts:", counts)
    print("Sum of histogram counts:", counts.sum())

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].imshow(gray, cmap="gray", vmin=0, vmax=255,
                   origin="upper", interpolation="nearest")
    axes[0].set_title("Grayscale ROI")
    axes[0].set_xlabel("Column within ROI (pixels)")
    axes[0].set_ylabel("Row within ROI (pixels)")
    axes[1].stairs(counts, edges, fill=True)
    axes[1].set_xlim(0, 256)
    axes[1].set_ylim(bottom=0)
    axes[1].set_title(f"Intensity histogram: {number_of_bins} bins")
    axes[1].set_xlabel("Stored intensity (0–255; uncalibrated)")
    axes[1].set_ylabel("Number of pixels per bin")
    fig.tight_layout()
    output_path = Path(__file__).resolve().parent / "lesson_06.png"
    fig.savefig(output_path, dpi=150)
    print("Saved figure:", output_path)
    plt.show()


if __name__ == "__main__":
    main()
