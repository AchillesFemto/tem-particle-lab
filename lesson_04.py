"""Lesson 4: select a rectangular region without changing the source array."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

import matplotlib.pyplot as plt
import tifffile


def main():
    image_path = teaching_tiff_path()
    with tifffile.TiffFile(image_path) as tif:
        image = tif.series[0].asarray()

    row_start = 100
    row_stop = 300  # Experiment: change only this to 400.
    column_start = 100
    column_stop = 400

    # Stop indices are excluded; the final colon keeps all RGB components.
    roi = image[row_start:row_stop, column_start:column_stop, :].copy()

    print("Original shape:", image.shape)
    print("ROI shape:", roi.shape)
    print("ROI dimensions:", roi.ndim)
    print("ROI storage type:", roi.dtype)
    print("First ROI pixel:", roi[0, 0])
    print("Matching original pixel:", image[row_start, column_start])

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.imshow(roi, origin="upper", interpolation="nearest", aspect="equal")
    ax.set_title(
        f"ROI: source rows {row_start}:{row_stop}, columns {column_start}:{column_stop}"
    )
    ax.set_xlabel("Column index within ROI (pixels)")
    ax.set_ylabel("Row index within ROI (pixels)")
    fig.tight_layout()
    output_path = Path(__file__).resolve().parent / "lesson_04.png"
    fig.savefig(output_path, dpi=150)
    print("Saved display:", output_path)
    plt.show()


if __name__ == "__main__":
    main()
