"""Correct the candidate review cameras after the v034 scale correction.

The first close-camera pass used an inverted Unreal pitch sign: it put the
roofless sky in most of every frame despite its targets being below the
camera.  This candidate-only correction uses the actual Unreal pitch
convention and frames the line at human height.  It changes neither machine
geometry nor environment geometry.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_camera_elevation_v035.json"
TAG = unreal.Name("LB.PressShop.2126.CameraElevation.v035")
CAMERAS = (
    ("CAM | 2126 Steam hero overview", (-12200.0, -8800.0, 850.0), (-1600.0, 250.0, 0.0), 42.0, "five-station hero with no roof in frame"),
    ("CAM | 2126 operator line", (-17250.0, -3700.0, 600.0), (-13200.0, 0.0, 250.0), 52.0, "separate bare coil plus coil-free Meshy feeder"),
    ("CAM | 2126 draw nexus", (-7800.0, -4500.0, 650.0), (-4200.0, 0.0, 270.0), 48.0, "Meshy draw press framed as the primary machine"),
    ("CAM | 2126 outbound autonomy", (-3000.0, -5200.0, 650.0), (-200.0, -1900.0, 250.0), 55.0, "reused steel-grey tender with the S04 Meshy press"),
)


def sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def unreal_camera_aim(source, target):
    dx = target.x - source.x
    dy = target.y - source.y
    dz = target.z - source.z
    elevation = math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy)))
    # Unreal's camera pitch has the same sign as the desired elevation.
    return unreal.Rotator(pitch=elevation, yaw=math.degrees(math.atan2(dy, dx)), roll=0.0)


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Camera elevation v035 is already applied")

rows = []
for label, source_values, target_values, focal_length, purpose in CAMERAS:
    camera = actors.get(label)
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Missing review camera: " + label)
    source = unreal.Vector(*source_values)
    target = unreal.Vector(*target_values)
    rotation = unreal_camera_aim(source, target)
    camera.set_actor_location(source, False, False)
    camera.set_actor_rotation(rotation, False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    camera.tags = list(camera.tags) + [TAG]
    rows.append({
        "label": label,
        "source_cm": list(source_values),
        "target_cm": list(target_values),
        "rotation_degrees": [rotation.pitch, rotation.yaw, rotation.roll],
        "focal_length_mm": focal_length,
        "purpose": purpose,
    })

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate map")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 changed")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__ROOFLESS_CANDIDATE_CAMERAS_REAIMED_AT_MACHINE_SCALE",
    "camera_rows": rows,
    "change_scope": "candidate camera transforms and lenses only",
    "machine_geometry_changed": False,
    "environment_geometry_changed": False,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_CAMERA_ELEVATION_V035_PASS")
