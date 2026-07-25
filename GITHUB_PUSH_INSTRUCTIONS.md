# GitHub push instructions

The GitHub-ready repository is already prepared on the RTX 5090 server:

```bash
/root/snowlotus-cellfm/outputs/github_release/SnowLotus-CellFM
```

The repository has Git LFS configured for the two frozen model files:

```text
models/SnowLotus_CellFM_best_annotation.pt
models/SnowLotus_CellFM_best_embedding.pt
```

## Fastest path

1. Create an empty GitHub repository, preferably `ahvsjags/SnowLotus-CellFM`.
2. Add this server deploy key to that repository with write access:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIO2eTUAlmDPil4rcJmm5Gq8jw6xtoubvkkIAX+ZfaflK snowlotus-cellfm-release-20260725
```

3. Run the push from the server:

```bash
cd /root/snowlotus-cellfm/outputs/github_release/SnowLotus-CellFM
git remote remove origin 2>/dev/null || true
git remote add origin git@github.com:ahvsjags/SnowLotus-CellFM.git
GIT_SSH_COMMAND='ssh -i ~/.ssh/snowlotus_cellfm_github_ed25519 -o IdentitiesOnly=yes' git push -u origin main
```

## If using a different repository name

Replace the remote URL before pushing:

```bash
cd /root/snowlotus-cellfm/outputs/github_release/SnowLotus-CellFM
git remote remove origin 2>/dev/null || true
git remote add origin git@github.com:OWNER/REPO.git
GIT_SSH_COMMAND='ssh -i ~/.ssh/snowlotus_cellfm_github_ed25519 -o IdentitiesOnly=yes' git push -u origin main
```

## Verify the release after clone

```bash
git lfs pull
sha256sum -c models/SHA256SUMS.txt
python -m pip install -e ".[singlecell,dev]"
pytest tests/test_snowcell_core.py -q
```

## Current blocker

The server can reach GitHub, but GitHub currently rejects the release deploy key with `Permission denied (publickey)`. The server-side package is otherwise ready to push once `ahvsjags/SnowLotus-CellFM` exists and the deploy key above has write access.
