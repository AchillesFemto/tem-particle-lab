# Five additions for users' own images

These additions extend `analyse_own_image.py` without changing the raw TIFF, inventing reference annotations or introducing machine learning. Each operation has a separate scientific purpose. Defaults leave preprocessing off. New reports record the settings, input/code hashes and package versions.

## 1. Noise reduction and background correction

**Problem:** grainy intensity fluctuations can fragment a particle, while uneven brightness can make a single threshold select different structures in different regions.

The window now has Gaussian sigma and background half-window controls. Change them, then click Update segmentation preview. The four panels show original pixels, the processed working image, threshold foreground and predicted outlines. Scroll the left controls if necessary. Exported `preprocessing.png` additionally shows estimated background and colour bars; panel display ranges can differ.

```python
working = image.astype(float, copy=True)
working = ndimage.gaussian_filter(working, sigma, mode="reflect")
background = ndimage.grey_closing(working, size=2 * radius + 1, mode="reflect")
working = working - background
```

The first line creates a floating-point working copy so smoothing and subtraction do not quantize values or wrap unsigned integers. The second suppresses fine fluctuations using a [Gaussian filter](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html); sigma describes its width in pixels. It also blurs boundaries and may bias dimensions.

For dark particles, [grayscale closing](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.grey_closing.html) suppresses dark depressions to estimate background. For bright particles, the code instead uses [grayscale opening](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.grey_opening.html) to suppress bright features. The square window is `2*radius+1` pixels across; choose it larger than relevant particle widths. Dense, large or uneven objects can contaminate the estimate. Reflection at crop boundaries is an assumption, not recovered outside-image information.

Background subtraction changes the threshold's numerical meaning: dark features often have negative corrected intensity, while bright features have positive corrected intensity. The GUI updates its threshold range and uses a midpoint only if the previous value is outside the new range. Inspect and choose the value; this is not automatic optimisation. Original native pixels remain stored as `image` in the NPZ; processed values and estimated background are saved separately.

Example for a suitable dark-feature image, with illustrative settings:

```powershell
.\.venv\Scripts\python.exe analyse_own_image.py --image "sample.tif" --threshold -500 --gaussian-sigma 1 --background-radius 30
```

**Experiment:** double sigma while keeping crop, background window and threshold fixed. Predict whether small details will disappear and whether particle area must stay the same. Compare boundaries before choosing either result.

## 2. Diameter distributions and descriptive summaries

Every user-image export now includes `distributions.png` and `distribution_summary.json`. They show area-equivalent diameter, maximum Feret span and ellipse aspect ratio, with count, mean, median, sample standard deviation, quartiles and range.

Automatic summaries exclude regions touching the crop edge and are labelled **complete automatic predictions; not validated**. Each saved human review produces its own distributions using only Correct, complete regions, recording border and review exclusions separately. Those outputs do not replace the automatic distributions. A small reviewed subset may be biased toward easier objects.

Histogram bins change display grouping, not the underlying measurements. Sample SD is undefined for one observation and recorded as null; an empty cohort gets null statistics and a clear empty plot. No experimental confidence interval is inferred. Individual particles from one field are not automatically independent experimental replicates.

**Experiment:** compare 8 and 20 histogram bins for the same measurements. Predict whether the median changes. It should not: binning affects the visual summary, not the numerical values.

## 3. Manual endpoint diameter/length checks

After export, click Manual endpoint measurements, or run:

```powershell
.\.venv\Scripts\python.exe manual_lengths.py --run results/YOUR_RUN --dataset own_image
```

Automatic outlines are hidden. Click two endpoints on the same visible particle, choose diameter, length or width, optionally enter its label and a note, then Record span. Use the toolbar to zoom before clicking. Save periodically. Each save creates a separate `manual_lengths/<revision>/` folder with CSV measurements and provenance. Closing saves recorded spans; an unfinished pair is not recorded.

```python
span_px = np.linalg.norm(point_2 - point_1)
span_nm = span_px * nm_per_pixel
```

The first line calculates the Euclidean straight-line separation between the two image-coordinate points. The second applies calibration only when supplied. Crop-local and full-plane endpoint coordinates are saved, with source/page/channel identity and the label-map fingerprint. Associated automatic diameter/Feret/ellipse values are saved for comparison when a label is supplied.

