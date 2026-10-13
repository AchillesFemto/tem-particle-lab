# Lesson 26: how are particles organised?

This is the third of our five larger lessons. Work through four connected sections: particle positions, nearest neighbours, clustering interpretation, and pair correlations with boundary correction.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_26.py
```

No new packages are required. Run Lesson 24 first if its saved files are absent. This lesson reads the saved calibration, crop and watershed labels, prints spatial summaries, saves `lesson_26.png`, and creates `lesson_26_results/` with reference/prediction position tables, pair-correlation values and a reproducibility summary. Rerunning replaces these generated files.

## A. Define positions and the observation window

Particle organisation is described by positions. We use each annotation's unweighted projected-area centroid as an approximate centre. A centroid is the mean location of its foreground pixels, not necessarily the intensity minimum, distance-map seed or geometric centre of a complex shape.

We calculate centroids from the **full annotations before cropping**, then include a particle if its centroid falls within our observation window. A partially visible particle may have a valid centre inside the window because the surrounding full-source annotation is available. Keeping only fully contained particles would preferentially exclude large particles near edges and alter the spatial sample.

The full polygons are rasterized in small local bounding boxes to avoid allocating 190 full-size masks. These numerical boxes are a memory convenience, not a new specimen crop. The spatial observation window is still the established source slice `[300:1100, 300:1100]`.

```python
points = (full_centres[inside] - [c0, r0]) * scale
```

`inside` is a Boolean selector requiring x and y within the window. We subtract its origin and multiply by the Lesson 24 scale to obtain positions in nanometres relative to the window's top-left corner. Here positions are stored as `(x, y)`, or `(column, row)`, unlike NumPy image indexing `(row, column)`.

The window is approximately **92.49 by 92.49 nm**. It contains **19 manual centres**. The current watershed produces **15 region centroids**.

The plot shows manual centres as green rings and unvalidated watershed centroids as orange crosses. All watershed regions are displayed as a bias demonstration, including the merges/border-affected cases from Lesson 25. We do not treat them as a reliable particle population. Using only the eight eligible matches would also give an incomplete, selected point pattern.

## B. Nearest-neighbour distances

The nearest-neighbour distance is the distance from a centre to its closest other observed centre. It answers a local spacing question.

```python
distances, indices = cKDTree(points).query(points, k=2)
nearest = distances[:, 1]
```

`cKDTree` builds a spatial search structure. `query(points, k=2)` finds the two closest stored points for each query. Since we query the same positions stored in the tree, the first result is the point itself at distance zero. The second is its nearest other point. `indices[:, 1]` identifies that neighbour so we can draw connecting lines.

For two positions, Euclidean centre separation is:

```text
d = sqrt((x2 - x1)² + (y2 - y1)²)
```

The manual-centre within-window median is **14.67 nm**; the unvalidated detection median is **14.22 nm**. Similar summary values do not prove similar point patterns or correct detections. Counts, positions, omissions and merged centroids differ.

These are centre-to-centre distances, not particle-surface gaps. Calculating a physical gap would require reliable boundaries and a justified shape model, particularly for overlapping projected particles.

### Boundary uncertainty

A centre near the window edge may have a closer neighbour outside the observed window. Its within-window nearest distance is then an upper bound on the nearest distance in the larger pattern.

```python
edge_distance = np.minimum.reduce([x, width - x, y, height - y])
safe = nearest < edge_distance
```

The minimum gives distance to the closest rectangle edge. If the observed neighbour lies closer than that edge, no point outside the rectangle can be nearer. That nearest-neighbour result is boundary-safe **assuming the point pattern inside the window is complete**.

Only **10 of our 19 reference centres** meet this sufficient condition. Red centres in the diagram are boundary-uncertain; blue are safe. Red does not mean the reported neighbour is definitely wrong. We retain all values for the illustrative histogram and explicitly label it within-window. Averaging only blue points would select a different subset and is not a general unbiased correction.

Full annotations outside this window could be used as a guard region in an expanded analysis. Here we deliberately study what can be inferred from a defined window and expose its boundary uncertainty.

## C. Clustering requires a comparison model

A small spacing alone does not establish clustering: increasing particle density also reduces typical spacing. We therefore generate 200 point patterns with the same count and rectangular window, but independent uniform positions:

```python
rng = np.random.default_rng(26)
random_points = rng.uniform([0, 0], [width, height], size=(len(points), 2))
```

The fixed seed makes runs reproducible. Each simulation has 19 size-free points, not simulated TEM particles or synthetic images. We calculate the same within-window quantities so the simulated and observed summaries use the same window convention.

Across simulations, the median nearest distance has approximate 2.5th, 50th and 97.5th percentiles of **6.90, 10.86 and 15.10 nm**. Our observed 14.67 nm lies within that illustrative range. We do not claim significant clustering or absence of clustering from this single comparison.

Crucially, real particles occupy area. Their centres cannot generally approach as freely as size-free random points. A deficit of short separations can arise from finite particle size, even without collective ordering. Projection, annotation errors, varying density and substrate structure can also influence patterns.

## D. Pair correlations examine more than the nearest neighbour

Nearest-neighbour analysis retains one distance per centre. Pair correlation considers all distinct centre pairs and asks whether some separation ranges occur more or less often than a uniform independent-point baseline.

We estimate a radial, annulus-averaged `g(r)`, not a continuously smoothed curve:

- Around 1: approximately the baseline pair density at that separation.
- Above 1: more pairs at that separation than the baseline expectation.
- Below 1: fewer pairs at that separation.

These interpretations depend on a spatially homogeneous pattern and radial averaging. A peak near a typical contact spacing may indicate packing rather than clustering. Radial averaging also hides directional organisation.

```python
i, j = np.triu_indices(n, k=1)
delta = points[i] - points[j]
radii = np.linalg.norm(delta, axis=1)
```

`np.triu_indices` lists each unordered pair once, excluding self-pairs. For 19 points this gives 171 distinct pairs. Coordinate differences give displacement vectors, and their Euclidean norms give distances. Each pair is not an independent experimental replicate.

### Account for the rectangular boundary

There are fewer opportunities to observe some pair displacements near the window edge. Simply dividing a distance histogram by ring area would underestimate pair density. We apply a rectangular translation correction:

```python
overlap_area = (width - abs(dx)) * (height - abs(dy))
weights = window_area / overlap_area
```

The denominator is the overlap between the original window and a copy shifted by the pair's displacement. Less observable overlap gives a larger weight. This is a statistical adjustment, not reconstruction of missing particle positions.

For each annulus:

```text
annulus area = pi × (r_outer² - r_inner²)
g = 2 × window area × sum(pair weights)
    / (N × (N - 1) × annulus area)
