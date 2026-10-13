# Source data licences

Code and data must be licensed separately. Retain each source's attribution and licence when sharing original inputs or derived media/results. This record does not assign a new licence to the project's code.

## Public single-image TEM sample

- Creators: Andrew Stewart and Natalia Da Silva De Sa.
- Dataset: Testing, Training and Validation Synthetic Dataset of Transmission Electron Microscopy (TEM) Images of Gold Nano-particles for Segmentation, PSDI record version 2.
- Source: https://data-collections.psdi.ac.uk/records/sgvf0-j3g53
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0).
- Experimental validation image and its manual annotations are used; the source's synthetic training images are not used.
- The selected annotation JSON is a documented subset/reformat. Image and mask bytes were extracted unchanged.
- See data/public_tem/README.md for experimental source attribution, extraction and scientific limitations.

## Public experimental movie and publication figure

- Citation: Kang et al., Real-space imaging of nanoparticle transport and interaction dynamics by graphene liquid cell TEM, Science Advances 7, eabi5419 (2021).
- DOI: https://doi.org/10.1126/sciadv.abi5419
- Licence: Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).
- Movie S1 is the source's drift-corrected supplementary movie; decoded PNGs derive from that compressed/processed recording.
- The labelled coalescence illustration is a crop from the published Figure 3A, not a raw detector sequence.
- See data/public_tem_series/kang_2021/README.md and provenance.json for extraction records, frame indices and processing distinctions.

## Personal microscopy input

The user's PG.tif appears in early lessons but is not part of this portable archive. Do not assume rights to publish personal research data based on the licences of these public examples.

The additional images in `data/holdout_tem/` and `data/rod_holdout_tem/` come from the same CC BY 4.0 PSDI source. Image bytes are unchanged; annotation JSONs are documented subsets/reformats. See their README and checksums. Tracking review records contain user-entered observations and are excluded from the public portable archive when present.