A hand-selected caliper span is not automatically the same quantity as area-equivalent diameter or ellipse length. The tool therefore does not label their difference an accuracy error. Endpoint choices have uncertainty and can be biased; hiding outlines does not establish independent ground truth. Curved centreline length, 3D size and instrument calibration are not inferred.

**Experiment:** repeat an endpoint measurement three times without looking at earlier endpoints. Predict how shifting one endpoint by one pixel affects the span; compare the repeated values rather than assuming click precision is absolute physical accuracy.

## 4. Batch analysis of your TIFFs

Copy `examples/own_images_batch.example.json` and replace its placeholder paths and thresholds. Relative paths resolve from the manifest file's directory; absolute paths also work. These private sample TIFFs are not supplied. Use a native/corrected threshold appropriate to each image, especially when storage type or preprocessing differs.

```powershell
.\.venv\Scripts\python.exe batch_own_images.py --manifest examples/own_images_batch.example.json
```

Shared defaults can describe a justified common protocol. Each image can override page, channel, crop, threshold, polarity, separation, preprocessing, filtering and reference-evaluation settings. Calibration is explicitly per image; setting `nm_per_pixel` in defaults is rejected. Unknown calibration remains null. To add references, give an image a `reference` TIFF path.

The batch runs images sequentially to limit memory demand. Every image has a separate full analysis/report under `results/batch_<id>/images/<image_id>/...`. The batch HTML/CSV/JSON report records successes and failures, units, complete-prediction counts and per-image medians. A failed image does not erase successful outputs; the command returns a failure exit code after writing its summary. Image reports include the correct nested review command.

The batch does not pool particles or calculate replicate-level significance. Independent specimen identity, field sampling and experimental grouping must come from the experiment. Automatic selection in the standalone review tools scans top-level runs; use the exact nested run path for a batch image.

**Experiment:** change calibration for one image only. Predict whether its pixel diameter changes, whether its nm diameter changes, and whether another image's measurements change.

## 5. Optional reference annotations for your images

Supply an **aligned, single-page instance-label TIFF** with the same full-plane shape as your selected source page/channel. Zero means background; each positive integer identifies one connected reference particle. A disconnected binary mask does not define particle identities and is rejected. Adjacent particles can have different IDs. Create references independently using an appropriate annotation editor; do not copy automatic predictions and then call them independent validation.

Choose the optional reference in the window before export, or run:

```powershell
.\.venv\Scripts\python.exe analyse_own_image.py --image "sample.tif" --threshold 140 --reference "reference_instances.tif"
```

The same crop is applied to source and reference. Image dimensions alone cannot verify registration, page identity, annotation correctness or exhaustive annotation coverage: inspect the exported reference preview. If only some particles are annotated, unlinked predictions cannot automatically be called false positives.

Validation records threshold IoU, possible split/merge relationships, references without links, predictions without links, and eligible size/shape errors. Link fraction (`--link-fraction`, default 0.1) compares overlap to the smaller object's area; accepted one-to-one matches also need IoU (`--min-match-iou`, default 0.5). These are explicit evaluation choices, not universal truth thresholds. No reference means no invented agreement scores.

Errors include only complete, unique accepted pairs. Reference particles cut by the crop or original image edge are excluded; predicted crop-edge particles are also excluded. Empty unions give undefined IoU, not a false perfect score. Files are `validation_summary.json`, `overlap_links.csv`, `reference_measurement_errors.csv` and `reference_preview.png`.

**Experiment:** raise only the match IoU cutoff from 0.5 to 0.8. Predict whether fewer pairs will qualify and whether the predicted boundaries change. Evaluation cutoffs affect acceptance, not segmentation.

## What remains an experimental responsibility

These additions do not guarantee a scientifically correct segmentation for every TEM image. Review acquisition/export, calibration, representativeness, contrast suitability, unresolved overlap and uncertainty. Especially in densely packed low-contrast images, a threshold plus watershed may still be inadequate. Preserve exclusions and failed cases rather than tuning until a desired diameter appears. Your raw images, local manifests and review outputs are not automatically uploaded.
