# Lesson 8: mean and median intensity

Today's concept is summarizing intensity with a single central value. We compare two summaries because they answer different questions and respond differently to unusually bright or dark pixels.

The histogram showed the full intensity distribution. A summary makes it easier to report or compare regions, but loses much of that detail. Neither summary describes particle size or identifies a material.

## Run

From your project's PowerShell window:

```powershell
.\.venv\Scripts\python.exe lesson_08.py
```

No new packages are needed. This lesson prints numerical results only; no plot window is expected. The TIFF and its pixel values remain unchanged.

## The mean: sum divided by count

For the invented values `90, 95, 100, 105, 110`:

```text
Mean = (90 + 95 + 100 + 105 + 110) / 5 = 100
```

Every value contributes to the sum. Raising any one value, while leaving the rest fixed, raises the mean.

```python
mean_intensity = np.mean(gray)
```

`np.mean` computes one mean across all pixels because no axis is specified. For this uint8 input, NumPy uses float64 arithmetic and returns a result that can have decimal places. It does not replace the image pixels with their mean or modify their storage type.

## The median: middle of the ordered values

Order the values from smallest to largest, then find the middle value:

```text
90, 95, [100], 105, 110
Median = 100
```

For an even number of values, the median is the mean of the two central ordered values. Our real ROI contains 60,000 pixels, so its median uses those two central positions. This refers to ordering by intensity, not the spatial center of the image.

```python
median_intensity = np.median(gray)
```

This computes one median across the whole array. With the default settings used here, it preserves the source array. The median is less sensitive than the mean to a few extreme values, but it is not automatically the scientifically correct choice and it does not remove artifacts.

## What are we measuring?

We reuse the rectangle at source rows 100:300 and columns 100:400, check RGB equality and copy its green component, as in Lesson 5. Both summaries include all 60,000 ROI pixels. The threshold from Lesson 7 is not applied.

If we selected only dark pixels and then reported their average as the average of the whole region, that would answer the wrong question. Any measurement must state what pixels were included.

These results describe stored intensity in this particular exported ROI. They are not calibrated concentration, thickness, height or particle measurements. Higher mean intensity alone does not establish more material. Acquisition settings, export adjustments, region selection and annotations can affect the numbers.

## Every important line

| Code | Meaning and purpose |
| --- | --- |
| `from pathlib import Path` | Imports the path tool used in previous lessons. |
| `import numpy as np` | Imports array operations and statistical summaries. |
| `import tifffile` | Imports the TIFF reader. |
| `def main():` | Groups the lesson into a function. |
| `image_path = Path(r"...")` | Identifies your TIFF; the raw string preserves Windows backslashes. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the file for reading and closes it after the indented block. |
| `image = tif.series[0].asarray()` | Reads the first image series, as before. |
| `roi = image[100:300, 100:400, :].copy()` | Selects the same fixed teaching rectangle and all RGB components. |
| `red`, `green`, `blue` assignments | Select the component planes. |
| `if not (np.array_equal(...) and np.array_equal(...)):` | Checks the planes are identical before representing them by one component. |
| `raise ValueError(...)` | Stops with an explanation if that assumption fails. |
| `gray = green.copy()` | Makes an independent grayscale array. |
| `mean_intensity = np.mean(gray)` | Computes the mean of all ROI pixel values. |
| `median_intensity = np.median(gray)` | Computes their median intensity, not the value of the central spatial pixel. |
| `gray.shape`, `gray.size` | Report the rectangle's dimensions and the number of pixels summarized. |
| `print(f"...{mean_intensity:.2f}")` | Displays the result with two decimal places; the `f` allows insertion of a value into text. The same formatting is used for the median. Display rounding does not change the result or image. |
| `last_value = 110` | Sets one invented example value for the controlled experiment. |
| `example = np.array([...], dtype=np.uint8)` | Creates five synthetic values in a separate one-dimensional array. It is not part of `image`, `roi` or `gray`. Keep example values within uint8's 0–255 range. |
| `print("\nSYNTHETIC EXAMPLE ...")` | Starts a new output section; `\n` adds a line break and the label keeps invented data distinct from real measurements. |
| `np.mean(example)`, `np.median(example)` | Apply exactly the same summaries to the small example you can calculate by hand. |
| Other `print(...)` statements | Display labels and values without editing them. |
| `if __name__ == "__main__": main()` | Runs the function when you execute this script directly. |

## What a single number cannot tell you

The arrays `[0, 200]` and `[100, 100]` both have mean 100 and median 100, but their distributions are very different. Keep the image and histogram alongside summaries when interpreting scientific data.

60,000 pixels are not automatically 60,000 independent experimental replicates. Neighboring image pixels may be related, and this is only one selected region. Today we report descriptive values, not uncertainty estimates or statistical significance.

Neither a decimal result nor two-decimal formatting establishes measurement accuracy. These are computations on an exported 8-bit image with unresolved acquisition and calibration limitations. A rare bright pixel could be real signal or an artifact; changing or deleting it requires evidence, not merely its influence on an average.

## Your one experiment

Change only `last_value = 110` to `last_value = 250`. This changes only the invented five-value example.

Before running, predict:

1. Will the example mean increase, decrease or stay the same?
2. Will the example median change?
3. Will the real ROI's mean or median change?

Calculate the example results by hand, then rerun to check. We are demonstrating sensitivity to an extreme value, not simulating the amount of noise in your TEM image.

References: [NumPy mean](https://numpy.org/doc/stable/reference/generated/numpy.mean.html) and [NumPy median](https://numpy.org/doc/stable/reference/generated/numpy.median.html).
