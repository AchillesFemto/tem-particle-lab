# Lesson 24: separate and measure particles

**Update:** the script now suppresses duplicate nearby seeds. Earlier numerical examples below are the preserved baseline; the correction section at the end gives current results.

This is the first of our five larger lessons. Work through its three sections in order: watershed separation, scale-bar calibration, then size and shape measurements. The aim is to understand the measurements and their limitations, not simply produce a particle-size number.

## Run and outputs

From PowerShell in the microscopy-analysis project folder:

```powershell
.\.venv\Scripts\python.exe lesson_24.py
```

Scikit-image 0.25.2 has been installed in the existing environment and added to requirements. For a fresh environment, install the requirements first:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The script prints measurements, saves `lesson_24.png`, and creates `lesson_24_results/` containing:

- `regions.csv`: all labelled-region measurements and status flags.
- `parameters.json`: calibration assumptions, crop, algorithm settings and coverage diagnostics.
- `segmentation.npz`: NumPy arrays for the mask, seeds, labels and connected components, reusable in Lesson 25.

Rerunning replaces these generated outputs. Input images remain unchanged. The outputs are ignored by Git; code, requirements and this guide remain reusable.

## Section A: separate touching foreground with watershed

### The scientific problem

A threshold can join several neighboring particles into one connected region. Connected-component counting then counts the cluster as one object, and its area combines several particles. We need a way to propose a division inside that cluster.

Watershed grows labelled regions from starting markers on a numerical landscape. Think of water filling valleys from several sources: each source owns a growing basin, and the boundaries occur where growing regions meet. This is a useful geometric model, not a physical theory of particle contact.

The distance map is high inside the selected foreground. We negate it so high interiors become low valleys. The Lesson 23 seeds identify proposed starting positions. The foreground mask restricts where growth is allowed.

```python
markers = np.zeros(mask.shape, dtype=np.int32)
for seed_id, (row, column) in enumerate(seeds, start=1):
    markers[row, column] = seed_id
labels = watershed(-distance, markers=markers, mask=mask,
                   connectivity=connectivity, watershed_line=False)
```

`np.zeros` creates an integer array initially containing background label zero. `enumerate(..., start=1)` gives each seed its own positive ID, starting at one. `(row, column)` unpacks each coordinate pair. Assignment writes that ID at the corresponding pixel.

`-distance` is the flooding landscape, not a negative intensity image. `markers` specifies sources; `mask` restricts growth to selected foreground. `connectivity` includes diagonal neighbors, matching our connected-component analysis. `watershed_line=False` assigns adjacent labelled regions without deliberately removing a dividing line of pixels.

The output is an integer label array. Zero means unassigned/background; positive integers identify algorithmic regions. Labels are identifiers, not intensities or size rankings.

### Check coverage and separation

The starting run gives:

| Diagnostic | Result |
| --- | ---: |
| Connected foreground components before watershed | 20 |
| Seeds | 16 |
| Labelled watershed regions | 16 |
| Components with no seed | 11 |
| Foreground pixels left unassigned | 23,434 |
| Labelled regions whose parent component touches the crop border | 7 |

Only nine of the 20 original components have seeds; those nine components are partitioned into 16 regions. Thus, 20 before and 16 after does not mean watershed simply reduced the number of particles. Some components were split; others received no label at all.

Components without a seed cannot be reached across background, so they remain zero in the watershed output. The script explicitly saves and reports this omission. Do not count that unassigned foreground as proven physical background.

Inspect the lower-left panel of the figure. Regions 12 and 13 divide the interior near the two closely spaced seeds from Lesson 23. This demonstrates possible excessive splitting. Region 16 spans a cluster connected to the bottom crop boundary, demonstrating that a single seed can also leave multiple particles merged. Seed quality matters: neither watershed nor a plausible colour map proves particle identity.

Colours can repeat between IDs. Read the label numbers rather than interpreting equal colours as guaranteed equal labels.

## Section B: convert pixels into physical units

### Establish the calibration basis

The unchanged source PNG includes a bar labelled 100 nm. Visual inspection and several rows through its interior show a white bar occupying columns 1424 through 2288 inclusive: **865 pixels wide**. In code, the exclusive-stop slice is `[1424:2289]`, at source row 2225.

This is an exported-bar estimate, assuming the label is correct, the bar and specimen share the same pixel scaling, and horizontal/vertical pixel spacing is equal. It is not an independent instrument calibration. The script checks the white run and its endpoints to detect an unexpected source change; that check cannot verify the microscope's calibration.

We use the bar's raster width convention. The centre-to-centre separation of its outermost pixel centres is 864 pixels; endpoint conventions and edge uncertainty are small but real. Record the convention rather than imply unlimited precision. Nonuniform resizing would invalidate using a horizontal bar for vertical lengths and areas without additional calibration.

