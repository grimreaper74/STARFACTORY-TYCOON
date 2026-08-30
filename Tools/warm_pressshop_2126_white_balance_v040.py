"""Apply a warm neutral white balance to the candidate's approved lighting rig."""

import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_white_balance_v040.json"
TAG = unreal.Name("LB.PressShop.2126.WhiteBalance.v040")


def sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("White-balance v040 already applied")

volume = actors.get("2126 | fixed Steam exposure")
if not isinstance(volume, unreal.PostProcessVolume):
    raise RuntimeError("Fixed exposure volume missing")
settings = volume.get_editor_property("settings")
settings.override_white_temp = True
settings.white_temp = 7000.0
settings.override_white_tint = True
settings.white_tint = 0.0
volume.set_editor_property("settings", settings)
volume.tags = list(volume.tags) + [TAG]

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate map")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__WARM_NEUTRAL_WHITE_BALANCE_APPLIED_TO_CANDIDATE",
    "white_temp_kelvin": 7000,
    "white_tint": 0.0,
    "b_stylized_light_counts_and_intensities_changed": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_WHITE_BALANCE_V040_PASS")
