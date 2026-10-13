"""Lesson 12: count pixels belonging to each connected region."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

import numpy as np
from scipy.ndimage import generate_binary_structure, label
import tifffile


def main():
    structure = generate_binary_structure(2, 1)  # Edge connections only.
    extra_pixel = 0  # Experiment: change only this to 1.
    example = np.array([[1, 1, 0], [extra_pixel, 0, 1], [0, 0, 1]], dtype=bool)
    example_labels, example_count = label(example, structure=structure)
    example_counts = np.bincount(example_labels.ravel())
    print("SYNTHETIC EXAMPLE: region IDs, not intensities")
    print(example_labels)
    print("Counts by ID, including 0:", example_counts)
    print("Region count:", example_count)
    print("Region sizes (pixels), excluding ID 0:", example_counts[1:])

    image_path = teaching_tiff_path()
    with tifffile.TiffFile(image_path) as tif:
        image = tif.series[0].asarray()
    roi = image[100:300, 100:400, :].copy()
    red, green, blue = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
    if not (np.array_equal(red, green) and np.array_equal(red, blue)):
        raise ValueError("Unequal RGB components: inspect the ROI before proceeding.")
    gray = green.copy()
    mask = gray < 80
    labels, region_count = label(mask, structure=structure)

    counts_by_label = np.bincount(labels.ravel())
    region_sizes = counts_by_label[1:]  # ID 0 is unselected, not a region.
    print("\nREAL ROI: mask-region sizes, NOT validated particle areas")
    print("Region count:", region_count)
    print("Unselected pixels:", counts_by_label[0])
    print("First ten region sizes (pixels):", region_sizes[:10])
    print("Sum of all region sizes:", region_sizes.sum())
    print("Selected pixels:", np.count_nonzero(mask))
    print("Totals agree:", region_sizes.sum() == np.count_nonzero(mask))


if __name__ == "__main__":
    main()
