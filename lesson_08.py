"""Lesson 8: describe ROI intensity using the mean and median."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

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

    # Summarize every pixel in the rectangle, without intensity-based selection.
    mean_intensity = np.mean(gray)
    median_intensity = np.median(gray)
    print("REAL ROI: stored intensities, not calibrated physical quantities")
    print("Shape and pixel count:", gray.shape, gray.size)
    print(f"Mean intensity: {mean_intensity:.2f}")
    print(f"Median intensity: {median_intensity:.2f}")

    # Invented values for a controlled experiment, separate from the TEM data.
    last_value = 110  # Experiment: change only this to 250.
    example = np.array([90, 95, 100, 105, last_value], dtype=np.uint8)
    print("\nSYNTHETIC EXAMPLE (not microscopy measurements)")
    print("Values:", example)
    print("Example mean:", np.mean(example))
    print("Example median:", np.median(example))


if __name__ == "__main__":
    main()
