"""Compose one close robotic hand-off and one tighter press-train hero."""

import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_robot_story_v044.json"
TAG = unreal.Name("LB.PressShop.2126.RobotStory.v044")
CAMERAS = (
    ("CAM | 2126 Steam hero overview", (-8500.0, -5000.0, 500.0), (-1500.0, 0.0, 250.0), 72.0, "tight four-press hero"),
    ("CAM | 2126 outbound autonomy", (-1000.0, -6000.0, 400.0), (-200.0, -2100.0, 150.0), 75.0, "S04 robotic tender foreground, Meshy press background"),
)


def sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Robot story v044 already applied")

rows = []
for label, source_values, target_values, focal_length, story in CAMERAS:
    camera = actors.get(label)
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Missing camera: " + label)
    source = unreal.Vector(*source_values)
    target = unreal.Vector(*target_values)
    camera.set_actor_location(source, False, False)
    camera.set_actor_rotation(aim(source, target), False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    camera.tags = list(camera.tags) + [TAG]
    rows.append({"label": label, "source_cm": list(source_values), "target_cm": list(target_values), "focal_length_mm": focal_length, "story": story})

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__PRESS_TRAIN_AND_ROBOT_HANDOFF_COMPOSED",
    "cameras": rows,
    "machine_geometry_changed": False,
    "robot_geometry_changed": False,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_ROBOT_STORY_V044_PASS")
