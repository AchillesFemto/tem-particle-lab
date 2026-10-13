# Lesson 23: find candidate starting points

Today we learn **local maxima**: positions whose distance-map value is at least as high as the values in a surrounding window. We will use them as candidate seeds for separating touching particles in the next lesson.

## Why look for peaks?

Thresholding can merge touching particles into one foreground region. The distance map may retain a high-distance interior for each rounded particle. Locating those high areas gives proposed starting points from which a later segmentation can grow separate regions.

A seed is simply a selected pixel coordinate. It is a hypothesis about an interior location. It is not automatically a physical centre or a detected particle.

## Run

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_23.py
```

No new packages are needed. The script prints candidate coordinates and saves `lesson_23.png`. Open the PNG if no plot window appears.

## Find the highest nearby value

```python
nearby_max = ndimage.maximum_filter(distance, size=window_size,
                                    mode="constant", cval=0)
peaks = (distance == nearby_max) & (distance >= min_height)
```

The maximum filter solves a local comparison problem: at every pixel, it finds the largest distance in a surrounding square window. It operates on the distance map, not on TEM intensities. It does not average or smooth the image.

With `window_size = 41`, the window extends 20 pixels in each direction from its centre. A pixel remains a candidate if its own value equals the window maximum. `==` means equal, whereas `=` assigns a value.

For example, among nearby distances 12, 25 and 18, the position with value 25 is a peak if no larger value occurs elsewhere in its window. Ties can leave more than one candidate.

The second condition requires distance at least `min_height = 20.0` pixels. `&` combines the two Boolean conditions element by element. The parentheses keep each comparison separate. This cutoff suppresses low-distance peaks in small or thin regions. It can also reject genuine small particles; it is a teaching parameter, not a validated minimum particle size.

`mode="constant", cval=0` supplies zero when the comparison window extends outside the array. We subsequently exclude a border band so retained peaks use a fully observed window. This boundary convention does not add background pixels to the distance-transform input.

## Deal with equal-height plateaus

```python
labels, count = ndimage.label(peaks, structure=np.ones((3, 3), dtype=bool))
positions = ndimage.maximum_position(distance, labels, range(1, count + 1))
```

Several adjacent pixels can share a maximum, forming a plateau. We group connected peak pixels using the connected-region concept from earlier lessons. The 3 by 3 structure includes diagonal neighbours, giving eight-neighbour connectivity.

Each group receives an integer label. `count` is the number of peak groups, not the number of foreground particles. `maximum_position` chooses one maximum-valued pixel from each specified label. `range(1, count + 1)` includes labels 1 through count, excluding background label zero.

When several pixels tie within a plateau, the chosen position is a computational representative. Do not interpret its exact coordinate as a precisely measured physical centre. Disconnected tied maxima remain separate groups, even if very close together. This algorithm does not guarantee a minimum Euclidean distance between seeds.

## Read the result

The starting settings produce **16 candidate seeds**. The figure shows red rings on the distance map and on the same TEM crop. Coordinates printed in the terminal are `(row, column)` within the crop. Add 300 to each coordinate to locate the point in the full source image.

Two candidates, near crop coordinates `(563, 432)` and `(565, 432)`, are only two rows apart. Inspect them in the image. Such duplicate candidates could cause excessive splitting if each is used to start a separate region. Other particles can lack seeds because they are partial, thin, small, or suppressed by a higher nearby peak.

This stage proposes seeds. It has not separated the mask, measured particle sizes, or established a particle count.

## Other important lines

| Code | Explanation |
| --- | --- |
| `from pathlib import Path` | Imports file-path construction. |
| NumPy, Matplotlib, Pillow and SciPy imports | Supply arrays, plotting, PNG reading and local image operations. |
| `from lesson_22 import foreground_distance` | Reuses the distance-map function without running Lesson 22. |
| `def distance_peak_seeds(...)` | Defines a reusable function with default window size and minimum height. |
| Distance shape, finite and nonnegative checks | Require a two-dimensional array with valid distances. `np.isfinite` rejects NaN/infinity; `np.all` requires every value to pass. |
| `isinstance(window_size, int)` | Requires an integer window size. |
| `window_size % 2 == 0` | Detects even sizes; `%` gives the remainder after division. We require an odd size so the window has a central pixel. |
| The minimum-height check | Requires a finite positive height, excluding background peaks. |
| `raise ValueError(...)` | Stops with a clear explanation when an input assumption fails. |
| `border = window_size // 2` | Calculates the half-width using integer division. |
| `peaks[:border, :] = False` | Removes peak candidates in the top border band. |
| `peaks[-border:, :] = False` | Removes the bottom band; negative indices count from the end. |
| The corresponding column slices | Remove left and right border bands. They change only the peak-candidate mask. |
| `if count == 0: return np.empty((0, 2), dtype=int)` | Returns a consistent two-column coordinate array if there are no seeds. |
| `np.asarray(positions, dtype=int)` | Converts coordinate tuples into an integer array, one row per seed. |
| `def main():` | Groups the lesson's execution steps. |
| `window_size = 41`, `threshold = 140`, `min_height = 20.0` | Set the comparison width, foreground threshold and minimum distance. Only window_size changes in the experiment. |
| `Path(__file__).resolve().parent` and joined path components | Locate the downloaded image relative to the project. |
| `with Image.open(...)`, then `np.array(source)` | Read stored PNG pixels into an array and close the file. |
| The image ndim/dtype check | Requires the expected two-dimensional uint8 grayscale image. |
| `image[300:1100, 300:1100]` | Keeps the same 800 by 800 crop as previous lessons. |
| `candidate = roi < threshold` | Selects dark pixels strictly below the cutoff. This approximates particles against the lighter background. |
| `distance = foreground_distance(candidate)` | Computes distance to background in pixels. |
| `seeds = distance_peak_seeds(...)` | Finds candidate seed coordinates using the chosen parameters. |
| `len(seeds)`, `print(...)` | Report the number of proposed points and their coordinates. |
| `plt.subplots(1, 2, ..., layout="constrained")` | Creates two panels with space for labels. |
| `imshow(distance, ...)`, `imshow(roi, ...)` | Display distances with a fixed colour scale and original intensities with fixed grayscale limits. |
| `interpolation="nearest"` | Avoids smoothing displayed pixels. |
| `seeds[:, 1]`, `seeds[:, 0]` | Select columns for horizontal positions and rows for vertical positions. NumPy row/column order differs from plotting x/y order. |
| `ax.scatter(..., facecolors="none", edgecolors="red")` | Draws hollow red rings so the image beneath remains visible. |
| Titles, axis labels, `legend` and `suptitle` | Identify arrays, coordinates and the meaning of the rings. |
| `fig.savefig(..., dpi=150)` | Saves a comparison figure without altering scientific arrays. |
| `plt.show()` | Requests a plot window. |
| `if __name__ == "__main__": main()` | Executes the lesson directly while allowing function reuse. |

