# Lesson 16: does the result depend strongly on the threshold?

One chosen threshold produces one result. Before trusting a measurement, we should ask how much it changes under other plausible choices. This is a parameter-sensitivity check. Today we vary only the threshold and inspect selected-pixel counts and connected-region counts.

We do not select an optimum, measure physical particle sizes or build an entire analysis pipeline in this lesson.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_16.py
```

No new packages are needed. The script prints a small comparison table. It does not create a plot or modify the TIFF.

## More selected pixels need not mean more regions

Consider three invented pixels in a row:

```text
Intensities: 40 90 40
```

With the rule `< 80`, the mask is `True, False, True`: two selected pixels forming two regions. With `< 100`, all three pixels are selected: the middle pixel connects the other two, forming one region.

Increasing a dark-pixel threshold cannot remove an already selected pixel. But it can create new isolated regions, expand existing regions or join separate regions. Therefore region count can increase, decrease or stay the same. Do not confuse this with Lesson 11's connectivity change: there the mask was fixed, while here the mask itself changes.

## Change one parameter at a time

We compare thresholds 60, 80 and 100 using the same:

- Original 200 × 300 grayscale ROI and strict `<` comparison.
- Edge-only connectivity.
- Unsmoothed values.
- No size filtering and no boundary exclusion.

This intentionally isolates the effect of threshold. Earlier script edits do not transfer automatically. Once a future analysis pipeline is defined, sensitivity should also be checked for its final measurements with other settings held fixed.

```python
for threshold in range(60, max_threshold + 1, 20):
    mask = gray < threshold
```

`range` starts at 60, stops before its second argument and advances in steps of 20. Adding 1 to `max_threshold` includes the endpoint when it lies on that sequence. With `max_threshold = 100`, the values are 60, 80 and 100.

The loop repeats its indented block for each threshold. Every mask is computed from the same original `gray`, not from a previous mask.

## Reading the table scientifically

Each row records a parameter setting and the result under that setting. The selected percentage describes the share of ROI pixels passing the rule. The region count describes connected pieces of that selection, not validated particles.

Large changes indicate sensitivity over the tested range. That is a reason to investigate segmentation and the measurement definition. It does not by itself prove the method is wrong. Conversely, similar results across thresholds do not prove the segmentation is correct: multiple bad masks can have similar counts.

Our thresholds are broad teaching choices, not a justified uncertainty interval. Inspect overlays at candidate settings and compare against independently supported boundaries or reference annotations before choosing parameters for scientific work. Never choose the threshold merely because it yields an expected particle count.

This table is not a confidence interval or variation across independent specimens. It describes parameter dependence on one fixed ROI. Pixel calibration, representative sampling and validation of real particle regions remain unresolved.

## Important lines

| Code | Meaning |
| --- | --- |
| `from pathlib import Path` | Imports the path tool. |
| `import numpy as np` | Imports arrays, equality checks and counting. |
| `from scipy.ndimage import generate_binary_structure, label` | Imports connectivity and region labeling. |
| `import tifffile` | Imports the TIFF reader. |
| `def main():` | Groups the lesson steps. |
| `generate_binary_structure(2, 1)` | Keeps edge-only connectivity fixed. |
| `np.array([[40, 90, 40]], dtype=np.uint8)` | Creates the separate synthetic one-row image. Double brackets make it 2D for our 2D connectivity rule. |
| `for threshold in (80, 100):` | Runs the example twice, using the two listed thresholds. |
| `example_mask = example < threshold` | Selects synthetic pixels below the current threshold. |
| `example_labels, example_count = label(...)` | Labels and counts the example's selected regions. |
| `np.count_nonzero(example_mask)` | Counts selected pixels so they can be distinguished from regions. |
| `image_path = Path(r"...")` | Identifies the original TIFF. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the file for reading and closes it after the block. |
| `image = tif.series[0].asarray()` | Reads the first image series. |
| `roi = image[100:300, 100:400, :].copy()` | Selects the fixed original teaching ROI. |
| `red, green, blue = ...` | Reads each RGB plane. |
| `if not (...)`, `raise ValueError(...)` | Stops if the planes are unequal. |
| `gray = green.copy()` | Creates an independent, verified grayscale array. |
| `max_threshold = 100` | Sets the endpoint of today's tested range. Use 120 for the experiment. |
| `for threshold in range(...)` | Repeats the real-image calculation for each setting, as explained above. |
| `mask = gray < threshold` | Creates a new mask from unchanged intensities. |
| `labels, region_count = label(...)` | Counts connected regions for that mask. |
| `selected_pixels = np.count_nonzero(mask)` | Counts all selected locations. |
| `100 * selected_pixels / gray.size` | Converts selected count into a percentage of the fixed ROI. |
| The formatted table `print` | Inserts values into aligned columns. `:9d`, `:15d` and `:7d` give integer column widths; `:15.2f` prints a decimal value to two places in a width of 15. Adjacent strings in this statement are joined into one line. Formatting does not alter results. |
| `np.array_equal(gray, green)` | Checks the original grayscale values still match the source component. |
| Other `print(...)` statements | Label and display output; `\n` separates example and real data. |
| `if __name__ == "__main__": main()` | Runs the lesson when executed directly. |

## Your one experiment

Change only `max_threshold = 100` to `max_threshold = 120`. This adds one table row without changing the earlier settings.

Predict:

1. Can the number of selected pixels at 120 be smaller than at 100 under our `<` rule?
2. Must the connected-region count increase as well?
3. Should the existing rows for 60, 80 and 100 change?

Run and inspect the new row. Explain any region-count change in terms of isolated selections and connecting paths, not changes in the actual specimen.
