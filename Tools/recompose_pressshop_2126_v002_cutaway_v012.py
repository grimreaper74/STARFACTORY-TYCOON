"""Give the roofless v002 line a readable cutaway-factory composition.

This pass is deliberately architectural, not a machine rebuild: a light
concrete floor and three perimeter elevations stop the management view reading
as isolated props in a black void.  There is explicitly no roof, canopy, or
overhead crossbeam geometry.
"""
import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_cutaway_composition_v012.json"
TAG = unreal.Name("LB.PressShop.2126.v002.CutawayComposition.v012")


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


def make_concrete():
    name = "M_LB_PS2126v002_WarmConcreteReadable"
    path = ROOT + "/" + name
    material = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        raise RuntimeError("Could not create warm concrete")
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -100)
    base.set_editor_property("constant", unreal.LinearColor(0.33, 0.30, 0.25, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 10)
    rough.set_editor_property("r", 0.86)
    emission = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -180)
    emission.set_editor_property("constant", unreal.LinearColor(0.020, 0.018, 0.014, 1.0))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(emission, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def spawn_wall(label, location, dimensions_cm, material, cube):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Could not place cutaway elevation " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, unreal.Name("LB.Architecture.CutawayElevation"), unreal.Name("LB.Visual.2126")]
    component = actor.static_mesh_component
    component.set_static_mesh(cube)
    component.set_world_scale3d(unreal.Vector(*(dimension / 100.0 for dimension in dimensions_cm)))
    component.set_material(0, material)
    component.set_visibility(True, True)
    component.set_render_in_main_pass(True)
    return actor


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate v002")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v012 cutaway composition already applied")

concrete = make_concrete()
glow_wall = unreal.load_asset(ROOT + "/M_LB_PS2126v002_ArchitecturalWarmWhiteGlow")
if not isinstance(glow_wall, unreal.Material):
    raise RuntimeError("Expected v008 architectural wall material")
deck = actors.get("2126 v002 | charcoal factory deck")
if not isinstance(deck, unreal.StaticMeshActor):
    raise RuntimeError("Missing factory deck")
deck.static_mesh_component.set_material(0, concrete)
deck.tags = list(deck.tags) + [TAG, unreal.Name("LB.Architecture.ConcreteFloor")]

cube = unreal.load_asset("/Engine/BasicShapes/Cube")
if not isinstance(cube, unreal.StaticMesh):
    raise RuntimeError("Native Unreal cube unavailable")
walls = (
    # A low foreground elevation preserves the high player's eye line while
    # enclosing the black exterior that spoiled the prior management capture.
    ("2126 v002 | front cutaway elevation", (-4200.0, -7200.0, 1650.0), (42000.0, 55.0, 3300.0)),
    ("2126 v002 | west cutaway elevation", (-22000.0, -1600.0, 1650.0), (55.0, 11200.0, 3300.0)),
    ("2126 v002 | east cutaway elevation", (13600.0, -1600.0, 1650.0), (55.0, 11200.0, 3300.0)),
)
placed = [spawn_wall(label, location, dimensions, glow_wall, cube).get_actor_label() for label, location, dimensions in walls]

camera = actors.get("CAM v002 | steam hero press run")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Missing hero camera")
source = unreal.Vector(-20000.0, -21000.0, 13500.0)
target = unreal.Vector(-5400.0, 0.0, 420.0)
rotation = aim(source, target)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 45.0)
camera.tags = list(camera.tags) + [TAG]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, rotation)

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v012 cutaway composition")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__ROOFLESS_CUTAWAY_COMPOSITION_APPLIED",
    "candidate_map": MAP,
    "deck_repaint": concrete.get_path_name(),
    "perimeter_elevations": placed,
    "new_dynamic_lights": 0,
    "new_machine_geometry": 0,
    "roof_created": False,
    "hero_camera": {"source_cm": [source.x, source.y, source.z], "target_cm": [target.x, target.y, target.z], "focal_length_mm": 45.0},
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_CUTAWAY_COMPOSITION_V012_PASS")
