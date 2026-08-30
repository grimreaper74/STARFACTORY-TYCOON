"""Tighten the roofless v003 candidate around the repaired Meshy hero press.

Only the isolated v003 map may change.  This is a presentation and flow-layout
pass: it neither edits source meshes nor creates replacement machinery.
"""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
MATERIALS = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_hero_story_v039.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
EXPECTED = {
    PROTECTED: "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    V002: "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
TAG = unreal.Name("LB.PressShop.2126.v003.HeroStory.v039")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().lower()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(
        roll=0.0,
        pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))),
        yaw=math.degrees(math.atan2(dy, dx)),
    )


def static_mesh(path):
    value = unreal.load_asset(path)
    if not isinstance(value, unreal.StaticMesh):
        raise RuntimeError("Static mesh unavailable: " + path)
    return value


def material(name):
    value = unreal.load_asset(MATERIALS + "/" + name)
    if not isinstance(value, unreal.MaterialInterface):
        raise RuntimeError("Candidate material unavailable: " + name)
    return value


def cube(label, location, size_cm, mat, tags):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Could not create native work island: " + label)
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(cube_mesh)
    actor.set_actor_scale3d(unreal.Vector(size_cm[0] / 100.0, size_cm[1] / 100.0, size_cm[2] / 100.0))
    actor.static_mesh_component.set_material(0, mat)
    actor.tags = [TAG] + list(tags)
    return actor


for path, expected in EXPECTED.items():
    actual = digest(path)
    if actual != expected:
        raise RuntimeError("Protected baseline changed before v039: " + str(path))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load isolated v003 candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Hero-story v039 was already applied")

required = (
    "2126 v003 | 02 | draw / form",
    "2126 v003 | 02 | coil-free hero draw/form body",
    "2126 v003 | 02 | coil-free hero draw/form rollers",
    "2126 v003 | active bare galvanized coil",
    "2126 v003 | wrapped graphite reserve coil",
    "2126 v003 | wrapped reserve coil saddle",
    "2126 v003 | finished-panel stillage 01",
    "2126 v003 | finished-panel stillage 02",
    "2126 v003 | safety flow datum operator",
    "2126 v003 | safety flow datum service",
    "CAM v003 | compact whole-flow overview",
    "CAM v003 | compact press hero",
    "CAM v003 | coil to first press story",
    "CAM v003 | inspection to stillage story",
)
missing = [label for label in required if label not in actors]
if missing:
    raise RuntimeError("Candidate actor missing: " + ", ".join(missing))

# v038 marked the rejected old first press hidden, but editor screenshots still
# saw its component.  Make the render state explicit and leave the actor in the
# map purely as the tagged historical comparison record.
hidden = []
for label in (
    "2126 v003 | 02 | draw / form",
    "2126 v003 | safety flow datum operator",
    "2126 v003 | safety flow datum service",
):
    actor = actors[label]
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Expected static mesh actor: " + label)
    actor.static_mesh_component.set_visibility(False, True)
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Visual.HiddenInV039")]
    hidden.append(label)

# Actual project coils remain separate from the repaired coil-free press.  One
# active bare coil begins the line; the wrapped coil is a clearly separate
# reserve on the service side, instead of a duplicate hidden in a machine.
actors["2126 v003 | active bare galvanized coil"].set_actor_location(unreal.Vector(-5575.0, 0.0, 187.3), False, False)
actors["2126 v003 | wrapped graphite reserve coil"].set_actor_location(unreal.Vector(-5525.0, 2150.0, 256.7), False, False)
actors["2126 v003 | wrapped reserve coil saddle"].set_actor_location(unreal.Vector(-5525.0, 2150.0, 33.3), False, False)

# Bring unloading inventory into the inspection story, not 21 m away from it.
actors["2126 v003 | finished-panel stillage 01"].set_actor_location(unreal.Vector(5590.0, 1050.0, 55.8), False, False)
actors["2126 v003 | finished-panel stillage 02"].set_actor_location(unreal.Vector(5590.0, -1050.0, 55.8), False, False)

