"""Restore a readable material hierarchy to the genuine Meshy station instances."""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_machine_hierarchy_v023.json"
TAG = unreal.Name("LB.PressShop.2126.v002.MachineHierarchy.v023")


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
        raise RuntimeError("Could not make candidate material " + name)
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -100)
    base.set_editor_property("constant", unreal.LinearColor(*base_colour, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 10)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 100)
    metal.set_editor_property("r", metallic)
    glow = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -170)
    glow.set_editor_property("constant", unreal.LinearColor(*emission_colour, 1.0))
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
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v023 pass already applied")

# Keep the approved six-colour vocabulary, but use it by role: charcoal main
# casings, warm-white panels, green only as an accent, and yellow/red safety
# details already present in the imported Meshy slots.  This reverses the
# blanket-green experiment without touching any source asset.
charcoal = make_surface("M_LB_PS2126v002_FoundryCharcoalReadable", (0.022, 0.027, 0.032), 0.56, 0.10, (0.018, 0.022, 0.027))
accent_green = make_surface("M_LB_PS2126v002_CairnwellGreenAccent", (0.0126, 0.0697, 0.0574), 0.45, 0.08, (0.004, 0.020, 0.016))
warm_concrete = make_surface("M_LB_PS2126v002_WarmConcreteFinalCandidate", (0.25, 0.23, 0.20), 0.88, 0.0, (0.020, 0.018, 0.015))
soft_zone = make_surface("M_LB_PS2126v002_PaleGreenZoneFinalCandidate", (0.20, 0.24, 0.21), 0.84, 0.0, (0.012, 0.016, 0.013))
warm_white = unreal.load_asset(ROOT + "/M_LB_PS2126v002_WarmWhite")
if not isinstance(warm_white, unreal.Material):
    raise RuntimeError("Expected candidate warm-white material")

press_labels = (
    "MESHY v002 | S02 Draw / form",
    "MESHY v002 | S03 Trim",
    "MESHY v002 | S04 Pierce",
    "MESHY v002 | S05 Flange / hem",
    "MESHY v002 | S06 Vision / outfeed",
)
for label in press_labels:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Meshy press unavailable: " + label)
    component = actor.static_mesh_component
    if len(component.static_mesh.static_materials) != 6:
        raise RuntimeError("Unexpected Meshy slots: " + label)
    component.set_material(0, charcoal)
    component.set_material(5, accent_green)
    if component.get_material(0).get_path_name() != charcoal.get_path_name():
        raise RuntimeError("Charcoal override rejected: " + label)
    if component.get_material(5).get_path_name() != accent_green.get_path_name():
        raise RuntimeError("Accent override rejected: " + label)
    actor.tags = list(actor.tags) + [TAG]

feeder = actors.get("S00 | Meshy coil-free autonomous feeder")
if not isinstance(feeder, unreal.StaticMeshActor):
    raise RuntimeError("Coil-free feeder unavailable")
feeder.static_mesh_component.set_material(0, warm_white)
feeder.tags = list(feeder.tags) + [TAG]

deck = actors.get("2126 v002 | charcoal factory deck")
if not isinstance(deck, unreal.StaticMeshActor):
    raise RuntimeError("Factory deck unavailable")
deck.static_mesh_component.set_material(0, warm_concrete)
deck.tags = list(deck.tags) + [TAG]
for label, actor in actors.items():
    if label.startswith("2126 v002 | pale-green process island") and isinstance(actor, unreal.StaticMeshActor):
        actor.static_mesh_component.set_material(0, soft_zone)
        actor.tags = list(actor.tags) + [TAG]

# The temporary cutaway walls did not survive the low camera test.  The new
# candidate remains roofless, and hiding these review-only walls opens the
# composition without deleting historical work.
hidden_walls = []
for label in ("2126 v002 | front cutaway elevation", "2126 v002 | west cutaway elevation", "2126 v002 | east cutaway elevation"):
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Expected review elevation missing: " + label)
    actor.static_mesh_component.set_visibility(False, True)
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Architecture.HiddenAfterCameraReview")]
    hidden_walls.append(label)

camera = actors.get("CAM v002 | coil-to-press story")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Inbound camera unavailable")
source = unreal.Vector(-20800.0, -6500.0, 2800.0)
target = unreal.Vector(-13600.0, 700.0, 620.0)
rotation = aim(source, target)
camera.set_actor_location(source, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 45.0)
camera.tags = list(camera.tags) + [TAG]
unreal.EditorLevelLibrary.set_level_viewport_camera_info(source, rotation)

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate map")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__MESHY_ROLE_BASED_PAINT_AND_ROOFLESS_CAMERA_COMPOSITION",
    "candidate_map": MAP,
    "source_meshes_modified": False,
    "press_slot_contract": {"0": "Foundry Charcoal", "1": "Warm White retained", "2": "Status Red retained", "3": "Safety Yellow retained", "4": "Steel retained", "5": "Cairnwell Green accent"},
    "review_elevations_hidden": hidden_walls,
    "camera": {"source_cm": [source.x, source.y, source.z], "target_cm": [target.x, target.y, target.z], "focal_length_mm": 45.0},
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_MACHINE_HIERARCHY_V023_PASS")
