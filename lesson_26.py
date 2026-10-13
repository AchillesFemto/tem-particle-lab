"""Lesson 26: nearest neighbours and pair correlations in a TEM point pattern."""

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from skimage.draw import polygon
from skimage.measure import regionprops


def annotation_centres(annotations, image_shape):
    """Measure centroids from full polygon masks before selecting the spatial window."""
    centres, ids = [], []
    for annotation in annotations:
        vertices = [np.asarray(p, dtype=float).reshape(-1, 2) for p in annotation["segmentation"]]
        xy = np.concatenate(vertices)
        c0, r0 = np.maximum(np.floor(xy.min(axis=0)).astype(int), 0)
        c1, r1 = np.minimum(np.ceil(xy.max(axis=0)).astype(int) + 1,
                            [image_shape[1], image_shape[0]])
        mask = np.zeros((r1 - r0, c1 - c0), dtype=bool)
        for points in vertices:
            rr, cc = polygon(points[:, 1] - r0, points[:, 0] - c0, shape=mask.shape)
            mask[rr, cc] = True
        if np.any(mask):
            row, column = regionprops(mask.astype(np.uint8))[0].centroid
            centres.append([column + c0, row + r0])
            ids.append(annotation["id"])
    return np.asarray(centres), np.asarray(ids)


def nearest_neighbours(points, width, height):
    """Return within-window nearest distances, neighbour indices and boundary flags."""
    if len(points) < 2:
        raise ValueError("At least two centres are needed.")
    if not np.all(np.isfinite(points)) or np.any(points < 0) or np.any(points >= [width, height]):
        raise ValueError("Centres must be finite and lie inside the observation window.")
    distances, indices = cKDTree(points).query(points, k=2)
    nearest = distances[:, 1]  # First neighbour is the query point itself.
    edge_distance = np.minimum.reduce([points[:, 0], width - points[:, 0],
                                       points[:, 1], height - points[:, 1]])
    safe = nearest < edge_distance
    return nearest, indices[:, 1], edge_distance, safe


def radial_pair_correlation(points, width, height, edges):
    """Annulus-averaged pair correlation with rectangular translation weights."""
    n = len(points)
    if n < 2:
        raise ValueError("At least two points are needed for pair correlations.")
    if edges[0] != 0 or np.any(np.diff(edges) <= 0) or edges[-1] > min(width, height) / 2:
        raise ValueError("Use increasing bins from zero up to at most half the shorter window side.")
    i, j = np.triu_indices(n, k=1)  # Every unordered pair once; no self-pairs.
    delta = points[i] - points[j]
    radii = np.linalg.norm(delta, axis=1)
    overlap_area = (width - np.abs(delta[:, 0])) * (height - np.abs(delta[:, 1]))
    area = width * height
    weights = area / overlap_area
    counts, _ = np.histogram(radii, bins=edges)
    weighted_counts, _ = np.histogram(radii, bins=edges, weights=weights)
    annulus_area = np.pi * (edges[1:] ** 2 - edges[:-1] ** 2)
    g = 2 * area * weighted_counts / (n * (n - 1) * annulus_area)
    return g, counts


