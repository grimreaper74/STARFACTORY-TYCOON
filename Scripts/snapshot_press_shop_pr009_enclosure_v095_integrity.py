"""Hash protected Press Shop, source, robot and PR-010 scope around v095 final gates."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from press_shop_pr009_enclosure_release_v095_config import TARGET_MAP


parser = argparse.ArgumentParser()
parser.add_argument("phase", choices=("gate_before", "gate_after"))
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Saved/Audits/PR009_InMap_v095" / f"integrity_{args.phase}.json"


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest().upper()


def row(path):
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}


def map_file(asset_path):
    return ROOT / "Content" / (asset_path.removeprefix("/Game/") + ".umap")


protected = [
    map_file("/Game/LineBoss/Maps/LB_PressShop_PR009TransferGuideCollisionCandidate_v089"),
    map_file("/Game/LineBoss/Maps/LB_PressShop_PR009EnclosurePilotCandidate_v094"),
    map_file(TARGET_MAP),
    ROOT / "Content/LineBoss/Maps/LB_PressShop_PR004Accepted_v006.umap",
]
protected += sorted((ROOT / "Content/LineBoss/Maps").glob("*PR004*v00[7-9].umap"))
protected += sorted((ROOT / "Content/LineBoss/Maps").glob("*PR004*v010.umap"))
source = sorted(path for path in (ROOT / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002").rglob("*") if path.is_file())
source += sorted(path for path in (ROOT / "SourceAssets/SharedSystems/AutomatedMachineEnclosure/Candidate_v002").rglob("*") if path.is_file())
robots = sorted(path for path in ROOT.rglob("*") if path.is_file() and any(
    token in path.relative_to(ROOT).as_posix().upper() for token in ("/MR01/", "/CR01/", "/RP01/")))
pr010 = sorted(path for path in ROOT.rglob("*") if path.is_file()
               and "PR010" in path.relative_to(ROOT).as_posix().upper()
               and "Saved/Audits/PR009_InMap_v095" not in path.relative_to(ROOT).as_posix())

payload = {
    "$schema": "cairnwell/audit/pr009-enclosure-v095-integrity/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "phase": args.phase,
    "target_map": TARGET_MAP,
    "protected_files": [row(path) for path in protected if path.exists()],
    "source_files": [row(path) for path in source],
    "robot_files": [row(path) for path in robots],
    "pr010_files": [row(path) for path in pr010],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"phase": args.phase, "protected": len(payload["protected_files"]),
                  "source": len(source), "robots": len(robots), "pr010": len(pr010)}, indent=2))
