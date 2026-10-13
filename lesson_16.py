"""Lesson 16: inspect threshold sensitivity without choosing an optimum."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

import numpy as np
from scipy.ndimage import generate_binary_structure, label
import tifffile


def main():
    structure = generate_binary_structure(2, 1)
    example = np.array([[40, 90, 40]], dtype=np.uint8)
    print("SYNTHETIC EXAMPLE: two dark pixels with a brighter bridge")
    for threshold in (80, 100):
        example_mask = example < threshold
        example_labels, example_count = label(example_mask, structure=structure)
        print("Threshold:", threshold, "labels:", example_labels,
              "selected pixels:", np.count_nonzero(example_mask),
              "regions:", example_count)

    image_path = teaching_tiff_path()
    with tifffile.TiffFile(image_path) as tif:
        image = tif.series[0].asarray()
    roi = image[100:300, 100:400, :].copy()
    red, green, blue = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
    if not (np.array_equal(red, green) and np.array_equal(red, blue)):
        raise ValueError("Unequal RGB components: inspect the ROI before proceeding.")
    gray = green.copy()

    max_threshold = 100  # Experiment: change only this to 120.
    print("\nREAL ROI: threshold sensitivity, NOT particle counts")
    print("Fixed: original ROI, strict <, edge-only connectivity, no smoothing")
    print("No size filtering or boundary exclusion in this comparison")
    print("threshold | selected pixels | selected percent | regions")
    for threshold in range(60, max_threshold + 1, 20):
        # Recompute each selection from the same original grayscale values.
        mask = gray < threshold
        labels, region_count = label(mask, structure=structure)
        selected_pixels = np.count_nonzero(mask)
        selected_percent = 100 * selected_pixels / gray.size
        print(f"{threshold:9d} | {selected_pixels:15d} | "
              f"{selected_percent:15.2f}% | {region_count:7d}")
    print("Original grayscale unchanged:", np.array_equal(gray, green))


if __name__ == "__main__":
    main()
