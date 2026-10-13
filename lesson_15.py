"""Lesson 15: retain labeled regions meeting a minimum pixel count."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

import numpy as np
from scipy.ndimage import generate_binary_structure, label
import tifffile


def keep_large_regions(labels, min_pixels):
    """Filter whole regions into a new array, preserving surviving IDs."""
    if min_pixels < 1:
        raise ValueError("Minimum size must be at least one pixel.")
    counts = np.bincount(labels.ravel())
    keep_id = counts >= min_pixels
    keep_id[0] = False  # Never include unselected pixels as a region.
    result = labels.copy()
    result[~keep_id[labels]] = 0
    return result


def main():
    min_pixels = 3  # Experiment: change only this to 5.
    # Invented label IDs with sizes 2, 4 and 6 pixels respectively.
    example_labels = np.array([
        [1, 1, 0, 2, 2, 0, 3, 3, 3],
        [0, 0, 0, 2, 2, 0, 3, 3, 3],
    ], dtype=np.int32)
    example_kept = keep_large_regions(example_labels, min_pixels)
    print("SYNTHETIC EXAMPLE: original region sizes (pixels)")
    print(np.bincount(example_labels.ravel())[1:])
    print("Minimum pixels:", min_pixels)
    print("Retained labels:")
    print(example_kept)
    print("Retained region count:", np.unique(example_kept[example_kept > 0]).size)

    image_path = teaching_tiff_path()
    with tifffile.TiffFile(image_path) as tif:
        image = tif.series[0].asarray()
    roi = image[100:300, 100:400, :].copy()
    red, green, blue = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
    if not (np.array_equal(red, green) and np.array_equal(red, blue)):
        raise ValueError("Unequal RGB components: inspect the ROI before proceeding.")
    gray = green.copy()
    mask = gray < 80
    structure = generate_binary_structure(2, 1)
    labels, region_count = label(mask, structure=structure)
    kept = keep_large_regions(labels, min_pixels)
    print("\nREAL ROI: size-filtered mask regions, NOT validated particles")
    print("Threshold: 80; edge-only connectivity; no border exclusion")
    print("Original and retained regions:", region_count,
          np.unique(kept[kept > 0]).size)
    print("Original and retained selected pixels:", np.count_nonzero(mask),
          np.count_nonzero(kept))
    print("Original selection preserved:", np.array_equal(labels > 0, mask))


if __name__ == "__main__":
    main()
