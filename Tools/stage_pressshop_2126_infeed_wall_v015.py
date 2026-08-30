"""Compose a sparse, roofless future infeed bay around the real Meshy feeder.

Architecture is intentionally limited to a floor zone and one open-air back
wall. No machines are blockouts: the feeder and coils remain the genuine
Meshy/project assets installed in v011.
"""

import hashlib
import json
import math
from pathlib import Path
import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
MATERIAL_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Materials"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_infeed_bay_v015.json"
TAG = unreal.Name("LB.PressShop.2126.InfeedBay.v015")
CUBE = "/Engine/BasicShapes/Cube"
CAMERA = "CAM | 2126 operator line"
OLD_WALLS = ("2126 | rear production facade pale-green supervision band", "2126 | rear production facade inbound field")


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)), roll=0.0)


def hide(actor):
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


def create_architecture(label, location, dimensions, material):
    cube = unreal.load_asset(CUBE)
    if not isinstance(cube, unreal.StaticMesh):
        raise RuntimeError("Native architecture cube missing")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        raise RuntimeError("Could not create " + label)
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(cube)
    actor.static_mesh_component.set_world_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    actor.static_mesh_component.set_material(0, material)
    actor.tags = [TAG, unreal.Name("LB.Architecture.OpenAir"), unreal.Name("LB.PressShop.Candidate")]
    return actor


before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("infeed bay v015 already staged")
for label in OLD_WALLS:
    wall = actors.get(label)
    if wall is None:
        raise RuntimeError("Missing prior candidate wall: " + label)
    hide(wall)
    wall.tags = list(wall.tags) + [TAG]

warm_white = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_WarmWhite")
pale_green = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_PaintedPaleGreen")
if not isinstance(warm_white, unreal.Material) or not isinstance(pale_green, unreal.Material):
    raise RuntimeError("Candidate architectural materials missing")

# A broad painted wall ends the view but remains open to the sky; the opening
# above it is deliberate, so this is not a roofed building.
floor = create_architecture("S00 | painted infeed floor zone | open-air", (-13200.0, 0.0, -9.0), (14000.0, 7000.0, 18.0), pale_green)
wall = create_architecture("S00 | warm-white open-air infeed back wall", (-13200.0, 3600.0, 2850.0), (14000.0, 180.0, 5700.0), warm_white)
band = create_architecture("S00 | Cairnwell-green infeed supervision band", (-13200.0, 3480.0, 1100.0), (13800.0, 40.0, 850.0), pale_green)

camera = actors.get(CAMERA)
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Infeed camera missing")
location = unreal.Vector(-16000.0, -7000.0, 1250.0)
camera.set_actor_location(location, False, False)
camera.set_actor_rotation(aim(location, unreal.Vector(-13200.0, 0.0, 300.0)), False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 45.0)
camera.tags = list(camera.tags) + [TAG]

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
after = sha256(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__SPARSE_ROOFLESS_INFEED_BAY_STAGED_AROUND_REAL_MESHY_FEEDER",
    "new_architecture": [floor.get_actor_label(), wall.get_actor_label(), band.get_actor_label()],
    "machine_policy": "No machine blockout added; the operational feeder and both coils remain existing real assets.",
    "camera": {"label": CAMERA, "location_cm": [-16000, -7000, 1250], "target_cm": [-13200, 0, 300], "focal_length_mm": 45.0},
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_INFEED_BAY_V015_PASS")
