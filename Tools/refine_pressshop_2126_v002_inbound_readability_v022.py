"""Repair the v002 inbound shot: credible coil staging, soft zones, low camera."""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_inbound_readability_v022.json"
TAG = unreal.Name("LB.PressShop.2126.v002.InboundReadability.v022")


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


def make_surface(name, base_colour, roughness, metallic, emission_colour):
    path = ROOT + "/" + name
    material = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        raise RuntimeError("Could not make candidate surface " + name)
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
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v022 pass already applied")

deck = actors.get("2126 v002 | charcoal factory deck")
wrapped = actors.get("S00 | wrapped master coil | project reuse")
bare = actors.get("S00 | bare master coil | project reuse")
camera = actors.get("CAM v002 | coil-to-press story")
if not all((isinstance(deck, unreal.StaticMeshActor), isinstance(wrapped, unreal.StaticMeshActor), isinstance(bare, unreal.StaticMeshActor), isinstance(camera, unreal.CineCameraActor))):
    raise RuntimeError("Inbound composition actors unavailable")

# Keep the factory bright but let the pale-green islands read as painted zones,
# not as a saturated green carpet in a low camera shot.
warm_concrete = make_surface("M_LB_PS2126v002_WarmConcreteSteam", (0.18, 0.16, 0.13), 0.86, 0.0, (0.035, 0.030, 0.022))
soft_green = make_surface("M_LB_PS2126v002_PaleGreenSteam", (0.13, 0.20, 0.15), 0.82, 0.0, (0.018, 0.030, 0.022))
graphite = make_surface("M_LB_PS2126v002_WrappedCoilGraphiteReadable", (0.10, 0.115, 0.125), 0.72, 0.08, (0.040, 0.048, 0.052))
deck.static_mesh_component.set_material(0, warm_concrete)
zones = []
for label, actor in actors.items():
    if label.startswith("2126 v002 | pale-green process island") and isinstance(actor, unreal.StaticMeshActor):
        actor.static_mesh_component.set_material(0, soft_green)
        actor.tags = list(actor.tags) + [TAG]
        zones.append(label)
if len(zones) != 4:
    raise RuntimeError("Expected four process zones")
wrapped.static_mesh_component.set_material(0, graphite)

# Restore the planned transfer state: the wrapped reserve sits on its existing
# changeover saddle; the bare coil remains installed at the coil-free feeder.
wrapped.set_actor_location(unreal.Vector(-15800.0, 1700.0, 257.69), False, False)
for actor in (deck, wrapped, bare):
    actor.tags = list(actor.tags) + [TAG]

# A near-level management camera shows feeder, active coil and reserve stock
# together, while the floor only anchors the composition.
source = unreal.Vector(-19100.0, -4800.0, 1300.0)
target = unreal.Vector(-13000.0, 350.0, 600.0)
rotation = aim(source, target)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 64.0)
camera.tags = list(camera.tags) + [TAG]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, rotation)

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate map")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__INBOUND_STOCK_STAGING_AND_LOW_CAMERA_REPAIRED",
    "candidate_map": MAP,
    "source_meshes_modified": False,
    "wrapped_reserve_location_cm": [-15800.0, 1700.0, 257.69],
    "bare_active_location_cm": [-13200.0, 0.0, 187.34],
    "camera": {"source_cm": [source.x, source.y, source.z], "target_cm": [target.x, target.y, target.z], "focal_length_mm": 64.0},
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_INBOUND_READABILITY_V022_PASS")