# Robots should read as transfer cells at the machines, rather than isolated
# figures in the foreground.  No poses or tool action are invented here.
robot_positions = {
    "2126 v003 | autonomous tend robot 01": (-1900.0, 1125.0, 0.0),
    "2126 v003 | autonomous tend robot 02": (-420.0, -1125.0, 0.0),
    "2126 v003 | autonomous tend robot 03": (875.0, 1125.0, 0.0),
    "2126 v003 | autonomous tend robot 04": (2200.0, -1125.0, 0.0),
    "2126 v003 | autonomous tend robot 05": (3500.0, 1125.0, 0.0),
}
for label, position in robot_positions.items():
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Automation actor missing: " + label)
    actor.set_actor_location(unreal.Vector(*position), False, False)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Automation.TransferCell")]

# Three large painted work islands give the wide open deck an intentional,
# readable hierarchy without reintroducing stripe clutter, walls, or a roof.
cube_mesh = static_mesh("/Engine/BasicShapes/Cube")
concrete = material("M_LB_PS2126v003_WarmConcrete")
work_islands = [
    cube("2126 v003 | broad infeed-and-hero work island", (-3460.0, 0.0, 25.0), (4400.0, 5200.0, 12.0), concrete, (unreal.Name("LB.Architecture.BroadWorkIsland"),)),
    cube("2126 v003 | broad transfer work island", (-125.0, 0.0, 25.0), (4000.0, 5200.0, 12.0), concrete, (unreal.Name("LB.Architecture.BroadWorkIsland"),)),
    cube("2126 v003 | broad outfeed work island", (3740.0, 0.0, 25.0), (3700.0, 5200.0, 12.0), concrete, (unreal.Name("LB.Architecture.BroadWorkIsland"),)),
]

# Tight, purpose-specific cameras.  The overview remains honest about the
# complete flow; the three story shots use the repaired hero, coil and outfeed
# assets as foreground structure rather than treating the floor as subject.
camera_specs = {
    "CAM v003 | compact whole-flow overview": (unreal.Vector(-6700.0, -8900.0, 3550.0), unreal.Vector(300.0, 0.0, 330.0), 54.0),
    "CAM v003 | compact press hero": (unreal.Vector(-4900.0, -3300.0, 1550.0), unreal.Vector(-1850.0, 0.0, 360.0), 45.0),
    "CAM v003 | coil to first press story": (unreal.Vector(-7100.0, -3200.0, 1450.0), unreal.Vector(-3950.0, 0.0, 330.0), 46.0),
    "CAM v003 | inspection to stillage story": (unreal.Vector(6350.0, -3600.0, 1500.0), unreal.Vector(4000.0, 0.0, 270.0), 48.0),
}
for label, (source, target, focal) in camera_specs.items():
    camera = actors[label]
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Camera actor invalid: " + label)
    camera.set_actor_location(source, False, False)
    camera.set_actor_rotation(aim(source, target), False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal)
    camera.tags = list(camera.tags) + [TAG]

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v039 candidate layout")
for path, expected in EXPECTED.items():
    actual = digest(path)
    if actual != expected:
        raise RuntimeError("Protected baseline changed during v039: " + str(path))

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__V003_HERO_STORY_LAYOUT_REFINED",
    "candidate_map": MAP,
    "protected_hashes": {str(path): digest(path) for path in EXPECTED},
    "hidden_non_candidate_rendering": hidden,
    "active_coil": {"actor": "2126 v003 | active bare galvanized coil", "location_cm": [-5575.0, 0.0, 187.3]},
    "wrapped_reserve": {"actor": "2126 v003 | wrapped graphite reserve coil", "location_cm": [-5525.0, 2150.0, 256.7]},
    "robots_repositioned": robot_positions,
    "work_islands": [actor.get_actor_label() for actor in work_islands],
    "camera_count_refined": len(camera_specs),
    "roof_created": False,
    "rect_lights_created": 0,
    "scope": "candidate-only layout, visibility, native painted floor islands, and camera refinement",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_HERO_STORY_V039_PASS")