## Scientific assumptions

Distance peaks depend on the threshold boundary, including its holes, bridges and errors. Irregular objects can have several maxima. Overlapping objects can have one maximum. Local peaks alone cannot prove particle identity.

The comparison window is a square with dimensions in pixels. Its suitable size depends on image sampling and object dimensions. A higher nearby peak can suppress a lower one even across different foreground regions; this lesson compares the distance map without restricting comparisons to individual components.

The excluded border band grows with window_size. Changes in seed count can therefore arise from both stronger local competition and border exclusion. Partial particles and missing background outside the crop can influence distances even for retained points; the border rule does not establish complete particles.

A larger centred window cannot add peak pixels before grouping, but removing pixels can fragment a plateau. Therefore a simple monotonic claim about the number of connected peak groups is not guaranteed. Nor does this method guarantee a prescribed minimum separation between tied peaks.

We have no calibrated physical centre positions or particle counts yet. Particle-level validation is still needed after separation. Source provenance is in the [sample README](data/public_tem/README.md).

References: SciPy [maximum_filter](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.ndimage.maximum_filter.html) and [maximum_position](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.ndimage.maximum_position.html).

## Your one experiment

Change only `window_size = 41` to `window_size = 81`. Predict:

1. Will each point be compared with a smaller or larger neighbourhood?
2. Will the underlying distance map change?
3. Must every particle have exactly one seed after this change?

Run and compare the red rings. Explain any lost candidates using nearby higher peaks or the wider excluded border band. Equal-height disconnected peaks can survive even in a larger window.
