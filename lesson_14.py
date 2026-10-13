"""Lesson 14: exclude entire labeled regions that touch the ROI boundary."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

import numpy as np
from scipy.ndimage import generate_binary_structure, label
import tifffile


def exclude_border_regions(labels):
    """Return a new label array; keep the source and surviving IDs unchanged."""
    boundary = np.concatenate((labels[0, :], labels[-1, :],
                               labels[:, 0], labels[:, -1]))
    border_ids = np.unique(boundary)
    border_ids = border_ids[border_ids > 0]
    result = labels.copy()
    result[np.isin(labels, border_ids)] = 0
    return result, border_ids


def main():
    remove_border = True  # Experiment: change only this to False.
    structure = generate_binary_structure(2, 1)
    example = np.array([
        [0, 1, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ], dtype=bool)
    example_labels, example_count = label(example, structure=structure)
    example_interior, example_border_ids = exclude_border_regions(example_labels)
    example_kept = example_interior if remove_border else example_labels.copy()
    print("SYNTHETIC EXAMPLE: original labels")
    print(example_labels)
    print("Border-touching IDs:", example_border_ids)
    print("Retained labels:")
    print(example_kept)
    print("Original region count:", example_count)
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
    labels, region_count = label(mask, structure=structure)
    interior, border_ids = exclude_border_regions(labels)
    kept = interior if remove_border else labels.copy()
    print("\nREAL ROI: computational regions, NOT validated particles")
    print("Exclude boundary regions:", remove_border)
    print("Original regions:", region_count)
    print("Regions touching boundary:", border_ids.size)
    print("Retained regions:", np.unique(kept[kept > 0]).size)
    print("Original and retained selected pixels:", np.count_nonzero(mask),
          np.count_nonzero(kept))
    print("Original mask preserved:", np.array_equal(labels > 0, mask))


if __name__ == "__main__":
    main()
