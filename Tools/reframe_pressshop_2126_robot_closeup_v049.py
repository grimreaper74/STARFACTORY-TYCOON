"""Reframe the validated robot tender as a machine-scale foreground story."""

import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_robot_closeup_v049.json"
TAG = unreal.Name("LB.PressShop.2126.RobotCloseup.v049")
LABEL = "CAM | 2126 outbound autonomy"
SOURCE = (-800.0, -3600.0, 150.0)
TARGET = (-200.0, -2150.0, 115.0)
FOCAL = 70.0


def sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x-source.x, target.y-source.y, target.z-source.z
    return unreal.Rotator(math.degrees(math.atan2(dz, math.sqrt(dx*dx+dy*dy))), math.degrees(math.atan2(dy, dx)), 0.0)


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Robot closeup v049 already applied")
camera = actors.get(LABEL)
robot = actors.get("ROBOT | S04 | pierce handling robot")
if not isinstance(camera, unreal.CineCameraActor) or not isinstance(robot, unreal.StaticMeshActor):
    raise RuntimeError("Required camera or S04 robot missing")
if not robot.static_mesh_component.is_visible():
    raise RuntimeError("Robot is not render-visible")
source, target = unreal.Vector(*SOURCE), unreal.Vector(*TARGET)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(aim(source, target), False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", FOCAL)
camera.tags = list(camera.tags) + [TAG]
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__RENDER_VISIBLE_REUSED_ROBOT_FRAMED_AS_FOREGROUND_HANDOFF",
    "camera": {"source_cm": list(SOURCE), "target_cm": list(TARGET), "focal_length_mm": FOCAL},
    "robot_mesh_changed": False,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_ROBOT_CLOSEUP_V049_PASS")
