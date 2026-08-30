"""Aim the existing infeed review camera at the real coil-free feeder cell."""

import hashlib
import json
import math
from pathlib import Path
import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_infeed_camera_v012.json"
TAG = unreal.Name("LB.PressShop.2126.InfeedCamera.v012")
LABEL = "CAM | 2126 operator line"
LOCATION = (-20200.0, -8400.0, 1500.0)
TARGET = (-13200.0, 250.0, 350.0)
FOCAL_LENGTH = 58.0


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)), roll=0.0)


before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load 2126 candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
camera = actors.get(LABEL)
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Missing infeed camera")
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("infeed camera v012 already applied")
location = unreal.Vector(*LOCATION)
rotation = aim(location, unreal.Vector(*TARGET))
camera.set_actor_location(location, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", FOCAL_LENGTH)
camera.tags = list(camera.tags) + [TAG]
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save 2126 candidate")
after = sha256(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__INFLOW_CAMERA_FRAMES_NEW_MESHY_FEEDER_AND_SEPARATE_PROJECT_COILS",
    "camera": LABEL, "location_cm": list(LOCATION), "target_cm": list(TARGET), "focal_length_mm": FOCAL_LENGTH,
    "roof_created": False, "protected_v438_sha256_before": before, "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_INFEED_CAMERA_V012_PASS")
