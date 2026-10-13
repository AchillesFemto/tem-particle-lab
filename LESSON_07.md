# Lesson 7: thresholding and Boolean masks

## What problem does thresholding solve?

Sometimes we want to select pixels based on their intensity. A histogram counts intensity values but discards their positions. Thresholding applies an intensity rule at every location and keeps the resulting selection in the image's spatial layout.

Today we ask only: **which pixels in this ROI have a stored intensity below 80?** This is a dark-pixel selection. It is not yet a validated identification of particles, phases or background.

## Run

From PowerShell in your project folder:

```powershell
.\.venv\Scripts\python.exe lesson_07.py
```

No new packages are needed. The script reads your original TIFF, uses the same original ROI from Lessons 5 and 6, and saves `lesson_07.png`. Rerunning replaces this generated figure, not the original TIFF.

## The central operation

```python
threshold = 80
mask = gray < threshold
```

`threshold` names the chosen cutoff. The `<` comparison asks, at every pixel: is its value strictly less than 80? NumPy returns a new array of answers called `mask`.

| Original value | Test | Mask value |
| --- | --- | --- |
| 40 | 40 < 80 | True |
| 79 | 79 < 80 | True |
| 80 | 80 < 80 | False |
| 120 | 120 < 80 | False |

The value exactly equal to the threshold is excluded because we used `<`, not `<=`. We select lower values because our teaching question concerns darker pixels. An opposite question would need a different rule.

`mask` has shape `(200, 300)`, matching `gray`, but its dtype is `bool` (Boolean): each entry is either `True` or `False`. A mask is a map of selected locations, not a modified intensity image. The original `gray` remains uint8 with unchanged values.

## Why 80?

It is a deliberately chosen teaching parameter. We have not established an optimum cutoff or validated particle boundaries. The preceding histogram does not establish a clean separation between particle and background intensities. Trying 80 lets us inspect what a simple intensity rule actually selects.

## Count the selection

```python
selected_pixels = np.count_nonzero(mask)
selected_percent = 100 * selected_pixels / gray.size
```

For a Boolean array, `np.count_nonzero` counts the `True` entries. Dividing by all 60,000 pixels and multiplying by 100 gives the selected pixel percentage.

This number means **the percentage of this ROI's pixels below the chosen threshold**. It is not a particle count, a measured particle area fraction, a volume fraction or a concentration. Such interpretations require a validated relationship between the mask and the structures of interest.

## Read the three panels

1. Original grayscale ROI, with fixed 0–255 display limits.
2. Mask: white means selected (`True`); black means unselected (`False`). White here does not mean bright in the original image. In fact, we selected dark pixels.
3. Original image with selected locations colored translucent red. This helps you check whether selected regions follow structures, cover their interiors, fragment them or join different structures.

The overlay is only a plot layer. It does not paint red pixels into your original data. Selected pixels do not become particles merely because they appear connected or have a distinct display color.

## Every important line

| Code | Meaning and purpose |
| --- | --- |
| `from pathlib import Path` | Imports the familiar file-path tool. |
| `import matplotlib.pyplot as plt` | Imports plotting functions. |
| `from matplotlib.colors import ListedColormap` | Imports a way to specify exact display colors for the two mask values. |
| `import numpy as np` | Imports array comparison and counting functions. |
| `import tifffile` | Imports the TIFF reader. |
| `def main():` | Groups the lesson into a function. |
| `image_path = Path(r"...")` | Identifies the original TIFF. The raw string preserves Windows backslashes. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the TIFF for reading and closes it after the indented block. |
| `image = tif.series[0].asarray()` | Loads the first series, as in Lesson 2. |
| `roi = image[100:300, 100:400, :].copy()` | Selects 200 rows, 300 columns and all RGB components, as in Lesson 4. |
| `red`, `green`, `blue` assignments | Read each RGB plane, as in Lesson 5. |
| `if not (np.array_equal(...) and np.array_equal(...)):` | Checks the whole ROI for identical RGB components; `raise ValueError(...)` stops if the check fails. |
| `gray = green.copy()` | Makes an independent grayscale array from the verified green component. |
| `threshold = 80` | Sets the teaching cutoff; this is the parameter you will change. |
| `mask = gray < threshold` | Creates the Boolean selection using a strict comparison. |
| `np.count_nonzero(mask)` | Counts selected locations, not connected objects. |
| `100 * selected_pixels / gray.size` | Computes the selected percentage of all ROI pixels. |
| `print(...)` | Reports the cutoff, mask shape/type and selection size. |
| `f"...{selected_percent:.2f}%"` | Inserts the percentage into text with two decimal places for display. This formatting does not change the computed value. |
| `fig, axes = plt.subplots(1, 3, figsize=(14, 4))` | Creates one row of three plots. The numbers in `figsize` are figure inches. |
| `axes[0].imshow(gray, ...)` | Shows the original grayscale ROI using familiar display settings. |
| `axes[1].imshow(mask, cmap="gray", vmin=0, vmax=1, ...)` | Displays False as black and True as white using the 0–1 scale. |
| `axes[2].imshow(gray, ...)` | Draws the original grayscale image under the overlay. |
| `ListedColormap([(0, 0, 0, 0), (1, 0, 0, 0.5)])` | Supplies two RGBA colors on a 0–1 scale. The fourth value is opacity: 0 makes False transparent; 0.5 makes True half-opaque red. These plotting color values are separate from the stored uint8 intensities. |
| `axes[2].imshow(mask, cmap=overlay_colors, ...)` | Adds the colored selection above the original plot. |
| `origin="upper"`, `interpolation="nearest"` | Keep orientation and rendering consistent across all layers. |
| `set_title(...)` | Labels each panel, inserting the actual threshold where needed. |
| `for ax in axes:` | Repeats the indented coordinate labels for all three plots. |
| `set_xlabel`, `set_ylabel` | Label local ROI coordinates in pixels. |
| `fig.tight_layout()` | Makes room for titles and labels. |
| `Path(__file__).resolve().parent / "lesson_07.png"` | Creates a figure path beside this script. |
| `fig.savefig(..., dpi=150)` | Saves a rendered figure for inspection, not a replacement for the arrays. |
| `plt.show()` | Requests a plot window; open the saved PNG if none appears. |
| `if __name__ == "__main__": main()` | Runs the function when you execute this file directly. |

## Scientific limits

This is one global threshold: the same rule is used everywhere in the ROI. It assumes intensity is useful for the particular selection you want. Uneven illumination, texture, noise and overlapping intensity distributions can all make a single cutoff unsuitable for identifying objects.

For this TEM export, no rule has yet been validated as identifying complete particles. Do not measure particle sizes from this mask. Visually inspect the overlay: dark boundaries and small textured patches may be selected while much of a structure's interior is omitted.

The ROI and its pixel values still have the limitations described earlier: selection bias, possible export adjustments, embedded annotations elsewhere in the file and no established physical pixel calibration. Reusing the same threshold across differently acquired or contrast-adjusted images is not automatically comparable.

## Your one experiment

Change only `threshold = 80` to `threshold = 100`. Keep the strict `<` rule and the ROI unchanged. Before running, predict:

1. Will more or fewer pixels be selected in this ROI?
2. Will pixels with values 80–99 now be selected?
3. Will the original grayscale values change?

After running, inspect both the count and red overlay. More selected pixels does not by itself mean a more scientifically accurate selection. We stop here before filtering, automatic threshold choice or object measurements.

Reference: [NumPy count_nonzero documentation](https://numpy.org/doc/stable/reference/generated/numpy.count_nonzero.html).
