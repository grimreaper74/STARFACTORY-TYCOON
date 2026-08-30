"""Correct review-camera target heights from centimetre-scale mesh evidence.

Live frames revealed that the targets inherited from an earlier blockout were
15--25 m above ground while the reused Meshy presses measure approximately
5.4 m high.  This uses equipment-centre heights in centimetres and preserves
the v030 Unreal vertical-axis correction.  Only camera positions, rotations
and lenses change.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_target_height_v032.json"
TAG = unreal.Name("LB.PressShop.2126.TargetHeight.v032")
CAMERAS = (
    ("CAM | 2126 Steam hero overview", (-12000.0, -8000.0, 650.0), (-1000.0, 0.0, 280.0), 50.0, "full real press train"),
    ("CAM | 2126 operator line", (-15400.0, -3800.0, 450.0), (-13000.0, 0.0, 220.0), 50.0, "separate bare coil and coil-free Meshy feeder"),
    ("CAM | 2126 draw nexus", (-6800.0, -3500.0, 600.0), (-2500.0, -300.0, 300.0), 50.0, "open draw and trim faces with actual tenders"),
    ("CAM | 2126 outbound autonomy", (-4300.0, -3500.0, 600.0), (-1200.0, -1500.0, 240.0), 45.0, "robot-to-press hand-off"),
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def unreal_camera_aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    elevation = math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy)))
    return unreal.Rotator(pitch=-elevation, yaw=math.degrees(math.atan2(dy, dx)), roll=0.0)


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Target-height correction v032 already applied")

rows = []
for label, source_values, target_values, focal_length, purpose in CAMERAS:
    camera = actors.get(label)
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Expected camera missing: " + label)
    source = unreal.Vector(*source_values)
    target = unreal.Vector(*target_values)
    rotation = unreal_camera_aim(source, target)
    camera.set_actor_location(source, False, False)
    camera.set_actor_rotation(rotation, False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    camera.tags = list(camera.tags) + [TAG]
    rows.append({"label": label, "source_cm": list(source_values), "target_cm": list(target_values), "focal_length_mm": focal_length, "purpose": purpose})

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__CAMERAS_REFOCUSED_ON_REAL_5M_MESHY_PRESS_HEIGHTS",
    "camera_rows": rows,
    "evidence": "Live v028-v030 frames showed machines below centre because prior targets were 1500-2550 cm high; measured S06 bound is 0-538 cm.",
    "no_mesh_material_light_or_actor_transform_changed": True,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_TARGET_HEIGHT_V032_PASS")
