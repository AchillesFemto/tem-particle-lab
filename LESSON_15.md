# Lesson 15: a minimum region size

## What problem does size filtering address?

A threshold mask can contain many tiny disconnected regions. If a scientific protocol has a justified minimum size, we can exclude regions smaller than that limit from further analysis. Today we learn how that rule works. We have not established that tiny regions in PG.tif are noise, or that the larger ones are particles.

This operation uses region pixel counts, not intensity values. It excludes entire connected regions; it does not smooth or shrink them.

## Run

In PowerShell in your project folder:

```powershell
.\.venv\Scripts\python.exe lesson_15.py
```

No new packages are needed. The script prints results only. It uses the same original ROI, threshold `< 80` and edge-only connectivity. To study size filtering alone, it applies neither smoothing nor Lesson 14's border exclusion. The original TIFF and source arrays are preserved.

## Start with known sizes

The synthetic labels are:

```text
1 1 0 2 2 0 3 3 3
0 0 0 2 2 0 3 3 3
```

| Region ID | Pixel count | Retain when minimum is 3? |
| --- | ---: | --- |
| 1 | 2 | No |
| 2 | 4 | Yes |
| 3 | 6 | Yes |

The rule is **retain a region if its pixel count is greater than or equal to the minimum**. Exactly three pixels would pass a minimum of three. This is an area-on-the-grid criterion, not a width or diameter criterion.

## The filtering function

```python
counts = np.bincount(labels.ravel())
keep_id = counts >= min_pixels
keep_id[0] = False
```

As in Lesson 12, `counts[1]` gives the size of region 1. Comparing counts against the minimum creates a Boolean decision for each ID. Index 0 is explicitly set to False because it represents unselected pixels, regardless of how many there are.

For our example, the decisions are:

```text
ID:       0      1     2     3
keep_id: False  False  True  True
```

Next:

```python
result = labels.copy()
result[~keep_id[labels]] = 0
```

`keep_id[labels]` looks up the decision for every pixel's label ID, producing a Boolean map the same shape as the image. A pixel labeled 2 receives `keep_id[2]`, which is True. A pixel labeled 1 receives False.

The `~` operator reverses True and False in this Boolean map. Thus the brackets select positions we should exclude, and `= 0` sets them to zero in the copy. It does not change the source intensities.

This lookup removes region 1 completely and leaves regions 2 and 3 intact. IDs are preserved, so count distinct positive IDs rather than taking the maximum label.

## Important lines

| Code | Meaning |
| --- | --- |
| `from pathlib import Path` | Imports the file-path tool. |
| `import numpy as np` | Imports array creation, pixel counting and Boolean operations. |
| `from scipy.ndimage import generate_binary_structure, label` | Imports the connectivity and labeling tools. |
| `import tifffile` | Imports the TIFF reader. |
| `def keep_large_regions(labels, min_pixels):` | Defines a reusable function receiving labels and a minimum pixel count. Use a positive integer for the lesson parameter. |
| `if min_pixels < 1: raise ValueError(...)` | Rejects a nonpositive minimum with an explanation. |
| `counts`, `keep_id`, `result` lines | Perform the counting, lookup and exclusion described above. |
| `return result` | Returns the new labels to the calling code. |
| `def main():` | Groups the lesson steps. |
| `min_pixels = 3` | Sets the single experiment parameter. This value is illustrative, not a validated cutoff for your specimen. |
| `np.array([...], dtype=np.int32)` | Builds an invented integer label array with region IDs already assigned. It is not intensity data. |
| `example_kept = keep_large_regions(...)` | Applies the function to the synthetic labels. |
| `np.bincount(example_labels.ravel())[1:]` | Prints known synthetic region sizes, excluding ID 0. |
| `np.unique(example_kept[example_kept > 0]).size` | Counts distinct retained positive IDs. The same expression counts real retained regions later. |
| `image_path = Path(r"...")` | Locates the original TIFF. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens it for reading and closes it after the block. |
| `image = tif.series[0].asarray()` | Reads its first image series. |
| `roi = image[100:300, 100:400, :].copy()` | Selects the fixed original teaching rectangle. |
| `red, green, blue = ...` | Reads its three RGB planes. |
| `if not (...)`, `raise ValueError(...)` | Stops if the planes are not identical. |
| `gray = green.copy()` | Makes an independent grayscale array. |
| `mask = gray < 80` | Selects pixels below the fixed intensity threshold. This 80 is unrelated to the minimum pixel count. |
| `generate_binary_structure(2, 1)` | Fixes edge-only connections in two dimensions. |
| `labels, region_count = label(...)` | Labels connected regions before size filtering. |
| `kept = keep_large_regions(labels, min_pixels)` | Applies the same minimum-size rule to real mask regions. |
| `np.count_nonzero(...)` | Counts selected pixels before and after exclusion. |
| `np.array_equal(labels > 0, mask)` | Checks that the original label selection still matches the original mask. |
| `print(...)` | Displays values; `\n` separates synthetic and real output. |
| `if __name__ == "__main__": main()` | Runs the lesson when the script is executed directly. |

## Scientific limits

Small regions can be real structures, noise, artifacts or fragments of incorrectly segmented objects. Large regions can also be artifacts or merged objects. Size filtering alone cannot decide which is which.

Raising the minimum systematically removes the small end of the observed size distribution. A cutoff therefore needs justification from the measurement goal, sampling resolution and validation. Do not adjust it just to obtain an attractive image or expected count.

A pixel cutoff is not automatically comparable across images with different physical pixel sizes. A justified physical area cutoff would require verified calibration first. Today's 3-pixel minimum is a teaching parameter only.

Filtering does not repair broken boundaries or separate touching particles. Border-touching regions may still be incomplete; we deliberately keep that policy separate here. Retained regions remain unvalidated particle candidates.

## Your one experiment

Change only `min_pixels = 3` to `min_pixels = 5`. Predict:

1. Which synthetic region IDs will remain, given sizes 2, 4 and 6?
2. Will more or fewer regions remain?
3. Will the original TIFF intensity values change?

Run and compare. The algorithm changes eligibility based on the same original labels; it does not alter the size of a surviving region.

Reference: [NumPy bincount](https://numpy.org/doc/stable/reference/generated/numpy.bincount.html).
