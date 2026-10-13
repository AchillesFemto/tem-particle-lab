# Lesson 14: regions touching the boundary

## The problem

A selected region touching the outer edge of an image or ROI might continue beyond it. Measuring only the visible fragment as a complete object could underestimate its size. One explicit policy is to exclude every region that touches the boundary before measuring complete-region sizes.

This is not proof that the object extends beyond the image, and exclusion is not always the right policy. Today we learn exactly what this policy does and what it cannot guarantee.

## Run

From your project folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe lesson_14.py
```

No new packages are needed. The script prints arrays and counts only. The original TIFF, grayscale data, mask and original labels are preserved. Exclusion is performed in a new label array.

## A small example

The initial label array is:

```text
0 1 0 0 0
0 1 0 0 0
0 0 0 0 0
0 0 2 2 0
0 0 0 0 0
```

Region 1 touches the top boundary. Region 2 is surrounded by unselected pixels and does not touch the outer boundary. Excluding boundary regions gives:

```text
0 0 0 0 0
0 0 0 0 0
0 0 0 0 0
0 0 2 2 0
0 0 0 0 0
```

Both pixels of region 1 are removed from the retained selection, including its pixel inside the image. Removing only the outer row would leave a smaller fragment; that is not the policy we intend.

Region 2 keeps its ID. The largest label is still 2, but only **one region** remains. After exclusion, label IDs can have gaps, so the maximum ID is no longer a reliable region count.

## How the code does it

The reusable function `exclude_border_regions(labels)` performs four steps:

1. Read IDs from the top, bottom, left and right boundaries.
2. Find the distinct positive IDs among them.
3. Copy the label array.
4. Set every occurrence of those IDs to zero in the copy.

```python
result[np.isin(labels, border_ids)] = 0
```

`np.isin(labels, border_ids)` creates a Boolean array: True wherever a label is in the boundary-ID list. Brackets select those positions, and `= 0` writes zero into the copy there. This excludes whole regions from the new selection. It does not turn their original grayscale intensities black.

## Every important line

| Code | Meaning |
| --- | --- |
| `from pathlib import Path` | Imports the path tool. |
| `import numpy as np` | Imports array creation, membership and counting operations. |
| `from scipy.ndimage import generate_binary_structure, label` | Imports the labeling tools from Lesson 11. |
| `import tifffile` | Imports the TIFF reader. |
| `def exclude_border_regions(labels):` | Defines a reusable operation. `labels` is its input; the indented statements run when it is called. |
| `labels[0, :]`, `labels[-1, :]` | Read the first and last rows. Index `-1` means the last item. |
| `labels[:, 0]`, `labels[:, -1]` | Read the first and last columns. |
| `np.concatenate((...))` | Joins those four sequences into one array of boundary IDs. Corners appear twice, which does not affect the next step. |
| `np.unique(boundary)` | Keeps one instance of each ID. |
| `border_ids[border_ids > 0]` | Keeps only positive region IDs, excluding unselected ID 0. This is Boolean selection, not ordinary range slicing. |
| `result = labels.copy()` | Makes the independent output array. |
| `result[np.isin(labels, border_ids)] = 0` | Excludes every pixel in each boundary-touching region. |
| `return result, border_ids` | Sends both the output array and flagged IDs back to the calling code. |
| `def main():` | Groups the lesson's execution steps. |
| `remove_border = True` | Enables exclusion. This is the experiment parameter. |
| `generate_binary_structure(2, 1)` | Uses edge-only connections in two dimensions, held fixed for the lesson. |
| `np.array([...], dtype=bool)` | Builds the synthetic selection from 1 and 0 values. |
| `example_labels, example_count = label(...)` | Labels its connected regions and counts them. |
| `example_interior, example_border_ids = exclude_border_regions(example_labels)` | Calls our function and stores its two returned values. |
| `example_interior if remove_border else example_labels.copy()` | Chooses the excluded result if the flag is True, otherwise a copy of all original regions. The real-data selection uses the same expression. |
| `np.unique(example_kept[example_kept > 0]).size` | Counts distinct surviving positive IDs, correctly handling gaps. |
| `image_path = Path(r"...")` | Locates the original TIFF. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the file for reading and closes it after the block. |
| `image = tif.series[0].asarray()` | Reads the first series. |
| `roi = image[100:300, 100:400, :].copy()` | Uses the same original teaching crop. Its boundaries are the boundaries tested, not the full TIFF's edges. |
| `red, green, blue = ...` | Reads the RGB planes. |
| `if not (...)`, `raise ValueError(...)` | Stops if a single component cannot represent identical RGB values. |
| `gray = green.copy()` | Creates the independent grayscale array. |
| `mask = gray < 80` | Recreates the fixed teaching selection, without smoothing. |
| `labels, region_count = label(...)` | Labels the real mask using the fixed connection rule. |
| `interior, border_ids = exclude_border_regions(labels)` | Applies exactly the same boundary policy to the real labels. |
| `border_ids.size` | Counts flagged regions, even when the flag is False and they are retained. |
| `np.unique(kept[kept > 0]).size` | Counts retained regions. |
| `np.count_nonzero(mask)`, `np.count_nonzero(kept)` | Counts selected pixels before and after the policy. |
| `np.array_equal(labels > 0, mask)` | Confirms the original label selection still matches the original mask. |
| `print(...)` | Displays results; `\n` separates synthetic and real-data output. |
| `if __name__ == "__main__": main()` | Runs the lesson when executed directly. |

## Scientific limits

Excluding boundary regions avoids reporting obvious edge fragments as complete regions, but it can preferentially exclude larger objects, which are more likely to intersect a boundary. It is not automatically an unbiased particle-count or size-distribution method. A future sampling plan must address this explicitly.

An interior region is not automatically a complete physical particle: segmentation can split particles, merge them or miss boundaries. Our threshold mask is still unvalidated, and the retained count is not a particle count. A thin connection to the boundary will cause the whole connected region to be excluded under this rule.

This policy changes which regions are eligible, not physical calibration, specimen geometry or acquisition data. We do not calculate physical particle sizes in this lesson. We also do not remove small regions merely because they are small.

## Your one experiment

Change only `remove_border = True` to `remove_border = False`, leaving both masks and connectivity unchanged.

Predict:

1. In the synthetic example, will one region or two be retained?
2. Will the pixels belonging to region 1 be retained now?
3. Will any original TIFF intensity values change?

Run and compare the retained counts. The set of flagged boundary IDs is unchanged; the parameter only decides whether to exclude them.

Reference: [NumPy membership testing](https://numpy.org/doc/stable/reference/generated/numpy.isin.html).
