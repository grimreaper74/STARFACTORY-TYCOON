"""Set a high management-camera hero for the roofless real-Meshy v002 line."""
import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_isometric_hero_v011.json"
TAG = unreal.Name("LB.PressShop.2126.v002.IsometricHero.v011")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    flat = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(
        roll=0.0,
        pitch=math.degrees(math.atan2(dz, flat)),
        yaw=math.degrees(math.atan2(dy, dx)),
    )


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate v002")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v011 isometric hero already applied")
camera = actors.get("CAM v002 | steam hero press run")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Missing hero camera")

# The view contains the separated inbound coil, coil-free Meshy feeder, five
# actual Meshy stations and their robot/transfer language in one readable flow.
source = unreal.Vector(-15400.0, -14100.0, 10800.0)
target = unreal.Vector(-4100.0, 0.0, 420.0)
rotation = aim(source, target)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 37.0)
actual = camera.get_actor_rotation()
if abs(actual.yaw - rotation.yaw) > 0.01 or abs(actual.pitch - rotation.pitch) > 0.01:
    raise RuntimeError("Named camera rotation did not apply")
camera.tags = list(camera.tags) + [TAG, unreal.Name("LB.ManagementCamera.Isometric")]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, rotation)
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v011 isometric camera")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__ISOMETRIC_MESHY_FLOW_HERO_FRAMED",
    "candidate_map": MAP,
    "camera": "CAM v002 | steam hero press run",
    "source_cm": [source.x, source.y, source.z],
    "target_cm": [target.x, target.y, target.z],
    "pitch": actual.pitch,
    "yaw": actual.yaw,
    "focal_length_mm": 37.0,
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_ISOMETRIC_HERO_V011_PASS")
