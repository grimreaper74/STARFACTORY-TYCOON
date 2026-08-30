"""Replace the weak first stage in v003 with the verified coil-free hero press.

Only the isolated candidate map changes.  The original Meshy stage remains in
the level as hidden historical evidence; imported candidate meshes and source
FBX stay unchanged.
"""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
FBX = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "HeroPressCell_MeshyNoCoil_v001" / "Runtime" / "SM_LB_PS_HeroPressCell_MeshyNoCoil_v001.fbx"
ROOT = "/Game/LineBoss/Candidates/PressShop/HeroPressCellNoCoil_v001"
MATERIALS = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_hero_nocoil_integration_v038.json"
TAG = unreal.Name("LB.PressShop.2126.v003.HeroNoCoilIntegration.v038")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)))


def mesh(path):
    result = unreal.load_asset(path)
    if not isinstance(result, unreal.StaticMesh):
        raise RuntimeError("Imported hero mesh unavailable: " + path)
    return result


def material(name):
    result = unreal.load_asset(MATERIALS + "/" + name)
    if not isinstance(result, unreal.MaterialInterface):
        raise RuntimeError("Candidate material unavailable: " + name)
    return result


def extent_x(actor):
    asset = actor.static_mesh_component.get_editor_property("static_mesh")
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError("Static-mesh actor has no mesh: " + actor.get_actor_label())
    bounds = asset.get_bounds().box_extent
    scale = actor.get_actor_scale3d()
    yaw = int(round(actor.get_actor_rotation().yaw)) % 180
    if yaw == 90:
        return abs(bounds.y * scale.y)
    if yaw != 0:
        raise RuntimeError("Flow actor has unsupported yaw: %s" % actor.get_actor_label())
    return abs(bounds.x * scale.x)


def move_x(actor, x):
    location = actor.get_actor_location()
    delta = x - location.x
    location.x = x
    actor.set_actor_location(location, False, False)
    return delta


if not FBX.is_file() or not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Required source or protected evidence file missing")
fbx_before, protected_before, v002_before = digest(FBX), digest(PROTECTED), digest(V002)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load isolated v003 candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Hero no-coil integration v038 already applied")
old_s02_label = "2126 v003 | 02 | draw / form"
feeder_label = "2126 v003 | 01 | coil-free autonomous feeder"
if not isinstance(actors.get(old_s02_label), unreal.StaticMeshActor) or not isinstance(actors.get(feeder_label), unreal.StaticMeshActor):
    raise RuntimeError("Required current candidate stages missing")
body = mesh(ROOT + "/SM_LB_PS_HeroPressCell_MeshyNoCoil_v001_Body")
rollers = mesh(ROOT + "/SM_LB_PS_HeroPressCell_MeshyNoCoil_v001_CleanRollers")
old_s02 = actors[old_s02_label]
origin = old_s02.get_actor_location()
hero_z = body.get_bounds().box_extent.z
hero_body = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(origin.x, origin.y, hero_z), unreal.Rotator())
hero_rollers = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(origin.x, origin.y, hero_z), unreal.Rotator())
if not isinstance(hero_body, unreal.StaticMeshActor) or not isinstance(hero_rollers, unreal.StaticMeshActor):
    raise RuntimeError("Could not spawn candidate hero press actors")
hero_body.set_actor_label("2126 v003 | 02 | coil-free hero draw/form body")
hero_body.static_mesh_component.set_static_mesh(body)
hero_rollers.set_actor_label("2126 v003 | 02 | coil-free hero draw/form rollers")
hero_rollers.static_mesh_component.set_static_mesh(rollers)
hero_body.static_mesh_component.set_material(0, material("M_LB_PS2126v003_WarmWhite"))
for slot, value in enumerate((material("M_LB_PS2126v003_FoundryCharcoal"), material("M_LB_PS2126v003_SteelGrey"), material("M_LB_PS2126v003_SafetyYellow"))):
    hero_rollers.static_mesh_component.set_material(slot, value)
hero_body.tags = [TAG, unreal.Name("LB.Process.Flow"), unreal.Name("LB.Meshy.Repaired"), unreal.Name("LB.Meshy.CoilFree")]
hero_rollers.tags = list(hero_body.tags)
hero_rollers.attach_to_actor(hero_body, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)

