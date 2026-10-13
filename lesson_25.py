"""Lesson 25: particle-level overlap diagnostics and matched-region errors."""

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from skimage.draw import polygon
from skimage.measure import regionprops


def reference_instances(annotations, row_range, column_range):
    """Rasterize each polygon independently, preserving separate particle identities."""
    r0, r1 = row_range
    c0, c1 = column_range
    masks, records = [], []
    for annotation in annotations:
        mask = np.zeros((r1 - r0, c1 - c0), dtype=bool)
        vertices = []
        if not isinstance(annotation["segmentation"], list):
            raise ValueError("This lesson expects polygon annotations, not encoded masks.")
        for coordinates in annotation["segmentation"]:
            xy = np.asarray(coordinates, dtype=float).reshape(-1, 2)
            vertices.append(xy)
            rr, cc = polygon(xy[:, 1] - r0, xy[:, 0] - c0, shape=mask.shape)
            mask[rr, cc] = True
        if np.any(mask):
            xy = np.concatenate(vertices)
            complete = bool(np.all((xy[:, 0] >= c0) & (xy[:, 0] < c1) &
                                   (xy[:, 1] >= r0) & (xy[:, 1] < r1)))
            masks.append(mask)
            records.append({"reference_id": annotation["id"], "complete_in_crop": complete})
    return masks, records


def overlap_diagnostics(reference_masks, labels, link_fraction=0.1):
    """Compare every reference to every positive label without forcing a match."""
    pred_ids = np.unique(labels[labels > 0])
    intersections = np.zeros((len(reference_masks), len(pred_ids)), dtype=int)
    reference_areas = np.array([np.count_nonzero(m) for m in reference_masks])
    predicted_areas = np.array([np.count_nonzero(labels == p) for p in pred_ids])
    for i, mask in enumerate(reference_masks):
        for j, pred_id in enumerate(pred_ids):
            intersections[i, j] = np.count_nonzero(mask & (labels == pred_id))
    union = reference_areas[:, None] + predicted_areas[None, :] - intersections
    iou = np.divide(intersections, union, out=np.zeros_like(union, dtype=float), where=union > 0)
    smaller_area = np.minimum(reference_areas[:, None], predicted_areas[None, :])
    overlap_fraction = np.divide(intersections, smaller_area,
                                 out=np.zeros_like(smaller_area, dtype=float), where=smaller_area > 0)
    links = (intersections > 0) & (overlap_fraction >= link_fraction)
    return pred_ids, intersections, iou, overlap_fraction, links


def shape_measurements(mask, scale):
    """Measure the selected instance in 2D using the same scale for both methods."""
    region = regionprops(mask.astype(np.uint8))[0]
    return {"area_nm2": region.area * scale ** 2,
            "diameter_nm": region.equivalent_diameter_area * scale,
            "eccentricity": region.eccentricity}


