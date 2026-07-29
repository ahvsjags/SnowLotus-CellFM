# Plant-CellFM v2 Training Artifact

The v2 all-plant continuation checkpoint is retained on the training server at:

`/root/snowlotus_cellfm_v2_4090/best.pt`

SHA256:

`04ba41d35965d8dbbd040d6f80d6672252871492addd97e2b246244b29fbfb5b`

The checkpoint was trained from the current plant-general backbone on the v2 public corpus and evaluated with the cross-species benchmark. It is retained as a research candidate and is not the online service checkpoint because the external leave-dataset, leave-sample, and leave-species metrics did not exceed the current candidate.
