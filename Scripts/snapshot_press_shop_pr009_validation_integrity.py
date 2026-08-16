"""Hash protected map/PR-010/handoff files before or after PR-009 verification."""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from press_shop_pr009_in_map_validation_config import TARGET_MAP


parser = argparse.ArgumentParser()
parser.add_argument("phase", choices=("before", "after"))
args = parser.parse_args()

ROOT = Path(__file__).resolve().parents[1]
MATCH = re.search(r"_v(\d+)$", TARGET_MAP, re.IGNORECASE)
VERSION = f"v{MATCH.group(1)}" if MATCH else "unknown"
OUT = ROOT / "Saved" / "Audits" / f"PR009_InMap_{VERSION}" / f"integrity_{args.phase}.json"


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest().upper()


def row(path):
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }


map_path = ROOT / "Content" / (TARGET_MAP.removeprefix("/Game/") + ".umap")
protected = [
    map_path,
    ROOT / "Docs" / "NEW_CHAT_HANDOVER_2026-08-03.md",
    ROOT / "Docs" / "PROJECT_HANDOFF.md",
    ROOT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_PR004Accepted_v006.umap",
]
protected += sorted((ROOT / "Content" / "LineBoss" / "Maps").glob("*PR004*v00[7-9].umap"))
protected += sorted((ROOT / "Content" / "LineBoss" / "Maps").glob("*PR004*v010.umap"))
protected = [path for path in protected if path.exists()]

pr010 = sorted(path for path in ROOT.rglob("*") if path.is_file()
               and "PR010" in path.relative_to(ROOT).as_posix().upper()
               and "Saved/Audits/PR009_InMap_" not in path.relative_to(ROOT).as_posix())

payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-validation-integrity/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "phase": args.phase,
    "target_map": TARGET_MAP,
    "protected_files": [row(path) for path in protected],
    "pr010_file_count": len(pr010),
    "pr010_files": [row(path) for path in pr010],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"phase": args.phase, "protected": len(protected), "pr010": len(pr010)}, indent=2))