```

The factor 2 accounts for using unordered pairs only once. `N(N-1)` uses the fixed-count independent-point normalization. Under independent uniform positions in a rectangle, the estimator's expectation is one over the analysed radius range. The implementation was checked using exact simple geometries and random patterns whose mean estimates were near one.

We limit separation to 40 nm, below half the shorter side, to avoid increasingly unstable large-displacement estimates. Correction does not eliminate finite-sample variation or bias from inhomogeneous density.

### Read our curve cautiously

The starting bins are 5 nm wide. There are no pairs below 10 nm, while the 10-15 and 15-20 nm bins have g values approximately **1.72 and 1.64**. These are observations of this annotated field. They do not establish a lattice, a quantum phase, or statistically significant clustering.

The gray band is the pointwise 2.5%-97.5% range from the independent uniform simulations. It is not a confidence interval for the material's true g(r), and it is not a simultaneous 95% significance envelope across all bins. The dashed line is the simulation median, which need not be exactly one in sparse bins; one is the baseline expectation, not every simulated outcome.

## Important code details

| Code | Explanation |
| --- | --- |
| csv/json/hashlib/Path imports | Save tables, structured settings, input fingerprints and portable paths. |
| NumPy, Matplotlib, Pillow imports | Supply arrays, plots and unchanged PNG reading. |
| cKDTree, polygon, regionprops | Supply neighbour search, annotation rasterization and area centroids. |
| annotation_centres(...) | Measures each full-source annotation before selecting the window. |
| np.asarray(...).reshape(-1,2) | Converts alternating polygon x/y values into vertex pairs. |
| np.concatenate(vertices) | Collects vertices for one annotation's bounds. |
| floor, ceil, astype(int), minimum/maximum | Build integer raster bounds, clipped to the full source image. |
| np.zeros(...,dtype=bool), polygon(...), mask[rr,cc]=True | Fill the local reference mask while preserving one annotation identity. |
| centroid + bounding-box origin | Return full-image x/y coordinates, reversing regionprops row/column order. |
| nearest_neighbours(...) and input checks | Require at least two finite positions in the defined window and return neighbour, edge and safety data. |
| np.minimum.reduce(...) | Takes the elementwise minimum of distances to four edges. |
| radial_pair_correlation(...) | Computes weighted pair histograms and normalized annulus averages. |
| Bin checks | Require increasing bins from zero, with a conservative maximum radius. |
| points[i] - points[j], norm(...,axis=1) | Calculate displacement vectors and one distance per pair. |
| np.abs(delta[:,0/1]) | Obtain horizontal/vertical displacement magnitudes for window overlap. |
| np.histogram(...,weights=weights) | Sum boundary-correction weights in each separation bin; an unweighted histogram separately records pair counts. |
| edges[1:], edges[:-1], **2 | Form corresponding outer/inner radii and squared lengths for ring areas. |
| save_rows and DictWriter | Write reproducible CSV tables with named columns. |
| main(), parameter assignments | Set bin width, radius range, simulation count and fixed random seed. |
| File-existence check | Explains that saved Lesson 24 segmentation is required. |
| json.loads and np.load(...,allow_pickle=False) | Load settings and numerical labels without pickled Python objects. |
| Saved crop and scale | Keep the same observation window and calibration across position sets. |
| Source/image_id checks and annotation filtering | Require annotations for the saved source image. |
| inside Boolean conditions | Include centres by position, not whether their whole polygon fits inside the window. |
| regionprops(labels) and centroid order reversal | Extract watershed region x/y positions; these remain unvalidated detections. |
| np.isclose, round and np.linspace | Require a bin width dividing 40 nm and build exact bin endpoints. |
| for _ in range(simulations) | Repeat random-pattern generation; the loop counter is not otherwise needed. |
| np.median, np.percentile(...,axis=0) | Summarize nearest distances and simulation distributions separately for each radial bin. |
| Lists of dictionaries | Store position, neighbour, boundary and pair statistics with explicit units. |
| neighbour indices and reference_ids[...] | Associate nearest positions with original annotation IDs. |
| JSON summary and SHA256 | Preserve assumptions, settings and the exact segmentation fingerprint. |
| print and rounding | Display results without rounding the underlying saved arrays. |
| imshow(...,extent=...) | Plot the TEM crop with window-relative nanometre axes. Pixel-display placement uses a raster extent convention, not new calibration. |
| scatter and hollow rings/crosses | Distinguish manual and detected positions. |
| np.where(safe,...), connecting-line loop | Colour boundary uncertainty and draw nearest-neighbour links. |
| set_xlim/set_ylim/set_aspect | Keep the physical rectangle and equal spatial scales; y increases downward like image rows. |
| Common histogram edges and histtype="step" | Compare within-window spacing counts on matching distance bins. |
| mid=(edges[:-1]+edges[1:])/2 | Place annulus averages at bin midpoints for display. |
| fill_between, plot and axhline | Show pointwise simulation ranges, median, observed g and baseline one. |
| Titles, legends and axis labels | Distinguish position sets, uncertainty, units and model interpretation. |
| fig.savefig, plt.show, main guard | Save the figure, request a window, and permit importing functions without running the lesson. |

## Scientific assumptions to retain

- These are projected two-dimensional area centroids from approximate annotations. They need not equal three-dimensional particle centres.
- Cropped watershed centroids can shift, and merges/misses distort counts and spacings. Manual annotations are the exploratory primary position set here, not proof of physical truth.
- The material's point density may vary across the image. A homogeneous uniform model can confuse density gradients with clustering.
- Radial averaging assumes direction is not central to the question. Directional order needs additional analysis.
- One field with 19 points gives sparse, correlated pair counts. Multiple representative fields and a physically justified null model are needed for strong conclusions.
- Scale-bar uncertainty propagates to all reported distances. Calibration rescaling alone does not change dimensionless pair-correlation values if bins and window are scaled consistently.

## Your one experiment

Change only `bin_width_nm = 5.0` to `bin_width_nm = 10.0`. Predict:

1. Will there be fewer or more radial bins between 0 and 40 nm?
2. Will the particle centres or nearest-neighbour distances change?
3. Will the broader bins preserve the same fine detail in g(r)?

Run and compare the curve and pair counts. Broader bins combine more pairs but reduce separation resolution. Peaks can change height or blend; changing a plotted peak through binning does not change the specimen. The simulation seed and point patterns stay the same.

References: [SciPy cKDTree.query](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.spatial.cKDTree.query.html) and the authors' [spatstat translation-edge-correction documentation](https://search.r-project.org/CRAN/refmans/spatstat.explore/html/edge.Trans.html). Source attribution: [TEM sample README](data/public_tem/README.md).
