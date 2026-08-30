"""Open the roofless candidate to a native Unreal sky and tighten the inbound view."""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_skyline_v024.json"
TAG = unreal.Name("LB.PressShop.2126.v002.OpenSkyline.v024")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)))


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v024 skyline pass already applied")

# These three were intentional temporary framing planes in the first candidate
# build.  They read as a roof in the low infeed view, so hide rather than delete
# them.  The factory remains consciously roofless.
hidden = []
for label in (
    "2126 v002 | warm-white rear elevation",
    "2126 v002 | Cairnwell supervision ribbon",
    "2126 v002 | safety-yellow process datum",
):
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Original review facade missing: " + label)
    actor.static_mesh_component.set_visibility(False, True)
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Architecture.HiddenForOpenSky")]
    hidden.append(label)

sun = actors.get("B_stylized | sun 0.30")
sky = actors.get("B_stylized | sky 0.20")
if not isinstance(sun, unreal.DirectionalLight) or not isinstance(sky, unreal.SkyLight):
    raise RuntimeError("Expected existing B_stylized sky lights")
sun.light_component.set_editor_property("atmosphere_sun_light", True)
sun.light_component.set_editor_property("atmosphere_sun_light_index", 0)
sun.light_component.set_editor_property("intensity", 2.0)
sky.light_component.set_editor_property("real_time_capture", True)
sky.light_component.set_editor_property("intensity", 1.5)
sun.tags = list(sun.tags) + [TAG]
sky.tags = list(sky.tags) + [TAG]

atmospheres = [actor for actor in unreal.EditorLevelLibrary.get_all_level_actors() if isinstance(actor, unreal.SkyAtmosphere)]
if atmospheres:
    atmosphere = atmospheres[0]
else:
    atmosphere = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())
    if not isinstance(atmosphere, unreal.SkyAtmosphere):
        raise RuntimeError("Could not create native Unreal Sky Atmosphere")
    atmosphere.set_actor_label("2126 v002 | open-air native sky atmosphere")
atmosphere.tags = list(atmosphere.tags) + [TAG, unreal.Name("LB.Architecture.OpenSky")]

camera = actors.get("CAM v002 | coil-to-press story")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Inbound camera missing")
source = unreal.Vector(-18300.0, -4000.0, 1500.0)
target = unreal.Vector(-13800.0, 800.0, 450.0)
rotation = aim(source, target)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 55.0)
camera.tags = list(camera.tags) + [TAG]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, rotation)

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate map")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__ROOFLESS_OPEN_SKYLINE_AND_INBOUND_CAMERA",
    "candidate_map": MAP,
    "new_machine_geometry": 0,
    "new_dynamic_lights": 0,
    "hidden_review_facades": hidden,
    "native_sky_actor": atmosphere.get_actor_label(),
    "camera": {"source_cm": [source.x, source.y, source.z], "target_cm": [target.x, target.y, target.z], "focal_length_mm": 55.0},
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_OPEN_SKYLINE_V024_PASS")
