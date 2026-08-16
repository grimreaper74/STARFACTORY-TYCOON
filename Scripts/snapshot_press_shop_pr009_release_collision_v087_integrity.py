"""Hash immutable parent/protected scope and v087 across build/validation phases."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from press_shop_pr009_release_collision_v087_config import PARENT_MAP, TARGET_MAP

parser = argparse.ArgumentParser()
parser.add_argument("phase", choices=("parent_before_build", "validation_before", "validation_after"))
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
out = root / "Saved/Audits/PR009_InMap_v087" / f"integrity_{args.phase}.json"

def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest().upper()

def row(path):
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}

def map_file(asset_path):
    return root / "Content" / (asset_path.removeprefix("/Game/") + ".umap")

protected = [
    map_file(PARENT_MAP),
    root / "Docs/NEW_CHAT_HANDOVER_2026-08-03.md",
    root / "Docs/PROJECT_HANDOFF.md",
    root / "Content/LineBoss/Maps/LB_PressShop_PR004Accepted_v006.umap",
]
protected += sorted((root / "Content/LineBoss/Maps").glob("*PR004*v00[7-9].umap"))
protected += sorted((root / "Content/LineBoss/Maps").glob("*PR004*v010.umap"))
source_staging = sorted(path for path in (root / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002").rglob("*") if path.is_file())
robot_files = sorted(path for path in root.rglob("*") if path.is_file() and any(
    token in path.relative_to(root).as_posix().upper() for token in ("/MR01/", "/CR01/", "/RP01/")))
pr010 = sorted(path for path in root.rglob("*") if path.is_file()
               and "PR010" in path.relative_to(root).as_posix().upper()
               and "Saved/Audits/PR009_InMap_v087" not in path.relative_to(root).as_posix())
target = map_file(TARGET_MAP)
payload = {
    "$schema": "cairnwell/audit/pr009-v087-integrity/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "phase": args.phase,
    "parent_map": PARENT_MAP,
    "target_map": TARGET_MAP,
    "protected_files": [row(path) for path in protected if path.exists()],
    "source_staging_files": [row(path) for path in source_staging],
    "robot_files": [row(path) for path in robot_files],
    "pr010_files": [row(path) for path in pr010],
    "target_map_file": row(target) if target.exists() else None,
    "promotion_authorized": False,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"phase": args.phase, "protected": len(payload["protected_files"]),
                  "source_staging": len(source_staging), "robot": len(robot_files),
                  "pr010": len(pr010), "target_exists": target.exists()}, indent=2))