def save_rows(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    min_match_iou = 0.50  # Experiment: change only this to 0.75.
    link_fraction = 0.10  # Exploratory substantial-overlap rule, not a universal standard.
    project = Path(__file__).resolve().parent
    inputs = project / "lesson_24_results"
    if not (inputs / "segmentation.npz").exists():
        raise FileNotFoundError("Run lesson_24.py first to save its segmentation.")
    parameters = json.loads((inputs / "parameters.json").read_text(encoding="utf-8"))
    with np.load(inputs / "segmentation.npz", allow_pickle=False) as archive:
        labels = archive["labels"]
        components = archive["components"]
        candidate = archive["candidate"]
    row_range, column_range = parameters["roi_rows"], parameters["roi_columns"]
    r0, r1 = row_range
    c0, c1 = column_range
    if labels.shape != (r1 - r0, c1 - c0) or components.shape != labels.shape:
        raise ValueError("Saved arrays and crop metadata do not agree.")
    annotations_path = project / "data" / "public_tem" / "annotations_L1-1-D.json"
    dataset = json.loads(annotations_path.read_text(encoding="utf-8"))
    if len(dataset["images"]) != 1 or dataset["images"][0]["file_name"] != Path(parameters["source"]).name:
        raise ValueError("Annotations do not describe this segmentation's source image.")
    image_id = dataset["images"][0]["id"]
    annotations = [a for a in dataset["annotations"] if a["image_id"] == image_id]
    ref_masks, records = reference_instances(annotations, row_range, column_range)
    pred_ids, intersections, iou, fractions, links = overlap_diagnostics(ref_masks, labels, link_fraction)
    ref_degree = links.sum(axis=1)
    pred_degree = links.sum(axis=0)
    border_parents = np.unique(np.concatenate((components[0], components[-1],
                                               components[:, 0], components[:, -1])))
    border_flags = []
    for pred_id in pred_ids:
        parent = int(components[labels == pred_id][0])
        border_flags.append(bool(parent in border_parents))

    reference_rows = []
    for i, record in enumerate(records):
        status = "no_substantial_overlap" if ref_degree[i] == 0 else (
            "possible_split" if ref_degree[i] > 1 else "one_link")
        reference_rows.append({"display_id": i + 1, **record,
                               "linked_regions": int(ref_degree[i]), "overlap_status": status})
    prediction_rows = []
    for j, pred_id in enumerate(pred_ids):
        status = "no_substantial_overlap" if pred_degree[j] == 0 else (
            "possible_merge" if pred_degree[j] > 1 else "one_link")
        prediction_rows.append({"predicted_label": int(pred_id), "parent_touches_border": border_flags[j],
                                "linked_references": int(pred_degree[j]), "overlap_status": status})
    errors, edge_rows, pair_errors = [], [], []
    for i, j in zip(*np.nonzero(links)):
        unique_pair = bool(ref_degree[i] == 1 and pred_degree[j] == 1)
        accepted = bool(unique_pair and iou[i, j] >= min_match_iou)
        eligible = bool(accepted and records[i]["complete_in_crop"] and not border_flags[j])
        edge_rows.append({"reference_display_id": int(i + 1), "reference_id": records[i]["reference_id"],
                          "predicted_label": int(pred_ids[j]), "intersection_px": int(intersections[i, j]),
                          "overlap_smaller_fraction": fractions[i, j], "iou": iou[i, j],
                          "unique_pair": unique_pair, "accepted_match": accepted,
                          "eligible_for_error_summary": eligible})
        reference = shape_measurements(ref_masks[i], parameters["nm_per_pixel"])
        predicted = shape_measurements(labels == pred_ids[j], parameters["nm_per_pixel"])
        measurement = {"reference_display_id": int(i + 1), "predicted_label": int(pred_ids[j]),
                       "iou": iou[i, j], "reference_area_nm2": reference["area_nm2"],
                       "predicted_area_nm2": predicted["area_nm2"],
                       "area_error_percent": 100 * (predicted["area_nm2"] / reference["area_nm2"] - 1),
                       "reference_diameter_nm": reference["diameter_nm"],
                       "predicted_diameter_nm": predicted["diameter_nm"],
                       "diameter_error_percent": 100 * (predicted["diameter_nm"] / reference["diameter_nm"] - 1),
                       "reference_eccentricity": reference["eccentricity"],
                       "predicted_eccentricity": predicted["eccentricity"],
                       "eccentricity_difference": predicted["eccentricity"] - reference["eccentricity"]}
        topology = "possible_split" if ref_degree[i] > 1 else "possible_merge" if pred_degree[j] > 1 else "one_link"
        pair_errors.append({**measurement, "topology": topology, "eligible_match": eligible})
        if eligible:
            errors.append(measurement)
    output = project / "lesson_25_results"
    output.mkdir(exist_ok=True)
    save_rows(output / "reference_diagnostics.csv", list(reference_rows[0]), reference_rows)
    save_rows(output / "prediction_diagnostics.csv", list(prediction_rows[0]), prediction_rows)
    edge_fields = ["reference_display_id", "reference_id", "predicted_label", "intersection_px",
                   "overlap_smaller_fraction", "iou", "unique_pair", "accepted_match", "eligible_for_error_summary"]
    save_rows(output / "overlap_links.csv", edge_fields, edge_rows)
    error_fields = ["reference_display_id", "predicted_label", "iou", "reference_area_nm2", "predicted_area_nm2",
                    "area_error_percent", "reference_diameter_nm", "predicted_diameter_nm", "diameter_error_percent",
                    "reference_eccentricity", "predicted_eccentricity", "eccentricity_difference"]
    save_rows(output / "matched_errors.csv", error_fields, errors)
    save_rows(output / "linked_pair_comparisons.csv", error_fields + ["topology", "eligible_match"], pair_errors)
    coverage = np.stack(ref_masks).sum(axis=0)
    with Image.open(project / "data" / "public_tem" / "L1-1-D_mask.png") as source:
        published_union = np.array(source)[r0:r1, c0:c1] > 0
    summary = {"segmentation_parameters": parameters, "link_fraction": link_fraction,
               "min_match_iou": min_match_iou, "reference_instances_in_crop": len(records),
               "complete_reference_instances": sum(r["complete_in_crop"] for r in records),
               "predicted_regions": len(pred_ids), "references_without_link": int(np.count_nonzero(ref_degree == 0)),
               "complete_references_without_link": int(sum(records[i]["complete_in_crop"] and ref_degree[i] == 0 for i in range(len(records)))),
               "possible_split_references": int(np.count_nonzero(ref_degree > 1)),
               "possible_merge_regions": int(np.count_nonzero(pred_degree > 1)),
               "predictions_without_link": int(np.count_nonzero(pred_degree == 0)),
               "accepted_unique_matches_including_border": sum(e["accepted_match"] for e in edge_rows),
               "eligible_error_pairs": len(errors),
               "overlapping_reference_pixels": int(np.count_nonzero(coverage > 1)),
               "polygon_union_vs_published_mask_disagreement_px": int(np.count_nonzero((coverage > 0) != published_union)),
               "npz_sha256": hashlib.sha256((inputs / "segmentation.npz").read_bytes()).hexdigest(),
               "annotations_sha256": hashlib.sha256(annotations_path.read_bytes()).hexdigest(),
               "status": "Exploratory same-crop comparison with approximate manual annotations"}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Source segmentation threshold:", parameters["threshold"])
    for key in ["reference_instances_in_crop", "complete_reference_instances", "predicted_regions",
                "references_without_link", "complete_references_without_link", "possible_split_references", "possible_merge_regions",
                "predictions_without_link", "accepted_unique_matches_including_border", "eligible_error_pairs",
                "overlapping_reference_pixels", "polygon_union_vs_published_mask_disagreement_px"]:
        print(key + ":", summary[key])
    print("R ID / label / area error (%) / diameter error (%) / eccentricity difference")
    for e in errors:
        print(f"{e['reference_display_id']:4d} {e['predicted_label']:5d} {e['area_error_percent']:16.2f} "
              f"{e['diameter_error_percent']:20.2f} {e['eccentricity_difference']:24.3f}")
    print("Possible merges:", pred_ids[pred_degree > 1].tolist())
    print("Possible splits (reference display IDs):", (np.flatnonzero(ref_degree > 1) + 1).tolist())
    print("Errors describe eligible matches only; misses, splits and merges are reported separately.")

    with Image.open(project / parameters["source"]) as source:
        roi = np.array(source)[r0:r1, c0:c1]
    fig, axes = plt.subplots(2, 2, figsize=(12, 10), layout="constrained")
    for ax in axes[0]:
        ax.imshow(roi, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        ax.set_xlabel("Column within crop (pixels)")
        ax.set_ylabel("Row within crop (pixels)")
    for i, mask in enumerate(ref_masks):
        axes[0, 0].contour(mask, levels=[0.5], colors=["lime"], linewidths=0.8)
        rows, columns = np.nonzero(mask)
        axes[0, 0].text(columns.mean(), rows.mean(), str(i + 1), color="yellow", ha="center", fontsize=8)
    for j, pred_id in enumerate(pred_ids):
        mask = labels == pred_id
        axes[0, 1].contour(mask, levels=[0.5], colors=["cyan"], linewidths=0.8)
        rows, columns = np.nonzero(mask)
        axes[0, 1].text(columns.mean(), rows.mean(), str(pred_id), color="yellow", ha="center", fontsize=8)
    axes[0, 0].set_title("Manual instances: reference display IDs")
    axes[0, 1].set_title("Watershed instances: label IDs")
    display = axes[1, 0].imshow(iou, cmap="viridis", vmin=0, vmax=1, aspect="auto", interpolation="nearest")
    axes[1, 0].set_xticks(np.arange(len(pred_ids)), pred_ids, fontsize=8)
    axes[1, 0].set_yticks(np.arange(len(records)), np.arange(1, len(records) + 1), fontsize=8)
    axes[1, 0].set_xlabel("Predicted label")
    axes[1, 0].set_ylabel("Reference display ID")
    axes[1, 0].set_title("Pairwise IoU; not a forced assignment")
    fig.colorbar(display, ax=axes[1, 0], label="IoU")
    if errors:
        x = [e["reference_diameter_nm"] for e in errors]
        y = [e["predicted_diameter_nm"] for e in errors]
        axes[1, 1].scatter(x, y)
        lower, upper = min(x + y) * 0.9, max(x + y) * 1.1
        axes[1, 1].plot([lower, upper], [lower, upper], "k--", label="Equal diameters")
        axes[1, 1].legend()
    else:
        axes[1, 1].text(0.5, 0.5, "No eligible matched pairs", ha="center", transform=axes[1, 1].transAxes)
    axes[1, 1].set_xlabel("Reference equivalent diameter (nm)")
    axes[1, 1].set_ylabel("Predicted equivalent diameter (nm)")
    axes[1, 1].set_title(f"{len(errors)} eligible one-to-one matches only")
    fig.savefig(project / "lesson_25.png", dpi=150)
    print("Saved diagnostic files in:", output)
    plt.show()


if __name__ == "__main__":
    main()
