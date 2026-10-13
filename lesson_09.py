"""Lesson 9: describe intensity spread using standard deviation."""

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

    mean_intensity = np.mean(gray)
    # Describe all pixels in this ROI, not uncertainty in an estimated mean.
    intensity_sd = np.std(gray, ddof=0)
    print("REAL ROI: uncalibrated stored intensities")
    print("Shape and pixel count:", gray.shape, gray.size)
    print(f"Mean intensity: {mean_intensity:.2f}")
    print(f"Intensity standard deviation: {intensity_sd:.2f}")

    # A separate invented example with values equally spaced around 100.
    spread = 10  # Experiment: change only this to 30.
    example = np.array([100 - spread, 100, 100 + spread], dtype=np.float64)
    print("\nSYNTHETIC EXAMPLE (not microscopy measurements)")
    print("Values:", example)
    print("Example mean:", np.mean(example))
    print("Example median:", np.median(example))
    print(f"Example standard deviation: {np.std(example, ddof=0):.2f}")


if __name__ == "__main__":
    main()
