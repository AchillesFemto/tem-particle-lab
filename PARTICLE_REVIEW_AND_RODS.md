# Particle review, then rod dimensions

We are adding only two capabilities: human review/correction of particle regions, and clearly defined rod dimensions. We are not changing threshold parameters or adding machine learning.

## First concept: a label is a proposed particle identity

In a label array, zero is background and positive integers identify predicted particles. A label is an algorithm's proposal, not proof of a real particle. One real rod might have two labels (split); two touching rods might share one label (merge). A missed particle can have no label at all. Reviewing only existing labels cannot reveal every omission: you also need to inspect the full image.

The review window starts from a saved analysis run. Original input images, automatic labels and previous results stay intact. Corrections and human judgments are saved as separate revisions.

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe analyse.py --config analysis_config_rods_v2.json --protocol validation_protocol_rods_v2.json --skip-tracking
.\.venv\Scripts\python.exe review_particles.py
```

Generate an analysis first on a fresh checkout. The review and measurement commands then select the newest compatible saved run, preferring its first successful development dataset, and print that choice. With the rod configuration above, this is L2-3-B. Specify `--run results/YOUR_RUN --dataset YOUR_DATASET_ID` to select an exact run; the run must contain a configuration snapshot and complete per-image outputs. A command with no available outputs explains how to generate them. Previously saved reviews resume rather than resetting their judgments.

### Your first review: do just one particle

1. Click the rod labelled **32** in the left image. It becomes yellow and appears enlarged on the right. Clicking a selected particle again deselects it.
2. Compare the yellow boundary with the visible particle. Ignore the ellipse axes while judging the boundary. Does it enclose one whole particle? Has it included a neighbour? Is any part missing?
3. If satisfied, enter a short reason, then click **Correct**. Otherwise use **Uncertain**, **Split issue** (a physical object divided into labels), or **Merge issue** (a label covering several objects).
4. Click **Save version**. The console prints the revision folder. Use **Next** to inspect another pending region.

Marking Correct records your judgment; it is not independent physical ground truth. Saved reference annotations are not displayed in this review window. New review sessions start with no pre-approved particles. Existing local sessions may already contain your recorded judgments; resuming preserves them. The author's local review covers a subset, not the entire image; personal review revisions are excluded from Git and the portable archive.

### Corrections, when the image supports them

| Control | What it does |
|---|---|
| Merge selected | Click two or more touching labels, enter a reason, then merge. The foreground is preserved; disconnected regions cannot be joined across background. |
| Draw split | Select one region, enter a reason and draw a polygon around one part in the RIGHT image. Click the starting vertex to close it. The polygon divides the existing foreground into two nonempty connected pieces; it does not fabricate a gap. |
| Redraw boundary | Select one region and draw its replacement outline. This may change foreground area. The correction cannot overwrite another label. |
| Add polygon | Clear selection, enter a reason and draw a missed particle. The new outline must not overlap existing labels. |
| Remove false + | Remove selected regions that are not particles; a reason is required. |
| Undo | Revert one of the last five session actions. Previous saved revisions remain available. |
| Cancel drawing | Abandon the current polygon without changing pixels. |
| Field inspected | Record a reason describing your inspection of the entire crop for missing objects. Edits invalidate this flag, requiring another full-field check. |

Edits return affected regions to Pending. Inspect them before marking Correct. If the boundary is invisible because of overlap or poor contrast, keep it uncertain rather than inventing a separation. Review objects near the image edge carefully; cropped objects are excluded from the accepted complete measurement table.

Each saved revision contains:

- `reviewed_labels.npz`: edited region identities.
- `reviewed_regions.csv`: measurements and statuses for every current region.
- `accepted_complete_regions.csv`: only Correct regions that do not touch the crop border.
- `review.json`: input identity, pixel calibration, action reasons, polygon vertices, code fingerprints, statuses and counts.

The review folder also retains `automatic_labels.npz` and `automatic_regions.csv`. Resuming opens the latest saved review and checks source-image/label fingerprints. Save versions during work; closing the window saves recorded session actions. In-progress unfinished polygons are not applied. The accepted count describes the accepted complete subset, not a proven total number of particles. Border exclusions, unresolved objects and missing-particle checks must accompany any count you report.

Testing on independent specimens and representative fields is still necessary to establish broader reliability. This tool supplies the review mechanism; it cannot perform an independent human validation on your behalf.

## Second concept: length depends on its definition

An area-equivalent diameter answers: "What circle has this particle's area?" It does not answer: "How long is this rod?" We now save three explicitly named shape dimensions and an aspect ratio, following the [scikit-image definitions](https://scikit-image.org/docs/0.25.x/api/skimage.measure.html#skimage.measure.regionprops).

| Measurement | Scientific meaning | Important limit |
|---|---|---|
| `feret_max_px` | Largest separation between points on the convex outline contour | Maximum 2D outline span; not necessarily centreline length, especially for curved rods |
| `ellipse_major_px` | Long axis of the ellipse with the region's second moments | Shape summary, not endpoints. It can extend beyond the actual rod. |
| `ellipse_minor_px` | Short axis of the same ellipse | An effective transverse dimension, not a direct local-width measurement |
| `ellipse_aspect_ratio` | Major axis divided by minor axis | Describes elongation; becomes undefined if the minor axis is zero |

These describe a **2D projection**, not the particle's full 3D geometry. Segmentation errors affect every dimension. Use one definition consistently when comparing samples or papers. Pixels become nanometres only when that image's calibration is verified; these rod images currently remain in pixels. The `_nm` columns are left empty rather than assigning an assumed scale.

For particle 32:

| Dimension | Automatic outline | Published manual outline |
|---|---:|---:|
| Maximum Feret span | 523.96 px | 529.09 px |
| Ellipse major axis | 579.31 px | 581.57 px |
| Ellipse minor axis | 224.78 px | 225.37 px |
| Ellipse aspect ratio | 2.577 | 2.580 |

The red/blue lines in the review window are the ellipse axes. A separate `rod_dimensions.png` figure includes the orange maximum Feret span. The ellipse being longer than the Feret span is not a calculation error: these are different definitions. For a uniform rectangular rod, the moment-equivalent ellipse's major axis can exceed its end-to-end extent.

### Important measurement lines

The reusable code is in `microscopy/measurements.py`:

```python
major = float(region.axis_major_length)
minor = float(region.axis_minor_length)
feret = float(region.feret_diameter_max)
aspect = major / minor if minor > 0 else None
```

`region` contains one labelled object's pixels. The first two lines obtain its moment-ellipse axes; the third obtains its maximum convex-outline span. `float` converts the numerical scalar into a plain Python number for portable JSON output. The final line avoids dividing by zero: `None` means undefined, not zero elongation.

The helper also multiplies each length by `nm_per_pixel` when calibration exists. Length scales linearly; area would scale with its square. Aspect ratio has no units and does not change under uniform scaling.

### Run the measurement comparison

```powershell
.\.venv\Scripts\python.exe measure_rods.py
```

This creates a timestamped `rod_measurements` folder beneath the selected image's existing analysis results, containing automatic measurements, manual-reference comparisons, a summary and a dimensions figure. It compares only the original run's eligible, complete, one-to-one matches. Future `analyse.py` runs also include these shape dimensions in their normal `regions.csv` export.

Our current development image has 15 eligible reference pairs, with mean absolute Feret-span error 0.81%. The fresh image has six such pairs, with 1.22% mean absolute error. These are errors against the supplied manual polygons on restricted subsets; they do not establish accuracy for all particles. No segmentation parameters were retuned for this measurement extension.

## Small experiment

On the development image, find one uncertain boundary. Save a review version, then redraw that boundary slightly inward, save another version and compare the CSVs. Predict first: will area decrease? Will maximum Feret span necessarily decrease if you changed only the sides and kept the endpoints? Will ellipse aspect ratio change? Use Undo afterward and save the restored version. Record the experimental reason; do not treat the deliberately changed boundary as a validated correction.
