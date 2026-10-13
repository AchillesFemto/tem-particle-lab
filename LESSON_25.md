# Lesson 25: validate individual particle regions

**Update:** the script now suppresses duplicate nearby seeds. Earlier numerical examples below are the preserved baseline; the correction section at the end gives current results.

This is the second of our five larger lessons. We move from comparing foreground pixels to comparing individual annotated particles and watershed regions. Work through three sections: reference identities, overlap relationships, and measurement differences.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_25.py
```

Run `lesson_24.py` first if its result files are absent. Lesson 25 reads the saved segmentation and its parameter record; it does not recompute or improve that segmentation. If you changed Lesson 24's threshold, this lesson assesses that changed result and reports its saved settings. No new packages are needed.

It saves `lesson_25.png` and the following in `lesson_25_results/`:

| File | Purpose |
| --- | --- |
| reference_diagnostics.csv | Completeness and number of linked predictions for each annotation |
| prediction_diagnostics.csv | Border flags and number of linked annotations for each predicted label |
| overlap_links.csv | Substantial-overlap relationships, IoU and match eligibility |
| matched_errors.csv | Size/shape differences for clear, complete eligible pairs only |
| linked_pair_comparisons.csv | Comparisons for every linked pair, including ambiguous splits/merges; these are not all valid particle matches |
| summary.json | Settings, diagnostics and input hashes for reproducibility |

Rerunning overwrites generated outputs, which are ignored by Git. It preserves Lesson 24's inputs.

## Section A: retain individual annotation identities

The published binary mask stores foreground and background only. Two touching white particles do not retain separate identities there. We therefore read the supplied instance polygons from `annotations_L1-1-D.json`.

Each annotation is rasterized independently onto our crop grid. We retain separate Boolean masks so overlapping annotations are not silently overwritten by one label image.

```python
xy = np.asarray(coordinates, dtype=float).reshape(-1, 2)
rr, cc = polygon(xy[:, 1] - r0, xy[:, 0] - c0, shape=mask.shape)
mask[rr, cc] = True
```

The source stores alternating x and y coordinates. `reshape(-1, 2)` groups them into coordinate pairs, with NumPy calculating the number of pairs. `polygon` needs rows and columns, so y goes first and x second. Subtracting the crop origin converts full-image coordinates to crop coordinates. The rasterization operation fills pixels inside each polygon; it does not segment the TEM intensities.

`shape=mask.shape` clips filled pixels to the observed crop. We retain any annotation with visible pixels, but flag it complete only if every vertex lies within the crop. An annotation cut by the crop can be used for coverage diagnostics, not complete-particle size comparisons.

The current crop has **23 visible annotations, of which 12 are fully inside it**. Reference display IDs 1-23 are short local IDs for plots; CSVs also retain the original source annotation IDs. They are distinct from predicted label IDs. Equal numeric IDs in the two panels do not imply a match.

### Check consistency rather than assuming identical references

The rasterized polygon union differs from the separately published binary mask at **3,452 crop pixels**. Some annotations also overlap: **654 pixels** belong to more than one reference instance. The provided representations and rasterization conventions need not produce identical boundaries. We record the differences without asserting an unverified cause.

Today's object comparisons consistently use these independently rasterized polygons. Scores are therefore not directly interchangeable with the earlier binary-mask metrics. Manual annotations are approximate references, not unquestionable physical truth.

## Section B: link objects by substantial overlap

We compare every reference instance with every positive watershed label. This avoids assuming that region numbers match or forcing an assignment when the geometry is ambiguous.

For each pair, calculate:

```text
intersection = pixels belonging to both objects
IoU = intersection / (reference area + predicted area - intersection)
overlap fraction = intersection / min(reference area, predicted area)
```

The overlap fraction detects fragments inside a larger object: a fragment can have low IoU with its full parent but still lie almost entirely inside it. Our exploratory link rule requires at least 10% overlap relative to the smaller object's area, with a nonzero intersection. This threshold is a teaching choice, not a universal scientific criterion. Small contacts and partial border fragments can create false links, so interpret them visually.

```python
links = (intersections > 0) & (overlap_fraction >= link_fraction)
ref_degree = links.sum(axis=1)
pred_degree = links.sum(axis=0)
```

`links` is a Boolean table: reference objects are rows, predicted objects are columns. `sum(axis=1)` counts predictions linked to each reference; `sum(axis=0)` counts references linked to each prediction.

| Relationship | Interpretation |
| --- | --- |
| Reference has no link | No substantial detection overlap; possible miss or inadequate overlap |
| Prediction has no link | No substantial annotation overlap; possible extra detection or annotation omission |
| Reference links to multiple predictions | Possible split |
| Prediction links to multiple references | Possible merge |
| One link in each direction | Candidate one-to-one correspondence |

Splits and merges can coexist in a complex cluster. Counts are diagnostic flags, not mutually exclusive categories or guaranteed true errors. A one-link relationship still needs an adequate IoU before it is accepted.

### Accept clear matches without forcing ambiguity away

```python
unique_pair = ref_degree[i] == 1 and pred_degree[j] == 1
accepted = unique_pair and iou[i, j] >= min_match_iou
eligible = accepted and reference_complete and not prediction_border_affected
```

In the script, these conditions use the corresponding record fields. The default `min_match_iou` is 0.50. It is explicit and changeable, not claimed to be universally acceptable.

We do not force a split fragment or merged cluster into a unique assignment. Accepted matches include some border objects for correspondence diagnostics, but measurement-error summaries require a complete annotation and a prediction whose original parent component does not touch the crop border. This conservative rule follows Lesson 24.

### Starting diagnostics

For Lesson 24 at threshold 140:

| Diagnostic | Count |
| --- | ---: |
| Visible reference instances | 23 |
| Predicted regions | 16 |
| References with no substantial overlap | 6 |
| Complete references with no substantial overlap | 0 |
| References flagged as possible splits | 1 |
| Predictions flagged as possible merges | 2 |
| Predictions with no substantial overlap | 0 |
| Accepted unique matches, including border cases | 12 |
| Eligible complete pairs for measurement comparisons | 7 |

All six zero-link annotations are partial border particles. Zero fully visible zero-link annotations does not mean every fully visible particle was correctly separated: one is split, and ambiguous relationships remain. We deliberately avoid presenting these diagnostic counts as overall detection accuracy.

## Section C: measure consequences for size and shape

Measure both objects in a matched pair using the same `regionprops` definitions and Lesson 24 calibration:

```text
area error (%) = 100 × (predicted area / reference area - 1)
diameter error (%) = 100 × (predicted diameter / reference diameter - 1)
eccentricity difference = predicted eccentricity - reference eccentricity
```

Negative percentage error means the prediction is smaller than its reference. Positive means larger. Eccentricity difference is an absolute dimensionless difference, not a percentage; dividing by a near-zero circular-reference eccentricity would be misleading.

For the seven eligible pairs, equivalent diameters are approximately 0.36%-3.54% smaller than their respective annotated diameters. This describes the selected successful pairs, not all particles or overall method accuracy. There is no population uncertainty estimate from this small chosen crop.

Because predicted and reference lengths share the same calibration, their relative errors cancel that scale factor. That does not validate the absolute nanometre values or the source scale bar.

### What the split does

Reference display ID **15** links to predicted labels **12 and 13**. Relative to the full annotated object:

| Predicted fragment | Area difference | Equivalent-diameter difference |
| --- | ---: | ---: |
| 12 | -61.32% | -37.81% |
| 13 | -41.81% | -23.72% |

If both fragments were treated as particles, one reference particle would become two smaller measured objects. These linked-pair comparisons demonstrate the effect; they are excluded from the valid-match error summary.

Predicted label **16** links to references 18 and 19, and label **15** links to references 21 and 22. Those annotations include partial border cases. Their comparisons demonstrate ambiguity and crop effects; they must not be interpreted as calibrated complete-particle merge errors. Inspect the geometry in the figure.

A merged region often increases apparent size and elongation; a split often reduces size and creates artificial shapes. The direction is not universally guaranteed when boundary errors, omissions and partial objects occur together.

## Read the four panels

1. Top left: the TEM crop with manual polygon boundaries and reference display IDs.
2. Top right: the same crop with watershed boundaries and prediction IDs.
3. Bottom left: pairwise IoU table. One reference row with multiple bright cells suggests a split; one prediction column with multiple cells suggests a merge. The link rule also considers the smaller-area overlap fraction, not IoU alone.
4. Bottom right: equivalent diameters for the seven eligible pairs. Points below the diagonal have smaller predicted diameters. Misses, splits and merges are absent from this scatter and remain separately reported.

## Important code details

| Code | Explanation |
| --- | --- |
| csv/json/Path imports | Save readable tables, structured records and portable paths. |
| hashlib import | Records SHA256 fingerprints of the exact saved segmentation and annotation inputs. A hash identifies bytes, not scientific correctness. |
| NumPy, Matplotlib, Pillow imports | Supply arrays, plots and PNG reading. |
| polygon, regionprops imports | Rasterize manual outlines and measure labelled-region geometry. |
| reference_instances(...) | Builds a separate mask and record for each visible annotation. |
| np.zeros(..., dtype=bool) | Creates an initially empty crop-sized mask. |
| isinstance(..., list) check | Requires the polygon format present in this dataset rather than an encoded mask. |
| vertices.append and np.concatenate | Collect all polygon vertices for completeness checks; multiple polygons of one annotation are combined in its mask. |
| np.any(mask), np.all(...) | Check for any visible foreground and require all vertices to lie inside the crop for completeness. |
| overlap_diagnostics(...) | Compares all object pairs and returns IDs, intersections, IoU, fractions and link flags. |
| np.unique(labels[labels > 0]) | Lists positive prediction IDs, excluding unassigned/background zero. |
| np.count_nonzero | Counts mask pixels or intersections. |
| [:, None] and [None, :] | Expand area vectors along different axes so broadcasting forms every pair's union and smaller-area denominator. |
| np.divide(..., out=..., where=...) | Computes ratios where denominators are positive, leaving zero elsewhere instead of dividing by zero. |
| shape_measurements(...) | Computes area, equivalent diameter and eccentricity consistently for one mask. |
| mask.astype(np.uint8) | Makes a single-label image; all foreground pixels belong to the same instance, including any disconnected pieces. |
| regionprops(...)[0] | Retrieves that positive instance's properties. |
| scale ** 2, multiplication by scale | Convert pixel area and lengths to the shared physical units. |
| save_rows(...) and csv.DictWriter | Write dictionaries as named CSV columns, including a header when there are no eligible errors. |
| main(), min_match_iou, link_fraction | Define the run and two distinct evaluation thresholds. Only min_match_iou changes in the experiment. |
| File-existence check | Explains that Lesson 24 must be run if its segmentation is absent. |
| json.loads(...read_text(...)) | Load saved settings and polygon data. |
| np.load(..., allow_pickle=False) | Read named numerical arrays without permitting pickled Python objects. The with block closes the archive. |
| Crop and source consistency checks | Reject mismatched metadata, dimensions or image identifiers; these checks alone cannot prove correct alignment. |
| The image_id filter | Selects only annotations for the saved source image. |
| np.unique(np.concatenate(...)) | Collects parent-component IDs on the crop edges for border flags. |
| components[labels == pred_id][0] | Gets the predicted region's original connected-component ID. |
| reference_rows, prediction_rows | Store object-wise link counts and flags. |
| zip(*np.nonzero(links)) | Iterates through linked row/column index pairs; * unpacks the two coordinate arrays. |
| bool(...) and int(...) | Convert NumPy scalars to ordinary values for CSV/JSON output. |
| Dictionaries with **record or **measurement | Copy existing fields into a new output dictionary before adding details. |
| if eligible: errors.append(...) | Restricts the primary measurement comparison to clear complete pairs. |
| pair_errors.append(...) | Retains ambiguous pair comparisons separately with topology and eligibility flags. |
| np.stack(ref_masks).sum(axis=0) | Counts how many annotation masks cover each crop pixel, preserving annotation overlaps. |
| Polygon union vs published mask comparison | Records differing foreground pixels rather than silently assuming reference representations agree. |
| sum(...), np.count_nonzero(...) | Count statuses and diagnostic cases. |
| read_bytes and hashlib.sha256(...).hexdigest() | Fingerprint the exact segmentation archive and polygon JSON. |
| json.dumps(..., indent=2), write_text | Save a readable summary. |
| print(...) and numeric formatting | Report diagnostics and rounded comparisons in the terminal. |
| np.flatnonzero(...) + 1 | Convert flagged reference row indices into one-based display IDs. |
| Image.open and np.array(...)[r0:r1,c0:c1] | Load the same TEM crop for plotting. |
| plt.subplots(2,2,layout="constrained") | Creates the comparison figure with space for labels. |
| contour(mask, levels=[0.5]) | Draws foreground boundaries between Boolean zero and one. This is display, not additional segmentation. |
| np.nonzero(mask), coordinates.mean() | Locate area centroids for display ID text. |
| imshow(iou, vmin=0,vmax=1) | Displays pairwise scores on a fixed scale. |
| set_xticks/set_yticks | Label prediction columns and reference rows with their IDs. |
| colorbar | Explains the displayed IoU colour scale. |
| scatter(x,y) and plot(...,"k--") | Plot eligible diameter pairs and their equality line. No regression or uncertainty model is fitted. |
| if errors / else | Handles an empty eligible-match set explicitly. |
| Axis labels, titles, text and legend | Distinguish identities, units and selected comparisons. |
| fig.savefig, plt.show | Save the figure and request a window. |
| Main guard | Runs the lesson directly while keeping helper functions importable. |

## Scientific limits

This is an exploratory comparison on the same crop used to develop the method. It does not establish performance on independent specimens. Approximate polygon outlines and rasterization choices contribute reference uncertainty. Annotation overlap is preserved rather than forced into an exclusive partition.

The overlap-link and match thresholds are explicit teaching conventions. Flags depend on them. Border truncation can manufacture apparent misses or merges. Matching only successful interior pairs selects easier objects and can hide the largest failures; always report the missed/split/merge diagnostics alongside matched errors.

Splits, merges and missing objects distort later size distributions and particle-position statistics. Do not automatically proceed to clustering analysis using all 16 watershed centroids. We will examine suitable position choices and resulting biases in the next larger lesson.

## Your one experiment

Change only `min_match_iou = 0.50` to `min_match_iou = 0.75`. Predict:

1. Can the number of accepted unique matches increase, or can it only stay the same or decrease?
2. Will the saved watershed boundaries change?
3. Will the possible split/merge counts change when the separate link_fraction stays fixed?

Run and compare the summary. A higher acceptance threshold can change which pairs enter the error comparison, so an improved-looking error summary need not mean an improved segmentation. All previously accepted pairs may still pass, giving unchanged counts.

References: scikit-image [polygon rasterization](https://scikit-image.org/docs/0.25.x/api/skimage.draw.html#skimage.draw.polygon) and [regionprops](https://scikit-image.org/docs/0.25.x/api/skimage.measure.html#skimage.measure.regionprops). Source attribution: [TEM sample README](data/public_tem/README.md).


## Nearby-seed correction after visual inspection

Your observation that the old predicted regions 12 and 13 were one particle led to a seed correction. The starting-run examples above describe the preserved **before-correction** result. The script now uses the corrected seed rule below.

```python
raw_seeds = distance_peak_seeds(distance, window_size, min_height)
seeds = suppress_nearby_seeds(distance, raw_seeds, candidate, 10.0)
```

The first line keeps the original peak detector. The second suppresses very close seeds **within the same connected foreground component** before watershed. It does not manually paint over the split boundary.

The helper is in `lesson_23.py`. It processes higher-distance peaks first, retaining earlier candidates when heights tie. For each candidate it checks already retained seeds in the same component. If one is less than 10 pixels away, it rejects that candidate. Different connected components do not suppress one another. It then returns surviving coordinates in their original order.

Important new operations:

- `ndimage.label(mask, structure=...)` identifies which foreground component contains each seed.
- `distance[seeds[:, 0], seeds[:, 1]]` reads each seed's distance-map height.
- `np.argsort(-heights, kind="stable")` ranks heights from largest to smallest and preserves original order for ties.
- `np.linalg.norm(seeds[index] - seeds[previous])` calculates straight-line separation in pixels.
- `any(...)` checks whether at least one retained, same-component seed is too close.
- `kept.append(...)` retains a candidate only when that condition is false.
- `seeds[np.sort(kept)]` returns the retained coordinates in the original ordering.

Ten pixels is a conservative teaching parameter for removing the observed two-pixel duplicate. It is not an independently established particle-spacing threshold. A larger value can remove genuine distinct-particle seeds and cause merges. This correction was informed by this crop and remains parameter development, not independent validation.

### Corrected result at threshold 140

- Seeds/regions: **16 to 15**.
- Reference display ID 15 now corresponds to **one predicted region, new label 12**.
- Its area is **179.57 nm²**, equivalent diameter **15.12 nm**, and eccentricity **0.643**.
- Relative to its polygon annotation, area is **3.14% smaller**, diameter **1.58% smaller**, and eccentricity differs by approximately **-0.052**.
- Possible split references: **1 to 0**.
- Possible merges: **2**, unchanged. Their labels are now 14 and 15 because subsequent IDs shifted.
- Eligible complete error-comparison pairs: **7 to 8**.
- The 11 seedless components, 23,434 unassigned foreground pixels and seven border-parent flags remain unchanged.

Verification compared the arrays directly: the union of old labels 12 and 13 is exactly new label 12; all other regions retain exactly their original pixels, allowing for renumbering. A synthetic check also confirmed that nearby seeds in separate components are retained.

Before-correction arrays, tables and figures are preserved under the corresponding `*_before_seed_correction` names. Current normal output filenames refer to the corrected results. No other defects were removed by this change.
