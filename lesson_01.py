"""Lesson 1: a synthetic grayscale image is a numerical array."""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def main():
    # Invented values for learning; these are not experimental measurements.
    image = np.array(
        [
            [10, 10, 10, 10, 10],
            [10, 40, 80, 40, 10],
            [10, 80, 200, 80, 10],
            [10, 40, 80, 40, 10],
        ],
        dtype=np.uint16,
    )

    print("Pixel values:\n", image)
    print("Dimensions:", image.ndim)
    print("Shape (rows, columns):", image.shape)
    print("Storage type:", image.dtype)
    print("Observed minimum and maximum:", image.min(), image.max())
    print("Value at row 2, column 2:", image[2, 2])

    display_max = 200  # Experiment: change only this to 400.
    fig, ax = plt.subplots()
    display = ax.imshow(
        image,
        cmap="gray",
        vmin=0,
        vmax=display_max,
        interpolation="nearest",
        origin="upper",
    )
    ax.set_title("Synthetic image: stored values shown as brightness")
    ax.set_xlabel("Column index (pixels)")
    ax.set_ylabel("Row index (pixels)")
    ax.set_xticks(range(image.shape[1]))
    ax.set_yticks(range(image.shape[0]))
    fig.colorbar(display, ax=ax, label="Synthetic intensity (arbitrary units)")
    fig.tight_layout()
    output_path = Path(__file__).resolve().parent / "lesson_01.png"
    fig.savefig(output_path, dpi=160)
    print("Figure saved to:", output_path)
    plt.show()


if __name__ == "__main__":
    main()
