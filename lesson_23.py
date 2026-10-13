"""Lesson 23: find candidate particle seeds from distance-map peaks."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import ndimage

from lesson_22 import foreground_distance


def distance_peak_seeds(distance, window_size=41, min_height=20.0):
    """Return one (row, column) seed per connected local-maximum plateau."""
    if distance.ndim != 2 or not np.all(np.isfinite(distance)) or np.any(distance < 0):
        raise ValueError("Use a finite, nonnegative two-dimensional distance map.")
    if not isinstance(window_size, int) or window_size < 3 or window_size % 2 == 0:
        raise ValueError("Use an odd integer window size of at least 3.")
    if not np.isfinite(min_height) or min_height <= 0:
        raise ValueError("Minimum peak height must be finite and positive.")
    nearby_max = ndimage.maximum_filter(distance, size=window_size,
                                        mode="constant", cval=0)
    peaks = (distance == nearby_max) & (distance >= min_height)
    # Avoid points whose comparison window extends outside the observed crop.
    border = window_size // 2
    peaks[:border, :] = False
    peaks[-border:, :] = False
    peaks[:, :border] = False
    peaks[:, -border:] = False
    # Group adjacent equal-height peak pixels, including diagonal neighbours.
    labels, count = ndimage.label(peaks, structure=np.ones((3, 3), dtype=bool))
    if count == 0:
        return np.empty((0, 2), dtype=int)
    positions = ndimage.maximum_position(distance, labels, range(1, count + 1))
    return np.asarray(positions, dtype=int)


def suppress_nearby_seeds(distance, seeds, mask, min_separation=10.0):
    """Keep stronger seeds, suppressing nearby ones in the same foreground component."""
    if distance.shape != mask.shape or mask.dtype != bool:
        raise ValueError("Use an aligned distance map and Boolean foreground mask.")
    if not np.isfinite(min_separation) or min_separation <= 0:
        raise ValueError("Minimum seed separation must be finite and positive.")
    seeds = np.asarray(seeds, dtype=int).reshape(-1, 2)
    if len(seeds) == 0:
        return seeds
    if np.any(seeds < 0) or np.any(seeds >= np.array(mask.shape)):
        raise ValueError("Seed coordinates must lie inside the array.")
    if not np.all(mask[seeds[:, 0], seeds[:, 1]]):
        raise ValueError("Seeds must lie in foreground.")
    components, _ = ndimage.label(mask, structure=np.ones((3, 3), dtype=bool))
    heights = distance[seeds[:, 0], seeds[:, 1]]
    order = np.argsort(-heights, kind="stable")
    kept = []
    for index in order:
        row, column = seeds[index]
        parent = components[row, column]
        duplicate = any(
            components[tuple(seeds[previous])] == parent and
            np.linalg.norm(seeds[index] - seeds[previous]) < min_separation
            for previous in kept
        )
        if not duplicate:
            kept.append(int(index))
    # Preserve the original order for the surviving points, not height ranking.
    return seeds[np.sort(kept)]


def main():
    window_size = 41  # Experiment: change only this to 81.
    threshold = 140
    min_height = 20.0  # Minimum distance to background, in pixels.
    project = Path(__file__).resolve().parent
    image_path = project / "data" / "public_tem" / "L1-1-D.png"
    with Image.open(image_path) as source:
        image = np.array(source)
    if image.ndim != 2 or image.dtype != np.uint8:
        raise ValueError("This lesson expects a two-dimensional uint8 image.")
    roi = image[300:1100, 300:1100]
    candidate = roi < threshold
    distance = foreground_distance(candidate)
    seeds = distance_peak_seeds(distance, window_size, min_height)
    print("Comparison window:", window_size, "by", window_size, "pixels")
    print("Minimum peak height:", min_height, "pixels")
    print("Candidate seeds:", len(seeds))
    print("Seed coordinates (row, column within crop):")
    print(seeds)
    print("Seeds are proposed starting points; their count is not a validated particle count.")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), layout="constrained")
    axes[0].imshow(distance, cmap="viridis", vmin=0, vmax=80, interpolation="nearest")
    axes[0].set_title("Distance map with candidate seeds")
    axes[1].imshow(roi, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
    axes[1].set_title("Same seeds on the TEM crop")
    for ax in axes:
        ax.scatter(seeds[:, 1], seeds[:, 0], s=70, facecolors="none",
                   edgecolors="red", linewidths=1.5, label="Candidate seed")
        ax.set_xlabel("Column within crop (pixels)")
        ax.set_ylabel("Row within crop (pixels)")
        ax.legend(loc="upper right")
    fig.suptitle(f"{len(seeds)} candidate seeds; comparison window = {window_size}")
    output_path = project / "lesson_23.png"
    fig.savefig(output_path, dpi=150)
    print("Saved figure:", output_path)
    plt.show()


if __name__ == "__main__":
    main()
