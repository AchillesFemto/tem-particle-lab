"""Lesson 24: watershed separation, scale-bar calibration, and region measurements."""

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.color import label2rgb
from skimage.measure import regionprops
from skimage.segmentation import watershed

from lesson_22 import foreground_distance
from lesson_23 import distance_peak_seeds, suppress_nearby_seeds


def separate_foreground(mask, distance, seeds):
    """Flood the negative distance map from uniquely numbered seed pixels."""
    if mask.shape != distance.shape or mask.dtype != bool:
        raise ValueError("Use an aligned Boolean mask and distance map.")
    if len(seeds) == 0:
        raise ValueError("Watershed needs at least one seed in this lesson.")
    markers = np.zeros(mask.shape, dtype=np.int32)
    for seed_id, (row, column) in enumerate(seeds, start=1):
        if not mask[row, column]:
            raise ValueError("Each seed must lie within foreground.")
        markers[row, column] = seed_id
    connectivity = np.ones((3, 3), dtype=bool)
    labels = watershed(-distance, markers=markers, mask=mask,
                       connectivity=connectivity, watershed_line=False)
    return labels, markers


def main():
    threshold = 140  # Experiment: change only this to 160.
    window_size = 41
    min_height = 20.0
    min_seed_separation = 10.0  # Suppress very close seeds within the same component.
    scale_bar_nm = 100.0
    scale_bar_pixels = 865.0  # Published bar: columns 1424 through 2288 inclusive.
    nm_per_pixel = scale_bar_nm / scale_bar_pixels
    project = Path(__file__).resolve().parent
    with Image.open(project / "data" / "public_tem" / "L1-1-D.png") as source:
        image = np.array(source)
    if image.ndim != 2 or image.dtype != np.uint8:
        raise ValueError("This lesson expects the original grayscale uint8 PNG.")
    # Check the measured white bar on the unchanged source pixel grid.
    if not np.all(image[2225, 1424:2289] == 255):
        raise ValueError("Scale bar differs from the inspected source; recheck calibration.")
    if image[2225, 1423] == 255 or image[2225, 2289] == 255:
        raise ValueError("Scale-bar endpoints need reinspection.")
    roi = image[300:1100, 300:1100]
    candidate = roi < threshold
    distance = foreground_distance(candidate)
    raw_seeds = distance_peak_seeds(distance, window_size, min_height)
    seeds = suppress_nearby_seeds(distance, raw_seeds, candidate, min_seed_separation)
    labels, markers = separate_foreground(candidate, distance, seeds)

    # Diagnose incomplete coverage rather than silently treating it as background.
    structure = np.ones((3, 3), dtype=bool)
    components, component_count = ndimage.label(candidate, structure=structure)
    seeded_components = np.unique(components[markers > 0])
    seedless_ids = np.setdiff1d(np.arange(1, component_count + 1), seeded_components)
    unassigned = candidate & (labels == 0)
    border_ids = np.unique(np.concatenate((components[0, :], components[-1, :],
                                          components[:, 0], components[:, -1])))
    border_ids = border_ids[border_ids > 0]

    fields = ["label", "parent_component", "parent_touches_crop_border",
              "area_px", "area_nm2", "equivalent_diameter_nm",
              "major_axis_nm", "minor_axis_nm", "eccentricity",
              "centroid_row_full_px", "centroid_column_full_px", "status"]
    rows = []
    for region in regionprops(labels):
        first_row, first_column = region.coords[0]
        parent = int(components[first_row, first_column])
        touches_border = bool(parent in border_ids)
        rows.append({
            "label": region.label,
            "parent_component": parent,
            "parent_touches_crop_border": touches_border,
            "area_px": int(region.area),
            "area_nm2": region.area * nm_per_pixel ** 2,
            "equivalent_diameter_nm": region.equivalent_diameter_area * nm_per_pixel,
            "major_axis_nm": region.axis_major_length * nm_per_pixel,
            "minor_axis_nm": region.axis_minor_length * nm_per_pixel,
            "eccentricity": region.eccentricity,
            "centroid_row_full_px": region.centroid[0] + 300,
            "centroid_column_full_px": region.centroid[1] + 300,
            "status": "border_parent_excluded" if touches_border else "unvalidated_candidate",
        })
    output = project / "lesson_24_results"
    output.mkdir(exist_ok=True)
    with (output / "regions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    np.savez_compressed(output / "segmentation.npz", labels=labels, markers=markers,
                        candidate=candidate, components=components)
    metadata = {
        "source": "data/public_tem/L1-1-D.png", "roi_rows": [300, 1100],
        "roi_columns": [300, 1100], "threshold": threshold,
        "window_size": window_size, "min_height_px": min_height,
        "min_seed_separation_px": min_seed_separation, "raw_seed_count": len(raw_seeds),
        "seed_suppression": "Descending distance height; ties retain earlier point; same-component only",
        "scale_bar_nm": scale_bar_nm, "scale_bar_pixels": scale_bar_pixels,
        "nm_per_pixel": nm_per_pixel,
        "calibration_basis": "Published PNG 100 nm bar, row 2225, columns [1424,2289); width convention",
        "calibration_assumption": "Correct source bar and equal horizontal/vertical pixel spacing",
        "calibration_status": "Scale-bar estimate; not independently verified instrument calibration",
        "connectivity": 8, "seed_count": len(seeds),
        "component_count": component_count, "seedless_component_ids": seedless_ids.tolist(),
        "unassigned_foreground_pixels": int(np.count_nonzero(unassigned)),
        "region_count": len(rows),
        "validation_status": "Illustrative watershed regions; particle identities are unvalidated",
    }
    (output / "parameters.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Scale-bar estimate: {nm_per_pixel:.6f} nm per pixel")
    print("Connected foreground components:", component_count)
    print("Seeds before / after nearby-seed suppression:", len(raw_seeds), "/", len(seeds))
    print("Candidate seeds / watershed regions:", len(seeds), "/", len(rows))
    print("Components without a seed:", len(seedless_ids))
    print("Unassigned foreground pixels:", np.count_nonzero(unassigned))
    print("Regions flagged through a border-touching parent:", sum(r["parent_touches_crop_border"] for r in rows))
    print("Label    Area (nm^2)    Eq. diameter (nm)    Eccentricity    Status")
    for r in rows:
        print(f"{r['label']:5d} {r['area_nm2']:14.2f} {r['equivalent_diameter_nm']:20.2f} "
              f"{r['eccentricity']:15.3f}    {r['status']}")
    print("Measurements describe algorithmic regions; do not report them as validated particle statistics.")
    print("Results saved in:", output)

    fig, axes = plt.subplots(2, 2, figsize=(11, 10), layout="constrained")
    axes[0, 0].imshow(roi, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
    axes[0, 0].scatter(seeds[:, 1], seeds[:, 0], facecolors="none", edgecolors="red", s=65)
    axes[0, 0].set_title("TEM crop and candidate seeds")
    axes[0, 1].imshow(label2rgb(components, bg_label=0), interpolation="nearest")
    axes[0, 1].set_title(f"Before separation: {component_count} connected regions")
    axes[1, 0].imshow(label2rgb(labels, bg_label=0), interpolation="nearest")
    for region in regionprops(labels):
        row, column = region.centroid
        axes[1, 0].text(column, row, str(region.label), color="white", ha="center", fontsize=8)
    axes[1, 0].set_title(f"Watershed: {len(rows)} labelled regions; unassigned = black")
    for ax in (axes[0, 0], axes[0, 1], axes[1, 0]):
        ax.set_xlabel("Column within crop (pixels)")
        ax.set_ylabel("Row within crop (pixels)")
    axes[1, 1].imshow(image[2180:2362, 1380:2320], cmap="gray", vmin=0, vmax=255,
                       extent=(1380, 2320, 2362, 2180), interpolation="nearest")
    axes[1, 1].set_title("Published 100 nm bar: width 865 pixels")
    axes[1, 1].set_xlabel("Column in full source image (pixels)")
    axes[1, 1].set_ylabel("Row in full source image (pixels)")
    fig.savefig(project / "lesson_24.png", dpi=150)
    plt.show()


if __name__ == "__main__":
    main()
