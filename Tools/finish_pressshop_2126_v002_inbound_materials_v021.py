"""Make the two approved coil states readable in the candidate only."""
import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_inbound_materials_v021.json"
TAG = unreal.Name("LB.PressShop.2126.v002.InboundMaterials.v021")


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


def make_material(name, base_colour, roughness, metallic, emission_colour):
    path = ROOT + "/" + name
    material = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        raise RuntimeError("Could not create " + name)
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -100)
    base.set_editor_property("constant", unreal.LinearColor(*base_colour, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 10)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 100)
    metal.set_editor_property("r", metallic)
    emissive = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -170)
    emissive.set_editor_property("constant", unreal.LinearColor(*emission_colour, 1.0))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
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
    raise RuntimeError("v021 inbound-material pass already applied")
wrapped = actors.get("S00 | wrapped master coil | project reuse")
bare = actors.get("S00 | bare master coil | project reuse")
camera = actors.get("CAM v002 | coil-to-press story")
if not isinstance(wrapped, unreal.StaticMeshActor) or not isinstance(bare, unreal.StaticMeshActor):
    raise RuntimeError("Candidate coil actor missing")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Inbound camera missing")

bare_paint = make_material("M_LB_PS2126v002_BareCoilGalvanized", (0.60, 0.68, 0.72), 0.36, 0.62, (0.12, 0.14, 0.15))
wrapped_paint = make_material("M_LB_PS2126v002_WrappedCoilGraphite", (0.055, 0.065, 0.072), 0.72, 0.08, (0.035, 0.040, 0.044))
bare.static_mesh_component.set_material(0, bare_paint)
wrapped.static_mesh_component.set_material(0, wrapped_paint)
if bare.static_mesh_component.get_material(0).get_path_name() != bare_paint.get_path_name():
    raise RuntimeError("Bare-coil material gate failed")
if wrapped.static_mesh_component.get_material(0).get_path_name() != wrapped_paint.get_path_name():
    raise RuntimeError("Wrapped-coil material gate failed")

# Compact staged stock, still on the existing saddle and behind the active
# feeder coil; it reads as a clear spare rather than a second operating coil.
wrapped.set_actor_location(unreal.Vector(-14200.0, 1400.0, 257.69), False, False)
for actor in (wrapped, bare):
    actor.tags = list(actor.tags) + [TAG]

source = unreal.Vector(-18100.0, -4300.0, 3000.0)
target = unreal.Vector(-13800.0, 430.0, 310.0)
rotation = aim(source, target)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 64.0)
camera.tags = list(camera.tags) + [TAG]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, rotation)

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v021 inbound material pass")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__SEPARATE_COIL_STATES_VISIBLE_AT_MANAGEMENT_SCALE",
    "candidate_map": MAP,
    "source_meshes_modified": False,
    "bare_material": bare_paint.get_path_name(),
    "wrapped_material": wrapped_paint.get_path_name(),
    "wrapped_spare_location_cm": [-14200.0, 1400.0, 257.69],
    "camera": {"source_cm": [source.x, source.y, source.z], "target_cm": [target.x, target.y, target.z], "focal_length_mm": 64.0},
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_INBOUND_MATERIALS_V021_PASS")
