"""Prune superseded native blockout and make a clean roofless Meshy-line stage.

The prior candidate contains an early complete native-cube press shop beneath
the later, user-selected Meshy press assets.  That overlaps silhouettes,
creates a high gantry forest, and makes it impossible to judge the real
machines.  This pass hides that old static blockout (it never deletes it),
preserves the approved bare and wrapped coils, and builds only broad
native-Unreal floor/backdrop/rail composition around the reusable Meshy line.
"""

import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001"
MATERIAL_ROOT = ROOT + "/Materials"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_blockout_prune_v038.json"
TAG = unreal.Name("LB.PressShop.2126.BlockoutPrune.v038")
V001 = unreal.Name("LB.PressShop.2126.v001")
CUBE = "/Engine/BasicShapes/Cube"
COIL_LABELS = {
    "S00 | approved bare master coil",
    "S00 | approved wrapped master coil",
}


def sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def hide(actor):
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


def material(name, colour, roughness, metallic=0.0):
    path = MATERIAL_ROOT + "/" + name
    result = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if result is None:
        result = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(result, unreal.Material):
        raise RuntimeError("Could not create candidate material: " + name)
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(result)
    base = mel.create_material_expression(result, unreal.MaterialExpressionConstant3Vector, -320, -80)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = mel.create_material_expression(result, unreal.MaterialExpressionConstant, -320, 25)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(result, unreal.MaterialExpressionConstant, -320, 120)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(result)
    unreal.EditorAssetLibrary.save_loaded_asset(result, only_if_is_dirty=False)
    return result


def box(label, location, dimensions, surface, role):
    mesh = unreal.load_asset(CUBE)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("Native cube unavailable")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Could not create architecture: " + label)
    actor.set_actor_label(label)
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_world_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component.set_material(0, surface)
    actor.tags = [TAG, unreal.Name("LB.Visual.2126"), unreal.Name("LB.Architecture.OpenAir"), unreal.Name(role)]
    return actor


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("Blockout pruning v038 already applied")

# Preserve the user's two project coils.  Everything else from the v001
# static-mesh layer is historical native blockout, not the chosen Meshy line.
hidden_v001 = []
for actor in actors:
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    if V001 not in actor.tags or actor.get_actor_label() in COIL_LABELS:
        continue
    hide(actor)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.PressShop.2126.NativePrototype.Hidden")]
    hidden_v001.append(actor.get_actor_label())

# Existing v034 architecture was correct in scale but was designed around the
# blockout.  Hide it and stage the real line as a single clean composition.
hidden_v034 = []
for actor in actors:
    if unreal.Name("LB.PressShop.2126.ScaleCorrectEnvironment.v034") not in actor.tags:
        continue
    if isinstance(actor, unreal.StaticMeshActor):
        hide(actor)
        actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.PressShop.2126.ScaleCorrectEnvironment.Hidden")]
        hidden_v034.append(actor.get_actor_label())

mats = {
    "deck": material("M_LB_PS2126_SteamDeck_v038", (0.015, 0.017, 0.021), 0.72, 0.04),
    "pale_green": material("M_LB_PS2126_SteamPaleGreen_v038", (0.38, 0.56, 0.38), 0.78),
    "cream": material("M_LB_PS2126_SteamWarmWhite_v038", (0.896, 0.880, 0.806), 0.68),
    "green": material("M_LB_PS2126_SteamCairnwell_v038", (0.014, 0.070, 0.057), 0.50, 0.15),
    "yellow": material("M_LB_PS2126_SteamSafetyYellow_v038", (0.887, 0.547, 0.0), 0.45, 0.10),
    "steel": material("M_LB_PS2126_SteamSteel_v038", (0.162, 0.184, 0.205), 0.42, 0.62),
}

created = []
def add(*args):
    created.append(box(*args).get_actor_label())

# Broad graphic planes only: solid deck, clear green production zones and two
# cream avenues.  No micro-railings, no roof and no duplicated machinery.
add("2126 | v038 charcoal open process deck", (-4500.0, 0.0, -95.0), (38000.0, 16000.0, 110.0), mats["deck"], "LB.Architecture.Deck")
for label, x, length in (
    ("inbound", -13200.0, 6600.0),
    ("press-line-west", -5000.0, 7000.0),
    ("press-line-east", 2000.0, 7000.0),
    ("outbound", 8000.0, 4000.0),
):
    add("2126 | v038 pale-green " + label + " process zone", (x, 0.0, -20.0), (length, 6600.0, 38.0), mats["pale_green"], "LB.Architecture.Paint")
add("2126 | v038 cream operator avenue", (-4500.0, -4650.0, 5.0), (38000.0, 1100.0, 42.0), mats["cream"], "LB.Architecture.Paint")
add("2126 | v038 cream service avenue", (-4500.0, 4650.0, 5.0), (38000.0, 900.0, 42.0), mats["cream"], "LB.Architecture.Paint")

# One uncluttered 12 m facade and one rail make the open bay legible.  Neither
# creates a roof: both terminate in open sky above the machinery.
add("2126 | v038 warm-white rear process facade", (-4500.0, 3650.0, 600.0), (30000.0, 45.0, 1200.0), mats["cream"], "LB.Architecture.Backdrop")
add("2126 | v038 Cairnwell supervision stripe", (-4500.0, 3615.0, 735.0), (29800.0, 24.0, 250.0), mats["green"], "LB.Architecture.Backdrop")
add("2126 | v038 Safety-Yellow production datum", (-4500.0, 3585.0, 1050.0), (29800.0, 24.0, 50.0), mats["yellow"], "LB.Architecture.Backdrop")
add("2126 | v038 autonomous transfer rail", (-2800.0, 2200.0, 930.0), (23500.0, 100.0, 100.0), mats["steel"], "LB.Architecture.OverheadHandling")
add("2126 | v038 autonomous transfer carriage", (-2100.0, 2200.0, 840.0), (620.0, 180.0, 160.0), mats["yellow"], "LB.Architecture.OverheadHandling")
for x in (-14200.0, 8800.0):
    add("2126 | v038 rail terminal " + str(int(x)), (x, 2200.0, 450.0), (130.0, 180.0, 900.0), mats["steel"], "LB.Architecture.OverheadHandling")

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate map")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 changed")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__SUPERSEDED_NATIVE_BLOCKOUT_HIDDEN__CLEAN_MESHY_LINE_STAGED",
    "hidden_native_v001_static_actors": hidden_v001,
    "preserved_user_project_coils": sorted(COIL_LABELS),
    "hidden_v034_scale_environment": hidden_v034,
    "created_open_air_architecture": created,
    "real_meshy_press_actors_changed": False,
    "reused_robot_actors_changed": False,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_BLOCKOUT_PRUNE_V038_PASS")
