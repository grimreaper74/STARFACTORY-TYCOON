"""Correct transfer-carriage scale and restore a below-rail management camera."""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_transfer_scale_v031.json"
TAG = unreal.Name("LB.PressShop.2126.v003.TransferScaleRepair.v031")


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
    raise RuntimeError("v031 repair already applied")

carriages = []
for index in range(1, 4):
    label = "2126 v003 | transfer carriage %02d" % index
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Transfer carriage missing: " + label)
    location = actor.get_actor_location()
    actor.set_actor_location(unreal.Vector(location.x, 0.0, 1080.0), False, False)
    # A 3.6 x 4.0 x 0.9 m travel head, not the mistaken 28.5m yellow panel.
    actor.set_actor_scale3d(unreal.Vector(3.6, 4.0, 0.9))
    actor.tags = list(actor.tags) + [TAG]
    carriages.append({"actor": label, "dimensions_cm": [360.0, 400.0, 90.0]})
for label in ("2126 v003 | transfer rail operator", "2126 v003 | transfer rail service"):
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Transfer rail missing: " + label)
    location = actor.get_actor_location()
    actor.set_actor_location(unreal.Vector(location.x, location.y, 1100.0), False, False)
    actor.tags = list(actor.tags) + [TAG]

camera = actors.get("CAM v003 | compact press hero")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Hero camera missing")
source = unreal.Vector(-2400.0, -10800.0, 820.0)
target = unreal.Vector(550.0, 0.0, 410.0)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(aim(source, target), False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 50.0)
camera.tags = list(camera.tags) + [TAG]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, camera.get_actor_rotation())

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v003 repair")
protected_after, v002_after = digest(PROTECTED), digest(V002)
if protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Protected evidence map changed during v031")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__TRANSFER_HEADS_RESCALED_AND_BELOW_RAIL_CAMERA_SET",
    "candidate_map": MAP,
    "carriages": carriages,
    "camera": {"source_cm": [source.x, source.y, source.z], "target_cm": [target.x, target.y, target.z], "focal_length_mm": 50.0},
    "roof_created": False,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_TRANSFER_SCALE_REPAIR_V031_PASS")
