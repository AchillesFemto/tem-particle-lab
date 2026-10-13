# Lesson 6: understanding an intensity histogram

A histogram counts how many pixel values fall into specified intensity intervals, called bins. It summarizes the distribution of stored values without changing the image. This helps us inspect the range and concentration of intensities before considering processing. We will not apply a threshold today.

## Start with a tiny example

Imagine five grayscale pixels with values `2, 2, 5, 9, 10`. If our bins are 0–7 and 8–15, the counts are 3 and 2. Each pixel contributes once, regardless of where it is in the image. The counts add to five.

For your ROI, there are 200 × 300 = 60,000 pixels. We reuse the RGB equality check from Lesson 5 and copy the green plane into a 2D grayscale array. Its values are identical to the red and blue planes in this verified region.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_06.py
```

No new packages are needed. The script prints the counts, saves `lesson_06.png` and requests a figure window. Rerunning replaces that figure only; the original TIFF remains unchanged.

## The new operation

```python
number_of_bins = 32
counts, edges = np.histogram(gray, bins=number_of_bins, range=(0, 256))
```

`np.histogram` looks through every value in `gray`. It treats the array as a collection of values for counting; it does not change `gray.shape` or edit its values. It returns two arrays, assigned to `counts` and `edges`.

- `bins=32` divides the specified range into 32 equal intervals.
- `range=(0, 256)` sets their outer boundaries. The value 256 is a boundary, not a possible uint8 pixel value.
- Each bin is 256 / 32 = 8 intensity units wide.
- The first bin counts integers 0–7; the second 8–15; the last 248–255.
- `counts` contains 32 pixel counts. `edges` contains 33 boundaries, because adjacent bins share edges.

NumPy includes each left edge and excludes each right edge, except that the final bin also includes its right edge. There are no values of 256 in this uint8 array, so that final exception does not change our counts. Values outside a histogram's specified range would be omitted; our range covers every possible value here.

## Read the figure

The left panel shows where intensities occur. The right panel counts them:

- Horizontal axis: stored intensity. Lower values are darker in the displayed grayscale image.
- Vertical axis: number of pixels in a bin. A tall bin means many pixels have values in that interval; it does not mean those pixels are brighter or physically taller.
- The histogram contains no position information. Rearranging the same pixel values into a different image leaves the histogram unchanged.

With 32 bins, we count groups of eight integer intensities, not each exact intensity separately. `counts.sum()` should equal `gray.size`: 60,000. This checks that every ROI pixel was counted.

## Important lines, including the setup

| Code | Meaning and purpose |
| --- | --- |
| `from pathlib import Path` | Imports the path tool. |
| `import matplotlib.pyplot as plt` | Imports plotting functions. |
| `import numpy as np` | Imports array comparison and histogram functions. |
| `import tifffile` | Imports the TIFF reader. |
| `def main():` | Groups the lesson in a function. |
| `image_path = Path(r"...")` | Identifies the original file; the raw string preserves Windows backslashes. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the TIFF for reading and closes it after the indented block. |
| `image = tif.series[0].asarray()` | Loads its first series, as in earlier lessons. |
| `roi = image[100:300, 100:400, :].copy()` | Selects Lesson 4's original rectangle, keeping RGB components. |
| `red`, `green`, `blue` assignments | Select each component using the slicing syntax from Lesson 5. |
| `same_components = ...` | Requires both whole-plane equality checks to pass. |
| `if not same_components: raise ValueError(...)` | Stops if selecting one component would discard different RGB values. |
| `gray = green.copy()` | Creates an independent 2D array from the verified green component. |
| `number_of_bins = 32` | Sets the single parameter for today's experiment. |
| `counts, edges = np.histogram(...)` | Computes the counts and boundaries described above. |
| `gray.size` | Counts all entries in this 2D array: one per pixel. |
| `gray.min()`, `gray.max()` | Report the actual observed range, distinct from the full storage range. |
| `edges[1] - edges[0]` | Subtracts the first boundary from the second to report bin width. |
| `counts.sum()` | Adds all bin counts. It counts pixels, not the sum of their intensities. |
| `print(...)` | Displays numerical results so you can inspect more than the plot's appearance. |
| `fig, axes = plt.subplots(1, 2, figsize=(11, 4))` | Creates an image panel and a histogram panel. |
| `axes[0].imshow(...)` | Displays the grayscale array using fixed 0–255 limits, as in Lesson 5. |
| `axes[1].stairs(counts, edges, fill=True)` | Draws the computed histogram as filled steps; it does not recount or modify the data. |
| `axes[1].set_xlim(0, 256)` | Keeps the displayed intensity range fixed for comparisons. |
| `axes[1].set_ylim(bottom=0)` | Starts the vertical count axis at zero. |
| `set_title`, `set_xlabel`, `set_ylabel` | Explain what each panel and axis represents. The `f` string inserts the bin number in the title. |
| `fig.tight_layout()` | Fits labels and titles within the figure. |
| `Path(__file__).resolve().parent / "lesson_06.png"` | Places the figure beside the script. |
| `fig.savefig(..., dpi=150)` | Saves the rendered comparison, not a replacement for the original numerical data. |
| `plt.show()` | Requests a plot window; open the saved PNG if no window appears. |
| `if __name__ == "__main__": main()` | Runs the lesson when the script is executed. |

## Scientific limits

A histogram peak is not automatically a particle population, a material phase or a background class. Different structures can have overlapping intensities, and the histogram discards their locations. A valley does not by itself establish a scientifically valid threshold.

The ROI is a teaching selection, not a representative sampling plan. Its histogram reflects that choice. Different-sized ROIs contain different numbers of pixels, so raw count heights alone are not a fair comparison of distributions.

This is an exported uint8 image with uncalibrated intensity values. Neither high values nor histogram endpoints alone establish original detector saturation, concentration or material identity. Equal RGB values do not prove raw acquisition data or remove gray annotations. Acquisition and export settings may change the distribution.

Bin width changes the summary's appearance without changing image values. Wider bins can hide detail and collect more pixels in each interval. This is grouping counts, not smoothing or denoising the image.

## Your one experiment

Change only `number_of_bins = 32` to `number_of_bins = 16`. Before running, predict:

1. Will each bin become wider or narrower?
2. Will the sum of all counts remain 60,000?
3. Will the source grayscale image change?

Rerun and compare the histogram, printed bin width and total count. Keep the image and intensity range fixed. Do not interpret taller bars after regrouping as brighter pixels.

Reference: [NumPy histogram documentation](https://numpy.org/doc/stable/reference/generated/numpy.histogram.html).
