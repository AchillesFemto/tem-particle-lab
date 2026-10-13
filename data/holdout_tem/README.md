# Held-out experimental TEM images

L2-3-B.png and L3-elite-3-A.png were selected as additional experimental validation images from the same [PSDI record](https://data-collections.psdi.ac.uk/records/sgvf0-j3g53). Attribution: Andrew Stewart and Natalia Da Silva De Sa; CC BY 4.0. Full experimental provenance is in ../public_tem/README.md.

Image bytes were extracted unchanged from images.zip and verified against individual ZIP CRC32 checks. Corresponding instance JSONs are subsets/reformats of the published validation annotations, retaining source IDs and metadata. SHA256SUMS.txt identifies the local inputs.

Segmentation and evaluation settings were frozen in ../../validation_protocol.json before these images were inspected. New images are independent of prior tuning, but the dataset does not establish that these are independently sampled specimens. They share the original data source. No physical pixel calibration has been verified for these two images; measurements remain in pixels.

Once these results are used to change the method, these images become development data for that changed method. Reserve another untouched set for its subsequent validation.
