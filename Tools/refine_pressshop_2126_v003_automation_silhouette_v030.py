"""Tighten the compact v003 automation read with a single roofless transfer rail."""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_automation_silhouette_v030.json"
TAG = unreal.Name("LB.PressShop.2126.v003.AutomationSilhouette.v030")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)))


def cube(label, location, dimensions_cm, material, tags=()):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Could not place simplified transfer component")
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(cube_mesh)
    actor.static_mesh_component.set_world_scale3d(unreal.Vector(*(value / 100.0 for value in dimensions_cm)))
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_visibility(True, True)
    actor.tags = [TAG, unreal.Name("LB.Automation.SingleTransferSilhouette")] + list(tags)
    return actor


if not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Protected evidence map missing")
protected_before, v002_before = digest(PROTECTED), digest(V002)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load compact v003 map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v030 automation silhouette already applied")

# Bring the five real robot arms beside their station faces; the prior 31.5m
# setback made them read as unrelated background props at management distance.
robots = []
for index in range(1, 6):
    label = "2126 v003 | autonomous tend robot %02d" % index
    robot = actors.get(label)
    if not isinstance(robot, unreal.StaticMeshActor):
        raise RuntimeError("Robot missing: " + label)
    location = robot.get_actor_location()
    side = 1200.0 if index % 2 else -1200.0
    robot.set_actor_location(unreal.Vector(location.x, side, location.z), False, False)
    robot.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=-90.0 if side > 0 else 90.0), False)
    robot.tags = list(robot.tags) + [TAG]
    robots.append({"actor": label, "station_side_y_cm": side})

cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
yellow = unreal.load_asset("/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_SafetyYellow")
steel = unreal.load_asset("/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials/M_LB_PS2126v003_SteelGrey")
if not isinstance(cube_mesh, unreal.StaticMesh) or not isinstance(yellow, unreal.Material) or not isinstance(steel, unreal.Material):
    raise RuntimeError("Expected v003 native transfer dependencies missing")

# One intentionally simple overhead automation silhouette.  It has no support
# columns or roof members; the open air remains visibly open in every view.
rails = [
    cube("2126 v003 | transfer rail operator", (0.0, -1450.0, 960.0), (11100.0, 100.0, 100.0), steel),
    cube("2126 v003 | transfer rail service", (0.0, 1450.0, 960.0), (11100.0, 100.0, 100.0), steel),
]
carriages = []
for index, x in enumerate((-2100.0, 0.0, 2100.0), start=1):
    carriages.append(cube("2126 v003 | transfer carriage %02d" % index, (x, 0.0, 875.0), (360.0, 2850.0, 150.0), yellow))

# Reframe the hero to contain the full press run while holding a recognisable
# three-quarter view of the real machines rather than an overhead diagram.
camera = actors.get("CAM v003 | compact press hero")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("v003 hero camera missing")
source = unreal.Vector(-5600.0, -12800.0, 6100.0)
target = unreal.Vector(300.0, 0.0, 420.0)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(aim(source, target), False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 44.0)
camera.tags = list(camera.tags) + [TAG]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, camera.get_actor_rotation())

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless compact candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v003 automation refinement")
protected_after, v002_after = digest(PROTECTED), digest(V002)
if protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Protected evidence map changed during v030")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__COMPACT_AUTOMATION_SILHOUETTE_AND_ROBOT_STANDOFF_REFINED",
    "candidate_map": MAP,
    "robots": robots,
    "single_transfer_rails": [actor.get_actor_label() for actor in rails],
    "single_transfer_carriages": [actor.get_actor_label() for actor in carriages],
    "new_large_machine_geometry": 0,
    "native_geometry_scope": "one simplified roofless transfer silhouette",
    "roof_created": False,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_AUTOMATION_SILHOUETTE_V030_PASS")
