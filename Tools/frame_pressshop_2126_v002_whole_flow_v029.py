"""Add one management overview camera for the full reused-plus-Meshy flow."""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_whole_flow_camera_v029.json"
TAG = unreal.Name("LB.PressShop.2126.v002.WholeFlowCamera.v029")
LABEL = "CAM v002 | full coil-to-outfeed management overview"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)))


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if LABEL in actors or any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v029 overview already applied")
source = unreal.Vector(-18800.0, -20000.0, 14000.0)
target = unreal.Vector(1000.0, 0.0, 420.0)
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CineCameraActor, source, aim(source, target))
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Could not create overview camera")
camera.set_actor_label(LABEL)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 38.0)
camera.tags = [TAG, unreal.Name("LB.ManagementCamera.WholeProcess")]
actual = camera.get_actor_rotation()
if abs(actual.pitch - aim(source, target).pitch) > 0.01 or abs(actual.yaw - aim(source, target).yaw) > 0.01:
    raise RuntimeError("Overview camera orientation did not apply")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate map")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__FULL_PROCESS_MANAGEMENT_CAMERA_ADDED",
    "candidate_map": MAP,
    "camera": LABEL,
    "source_cm": [source.x, source.y, source.z],
    "target_cm": [target.x, target.y, target.z],
    "focal_length_mm": 38.0,
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_WHOLE_FLOW_CAMERA_V029_PASS")
