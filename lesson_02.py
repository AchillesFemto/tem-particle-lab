"""Lesson 2: read a TIFF and inspect its array without modifying it."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

import tifffile


def main():
    image_path = teaching_tiff_path()

    # Read the first series explicitly; check counts before assuming one image.
    with tifffile.TiffFile(image_path) as tif:
        print("TIFF pages:", len(tif.pages))
        print("Image series:", len(tif.series))
        series = tif.series[0]
        print("Axis labels:", series.axes)
        print("Pixel interpretation:", tif.pages[0].photometric.name)
        image = series.asarray()

    print("Dimensions:", image.ndim)
    print("Shape:", image.shape)
    print("Storage type:", image.dtype)
    print("Observed minimum and maximum:", image.min(), image.max())

    row = 428  # Experiment: change only this to 428.
    column = 0
    print("Selected row and column:", row, column)
    print("Stored value(s) at that pixel:", image[row, column])


if __name__ == "__main__":
    main()
