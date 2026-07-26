from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


RUN_ID = "foundation_5090_mlm_public_expansion_continuation_v0_3_seed47_b8_vocabwarm"
CHECKPOINT = Path("outputs") / RUN_ID / "best.pt"
HISTORY = Path("outputs") / RUN_ID / "history.json"
PROGRESS = Path("outputs") / RUN_ID / "progress_latest.json"
DOCS_DIR = Path("github_release_docs")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def best_metrics() -> tuple[int, float]:
    history = read_json(HISTORY)
    epochs = history.get("epochs") or []
    scored = [
        (int(item["epoch"]), float(item["eval_loss"]))
        for item in epochs
        if isinstance(item, dict) and item.get("eval_loss") is not None
    ]
    if not scored:
        return 0, float("nan")
    return min(scored, key=lambda item: item[1])


def active_epoch() -> int:
    progress = read_json(PROGRESS)
    try:
        return int(progress.get("epoch") or 0)
    except Exception:
        return 0


def update_file(path: Path, sha: str, best_epoch: int, best_loss: float, current_epoch: int) -> bool:
    text = path.read_text(encoding="utf-8")
    old = text
    loss = f"{best_loss:.4f}" if best_loss == best_loss else "pending"
    active = current_epoch if current_epoch > 0 else best_epoch + 1

    text = re.sub(
        r"(Best embedding checkpoint:.*?SHA256 `)[0-9a-f]{64}(`)",
        rf"\g<1>{sha}\2",
        text,
    )
    text = re.sub(
        r"(Embedding checkpoint:.*?SHA256 `)[0-9a-f]{64}(`)",
        rf"\g<1>{sha}\2",
        text,
    )
    text = re.sub(
        r"(`SnowLotus_CellFM_best_embedding\.pt` \| [^\n]*?SHA256 `)[0-9a-f]{64}(`)",
        rf"\g<1>{sha}\2",
        text,
    )
    text = re.sub(
        r"Current best evidence: v0\.3 epoch-\d+ evaluation loss [0-9.]+",
        f"Current best evidence: v0.3 epoch-{best_epoch} evaluation loss {loss}",
        text,
    )
    text = re.sub(
        r"v0\.3 epoch-\d+ training is still running",
        f"v0.3 epoch-{active} training is still running",
        text,
    )
    text = re.sub(
        r"Current best v0\.3 epoch-\d+ checkpoint, eval loss [0-9.]+; SHA256 `[0-9a-f]{64}`",
        f"Current best v0.3 epoch-{best_epoch} checkpoint, eval loss {loss}; SHA256 `{sha}`",
        text,
    )
    text = re.sub(
        r"its (first|second|third|fourth|fifth|\d+(?:st|nd|rd|th)) audited evaluation",
        f"its epoch-{best_epoch} audited evaluation",
        text,
    )
    text = re.sub(
        r"active v0\.3 epoch-\d+ run remains in progress",
        f"active v0.3 epoch-{active} run remains in progress",
        text,
    )
    text = re.sub(
        r"current best v0\.3 epoch-\d+ eval loss [0-9.]+, SHA256 `[0-9a-f]{64}`",
        f"current best v0.3 epoch-{best_epoch} eval loss {loss}, SHA256 `{sha}`",
        text,
    )

    if text != old:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    if not CHECKPOINT.exists():
        raise SystemExit(f"missing checkpoint: {CHECKPOINT}")
    sha = sha256_file(CHECKPOINT)
    best_epoch, best_loss = best_metrics()
    current_epoch = active_epoch()
    changed = []
    for filename in [
        "README.md",
        "MODEL_RELEASE_NOTES_v0_2.md",
        "MODEL_RELEASE_NOTES_v0_3.md",
        "EDITOR_HANDOFF.md",
    ]:
        path = DOCS_DIR / filename
        if path.exists() and update_file(path, sha, best_epoch, best_loss, current_epoch):
            changed.append(filename)
    payload = {
        "run_id": RUN_ID,
        "checkpoint": CHECKPOINT.as_posix(),
        "sha256": sha,
        "best_epoch": best_epoch,
        "best_eval_loss": best_loss,
        "active_epoch": current_epoch,
        "changed_docs": changed,
    }
    out = Path("outputs/post_training_release/editor_v0_3_current_best.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
