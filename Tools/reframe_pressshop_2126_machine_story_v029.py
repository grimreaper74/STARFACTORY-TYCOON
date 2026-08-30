"""Reframe the 2126 candidate around its real machines, not the empty sky.

The v028 live capture proved the line has the right equipment but the old
wide/high cameras spent too much screen space on horizon and blank backdrop.
This pass changes only the four candidate camera transforms and lenses.  It
keeps the roofless map, real Meshy presses, separate coils and the visible
reused robotic tenders exactly as they are.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_machine_story_v029.json"
TAG = unreal.Name("LB.PressShop.2126.MachineStory.v029")

# Each shot runs level with the machinery.  The back walls may still end the
# view, but the sky no longer gets half of a Steam-frame.
CAMERAS = (
    ("CAM | 2126 Steam hero overview", (-15000.0, -8000.0, 1700.0), (-500.0, 0.0, 1500.0), 50.0, "five-station press train and visible robotic tending"),
    ("CAM | 2126 operator line", (-16800.0, -4500.0, 900.0), (-13000.0, 0.0, 800.0), 65.0, "separate bare coil plus coil-free real Meshy feeder"),
    ("CAM | 2126 draw nexus", (-8000.0, -5000.0, 1500.0), (-2600.0, 0.0, 1300.0), 65.0, "open machine faces and S02/S04 robotic tending"),
    ("CAM | 2126 outbound autonomy", (-5500.0, -4500.0, 1400.0), (-1100.0, -1200.0, 1050.0), 65.0, "robot-to-press hand-off; replaces the physically weak outbound gate shot"),
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load 2126 candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Machine-story camera pass v029 is already applied")

rows = []
for label, location_values, target_values, focal_length, purpose in CAMERAS:
    camera = actors.get(label)
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Expected named candidate camera missing: " + label)
    location = unreal.Vector(*location_values)
    camera.set_actor_location(location, False, False)
    camera.set_actor_rotation(aim(location, unreal.Vector(*target_values)), False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    camera.tags = list(camera.tags) + [TAG]
    rows.append({"label": label, "location_cm": list(location_values), "target_cm": list(target_values), "focal_length_mm": focal_length, "purpose": purpose})

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save 2126 candidate after camera reframe")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed during candidate-only camera pass")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__MESHY_MACHINE_STORY_CAMERAS_REFRAMED_FROM_LIVE_V028_REVIEW",
    "changed": "camera transforms and focal lengths only",
    "camera_rows": rows,
    "no_machine_mesh_modified_or_created": True,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_MACHINE_STORY_V029_PASS")
