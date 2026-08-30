"""Reject the obstructive transfer experiment and restore the clean compact press view."""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_transfer_rejected_v032.json"
TAG = unreal.Name("LB.PressShop.2126.v003.TransferRejected.v032")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)))


if not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Protected evidence map missing")
protected_before, v002_before = digest(PROTECTED), digest(V002)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load compact v003 map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v032 transfer rejection already applied")
hidden = []
for label in (
    "2126 v003 | transfer rail operator",
    "2126 v003 | transfer rail service",
    "2126 v003 | transfer carriage 01",
    "2126 v003 | transfer carriage 02",
    "2126 v003 | transfer carriage 03",
):
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Transfer test component missing: " + label)
    actor.static_mesh_component.set_visibility(False, True)
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Automation.RejectedObstructiveTransfer")]
    hidden.append(label)
camera = actors.get("CAM v003 | compact press hero")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Hero camera missing")
source = unreal.Vector(-1818.0, -10500.0, 5200.0)
target = unreal.Vector(1010.0, 0.0, 380.0)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(aim(source, target), False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 54.0)
camera.tags = list(camera.tags) + [TAG]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, camera.get_actor_rotation())
if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v003 transfer rejection")
protected_after, v002_after = digest(PROTECTED), digest(V002)
if protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Protected evidence map changed during v032")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__OBSTRUCTIVE_TRANSFER_EXPERIMENT_REJECTED",
    "candidate_map": MAP,
    "hidden_candidate_only_components": hidden,
    "camera": {"source_cm": [source.x, source.y, source.z], "target_cm": [target.x, target.y, target.z], "focal_length_mm": 54.0},
    "roof_created": False,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_TRANSFER_REJECTED_V032_PASS")
