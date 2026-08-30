"""Correct only the candidate review cameras after a positional Rotator bug.

Unreal Python's positional Rotator constructor is not (pitch, yaw, roll).
The prior pitch-compaction helper used positional arguments, so it mapped pitch
into roll and left yaw zero. This candidate-only repair uses named fields and
records the protected v438 hash before and after saving the fresh map.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_review_camera_orientation_v001.json"
SPECS = (
    ("CAM | 2126 Steam hero overview", (-14500.0, -19500.0, 6800.0), (-300.0, 0.0, 2300.0), 36.0),
    ("CAM | 2126 operator line", (-10200.0, -13500.0, 4400.0), (-600.0, 0.0, 2200.0), 42.0),
    ("CAM | 2126 draw nexus", (-10400.0, -8600.0, 3300.0), (-4200.0, 0.0, 2200.0), 48.0),
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    flat = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, flat)),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load fresh candidate")

actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
records = []
for label, location_values, target_values, focal_length in SPECS:
    camera = actors.get(label)
    if camera is None or not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Missing CineCameraActor: " + label)
    location = unreal.Vector(*location_values)
    target = unreal.Vector(*target_values)
    rotation = aim(location, target)
    camera.set_actor_location(location, False, False)
    camera.set_actor_rotation(rotation, False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    forward = camera.get_actor_forward_vector()
    records.append({
        "label": label,
        "location_cm": list(location_values),
        "target_cm": list(target_values),
        "rotation": [rotation.pitch, rotation.yaw, rotation.roll],
        "forward": [forward.x, forward.y, forward.z],
        "focal_length_mm": focal_length,
    })

hero_location = unreal.Vector(*SPECS[0][1])
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero_location, aim(hero_location, unreal.Vector(*SPECS[0][2])))
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save fresh candidate camera repair")
after = sha256(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 map changed during camera-only repair")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__CANDIDATE_CAMERA_ORIENTATION_REPAIRED_WITH_NAMED_ROTATOR_FIELDS",
    "candidate_map": MAP,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
    "cameras": records,
    "scope": "candidate review cameras only",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_CAMERA_ORIENTATION_REPAIRED")
