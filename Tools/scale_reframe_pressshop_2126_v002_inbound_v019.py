"""Scale only candidate coil instances to the imported feeder's review scale.

The project coil source meshes are retained untouched. Their map instances are
set to a 2x management-view scale and re-seated on the existing saddle/feeder.
"""
import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_inbound_scale_reframe_v019.json"
TAG = unreal.Name("LB.PressShop.2126.v002.InboundScaleReframe.v019")


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


def bounds(actor):
    origin, extent = actor.get_actor_bounds(False, True)
    return {"origin": [origin.x, origin.y, origin.z], "extent": [extent.x, extent.y, extent.z]}


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate v002")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v019 inbound scaling already applied")
wrapped = actors.get("S00 | wrapped master coil | project reuse")
bare = actors.get("S00 | bare master coil | project reuse")
saddle = actors.get("S00 | wrapped coil changeover saddle | kit reuse")
feeder = actors.get("S00 | Meshy coil-free autonomous feeder")
camera = actors.get("CAM v002 | coil-to-press story")
if not all(isinstance(actor, unreal.StaticMeshActor) for actor in (wrapped, bare, saddle, feeder)):
    raise RuntimeError("Inbound asset missing")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Inbound camera missing")

scale = unreal.Vector(2.0, 2.0, 2.0)
wrapped.set_actor_scale3d(scale)
bare.set_actor_scale3d(scale)
# Measured source extents are 95.02cm / 93.67cm vertically. Explicit re-seating
# preserves contact after scaling: saddle top 67.65cm and feeder floor 0cm.
wrapped.set_actor_location(unreal.Vector(-15800.0, 1700.0, 257.69), False, False)
bare.set_actor_location(unreal.Vector(-13200.0, 0.0, 187.34), False, False)
wrapped_bounds = bounds(wrapped)
bare_bounds = bounds(bare)
if abs(wrapped_bounds["origin"][2] - wrapped_bounds["extent"][2] - 67.65) > 1.0:
    raise RuntimeError("Wrapped coil no longer seated on saddle")
if abs(bare_bounds["origin"][2] - bare_bounds["extent"][2]) > 1.0:
    raise RuntimeError("Bare coil no longer seated on feeder floor")
if wrapped_bounds["extent"][2] < 180.0 or bare_bounds["extent"][2] < 180.0:
    raise RuntimeError("Coil scale gate failed")
for actor in (wrapped, bare):
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Reused.ProjectCoil.ManagementScale")]

source = unreal.Vector(-19000.0, -6500.0, 4200.0)
target = unreal.Vector(-14000.0, 500.0, 320.0)
rotation = aim(source, target)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 50.0)
camera.tags = list(camera.tags) + [TAG]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, rotation)

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v019 inbound scale/reframe")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__INBOUND_COILS_MANAGEMENT_SCALE_AND_CONTACT_VERIFIED",
    "candidate_map": MAP,
    "source_meshes_modified": False,
    "instance_scale": 2.0,
    "wrapped_bounds_cm": wrapped_bounds,
    "bare_bounds_cm": bare_bounds,
    "camera": {"source_cm": [source.x, source.y, source.z], "target_cm": [target.x, target.y, target.z], "focal_length_mm": 50.0},
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_INBOUND_SCALE_REFRAME_V019_PASS")
