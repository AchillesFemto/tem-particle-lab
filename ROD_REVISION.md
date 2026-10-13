# Why one rod became several particles

The distance map records how far every foreground pixel lies from background. A long rod has a broad ridge along its centre. Small changes in width produce several local peaks on that ridge. The original method treated those peaks as separate particle seeds. Watershed then placed a boundary inside one physical rod, making its pieces look smaller and changing their shape measurements.

The revision groups existing seeds around peaks with sufficient prominence. Prominence describes the drop needed to connect a peak to an equal or higher peak; it is different from absolute distance to background. See the [official h_maxima documentation](https://scikit-image.org/docs/0.25.x/api/skimage.morphology.html#skimage.morphology.h_maxima).

The important lines in `microscopy/seeds.py` are:

| Python operation | Meaning and scientific purpose |
|---|---|
| `ndimage.label(mask, structure)` | Identify connected foreground components using eight neighbours. Seeds from disconnected objects must never be grouped together. |
| `ndimage.find_objects(components)` | Get a small bounding box for each component so the calculation does not repeatedly process the entire image. |
| `local_distance = np.where(local_mask, distance[box], 0)` | Keep distance values for this component, setting everything else to background. Neighbouring components should not influence its peak grouping. |
| `height = float(local_distance.max()) * prominence_fraction` | Set the required prominence to 25% of this component's largest distance. The fraction is dimensionless; the resulting height is in pixels. This is a development choice, not a universal physical constant. |
| `h_maxima(local_distance, height, footprint=structure)` | Find sufficiently prominent maxima, including the global maximum. Shallow fluctuations along a rod no longer count as independent guides. |
| `ndimage.label(significant, structure)` | Give each connected group of significant maximum pixels a guide number. A plateau is one guide, not one guide per pixel. |
| `watershed(-local_distance, guides, mask=local_mask, ...)` | Divide the component into basins around those guides. Negating distance makes the thick interiors act as valley bottoms. Here watershed groups proposed seeds; final particle separation still runs afterwards. |
| `assignments = basins[local_seeds[:, 0], local_seeds[:, 1]]` | Find which guide basin contains each existing seed. Seeds in the same basin propose the same region. |
| `np.argmax(heights)` | Keep the existing seed deepest inside the foreground for each occupied basin. No new seed is invented, and each previously seeded component retains a seed. |

The threshold is unchanged. Both methods assign exactly the same foreground pixels in our comparisons. Particle boundaries and identities can change, so counts, area, equivalent diameter and eccentricity can change even though the selected foreground does not.

## Fair comparison

Original lesson results and `validation_protocol.json` remain unchanged. The original 800-pixel rod crop has five possible splits before grouping and zero afterwards; two possible merges remain. It cuts particles at the edges, leaving no eligible complete one-to-one matches for size validation.

`compare_rods.py` therefore compares both methods on the same larger crop, rows and columns `[100:2100]`. This excludes the bottom scale-bar region and retains more complete rods. These results are a separate experiment, not a replacement for the original crop's results.

L2-3-B is now development data for the revision. The new image L2-2-D was selected by filename, with revision parameters frozen before it was downloaded or viewed. Both are experimental TEM images from the same [CC BY 4.0 PSDI dataset](https://data-collections.psdi.ac.uk/records/sgvf0-j3g53). Independent specimens have not been established. Neither image has verified physical calibration in this project, so sizes remain in pixels.

From this project folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe compare_rods.py
.\.venv\Scripts\python.exe analyse.py --config analysis_config_rods_v2.json --protocol validation_protocol_rods_v2.json --skip-tracking
```

The comparison report is `results/rod_revision_comparison/report.html`. The accompanying JSON, per-method CSVs and array files preserve the numerical evidence. `example_rod_measurements.json` compares the illustrated manual rod with its predicted pieces and revised region. Equivalent diameter is the diameter of a circle with the same area; it is not rod length. Eccentricity measures elongation, not chemical identity or crystallinity.

For the illustrated manual particle, the actual measurements are:

| Region | Area (pixels) | Equivalent diameter (pixels) | Eccentricity |
|---|---:|---:|---:|
| Manual rod | 98,743 | 354.58 | 0.92186 |
| Original piece 1 | 46,193 | 242.52 | 0.57332 |
| Original piece 2 | 52,133 | 257.64 | 0.68003 |
| Revised whole rod | 98,326 | 353.83 | 0.92166 |

The original pieces falsely suggest two smaller, less elongated particles. The revision restores one region whose geometry closely agrees with this manual annotation. This is one example, not proof of accuracy for every rod.

On the larger common crop, development possible splits fall from 31 to zero, with two possible merges remaining. Fresh-image possible splits fall from 26 to zero, with five possible merges remaining. The revised method has 15 eligible development matches and six eligible fresh-image matches. Their mean absolute equivalent-diameter errors are 0.74% and 1.34%, respectively; these restricted subsets do not validate all particles. Both original methods have zero eligible matches here because of split, merge and border exclusions, so an aggregate before/after size-error comparison is undefined.

The comparison runner rebuilds its report at a fixed location. The general `analyse.py` workflow saves separate timestamped runs. A changed configuration will fail the frozen-protocol check; keep experimental changes in a separate file rather than editing the frozen protocol.

## Limits and small experiment

A distance-map neck is a geometric clue, not proof that two particles are separate. Grouping can merge true touching particles, cannot restore missing seeds, and cannot resolve projected overlap from this image alone. The remaining merge diagnostics need review. Size and shape errors include only complete, unique accepted matches; changing eligibility prevents treating averages as a paired improvement for all particles.

For an experiment, use **only the development rod**, keeping the frozen configuration untouched. Compare `collapse_shallow_peak_seeds(distance, seeds, mask, prominence_fraction=0.25)` with a fraction of `0.50` using copies of the same arrays. Predict before running: will a stricter prominence requirement usually keep more or fewer seeds? Will the threshold mask change? Could two real touching particles become one predicted region? Do not tune on the fresh holdout image and then continue calling it held out.
