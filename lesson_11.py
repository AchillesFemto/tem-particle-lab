"""Lesson 11: label connected regions; do not interpret them as particles."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

import numpy as np
from scipy.ndimage import generate_binary_structure, label
import tifffile


def main():
    connectivity = 1  # Experiment: change only this to 2 to include diagonals.
    structure = generate_binary_structure(2, connectivity)

    # Three invented selected pixels touching only at corners.
    example = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=bool)
    example_labels, example_count = label(example, structure=structure)
    print("SYNTHETIC EXAMPLE: integer labels (0 = unselected)")
    print(example_labels)
    print("Selected pixels:", np.count_nonzero(example))
    print("Connected regions:", example_count)

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

    # Hold the input mask fixed while studying connectivity; no smoothing here.
    threshold = 80
    mask = gray < threshold
    labels, region_count = label(mask, structure=structure)
    print("\nREAL ROI: connected dark-pixel regions, NOT particle counts")
    print("Threshold:", threshold)
    print("Connectivity setting:", connectivity)
    print("Selected pixels:", np.count_nonzero(mask))
    print("Connected regions:", region_count)
    print("Label array shape and dtype:", labels.shape, labels.dtype)
    print("Same selected locations:", np.array_equal(labels > 0, mask))


if __name__ == "__main__":
    main()
