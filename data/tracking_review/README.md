# Human tracking review

Run review_tracking.py from the project folder and click a consistent centre of the prominent particle in the zoomed patch. Predicted trajectories are hidden. Three independently entered clicks per selected frame measure click repeatability; they are not three independent images or annotators.

The tool writes manual_centres.csv and a movie fingerprint in manual_centres.json. Before that review, the automatic report explicitly marks human validation pending. A blank review_template.csv is provided for external entry; do not fill it using the predicted track.

Validation compares changes relative to frame zero, avoiding a fixed offset between a template anchor and a visual area centre. This does not remove changing anchor bias or errors in the first reference point. Multiple annotators, stationary fiducials, and independently justified localization models would strengthen uncertainty assessment.
