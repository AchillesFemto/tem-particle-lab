# Lesson 12: how many pixels belong to each region?

Last lesson grouped connected pixels. Today we measure the size of each group by counting its pixels. This is a first region measurement, but our threshold regions are not validated particles.

## Run

In PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_12.py
```

No new dependencies are needed. The script prints results only and leaves the TIFF unchanged. It uses the fixed original ROI, threshold `< 80` and edge-only connectivity; edits to earlier lesson parameters do not transfer automatically.

## Separate three ideas

For this synthetic label array:

```text
1 1 0
0 0 2
0 0 2
```

- There are **two regions**: IDs 1 and 2.
- Region 1 contains **two pixels**, because 1 appears twice.
- Region 2 contains **two pixels**, because 2 appears twice.
- There are **four selected pixels** in total and five unselected pixels, labeled 0.

An ID is a name, not a size: region 1 does not necessarily have one pixel. Zero denotes unselected pixels; they are not counted as one additional selected region.

## The new operation

```python
counts_by_label = np.bincount(labels.ravel())
region_sizes = counts_by_label[1:]
```

`labels.ravel()` presents the 2D label array as a one-dimensional sequence, as required by `bincount`. It does not rearrange or edit `labels` itself. The counting operation does not need pixel coordinates because connectivity has already been determined.

`np.bincount` counts how often each nonnegative integer occurs. The array index identifies which label is being counted:

```text
counts_by_label = [5, 2, 2]
                  ↑  ↑  ↑
                 ID0 ID1 ID2
```

`counts_by_label[0]` is the count of unselected pixels. `[1:]` selects everything from index 1 onward, removing that count from our list of region sizes. Here `region_sizes` becomes `[2, 2]`.

After removing index 0, `region_sizes[0]` belongs to label 1, `region_sizes[1]` to label 2, and so on. The entries follow label order, not size order.

This resembles a histogram, but we are counting integer **region IDs**, not intensities. Each selected pixel belongs to exactly one region. Therefore the sum of region sizes must equal the selected-pixel count.

## Important lines

| Code | Meaning |
| --- | --- |
| `from pathlib import Path` | Imports the path tool. |
| `import numpy as np` | Imports array creation, checks and counting. |
| `from scipy.ndimage import generate_binary_structure, label` | Imports the connectivity and labeling tools from Lesson 11. |
| `import tifffile` | Imports the TIFF reader. |
| `def main():` | Groups the lesson into a function. |
| `generate_binary_structure(2, 1)` | Uses two spatial dimensions and edge-only (4-neighbor) connectivity. |
| `extra_pixel = 0` | Controls one synthetic pixel for the experiment. |
| `np.array([...], dtype=bool)` | Creates the invented mask; 1 becomes True and 0 becomes False. |
| `example_labels, example_count = label(...)` | Labels its connected groups and returns their count. |
| `example_counts = np.bincount(example_labels.ravel())` | Counts pixels at each synthetic label ID. |
| `example_counts[1:]` | Excludes unselected pixels from the synthetic region sizes. |
| `image_path = Path(r"...")` | Locates the original TIFF with literal Windows backslashes. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the file for reading and closes it after the indented block. |
| `image = tif.series[0].asarray()` | Reads the first series. |
| `roi = image[100:300, 100:400, :].copy()` | Selects the original teaching rectangle and RGB components. |
| `red, green, blue = ...` | Assigns the three component planes to their respective names in one statement. |
| `if not (...)`, `raise ValueError(...)` | Stops if the RGB planes are not identical. |
| `gray = green.copy()` | Creates the independent, verified grayscale array. |
| `mask = gray < 80` | Recreates the fixed dark-pixel selection without smoothing. |
| `labels, region_count = label(...)` | Groups it using the same edge-only rule. |
| `counts_by_label`, `region_sizes` | Compute the real region sizes using the operation explained above. |
| `region_sizes[:10]` | Prints the first ten entries, stopping before index 10. These are not the ten largest regions. |
| `region_sizes.sum()` | Adds all region pixel counts. |
| `np.count_nonzero(mask)` | Independently counts selected pixels directly from the mask. |
| `region_sizes.sum() == np.count_nonzero(mask)` | Uses `==` to test whether the two totals match; this should print True. |
| `print(...)` | Displays labels and values. `\n` starts a new line to separate real data from the synthetic example. |
| `if __name__ == "__main__": main()` | Runs the lesson when executed directly. |

## Scientific interpretation

A region's pixel count describes the area occupied by its selected pixels on the image grid. It is not its diameter or a physical area in nm². With a verified calibration, physical area would be pixel count × pixel width × pixel height. We have not established that calibration here.

Our regions can be fragments, dark boundaries, small isolated pixels or merged structures. Numerical precision does not make the mask biologically or physically correct. These counts must not be published as particle areas without validating segmentation.

Regions crossing the ROI border are incomplete. A single particle may be split into several groups, or several particles joined together. Tiny regions are not automatically noise, and large regions are not automatically valid particles. We do not delete anything in this lesson.

## Your one experiment

Change only `extra_pixel = 0` to `extra_pixel = 1`. The synthetic mask will be:

```text
1 1 0
1 0 1
0 0 1
```

Keep edge-only connectivity fixed. Before running, predict:

1. How many regions will there be?
2. How many pixels will each region contain?
3. Will the real TIFF results change?

Trace the connected pixels by hand, then compare the printed labels and sizes. Adding a pixel to an existing region is different from creating a new region.

Reference: [NumPy bincount documentation](https://numpy.org/doc/stable/reference/generated/numpy.bincount.html).
