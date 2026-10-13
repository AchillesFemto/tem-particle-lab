# Lesson 9: intensity spread and standard deviation

The mean tells us a distribution's average value. It does not tell us how widely the values vary. Today's single new concept is standard deviation (SD), a measure of spread around the mean.

For example, `[100, 100, 100]` and `[90, 100, 110]` both have mean and median 100. The first has no variation: SD = 0. The second has SD approximately 8.16 using the definition below.

## Run

In PowerShell in your project folder:

```powershell
.\.venv\Scripts\python.exe lesson_09.py
```

No new packages are needed. This lesson prints numbers only. It neither generates a figure nor changes your original TIFF. The real ROI and the synthetic example are labeled separately.

## How SD is calculated

For `[90, 100, 110]`:

1. Find the mean: 100.
2. Subtract that mean from each value: -10, 0, 10.
3. Square those differences: 100, 0, 100. This prevents negative and positive differences from canceling.
4. Average the squared differences: 200 / 3, approximately 66.67. This quantity is called variance.
5. Take the square root: approximately 8.16. The square root brings the result back to intensity units.

SD is the square root of the mean squared deviation. It is not simply the average absolute distance from the mean, and not the maximum minus minimum.

In code:

```python
intensity_sd = np.std(gray, ddof=0)
```

`np.std` computes one number over all array entries when no axis is specified. `ddof=0` means the average squared difference uses the divisor N, the number of pixels. We explicitly use this to describe the full set of intensities in this chosen ROI. We are not estimating variation across specimens or uncertainty in a mean. Other statistical contexts may use different conventions; keep this one fixed for today's lesson.

NumPy uses float64 arithmetic for our uint8 input, so the result can have decimal places. This call does not modify the image or change its dtype.

## Scientific meaning

The result describes variation among the stored intensities of all 60,000 pixels in the ROI. It can help compare intensity spread when acquisition, calibration, processing and region selection are comparable.

A larger SD does not automatically mean a better image, more noise or more particles. Specimen structure, dark boundaries, texture, noise, illumination gradients and export contrast adjustments can all contribute. The SD of this textured TEM region is not a validated noise estimate.

SD is also not the uncertainty of the mean. Neighboring pixels are not automatically independent experimental replicates. A mean and SD from one selected region do not provide evidence about variation across independent specimens.

Do not interpret mean ± SD as a guaranteed range containing a particular percentage of pixels; that depends on the distribution. As with a histogram, rearranging pixel locations leaves the mean and SD unchanged. Inspect spatial structure too.

Our existing limitations remain: this is an exported image, the ROI is a teaching selection, and intensities are not calibrated physical quantities. Printed decimal places are formatting, not proof of measurement accuracy.

## Every important line

| Code | Meaning |
| --- | --- |
| `from pathlib import Path` | Imports the familiar path tool. |
| `import numpy as np` | Imports array and statistical operations. |
| `import tifffile` | Imports the TIFF reader. |
| `def main():` | Groups the lesson into a function. |
| `image_path = Path(r"...")` | Locates your TIFF; the raw string preserves Windows backslashes. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the TIFF for reading and closes it after the indented block. |
| `image = tif.series[0].asarray()` | Reads the first image series. |
| `roi = image[100:300, 100:400, :].copy()` | Uses the same 200 × 300 teaching rectangle and retains all RGB components. |
| `red`, `green`, `blue` assignments | Read the separate RGB planes. |
| `if not (np.array_equal(...) and np.array_equal(...)):` | Checks every pixel for redundant RGB components. |
| `raise ValueError(...)` | Stops if selecting a single component is not justified by equality. |
| `gray = green.copy()` | Makes an independent 2D grayscale array after the check. |
| `mean_intensity = np.mean(gray)` | Computes the familiar average. |
| `intensity_sd = np.std(gray, ddof=0)` | Computes the spread measure explained above. |
| `gray.shape`, `gray.size` | Report the dimensions and number of pixels included. No threshold is applied. |
| `print(f"...{intensity_sd:.2f}")` | Inserts the value into text with two decimal places; the mean uses the same formatting. |
| `spread = 10` | Sets the distance of the two outer synthetic values from 100. This parameter is not itself the calculated SD. |
| `np.array([100 - spread, 100, 100 + spread], dtype=np.float64)` | Creates three invented values centered on 100. `float64` stores decimal-capable numbers and avoids unsigned integer arithmetic issues for this demonstration. It does not convert or alter the real image. |
| `print("\nSYNTHETIC EXAMPLE ...")` | Begins a separate labeled output section. `\n` starts a new line. |
| `np.mean(example)`, `np.median(example)` | Show whether the center changes as the example's values spread out. |
| `np.std(example, ddof=0)` | Applies the same SD definition to the invented example. |
| Other `print(...)` statements | Display the values and labels without changing arrays. |
| `if __name__ == "__main__": main()` | Runs the function when the file is executed directly. |

## Your one experiment

Change only `spread = 10` to `spread = 30`. This changes the invented array from `[90, 100, 110]` to `[70, 100, 130]`.

Before running, predict:

1. Will the example mean change?
2. Will its standard deviation increase, decrease or stay the same?
3. Will the real ROI's standard deviation change?

Run and explain the result in terms of distance from the mean. The synthetic values are separate from the TEM pixels. We stop here before using filters or estimating noise.

Reference: [NumPy standard deviation documentation](https://numpy.org/doc/stable/reference/generated/numpy.std.html).
