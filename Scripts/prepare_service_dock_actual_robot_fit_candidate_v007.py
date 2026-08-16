"""Prepare the isolated v007 fit map without opening it in this process."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v005"
TARGET = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v007"
SOURCE_FILE = ROOT / "Content/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v005.umap"
TARGET_FILE = ROOT / "Content/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v007.umap"
V253_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253.umap"
OUT = ROOT / "Saved/Audits/SupportRobots/service_dock_actual_robot_fit_prepare_v007.json"
LIB = unreal.EditorAssetLibrary


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


if LIB.does_asset_exist(TARGET) or TARGET_FILE.exists():
    raise RuntimeError("Refusing to overwrite preserved v007 fit candidate")
source_before = sha256(SOURCE_FILE)
v253_before = sha256(V253_FILE)
if not LIB.duplicate_asset(SOURCE, TARGET):
    raise RuntimeError("Could not duplicate retained v005 source to v007")
if not LIB.save_asset(TARGET, only_if_is_dirty=False):
    raise RuntimeError("Could not save duplicated v007 package")
if not TARGET_FILE.exists():
    raise RuntimeError("v007 package was not written")
source_after = sha256(SOURCE_FILE)
v253_after = sha256(V253_FILE)
if source_after != source_before or v253_after != v253_before:
    raise RuntimeError("A protected source changed during prepare-only duplication")

payload = {
    "$schema": "cairnwell/audit/service-dock-actual-robot-fit-prepare-v007/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_V007_DUPLICATED_WITHOUT_OPENING__BUILD_PROCESS_REQUIRED",
    "source_map": SOURCE,
    "target_map": TARGET,
    "target_sha256_after_duplicate": sha256(TARGET_FILE),
    "source_v005_sha256_before": source_before,
    "source_v005_sha256_after": source_after,
    "protected_v253_sha256_before": v253_before,
    "protected_v253_sha256_after": v253_after,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_SERVICE_DOCK_FIT_V007_PREPARE_PASS")
