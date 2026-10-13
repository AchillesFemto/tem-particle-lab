# Experimental gold-nanoparticle TEM sample

Source: [PSDI dataset record, version 2](https://data-collections.psdi.ac.uk/records/sgvf0-j3g53), published 30 April 2026. Retrieved 7 October 2026.

Dataset title: Testing, Training and Validation Synthetic Dataset of Transmission Electron Microscopy (TEM) Images of Gold Nano-particles for Segmentation.

Creators: Andrew Stewart and Natalia Da Silva De Sa. The source describes the validation images as experimental TEM images from Professor Lee Cronin, University of Glasgow, associated with https://doi.org/10.1038/s41467-020-16501-4. Although the dataset title mentions synthetic images, this sample comes from its **experimental validation** subset.

License: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). Retain this attribution and identify any future modifications when sharing derived work.

## Files

- `L1-1-D.png`: unchanged image bytes extracted from `images.zip`, member `val/L1-1-D.png`.
- `L1-1-D_mask.png`: unchanged reference mask extracted from `val_binary_masks.zip`, member `binary_masks/L1-1-D_mask.png`. Values are 0 (background) and 255 (particle foreground).
- `annotations_L1-1-D.json`: a subset of `instances_annotations_val.json`, retaining the selected image, its annotations, and source category/information fields. This JSON was reformatted and other images and their annotations were removed.
- `SHA256SUMS.txt`: checksums of these local files.

The mask archive and original annotation JSON were checked against the repository's published MD5 checksums. The selected image was extracted using HTTP byte ranges and checked against its ZIP CRC32. The entire 926 MB image archive was not downloaded, so its full-archive MD5 was not checked.

Both PNGs have shape `(2362, 2362)` and dtype `uint8`: one grayscale value per pixel. The image includes a visible 100 nm scale bar near its bottom edge.

## Why this helps our lessons

The image and corresponding manual annotation let us practise intensity inspection, thresholding, connected regions, and agreement with a human reference. No machine learning is needed. The mask is a reference for comparison, not a processed TEM intensity image.

## Scientific limits

- These are published PNG exports; do not assume they contain raw detector intensities or full acquisition metadata.
- Later lessons measured the visible 100 nm scale bar as 865 pixels, giving an image-derived calibration of 100/865 nm per pixel for this image only. This is not an independently certified instrument calibration; do not transfer it to other images. The other rod examples remain uncalibrated and use pixels.
- Exclude the bottom scale bar/text and other image-edge markings from intensity and segmentation analysis. They are graphics, not specimen structures, and obscure some particle pixels.
- Manual annotations are useful references, but their boundaries can be approximate. Agreement with this mask does not prove exact physical particle boundaries.
- Touching particles can merge into one connected foreground region. A binary mask does not preserve separate particle identities; the JSON contains individual annotations.
- Particles at image borders may be incomplete. This single field of view cannot establish a representative size distribution for the whole material.

The existing lessons continue using their original inputs. This sample is ready for a future lesson, one concept at a time.
