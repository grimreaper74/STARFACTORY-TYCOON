"""Tighten the camera series around the actual Meshy press assets.

The v035 correction proved the geometry but still used broad design-review
coverage.  Steam review needs product framing: each camera now uses a tighter
portrait of its machine story, avoiding empty deck and avoiding a roof.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_steam_crop_v042.json"
TAG = unreal.Name("LB.PressShop.2126.SteamCrop.v042")
CAMERAS = (
    ("CAM | 2126 Steam hero overview", (-10000.0, -6500.0, 600.0), (-1200.0, 0.0, 350.0), 55.0, "four-Meshy-press visual train"),
    ("CAM | 2126 operator line", (-17250.0, -3000.0, 430.0), (-13200.0, 0.0, 260.0), 70.0, "independent bare coil with user-selected coil-free feeder"),
    ("CAM | 2126 draw nexus", (-7700.0, -3300.0, 500.0), (-4200.0, 0.0, 300.0), 72.0, "full featured press, not a distant layout diagram"),
    ("CAM | 2126 outbound autonomy", (-2800.0, -4000.0, 460.0), (-200.0, -1900.0, 200.0), 72.0, "robot tender and actual press in one machine-scale frame"),
)


def sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx = target.x - source.x
    dy = target.y - source.y
    dz = target.z - source.z
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
    raise RuntimeError("Steam crop v042 already applied")

rows = []
for label, source_values, target_values, focal_length, story in CAMERAS:
    actor = actors.get(label)
    if not isinstance(actor, unreal.CineCameraActor):
        raise RuntimeError("Missing review camera: " + label)
    source = unreal.Vector(*source_values)
    target = unreal.Vector(*target_values)
    rotation = aim(source, target)
    actor.set_actor_location(source, False, False)
    actor.set_actor_rotation(rotation, False)
    actor.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    actor.tags = list(actor.tags) + [TAG]
    rows.append({"label": label, "source_cm": list(source_values), "target_cm": list(target_values), "focal_length_mm": focal_length, "story": story})

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate map")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__MESHY_MACHINE_CAMERA_SERIES_TIGHTENED_FOR_STEAM_REVIEW",
    "cameras": rows,
    "scene_geometry_changed": False,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_STEAM_CROP_V042_PASS")
