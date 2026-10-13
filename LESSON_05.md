# Lesson 5: one grayscale value per pixel

Today we learn how to select one component from an RGB array, and when it can represent the stored grayscale information exactly.

Why this matters: when we later describe an intensity distribution, we want to know what one numerical value per pixel represents. Three duplicate RGB components add no extra information. But genuinely different components must not be discarded without a scientific reason.

## Run

In your project's PowerShell window:

```powershell
.\.venv\Scripts\python.exe lesson_05.py
```

No new packages are required. The script saves `lesson_05.png`, comparing RGB and grayscale displays. It reads the original TIFF without changing it. Each run replaces only this generated PNG.

## Begin with the familiar ROI

```python
roi = image[100:300, 100:400, :].copy()
```

We explicitly use Lesson 4's original selection: 200 rows, 300 columns, three RGB components. Changes you made in another lesson's script do not automatically change this file.

At its first pixel:

```text
RGB:       [99, 99, 99]
Grayscale:  99
```

One gray-looking pixel is not enough evidence. We must check the whole ROI.

## Select and compare components

```python
red = roi[:, :, 0]
green = roi[:, :, 1]
blue = roi[:, :, 2]
```

In each line, the first `:` keeps every row, the second `:` keeps every column, and the integer selects one RGB component. Component indices are 0 for red, 1 for green and 2 for blue. Because we select one component using an integer, its axis disappears. Each result has shape `(200, 300)`.

These component arrays are views, sharing memory with `roi`. We only read them.

```python
same_components = np.array_equal(red, green) and np.array_equal(red, blue)
```

`np.array_equal` checks whether two arrays have identical shapes and values at every corresponding location. It returns `True` or `False`. The word `and` requires both comparisons to be true. If red equals green and red equals blue, all three are identical.

For this ROI, the result is `True`. For the complete PG image, red and green are not identical: it contains colored annotations.

```python
if not same_components:
    raise ValueError("This ROI contains unequal RGB values; stop and inspect it.")
```

`if` runs the indented statement only when its condition is true. `not` reverses the truth value, so the error is raised if the components are unequal. `raise ValueError(...)` stops execution with an explanation. It prevents this particular shortcut from silently being applied to unsuitable data.

## Make the grayscale array

```python
component = 0
gray = roi[:, :, component].copy()
```

We select the red component and make an independent copy. Here red has exactly the same values as green and blue, so this preserves all the distinct stored numerical values in the ROI. No averaging, filtering, normalization or rounding is involved.

```text
roi.shape:   (200, 300, 3)     gray.shape: (200, 300)
roi.ndim:    3                gray.ndim:  2
roi.dtype:   uint8            gray.dtype: uint8
```

The spatial sampling is unchanged. Only the redundant color-component axis is removed in the new array. The original `image` and `roi` arrays retain their shapes.

## Remaining important lines

| Code | What it does |
| --- | --- |
| `from pathlib import Path` | Imports the file-path tool from earlier lessons. |
| `import matplotlib.pyplot as plt` | Imports plotting functions. |
| `import numpy as np` | Imports NumPy, now used explicitly to compare arrays. |
| `import tifffile` | Imports the TIFF reader. |
| `def main():` | Groups the lesson into a function. |
| `image_path = Path(r"...")` | Locates the TIFF; the raw string preserves Windows backslashes. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the TIFF for reading and closes it after the indented block. |
| `image = tif.series[0].asarray()` | Loads the first series, previously verified for this file. |
| `print(...)` statements | Show equality checks, selected component, shapes, storage type and example pixel values. `gray[0, 0]` is a single value, while `roi[0, 0]` contains three. |
| `np.array_equal(gray, red)` | Checks every grayscale value against the red plane; more informative than comparing just one pixel. |
| `fig, axes = plt.subplots(1, 2, figsize=(10, 4))` | Creates one row of two plotting areas in a figure 10 inches wide and 4 inches high. `axes[0]` is the left plot and `axes[1]` the right. |
| `axes[0].imshow(roi, ...)` | Displays the RGB ROI using its existing colors. |
| `axes[1].imshow(gray, cmap="gray", vmin=0, vmax=255, ...)` | Displays the 2D array with 0 mapped to black and 255 to white. Fixed limits match the uint8 RGB display, preventing automatic contrast stretching from confusing the comparison. |
| `origin="upper"`, `interpolation="nearest"` | Keep the orientation and rendering choices from Lesson 3. |
| `axes[0].set_title(...)`, `axes[1].set_title(...)` | Label the two representations. |
| `for ax in axes:` | Repeats the indented label-setting statements once for each plot. |
| `ax.set_xlabel(...)`, `ax.set_ylabel(...)` | Label coordinates within the ROI, not physical distances. |
| `fig.tight_layout()` | Makes room for titles and labels. |
| `Path(__file__).resolve().parent / "lesson_05.png"` | Builds an output path beside the script. |
| `fig.savefig(..., dpi=150)` | Saves the comparison figure. This is a rendered figure, not a replacement for the scientific arrays. |
| `plt.show()` | Requests an interactive window; if unavailable, open the saved PNG. |
| `if __name__ == "__main__": main()` | Runs the lesson when you execute the script directly. |

## Scientific limits

This is a special case of redundant RGB storage, not a general RGB-to-grayscale conversion method. Selecting one component from genuinely colored data loses information. RGB components are also not automatically independent microscopy acquisition channels.

Identical RGB components do not prove an image is raw or scientifically calibrated. Gray or black annotations can also have identical components and pass this check. Your chosen ROI was visually inspected; equality alone does not detect all annotations. Export adjustments and the missing physical pixel calibration remain unresolved.

We call the array `gray` because of its numerical representation, not because its values have been validated as a particular physical quantity. Do not treat these stored values as concentration, height or material identity.

## Your one experiment

Change only `component = 0` to `component = 1`. Before running, predict:

1. Which RGB component will now be selected?
2. Will `gray.shape` or `gray.ndim` change?
3. Will the grayscale values and displayed shades change in this verified ROI?

Run again and examine `Grayscale equals red plane`. Explain why the result follows from the equality check. Stop here; we will use the 2D array for a later lesson on intensity distributions.

Reference: [NumPy array_equal documentation](https://numpy.org/doc/stable/reference/generated/numpy.array_equal.html).
