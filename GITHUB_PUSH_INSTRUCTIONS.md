# GitHub release status

The editor-v0.3 repository has been created on GitHub:

https://github.com/ahvsjags/SnowLotus-CellFM

Current visibility: private.

Main branch: current release source tree plus publication-status documentation updates.

Release tag:

https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/editor-v0.3

## Uploaded release assets

- `SnowLotus-CellFM_editor-v0.3_submit-now.zip`
- `snowlotus-cellfm-editor-v0.3-source-metadata.tar.gz`
- `snowlotus-cellfm-editor-v0.3-manuscript.tar.gz`
- `snowlotus-cellfm-editor-v0.3-full-with-models.tar.gz`

The full model archive should be checked against the GitHub-reported release-asset digest and the top-level `ARCHIVE_SHA256SUMS.txt` distributed with the editor package.

It contains the current frozen best embedding checkpoint:

`649448b2071816856cd5f92a43985c6d865d115d45d91274db94cb5f9348d577`

## Verify the release after clone

```bash
python -m pip install -e ".[singlecell,dev]"
pytest tests/test_snowcell_core.py -q
```

After downloading the full model archive, verify:

```bash
tar -xzf snowlotus-cellfm-editor-v0.3-full-with-models.tar.gz
cd SnowLotus-CellFM/models
sha256sum -c SHA256SUMS.txt
```

## Submission note

Because the repository is private, grant editor/reviewer access or switch the repository visibility to public before using the GitHub URL as a reviewer-facing link.
