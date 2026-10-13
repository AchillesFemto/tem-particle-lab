# Lesson 4: selecting a region of interest

A region of interest (ROI) is a selected part of an image. Today we select a rectangle using NumPy slicing. This is useful when we want to inspect a defined area in detail. It does not identify objects or their boundaries automatically.

We will keep the original array and make a separate array called `roi`. No pixel intensities are changed and the original TIFF is never overwritten. No new packages are needed.

## Run

From PowerShell in your project folder:

```powershell
.\.venv\Scripts\python.exe lesson_04.py
```

The script prints array properties and saves `lesson_04.png`, a display of the selected region. It also requests a plot window. Rerunning replaces the generated PNG only.

## The new concept: the colon selects a range

Previously, `image[428, 0]` selected one pixel. Now:

```python
roi = image[100:300, 100:400, :].copy()
```

Read this from left to right:

| Part | Meaning |
| --- | --- |
| `100:300` | Select row indices 100 through 299: 200 rows. |
| `100:400` | Select column indices 100 through 399: 300 columns. |
| Final `:` | Keep all three RGB components. |
| `.copy()` | Store the selected values in independent memory. |
| `roi =` | Give this new array the name `roi`. |

The rule is **include the start, exclude the stop**. With these in-bounds ranges and a step of one, the selected length is `stop - start`.

Expected shapes:

```text
image.shape = (857, 857, 3)
roi.shape   = (200, 300, 3)
```

The ROI still has three axes and stores `uint8` values. Selecting a smaller rectangle changes how many rows and columns the new array contains; it does not change the original array or remove its RGB axis.

## Why `.copy()` matters

Basic NumPy slicing normally produces a view: an array sharing the original array's memory. Editing values through that view could also change the original array in memory. `.copy()` makes the ROI independent. Reading a view alone would not change anything, and neither a view nor a copy automatically writes changes back to the TIFF file.

## Coordinates start again within the ROI

The first pixel of the ROI is `roi[0, 0]`. It contains the same RGB values as `image[100, 100]`, because that is where our selection starts.

For this selection, to convert an ROI coordinate back to the original image:

```text
original row    = ROI row + 100
original column = ROI column + 100
```

The saved plot labels coordinates within the ROI. The title records the original selection ranges. These are pixel coordinates, not nanometres.

## Every important line in the script

| Code | Purpose |
| --- | --- |
| `from pathlib import Path` | Imports the path tool from previous lessons. |
| `import matplotlib.pyplot as plt` | Imports plotting functions. |
| `import tifffile` | Imports the TIFF reader. |
| `def main():` | Groups the lesson into a function. |
| `image_path = Path(r"...")` | Locates your TIFF; the raw string preserves Windows backslashes. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the TIFF for reading and closes it after the indented block. |
| `image = tif.series[0].asarray()` | Reads the first image series, as in Lesson 2. |
| `row_start`, `row_stop`, `column_start`, `column_stop` | Name the selection limits, making it easy to change and record them. |
| `roi = image[row_start:row_stop, column_start:column_stop, :].copy()` | Applies the slicing operation explained above, using named limits instead of literal numbers. |
| `print(..., image.shape)` | Confirms the original array retains its shape. |
| `print(..., roi.shape)`, `roi.ndim`, `roi.dtype` | Reports the selected array's size, number of axes and storage type. |
| `roi[0, 0]` and `image[row_start, column_start]` | Read the same location in two coordinate systems. The printed RGB values should match. |
| `fig, ax = plt.subplots(figsize=(7, 5))` | Creates a figure and plotting area; dimensions are figure inches, not specimen dimensions. |
| `ax.imshow(roi, ...)` | Displays the ROI using the same orientation and rendering settings as Lesson 3. |
| `ax.set_title(f"...")` | Labels the source ranges. The `f` allows values inside `{...}` to be inserted into the text. |
| `ax.set_xlabel(...)`, `ax.set_ylabel(...)` | Explicitly label coordinates as local to the ROI. |
| `fig.tight_layout()` | Fits the plot labels within the figure. |
| `Path(__file__).resolve().parent / "lesson_04.png"` | Builds an output path beside the script. |
| `fig.savefig(..., dpi=150)` | Saves a rendered figure. Use the original array or ROI array, not this annotated PNG, for later numerical analysis. |
| `plt.show()` | Requests an interactive figure window. |
| `if __name__ == "__main__": main()` | Runs the function when you execute the script directly. |

## Scientific assumptions

This rectangle is a teaching example, not a representative sampling plan. Choosing only regions with attractive or clearly separated particles could bias future size statistics. Quantitative sampling needs a defined selection rule across suitable fields of view.

The displayed default rectangle avoids the visible measurement annotations in this image, but it is not certified raw detector data. Cropping cannot undo earlier contrast adjustments or recover lost information. A different selection may include the embedded labels. Inspect it before interpreting its contents as specimen signal.

Objects crossing an ROI edge are only partially visible. Measuring such fragments as whole particles would bias results. We are not measuring particles in this lesson.

Slicing keeps the original pixel sampling; it does not resize or interpolate the selected data. No physical calibration has been established yet. Keep source coordinates within the image bounds: rows and columns span indices 0–856 here. NumPy can silently truncate slices beyond the boundary, so always inspect the actual resulting shape.

## Your one experiment

Change only `row_stop = 300` to `row_stop = 400`. Before running, predict:

1. What will `roi.shape` become?
2. Will the selection extend upward, downward, left or right in the original image?
3. Will `image.shape` change?

Run and compare. The selection origin is unchanged, so the first ROI pixel should still correspond to the same original pixel. Stop here before doing further processing.

Reference: [NumPy slicing documentation](https://numpy.org/doc/stable/user/basics.indexing.html).
