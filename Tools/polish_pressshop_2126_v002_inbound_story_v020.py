"""Finish the readable inbound coil state without altering source assets."""
import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_inbound_polish_v020.json"
TAG = unreal.Name("LB.PressShop.2126.v002.InboundPolish.v020")


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


def make_galvanized():
    name = "M_LB_PS2126v002_BareCoilGalvanized"
    path = ROOT + "/" + name
    material = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        raise RuntimeError("Could not create galvanized coil material")
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -100)
    base.set_editor_property("constant", unreal.LinearColor(0.35, 0.40, 0.43, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 10)
    rough.set_editor_property("r", 0.32)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 100)
    metal.set_editor_property("r", 0.75)
    glow = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -170)
    glow.set_editor_property("constant", unreal.LinearColor(0.030, 0.035, 0.038, 1.0))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate v002")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v020 inbound polish already applied")
wrapped = actors.get("S00 | wrapped master coil | project reuse")
bare = actors.get("S00 | bare master coil | project reuse")
camera = actors.get("CAM v002 | coil-to-press story")
if not isinstance(wrapped, unreal.StaticMeshActor) or not isinstance(bare, unreal.StaticMeshActor):
    raise RuntimeError("Candidate coil actor missing")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Inbound camera missing")

# Keep a compact reserve coil behind the active feeder coil.  The two states
# are intentionally distinct: dark wrapped stock versus reflective bare steel.
wrapped.set_actor_location(unreal.Vector(-14900.0, 1500.0, 257.69), False, False)
galvanized = make_galvanized()
bare.static_mesh_component.set_material(0, galvanized)
if bare.static_mesh_component.get_material(0).get_path_name() != galvanized.get_path_name():
    raise RuntimeError("Bare-coil instance paint did not apply")
for actor in (wrapped, bare):
    actor.tags = list(actor.tags) + [TAG]

source = unreal.Vector(-18400.0, -5200.0, 3300.0)
target = unreal.Vector(-14000.0, 450.0, 320.0)
rotation = aim(source, target)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 52.0)
camera.tags = list(camera.tags) + [TAG]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, rotation)

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v020 inbound polish")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__INBOUND_STOCK_AND_ACTIVE_COIL_STATES_POLISHED",
    "candidate_map": MAP,
    "source_meshes_modified": False,
    "wrapped_spare_location_cm": [-14900.0, 1500.0, 257.69],
    "bare_coil_material_override": galvanized.get_path_name(),
    "camera": {"source_cm": [source.x, source.y, source.z], "target_cm": [target.x, target.y, target.z], "focal_length_mm": 52.0},
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_INBOUND_POLISH_V020_PASS")
