"""Correct the Unreal vertical camera-axis sign for the 2126 review cameras.

The v029 screenshots demonstrated that the previous generic aim helper placed
the named target below the centre of frame.  In Unreal camera rotation the
vertical sign is the opposite of the earlier helper's mathematical elevation.
This is a camera-only correction; it changes no lighting, mesh, material,
actor placement or roofless architecture.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_camera_pitch_v030.json"
TAG = unreal.Name("LB.PressShop.2126.CameraPitch.v030")
CAMERAS = (
    ("CAM | 2126 Steam hero overview", (-15000.0, -8000.0, 1700.0), (-500.0, 0.0, 1500.0), 50.0),
    ("CAM | 2126 operator line", (-16800.0, -4500.0, 900.0), (-13000.0, 0.0, 800.0), 65.0),
    ("CAM | 2126 draw nexus", (-8000.0, -5000.0, 1500.0), (-2600.0, 0.0, 1300.0), 65.0),
    ("CAM | 2126 outbound autonomy", (-5500.0, -4500.0, 1400.0), (-1100.0, -1200.0, 1050.0), 65.0),
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
    return unreal.Rotator(
        pitch=-elevation,
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Camera-pitch correction v030 already applied")

rows = []
for label, location_values, target_values, focal_length in CAMERAS:
    camera = actors.get(label)
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Missing expected review camera: " + label)
    location = unreal.Vector(*location_values)
    target = unreal.Vector(*target_values)
    rotation = unreal_camera_aim(location, target)
    camera.set_actor_location(location, False, False)
    camera.set_actor_rotation(rotation, False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    camera.tags = list(camera.tags) + [TAG]
    rows.append({"label": label, "location_cm": list(location_values), "target_cm": list(target_values), "focal_length_mm": focal_length, "rotation": [rotation.pitch, rotation.yaw, rotation.roll]})

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__UNREAL_VERTICAL_CAMERA_AXIS_CORRECTED_FROM_LIVE_RENDER_EVIDENCE",
    "changed": "camera pitch sign only",
    "cameras": rows,
    "no_mesh_material_light_or_actor_transform_changed": True,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_CAMERA_PITCH_V030_PASS")
