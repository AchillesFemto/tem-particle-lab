# Measure particles in your own TIFF

This workflow accepts your TIFF directly. No manual reference mask, polygon annotations or public example dataset is required. It produces automatic measurements and a boundary preview; it does not claim that those predictions are correct without review.

## Start with the file chooser

Install the project's current dependencies, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe analyse_own_image.py
```

Choose a `.tif` or `.tiff`. The window lets you select a page/channel, crop, threshold, contrast polarity, particle-separation method, minimum area and optional calibration. It shows the original selected plane, threshold foreground and numbered region outlines. The installed `imagecodecs` dependency handles common compressed TIFFs, including the tested LZW example. This is a 2D-plane workflow, not full 3D segmentation or automatic series/pyramid interpretation.

You can also open a particular image interactively:

```powershell
.\.venv\Scripts\python.exe analyse_own_image.py --image "my_sample.tif" --gui
```

## One concept first: select the numerical plane you intend to measure

A TIFF can contain several pages and samples/channels. A page is not necessarily a time point or a single scientific acquisition: inspect its relationship to your instrument's export. Page and channel indices start at zero. Use this command to list page/series shapes, axes and types:

```powershell
.\.venv\Scripts\python.exe analyse_own_image.py --image "my_sample.tif" --inspect
```

The command-line analysis requires an explicit `--page` when a file contains multiple pages. The window displays the selected page index and lets you change it before exporting. Distinct RGB planes are not silently averaged: select a channel explicitly. Identical RGB planes can be reduced to their first plane without changing any values. Alpha is transparency, not a particle-intensity channel. Grayscale uint8, uint16 and finite real-valued planes are supported; non-finite data and a 3D volume stored inside one page require a separate handling strategy. No maximum-intensity projection is performed.

The reader uses [tifffile](https://github.com/cgohlke/tifffile) to inspect page axes and return a numerical array. Native values are preserved: a 16-bit image is not converted to 8-bit merely for convenient thresholding. Display brightness maps the selected range to a grayscale display; it does not change the underlying array.

## Choose a crop and calibration

Crop syntax is `r0 r1 c0 c1`: first/stop row and first/stop column, with stop endpoints excluded. Leave it blank to use the full selected plane. Exclude scale bars, text, borders and unrelated image content. A crop also defines your sampling region; choosing only easy objects can bias a size distribution.

Leave nm/pixel blank if calibration is unknown. Measurements remain in pixels and physical-unit columns stay empty. If a verified 100 nm scale bar spans 500 pixels, the isotropic scale is `100 / 500 = 0.2 nm/pixel`. Enter 0.2 only if that calibration applies to this exact image/export. One scalar assumes equal X/Y pixel size; anisotropic pixels need a different measurement workflow. The software records your supplied scale but does not independently certify it or infer it from microscope magnification.

## What the processing solves

- **Thresholding** separates candidate particle foreground from background using intensity. Dark mode selects `image < threshold`; bright mode selects `image > threshold`. The GUI midpoint is only a starting guess. Thresholds use native units, so 140 from an 8-bit example is not a transferable setting for a 16-bit image.
- **Connected components** group adjacent foreground pixels into proposed objects using eight-neighbour connectivity. This is the simplest default, appropriate when particles are separated. Touching particles can remain merged; one object with disconnected contrast can be split into several components.
- **Watershed** attempts to separate touching foreground around distance-map seeds. It uses the existing shallow-peak grouping revision. Seed window, minimum distance, seed separation and prominence control this proposal. The settings are exploratory for your image. Thin and border regions may lack seeds; the tool reports seedless foreground rather than counting it as valid background.
- **Minimum area** excludes whole predicted regions below the selected pixel count. It can remove small noise regions, but can also remove real small particles and bias the distribution. Removed region/pixel counts are recorded separately from seedless foreground.

After changing controls, click **Update segmentation preview**. Inspect the numbered boundaries. A convincing-looking figure is not sufficient validation, especially for touching objects, aggregates or strong background variation.

## Export and review

Click **Export measurements + report**. A new ignored `results/<run>/` folder contains:

| File | Purpose |
|---|---|
| `report.html` | Local visual report, caveats and links to measurements |
| `own_image/regions.csv` | Each predicted region's area, equivalent diameter, eccentricity, maximum Feret span, ellipse axes, aspect ratio and crop-border flag |
| `own_image/arrays.npz` | Selected native-intensity crop, threshold mask and labels |
| `own_image/summary.json` | Input identity, page/channel selection, calibration declaration, counts, exclusions and absence of reference validation |
| `config_snapshot.json`, `run_manifest.json` | Recorded settings, source identity and workflow provenance |

`diameter_px` is the **area-equivalent diameter**, not a literal width for an irregular particle. `diameter_nm` is populated only with a supplied scale. Ellipse axes summarize shape and can extend beyond a particle's outline. All dimensions describe a 2D projection.

All exported automatic regions start Pending. Click **Review exported particles** to open the existing versioned review tool, or run the exact review command printed in the console. Human corrections and accepted complete measurements remain separate from the automatic output. Source TIFFs are not uploaded by this workflow; local run folders and review records are ignored by Git. Keep your own raw TIFF outside the repository, or in ignored `data/private/`, to avoid accidentally staging it yourself.

An empty overlap table is saved only for compatibility with the existing run selector; it contains no invented annotations or agreement scores. Reference-error metrics are unavailable without independent annotations. The `measure_rods.py` command also recognises these runs and points to their already-exported diameter/shape measurements rather than demanding a reference file.

## Noninteractive example

Choose the values based on your image; these are illustrative settings, not a universal protocol:

```powershell
.\.venv\Scripts\python.exe analyse_own_image.py --image "my_sample.tif" --page 0 --threshold 30000 --polarity dark --method connected --min-area 20 --nm-per-pixel 0.2
```

For a page with distinct channels, add `--channel 1`. For a crop, add `--crop 50 750 50 950` only if those bounds fit your selected plane. Omit `--nm-per-pixel` when unknown. Use `--method watershed --window-size 11 --min-peak-height 2 --min-seed-separation 5 --prominence 0.25` to try seeded separation after reviewing its assumptions.

## Important Python lines

The implementation is in `microscopy/user_images.py`:

```python
array = source.asarray()
candidate = plane < threshold
labels, _ = ndimage.label(candidate, np.ones((3, 3), bool))
rows = measure_labels(labels, nm_per_pixel)
```

The first line decodes the chosen TIFF page into its original numerical type. The second creates a Boolean foreground mask without overwriting intensities (bright mode reverses the comparison). The third identifies connected proposals: each positive label identifies one region and zero is background. The final line measures those labelled outlines and conditionally converts lengths to physical units. No annotation file is needed for these operations; independent annotations serve a different purpose, validation.

## Small experiment

Use the same crop and connected mode. Save one run, then increase only the threshold for dark foreground and save a second run. Predict: will selected foreground grow or shrink? Must the particle count increase, or can growing regions merge? Will the original TIFF values change? Compare the masks and CSVs before interpreting a change in diameter.
