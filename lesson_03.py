"""Lesson 3: display the original RGB array with pixel coordinates."""

from pathlib import Path
from microscopy.teaching_input import teaching_tiff_path

import matplotlib.pyplot as plt
import tifffile


def main():
    image_path = teaching_tiff_path()
    with tifffile.TiffFile(image_path) as tif:
        image = tif.series[0].asarray()

    print("Loaded shape:", image.shape)
    print("Pixel at row 428, column 0:", image[428, 0])

    figure_size = 9  # Experiment: change only this to 9.
    fig, ax = plt.subplots(figsize=(figure_size, figure_size))
    # RGB values already specify color; no grayscale colormap is needed.
    ax.imshow(image, origin="upper", interpolation="nearest", aspect="equal")
    ax.set_title("PG.tif — original RGB array")
    ax.set_xlabel("Column index (pixels)")
    ax.set_ylabel("Row index (pixels)")
    fig.tight_layout()

    output_path = Path(__file__).resolve().parent / "lesson_03.png"
    fig.savefig(output_path, dpi=150)
    print("Saved display:", output_path)
    print("Shape after plotting:", image.shape)
    print("Pixel after plotting:", image[428, 0])
    plt.show()


if __name__ == "__main__":
    main()