# Keep clear 2.5 m machine gaps.  The hero press is wider than the prior S02;
# all movement is along flow X, while each robot stays paired with its station.
gap = 250.0
hero_half = body.get_bounds().box_extent.x
feeder = actors[feeder_label]
hero_left = origin.x - hero_half
feeder_right = feeder.get_actor_location().x + extent_x(feeder)
feeder_shift = min(0.0, hero_left - gap - feeder_right)
if feeder_shift:
    for label in (feeder_label, "2126 v003 | active bare galvanized coil", "2126 v003 | wrapped reserve coil saddle", "2126 v003 | wrapped graphite reserve coil"):
        actor = actors.get(label)
        if actor is None:
            raise RuntimeError("Infeed companion missing: " + label)
        move_x(actor, actor.get_actor_location().x + feeder_shift)

station_specs = (
    ("2126 v003 | 03 | trim", "2126 v003 | autonomous tend robot 02"),
    ("2126 v003 | 04 | pierce", "2126 v003 | autonomous tend robot 03"),
    ("2126 v003 | 05 | flange / hem", "2126 v003 | autonomous tend robot 04"),
    ("2126 v003 | 06 | vision / outfeed", "2126 v003 | autonomous tend robot 05"),
    ("2126 v003 | 07 | powered outfeed conveyor", None),
    ("2126 v003 | 08 | inspection unload cell", None),
)
cursor = origin.x + hero_half + gap
reflow = []
for label, robot_label in station_specs:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Flow actor missing: " + label)
    half = extent_x(actor)
    target_x = cursor + half
    delta = move_x(actor, target_x)
    if robot_label:
        robot = actors.get(robot_label)
        if not isinstance(robot, unreal.StaticMeshActor):
            raise RuntimeError("Paired robot missing: " + robot_label)
        move_x(robot, robot.get_actor_location().x + delta)
    reflow.append({"actor": label, "new_x_cm": round(target_x, 2), "delta_x_cm": round(delta, 2)})
    cursor = target_x + half + gap

# Stillages follow the inspection cell along the same flow direction.
inspection = actors["2126 v003 | 08 | inspection unload cell"]
stillage_x = inspection.get_actor_location().x + extent_x(inspection) + 450.0
for label in ("2126 v003 | finished-panel stillage 01", "2126 v003 | finished-panel stillage 02"):
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Outfeed stillage missing: " + label)
    move_x(actor, stillage_x)

old_s02.static_mesh_component.set_visibility(False, True)
old_s02.set_actor_hidden_in_game(True)
old_s02.set_is_temporarily_hidden_in_editor(True)
old_s02.tags = list(old_s02.tags) + [TAG, unreal.Name("LB.Meshy.RejectedWeakS02")]

# Reframe the existing management cameras to the widened but still compact line.
camera_specs = {
    "CAM v003 | compact whole-flow overview": (unreal.Vector(-6900.0, -8600.0, 4850.0), unreal.Vector(400.0, 0.0, 320.0), 48.0),
    "CAM v003 | compact press hero": (unreal.Vector(-2500.0, -9000.0, 4400.0), unreal.Vector(550.0, 0.0, 400.0), 54.0),
    "CAM v003 | coil to first press story": (unreal.Vector(-7300.0, -6500.0, 2700.0), unreal.Vector(-3500.0, 0.0, 360.0), 54.0),
    "CAM v003 | inspection to stillage story": (unreal.Vector(9000.0, -6800.0, 2600.0), unreal.Vector(cursor - 1000.0, 0.0, 260.0), 54.0),
}
for label, (source, target, focal) in camera_specs.items():
    camera = actors.get(label)
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Management camera missing: " + label)
    camera.set_actor_location(source, False, False)
    camera.set_actor_rotation(aim(source, target), False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal)
    camera.tags = list(camera.tags) + [TAG]

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save isolated v003 candidate")
fbx_after, protected_after, v002_after = digest(FBX), digest(PROTECTED), digest(V002)
if fbx_before != fbx_after or protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Source FBX or protected map changed during v038")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__COIL_FREE_HERO_PRESS_INTEGRATED_IN_CANDIDATE_ONLY",
    "candidate_map": MAP,
    "source_fbx_sha256_before": fbx_before,
    "source_fbx_sha256_after": fbx_after,
    "hidden_original_stage": old_s02_label,
    "hero_actor_labels": [hero_body.get_actor_label(), hero_rollers.get_actor_label()],
    "feeder_shift_x_cm": round(feeder_shift, 2),
    "reflow": reflow,
    "roof_created": False,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_HERO_NOCOIL_V003_INTEGRATION_V038_PASS")