def save_rows(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    bin_width_nm = 5.0  # Experiment: change only this to 10.0.
    max_radius_nm = 40.0
    simulations = 200
    random_seed = 26
    project = Path(__file__).resolve().parent
    inputs = project / "lesson_24_results"
    if not (inputs / "segmentation.npz").exists():
        raise FileNotFoundError("Run lesson_24.py first.")
    parameters = json.loads((inputs / "parameters.json").read_text(encoding="utf-8"))
    with np.load(inputs / "segmentation.npz", allow_pickle=False) as archive:
        labels = archive["labels"]
    r0, r1 = parameters["roi_rows"]
    c0, c1 = parameters["roi_columns"]
    scale = parameters["nm_per_pixel"]
    width, height = (c1 - c0) * scale, (r1 - r0) * scale
    with Image.open(project / parameters["source"]) as source:
        image = np.array(source)
    dataset = json.loads((project / "data/public_tem/annotations_L1-1-D.json").read_text(encoding="utf-8"))
    if len(dataset["images"]) != 1 or dataset["images"][0]["file_name"] != Path(parameters["source"]).name:
        raise ValueError("Reference annotations and image must correspond.")
    image_id = dataset["images"][0]["id"]
    annotations = [a for a in dataset["annotations"] if a["image_id"] == image_id]
    full_centres, full_ids = annotation_centres(annotations, image.shape)
    inside = ((full_centres[:, 0] >= c0) & (full_centres[:, 0] < c1) &
              (full_centres[:, 1] >= r0) & (full_centres[:, 1] < r1))
    points = (full_centres[inside] - [c0, r0]) * scale
    reference_ids = full_ids[inside]
    # All algorithmic regions are displayed as a bias demonstration, not trusted particles.
    properties = regionprops(labels)
    predicted = np.array([[p.centroid[1], p.centroid[0]] for p in properties]) * scale
    predicted_ids = [p.label for p in properties]
    nn, neighbours, edge_distances, safe = nearest_neighbours(points, width, height)
    pred_nn, _, _, _ = nearest_neighbours(predicted, width, height)
    if bin_width_nm <= 0 or not np.isclose(max_radius_nm / bin_width_nm,
                                         round(max_radius_nm / bin_width_nm)):
        raise ValueError("Choose a positive bin width that divides 40 nm exactly.")
    edges = np.linspace(0, max_radius_nm, round(max_radius_nm / bin_width_nm) + 1)
    g, pair_counts = radial_pair_correlation(points, width, height, edges)
    rng = np.random.default_rng(random_seed)
    null_g, null_nn_medians = [], []
    for _ in range(simulations):
        random_points = rng.uniform([0, 0], [width, height], size=(len(points), 2))
        simulated_g, _ = radial_pair_correlation(random_points, width, height, edges)
        simulated_nn, _, _, _ = nearest_neighbours(random_points, width, height)
        null_g.append(simulated_g)
        null_nn_medians.append(float(np.median(simulated_nn)))
    low, median, high = np.percentile(null_g, [2.5, 50, 97.5], axis=0)
    output = project / "lesson_26_results"
    output.mkdir(exist_ok=True)
    rows = [{"annotation_id": int(reference_ids[i]), "x_nm": x, "y_nm": y,
             "nearest_annotation_id": int(reference_ids[neighbours[i]]),
             "nearest_distance_nm": nn[i], "distance_to_window_edge_nm": edge_distances[i],
             "nearest_is_boundary_safe": bool(safe[i])} for i, (x, y) in enumerate(points)]
    save_rows(output / "reference_positions.csv", list(rows[0]), rows)
    pred_rows = [{"predicted_label": int(predicted_ids[i]), "x_nm": x, "y_nm": y,
                  "nearest_distance_nm": pred_nn[i], "status": "unvalidated_detection"}
                 for i, (x, y) in enumerate(predicted)]
    save_rows(output / "predicted_positions.csv", list(pred_rows[0]), pred_rows)
    pair_rows = [{"r_start_nm": edges[i], "r_stop_nm": edges[i+1],
                  "pairs_in_bin": int(pair_counts[i]), "g_reference": g[i],
                  "uniform_pointwise_2p5": low[i], "uniform_median": median[i],
                  "uniform_pointwise_97p5": high[i]} for i in range(len(g))]
    save_rows(output / "pair_correlation.csv", list(pair_rows[0]), pair_rows)
    summary = {"segmentation_parameters": parameters, "reference_centres_in_window": len(points),
               "predicted_centres": len(predicted), "window_width_nm": width, "window_height_nm": height,
               "reference_within_window_nn_median_nm": float(np.median(nn)),
               "predicted_within_window_nn_median_nm": float(np.median(pred_nn)),
               "boundary_safe_reference_points": int(safe.sum()),
               "uniform_nn_median_percentiles_nm": np.percentile(null_nn_medians, [2.5, 50, 97.5]).tolist(),
               "bin_width_nm": bin_width_nm, "max_radius_nm": max_radius_nm,
               "simulations": simulations, "random_seed": random_seed,
               "edge_correction": "Rectangular translation; annulus-average; N(N-1) fixed-count normalization",
               "null_model": "Independent uniform points conditional on observed count; no size exclusion",
               "status": "Exploratory single-window spatial statistics; no formal clustering claim",
               "segmentation_sha256": hashlib.sha256((inputs / "segmentation.npz").read_bytes()).hexdigest()}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Observation window: {width:.2f} by {height:.2f} nm")
    print("Manual centres / unvalidated detected centres:", len(points), "/", len(predicted))
    print(f"Reference within-window nearest-neighbour median: {np.median(nn):.2f} nm")
    print(f"Detection within-window nearest-neighbour median: {np.median(pred_nn):.2f} nm")
    print("Boundary-safe reference nearest neighbours:", safe.sum(), "of", len(points))
    print("Uniform-point simulation median-NN percentiles (nm):", summary["uniform_nn_median_percentiles_nm"])
    print("Radial pair counts:", pair_counts.tolist())
    print("g(r) annulus averages:", np.round(g, 3).tolist())
    print("Finite particles are not size-free random points; simulations are an illustrative baseline.")

    fig, axes = plt.subplots(2, 2, figsize=(12, 10), layout="constrained")
    axes[0, 0].imshow(image[r0:r1,c0:c1], cmap="gray", vmin=0, vmax=255,
                       extent=(0,width,height,0), interpolation="nearest")
    axes[0, 0].scatter(points[:,0],points[:,1],facecolors="none",edgecolors="lime",s=80,label="Manual centres")
    axes[0, 0].scatter(predicted[:,0],predicted[:,1],marker="x",color="orange",s=35,label="Unvalidated detections")
    axes[0, 0].set_title("Two position sets; segmentation can bias spacing")
    axes[0, 0].legend(fontsize=8)
    axes[0, 1].scatter(points[:,0],points[:,1],c=np.where(safe,"tab:blue","tab:red"))
    for i,j in enumerate(neighbours):
        axes[0, 1].plot(points[[i,j],0],points[[i,j],1],color="gray",linewidth=0.7)
    axes[0, 1].set_xlim(0,width)
    axes[0, 1].set_ylim(height,0)
    axes[0, 1].set_aspect("equal")
    axes[0, 1].set_title("Nearest neighbours: red = boundary-uncertain")
    for ax in axes[0]:
        ax.set_xlabel("x within observation window (nm)")
        ax.set_ylabel("y within observation window (nm)")
    hist_edges=np.linspace(0,max(nn.max(),pred_nn.max())*1.05,9)
    axes[1,0].hist(nn,bins=hist_edges,histtype="step",linewidth=2,label="Manual centres")
    axes[1,0].hist(pred_nn,bins=hist_edges,histtype="step",linewidth=2,label="Unvalidated detections")
    axes[1,0].set_xlabel("Within-window nearest-neighbour distance (nm)")
    axes[1,0].set_ylabel("Number of centres")
    axes[1,0].set_title("Centre-to-centre distances; includes boundary uncertainty")
    axes[1,0].legend(fontsize=8)
    mid=(edges[:-1]+edges[1:])/2
    axes[1,1].fill_between(mid,low,high,color="lightgray",label="Uniform simulations: pointwise 95% range")
    axes[1,1].plot(mid,median,"k--",label="Uniform simulation median")
    axes[1,1].plot(mid,g,"o-",label="Manual-centre g(r)")
    axes[1,1].axhline(1,color="gray",linewidth=0.8)
    axes[1,1].set_xlabel("Centre separation r (nm)")
    axes[1,1].set_ylabel("Annulus-averaged g(r)")
    axes[1,1].set_title("Translation-corrected, exploratory pair correlation")
    axes[1,1].legend(fontsize=7)
    fig.savefig(project / "lesson_26.png", dpi=150)
    print("Saved diagnostic files in:", output)
    plt.show()


if __name__ == "__main__":
    main()