```python
nm_per_pixel = scale_bar_nm / scale_bar_pixels
```

This gives `100 / 865`, approximately **0.115607 nm per pixel**.

For isotropic pixels:

```text
length_nm = length_px × nm_per_pixel
area_nm²  = area_px × nm_per_pixel²
```

Length needs one scale factor. Area needs two because it spans two dimensions. A 10 by 10 pixel square has 100 pixels of area, and each pixel occupies `(nm_per_pixel)²` square nanometres. Do not multiply an area by the length scale only.

Changing calibration changes reported physical dimensions without changing segmentation. A 1% scale error produces approximately a 1% length error and a 2% area error. We have not quantified a full uncertainty budget in this lesson.

## Section C: measure each proposed region

```python
for region in regionprops(labels):
    area_nm2 = region.area * nm_per_pixel ** 2
    diameter_nm = region.equivalent_diameter_area * nm_per_pixel
```

`regionprops` computes properties separately for each positive label. `region.area` counts its pixels because we have not supplied physical spacing. `** 2` means square the scale factor. The equivalent diameter is the diameter of a circle with the same projected area:

```text
equivalent diameter = sqrt(4 × area / pi)
```

It describes area as a length; it does not establish that the object is circular or spherical. These are projected two-dimensional TEM regions, not three-dimensional particle volumes.

The table also includes major/minor axis lengths of a moment-based equivalent ellipse, eccentricity, and the unweighted area centroid. The ellipse captures the region's spatial spread; its axes are not automatically the longest and shortest observed chords. Eccentricity is dimensionless: zero for the equivalent circle, increasing toward one for elongated ellipses. It is not a direct crystallographic shape identification.

For example, label 1 has approximately 119.34 nm² area, 12.33 nm equivalent diameter, and eccentricity 0.214 at the starting settings. These are measurements of one algorithmic region, pending particle-level validation.

### Treat crop boundaries conservatively

We flag any region whose original connected foreground component touches the crop border. This is stricter than testing only the final watershed label: a label apparently inside the crop can belong to an incomplete cluster whose partition was influenced by missing material outside the crop.

Flagged rows remain in the CSV for inspection, with status `border_parent_excluded`; they are excluded from interpretation as complete-particle measurements. Other rows have status `unvalidated_candidate`, not "valid particle". No validated population mean or distribution is calculated.

A border flag can also exclude a complete particle connected to an incomplete neighbor. This conservative rule can bias later samples, especially toward small or isolated particles. A larger field of view and a justified sampling strategy are needed for population statistics.

## Important code details

