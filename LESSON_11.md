# Lesson 11: connected regions and integer labels

## What problem does labeling solve?

A threshold mask says which pixels are selected, but not which selected pixels belong together. Connected-component labeling groups selected pixels that can be reached from one another through neighboring selected pixels. Each group receives an integer ID.

This is a computational definition of a region, not proof of a physical particle. We first use three invented pixels so you can check the result yourself.

## Run

In PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe lesson_11.py
```

SciPy is already installed. This lesson prints results only; no plot window is expected. It does not write to the original TIFF or change earlier lesson scripts.

## What counts as a neighbor?

In a 2D array there are two common rules:

- **4-connected:** up, down, left and right. Touching only at a corner does not connect pixels.
- **8-connected:** the same four directions plus all four diagonals. Corner contact counts.

We specify the rule using:

```python
connectivity = 1
structure = generate_binary_structure(2, connectivity)
```

The first `2` means two spatial dimensions. In this function, connectivity `1` generates the 4-neighbor rule and connectivity `2` generates the 8-neighbor rule. The setting itself is not the number of neighbors.

`structure` is a small Boolean array describing allowed connections. It is not a smoothing filter and does not add pixels to the mask.

## A small example

The invented mask contains three selected pixels:

```text
1 0 0
0 1 0
0 0 1
```

Here 1 represents True and 0 represents False. With the 4-neighbor rule, these pixels are separate because they touch only diagonally.

```python
example_labels, example_count = label(example, structure=structure)
```

`label` returns two results: a label array and a region count. For the default example they are:

```text
1 0 0
0 2 0
0 0 3

Region count: 3
```

Label 0 means unselected. Label 1 identifies the first connected region, 2 the second and so on. These numbers are IDs, not intensities, sizes, importance rankings or physical identities. A region may contain one selected pixel or many. The number of selected pixels and the number of regions answer different questions.

For the experiment, predict how allowing diagonal connections changes this grouping.

## Apply the same idea to your TIFF

We recreate the same ROI and RGB equality check used earlier. We then use the fixed rule `mask = gray < 80`, reproducing Lesson 7's original dark-pixel selection. We intentionally hold this mask fixed; smoothing and threshold changes would change the input and obscure the effect of connectivity. Settings in other scripts do not automatically transfer here.

```python
labels, region_count = label(mask, structure=structure)
```

The output label array has the same shape as the mask. All originally unselected positions remain zero; selected positions get positive IDs. Calling `label` this way does not modify the input mask or image.

```python
np.array_equal(labels > 0, mask)
```

`labels > 0` asks which positions have positive region IDs. Comparing it to `mask` checks that exactly the same pixels are selected after grouping.

## Important code lines

| Code | Meaning |
| --- | --- |
| `from pathlib import Path` | Imports the path tool. |
| `import numpy as np` | Imports array creation, equality checks and counting. |
| `from scipy.ndimage import generate_binary_structure, label` | Imports tools for defining neighbors and grouping connected pixels. |
| `import tifffile` | Imports the TIFF reader. |
| `def main():` | Groups the lesson into a function. |
| `connectivity`, `generate_binary_structure(...)` | Set the neighborhood rule described above. |
| `np.array([...], dtype=bool)` | Creates the small synthetic mask, converting 1 to True and 0 to False. |
| `example_labels, example_count = label(...)` | Groups the synthetic mask and assigns both returned results to names. |
| `print(example_labels)` | Prints the integer IDs so you can inspect the grouping. |
| `np.count_nonzero(example)` | Counts selected pixels, not groups. |
| `image_path = Path(r"...")` | Identifies the TIFF; raw-string notation preserves Windows backslashes. |
| `with tifffile.TiffFile(image_path) as tif:` | Opens the TIFF for reading and closes it after the indented block. |
| `image = tif.series[0].asarray()` | Reads the first series. |
| `roi = image[100:300, 100:400, :].copy()` | Selects the original teaching rectangle and all RGB components. |
| `red`, `green`, `blue` assignments | Read each color component for validation. |
| `if not (...)`, `raise ValueError(...)` | Stop if all three component planes are not identical. |
| `gray = green.copy()` | Creates the verified grayscale array. |
| `threshold = 80`, `mask = gray < threshold` | Select strictly darker-than-80 pixels without changing the grayscale image. |
| `labels, region_count = label(...)` | Groups this mask using the chosen neighborhood rule. |
| `np.count_nonzero(mask)` | Reports the number of selected real-image pixels. |
| `labels.shape`, `labels.dtype` | Report dimensions and integer storage type of the region-ID array. Labels should not be converted to uint8: there can be more than 255 regions. |
| `np.array_equal(labels > 0, mask)` | Confirms that labeling preserved the selected locations. |
| `print("\nREAL ROI ...")` | Starts a clearly separated section; `\n` adds a new line. |
| Other `print(...)` statements | Display settings and results without modifying them. |
| `if __name__ == "__main__": main()` | Runs the lesson when executed directly. |

## Scientific meaning and limits

Our threshold mask contains many scattered pixels and fragments. One particle may produce several disconnected regions; separate particles can become one region if a selected bridge joins them. A connected region can also be a dark boundary or artifact. Thus, do not report `region_count` as a particle count or use it as a validated size-distribution input.

The connectivity convention changes what counts as one region. It must be documented and justified in future analysis. Neither rule is universally correct. Label IDs are not stable identifiers for tracking structures across parameter changes or images.

ROI boundaries can cut objects or remove connecting paths. The current crop is a teaching selection, not a representative sampling plan, and physical calibration remains unresolved.

With the same mask, permitting diagonal paths can merge groups or leave them unchanged; it cannot split an existing 4-connected group. It also cannot increase the number of selected pixels.

## Your one experiment

Change only `connectivity = 1` to `connectivity = 2`. Before running, predict:

1. How many regions will the three diagonal synthetic pixels form?
2. Will their selected-pixel count change?
3. For the unchanged real mask, can allowing diagonal connections increase the number of regions?

Run and inspect the example label array, both region counts and the selected-pixel checks. Explain the result in terms of permitted connections, not a change in the specimen.

Reference: [SciPy labeling documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.label.html).
