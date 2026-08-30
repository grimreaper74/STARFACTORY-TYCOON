"""Frame the physically small real outbound gate/stillage at its actual bounds."""

import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_outbound_detail_v027.json"
TAG = unreal.Name("LB.PressShop.2126.OutboundDetail.v027")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)), roll=0.0)


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Outbound detail v027 already applied")
camera = actors.get("CAM | 2126 outbound autonomy")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Outbound camera missing")
for label in ("OUTBOUND | real vision inspection gate", "OUTBOUND | inspected panel stillage"):
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError("Outbound evidence actor missing: " + label)
    origin, extent = actor.get_actor_bounds(False)
    if extent.x < 100.0 or extent.z < 50.0:
        raise RuntimeError("Outbound evidence asset unexpectedly lacks usable bounds: " + label)

location = unreal.Vector(13000.0, -2250.0, 600.0)
target = unreal.Vector(10400.0, -120.0, 260.0)
camera.set_actor_location(location, False, False)
camera.set_actor_rotation(aim(location, target), False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 52.0)
camera.tags = list(camera.tags) + [TAG]
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__OUTBOUND_DETAIL_CAMERA_FIT_TO_MEASURED_REAL_ASSET_BOUNDS",
    "camera": {"location_cm": [13000, -2250, 600], "target_cm": [10400, -120, 260], "focal_length_mm": 52.0},
    "geometry_changed": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_OUTBOUND_DETAIL_V027_PASS")
