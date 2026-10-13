# Lesson 3: displaying an image is not changing its data

You have loaded your TIFF and read a pixel. Now we will display the same array with labeled coordinates. No new packages are needed.

Scientific purpose: inspecting a display helps us notice orientation, colored annotations and other visible features before making measurements. A display is a rendering of the numbers, not a substitute for the original data.

## Run

In PowerShell, from your project folder:

```powershell
.\.venv\Scripts\python.exe lesson_03.py
```

The script requests a plot window and saves `lesson_03.png` in the project folder. If no window appears, open that PNG. Rerunning replaces only this generated PNG; it does not overwrite `PG.tif`.

## The central line

```python
ax.imshow(image, origin="upper", interpolation="nearest", aspect="equal")
```

`imshow` displays your array inside a plotting area named `ax`.

- `image` is the `(857, 857, 3)` RGB array you already understand.
- `origin="upper"` puts row zero at the top. Row numbers increase downward, like reading the array from top to bottom.
- `interpolation="nearest"` avoids blending neighboring samples into smooth transitions during rendering. When enlarged sufficiently, pixels look like blocks. This changes rendering, not the stored values. A reduced display cannot show every source pixel distinctly.
- `aspect="equal"` gives one row step and one column step equal lengths on the display. It prevents visual stretching in pixel coordinates. This does not prove the original microscope sampled equal physical distances along both axes.

The horizontal axis is **column** and the vertical axis is **row**. Thus, `image[428, 0]` lies at horizontal position 0 and vertical position 428: the left edge, roughly halfway down the image. Plot coordinates are usually described as x, y; array indexing is row, column, in the opposite order.

## Why there is no `cmap="gray"`

In Lesson 1, each pixel had one number, so we chose a map from that number to a gray shade. Here each pixel already contains red, green and blue values. Matplotlib uses those RGB colors directly. The red labels remain red. Adding `cmap="gray"` to an RGB display would not convert it to grayscale; the colormap argument is ignored for RGB input.

## Remaining important lines

| Code | Meaning |
| --- | --- |
| `from pathlib import Path` | Provides the file-path tool used in Lessons 1 and 2. |
| `import matplotlib.pyplot as plt` | Imports Matplotlib's plotting interface under the short name `plt`. |
| `import tifffile` | Imports the TIFF reader from Lesson 2. |
| `def main():` | Groups the statements into a function. |
| `image_path = Path(r"...")` | Locates your original TIFF. The raw string keeps Windows backslashes literal. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the file for reading and closes it after the indented block. |
| `image = tif.series[0].asarray()` | Loads its first series into memory, as in Lesson 2. We previously checked that this file contains one series. |
| `print(..., image.shape)` | Reports the array dimensions before and after plotting. |
| `print(..., image[428, 0])` | Reads the pixel you inspected previously, before and after plotting. |
| `figure_size = 6` | Sets the figure's nominal side length in inches. These are figure units, not specimen dimensions. |
| `fig, ax = plt.subplots(figsize=(figure_size, figure_size))` | Creates the whole figure (`fig`) and one plotting area inside it (`ax`). The pair in `figsize` specifies width and height. |
| `ax.set_title(...)` | Adds a descriptive title. |
| `ax.set_xlabel(...)`, `ax.set_ylabel(...)` | Label the horizontal and vertical axes in pixel indices. We do not label them in nm without calibration. |
| `fig.tight_layout()` | Adjusts plot spacing to accommodate labels. |
| `Path(__file__).resolve().parent / "lesson_03.png"` | Builds a path beside the script for the generated figure. |
| `fig.savefig(output_path, dpi=150)` | Saves the rendered figure at 150 dots per inch. A six-inch figure is 900 × 900 output pixels, including axes and margins. These are not the original image's pixels. |
| `plt.show()` | Requests an interactive display window when the environment supports one. |
| `if __name__ == "__main__": main()` | Runs the lesson when the file is executed directly. |

## Scientific limits

The saved PNG includes axes, labels and a rendered version of the TIFF. Do not use it as the input to quantitative analysis: retain the original TIFF array. A larger figure does not reveal new measured detail or improve microscope resolution. Display sampling can also hide fine features, so a small preview is not sufficient for inspecting every source pixel.

Your TIFF already contains measurement lines, numbers and a scale bar embedded in its RGB pixels. Plotting does not remove them or validate their calibration. We are not interpreting brightness as height, chemical composition or particle identity.

## Your one experiment

Before running, predict what happens when you change only `figure_size = 6` to `figure_size = 9`:

1. Does the saved figure become larger or smaller?
2. Does the original array shape change from `(857, 857, 3)`?
3. Does `image[428, 0]` change from `[119, 119, 119]`?

Run again and compare the printed results and saved figure. Explain which changed: the display, the source data, or both. Stop here before introducing any processing.

Reference: [Matplotlib imshow documentation](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.imshow.html).
