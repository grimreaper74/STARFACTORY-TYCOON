"""Frame the separate project coils and coil-free Meshy feeder for review."""
import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_inbound_story_v017.json"
TAG = unreal.Name("LB.PressShop.2126.v002.InboundStory.v017")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    flat = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(dz, flat)), yaw=math.degrees(math.atan2(dy, dx)))


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate v002")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v017 inbound story already applied")
for label in (
    "S00 | wrapped master coil | project reuse",
    "S00 | bare master coil | project reuse",
    "S00 | Meshy coil-free autonomous feeder",
    "MESHY v002 | S02 Draw / form",
):
    if label not in actors:
        raise RuntimeError("Inbound composition object missing: " + label)
camera = actors.get("CAM v002 | coil-to-press story")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Missing inbound camera")

source = unreal.Vector(-20500.0, -12000.0, 8500.0)
target = unreal.Vector(-11000.0, 0.0, 400.0)
rotation = aim(source, target)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 45.0)
camera.tags = list(camera.tags) + [TAG, unreal.Name("LB.ManagementCamera.Inbound")]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, rotation)
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v017 inbound camera")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__SEPARATE_WRAPPED_BARE_COIL_AND_FEEDER_FRAMED",
    "candidate_map": MAP,
    "camera": "CAM v002 | coil-to-press story",
    "source_cm": [source.x, source.y, source.z],
    "target_cm": [target.x, target.y, target.z],
    "focal_length_mm": 45.0,
    "embedded_meshy_coils": 0,
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_INBOUND_STORY_V017_PASS")