| Code | Purpose |
| --- | --- |
| `import csv`, `import json` | Use Python's standard library to save a tabular CSV and structured parameter record. |
| Path, NumPy, Matplotlib, Pillow and SciPy imports | Provide paths, arrays, plotting, PNG reading and connected components. |
| `label2rgb`, `regionprops`, `watershed` | Supply labelled-region display, measurement and separation from scikit-image. |
| Imports from Lessons 22 and 23 | Reuse distance and seed functions without running those lessons. |
| `def separate_foreground(...)` | Defines reusable watershed logic and returns both labels and markers. |
| Shape/dtype and seed checks | Reject incompatible arrays, absent seeds, or seeds outside selected foreground. |
| `raise ValueError(...)` | Stops with an explanation instead of proceeding with an invalid assumption. |
| `np.int32` | Stores integer marker IDs; they are not Boolean selections. |
| `np.ones((3, 3), dtype=bool)` | Defines eight-neighbor connectivity, including diagonal contacts. |
| `return labels, markers` | Returns two arrays that the caller unpacks. |
| `def main()` and parameter assignments | Group execution and set the threshold, seed window, height and calibration values. |
| `Path(__file__).resolve().parent` | Finds the project folder from the script location. |
| `with Image.open(...)`, `np.array(source)` | Read original pixel values into NumPy and close the file. |
| Image ndim/dtype and scale-bar checks | Verify the expected input format and inspected bar run, without proving calibration accuracy. |
| `image[300:1100, 300:1100]` | Keeps the established crop, excluding the scale bar from segmentation. |
| `candidate = roi < threshold` | Selects dark pixels strictly below the cutoff; the scientific assumption remains approximate. |
| Distance and seed function calls | Describe foreground geometry and propose growth sources. |
| `ndimage.label(candidate, structure=structure)` | Labels all original foreground components for coverage and border diagnostics. |
| `np.unique(components[markers > 0])` | Finds which original components have at least one seed. |
| `np.arange(1, component_count + 1)` | Creates all positive component IDs. |
| `np.setdiff1d(..., seeded_components)` | Finds IDs with no seed. |
| `candidate & (labels == 0)` | Selects original foreground that watershed left unassigned. |
| `np.concatenate(...)`, then `np.unique` | Combine IDs on all four crop edges and remove repetitions. |
| `border_ids[border_ids > 0]` | Removes background ID zero from that list. |
| `fields`, `rows = []` | Define CSV column names and initialize the list of row dictionaries. |
| `region.coords[0]` | Gets one labelled pixel to determine its original parent component. All pixels of this watershed region lie within that component. |
| `int(...)`, `bool(...)` | Convert values to standard integer and Boolean representations for output. |
| `parent in border_ids` | Tests whether the original component touches the crop edge. |
| `rows.append({...})` | Adds one dictionary of measurements and flags per region. |
| Axis-length properties times `nm_per_pixel` | Convert equivalent-ellipse lengths from pixels to nanometres. |
| `region.centroid[0] + 300`, `region.centroid[1] + 300` | Convert crop centroid row/column coordinates to full-image pixel coordinates. These are area centroids, not seed locations. |
| Conditional status expression | Records whether the parent is border affected or remains an unvalidated interior candidate. |
| `output.mkdir(exist_ok=True)` | Creates the results folder if needed. |
| `open(..., "w", newline="", encoding="utf-8")` | Opens the CSV for replacement, handling text encoding and Windows CSV newlines. |
| `csv.DictWriter`, `writeheader`, `writerows` | Write named columns followed by all measurement rows. |
| `np.savez_compressed(...)` | Saves named arrays in a compressed NumPy archive for reuse. |
| `metadata = {...}`, `json.dumps(..., indent=2)` | Assemble and format a readable parameter/diagnostic record. |
| `tolist()` | Converts a NumPy array of IDs into a JSON-compatible list. |
| `write_text(..., encoding="utf-8")` | Saves the metadata record. |
| `sum(...)` on border flags | Counts how many output rows carry the flag. |
| `print`, numeric field widths, `:.2f` and `:.3f` | Display aligned summaries, rounded for reading without changing saved numeric values. |
| `plt.subplots(2, 2, ..., layout="constrained")` | Creates four labelled panels. |
| `imshow(..., interpolation="nearest")` | Displays arrays without smoothing displayed pixels. |
| `scatter(seeds[:, 1], seeds[:, 0], ...)` | Plots columns horizontally and rows vertically as hollow seed rings. |
| `label2rgb(..., bg_label=0)` | Converts identifiers to display colours with zero shown black. Colour is not a measurement. |
| `ax.text(column, row, str(region.label), ...)` | Prints each ID near its area centroid for correspondence with CSV rows. |
| Titles and axis labels | Distinguish original intensities, connected components, watershed IDs and calibration. |
| Calibration `extent=(1380,2320,2362,2180)` | Labels the displayed scale-bar crop using full-source pixel coordinates and downward-increasing rows. |
| `fig.savefig(..., dpi=150)`, `plt.show()` | Save the comparison figure and request a window. |
| `if __name__ == "__main__": main()` | Runs the lesson directly while keeping its function importable. |

## Interpretation and scientific limits

Inspect geometry against the original TEM image. Multiple seeds can split one particle; a missing seed can leave a particle unassigned or merge several particles in a seeded cluster. Watershed partitions the threshold foreground but cannot recover pixels outside that foreground, and its dividing boundaries need not match true interfaces.

The region measurements depend on threshold, seeds, connectivity, crop and calibration. A reliable calculation can still describe an incorrect region. We therefore keep the settings, labels, omissions and status flags together. Lesson 25 will compare individual detections with the supplied instance annotations and investigate misses, merges and splits.

Do not use this one crop to claim a representative particle-size distribution. The source is a published PNG with a rendered calibration bar. Projected size, uncertain boundaries, sampling bias and calibration assumptions must accompany any later scientific result.

## Your one experiment

Change only `threshold = 140` to `threshold = 160`. Keep seed settings and calibration fixed. Before running, predict:

1. Will the initial foreground selection grow or shrink?
2. Will the nm-per-pixel scale change?
3. Must the equivalent diameter of every final labelled region increase?

For the third question, consider that recomputing the distance map and seeds can change the partitions, omissions and number of regions. Label 12 in one run need not represent the same physical object as label 12 in another. Compare the figure and diagnostics before comparing table rows. Save the starting outputs elsewhere if you want to retain both runs; rerunning overwrites generated results.

References: scikit-image 0.25.2 [watershed](https://scikit-image.org/docs/0.25.x/api/skimage.segmentation.html#skimage.segmentation.watershed) and [regionprops](https://scikit-image.org/docs/0.25.x/api/skimage.measure.html#skimage.measure.regionprops). Source attribution: [TEM sample README](data/public_tem/README.md).


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
