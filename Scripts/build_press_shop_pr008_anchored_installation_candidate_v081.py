"""Build exact-footprint installation anchors on retained PR-008 v079."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008CalibratedLightingCandidate_v079"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008AnchoredInstallationCandidate_v081"
PREFIX = "LB_PR008_V081_"
DEST = "/Game/LineBoss/Stations/Press/PR008/AnchoredInstallation_v081"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_anchored_installation_candidate_v081.json"
INVENTORY = ROOT / "Saved/Audits/press_shop_pr008_grounding_inventory_v079.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_editing = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008AnchoredInstallationCandidate_v081.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate retained v079 to isolated v081")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v081 map")
    unreal.log("LINE_BOSS_PR008_V081_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)

inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
rows = {row["actor"]: row for row in inventory["actors"]}
base_labels = [
    "LB_PR008_V064_SM_CA_MW_PR008_EntryLoop_Frame_01",
    "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedFrame_01",
    "LB_PR008_V068_SM_CA_MW_PR008_PrePunchFrame_01",
    "LB_PR008_V069_SM_CA_MW_PR008_ShearFrame_01",
    "LB_PR008_V071_SM_CA_MW_PR008_HPU_BundSkid_01",
    "LB_PR008_V072_SM_CA_MW_PR008_CabinetPlinth_01",
]
missing = [label for label in base_labels if label not in rows]
if missing:
    raise RuntimeError(f"Grounding inventory is missing required bases: {missing}")


def anchor_material():
    name = "M_CA_MW_PR008_InstalledAnchorSteel_v081"
    path = f"{DEST}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create {path}")
    material_editing.delete_all_material_expressions(material)
    colour = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -300, -80)
    colour.set_editor_property("constant", unreal.LinearColor(0.24, 0.27, 0.28, 1.0))
    metallic = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 30)
    metallic.set_editor_property("r", 0.96)
    roughness = material_editing.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 120)
    roughness.set_editor_property("r", 0.31)
    material_editing.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    material_editing.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
    material_editing.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material_editing.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


material = anchor_material()


def spawn(label, mesh_path, location, scale):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        raise RuntimeError(f"Could not spawn {label}")
    actor.set_actor_label(PREFIX + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v081", "LB.Asset.CandidateNotPromoted",
        "LB.Foundation.PR008.MeasuredAnchor", "LB.Navigation.Neutral")]
    component = actor.static_mesh_component
    component.set_static_mesh(library.load_asset(mesh_path))
    component.set_world_scale3d(unreal.Vector(*scale))
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


assemblies = []
for base_index, base_label in enumerate(base_labels, start=1):
    row = rows[base_label]
    min_x, min_y = row["minimum_cm"][0], row["minimum_cm"][1]
    max_x, max_y = row["maximum_cm"][0], row["maximum_cm"][1]
    inset_x = min(5.0, (max_x - min_x) * 0.12)
    inset_y = min(5.0, (max_y - min_y) * 0.12)
    corners = [
        (min_x + inset_x, min_y + inset_y),
        (min_x + inset_x, max_y - inset_y),
        (max_x - inset_x, min_y + inset_y),
        (max_x - inset_x, max_y - inset_y),
    ]
    for corner_index, (x, y) in enumerate(corners, start=1):
        plate = spawn(
            f"Base{base_index:02d}_Anchor{corner_index:02d}_Plate",
            "/Engine/BasicShapes/Cube.Cube", (x, y, 6.25), (0.10, 0.10, 0.008))
        stud = spawn(
            f"Base{base_index:02d}_Anchor{corner_index:02d}_Stud",
            "/Engine/BasicShapes/Cylinder.Cylinder", (x, y, 8.0), (0.035, 0.035, 0.025))
        assemblies.append({
            "base_actor": base_label,
            "corner": corner_index,
            "world_xy_cm": [x, y],
            "plate_actor": plate.get_actor_label(),
            "stud_actor": stud.get_actor_label(),
        })

if len(assemblies) != 24:
    raise RuntimeError(f"Expected 24 measured anchor assemblies, built {len(assemblies)}")

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-anchored-installation-candidate-v081/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "MEASURED_MAJOR_BASE_FOOTPRINT_ANCHORS_BUILT_FROM_RETAINED_V079__EARLY_MOTION_CAMERA_GATE_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "inventory": str(INVENTORY.relative_to(ROOT)).replace("\\", "/"),
    "base_actor_count": len(base_labels),
    "anchor_assembly_count": len(assemblies),
    "anchor_actor_count": len(assemblies) * 2,
    "assemblies": assemblies,
    "plate_dimensions_cm": [10.0, 10.0, 0.8],
    "stud_diameter_height_cm": [3.5, 2.5],
    "native_machine_geometry_modified": False,
    "native_motion_modified": False,
    "measured_datums_modified": False,
    "new_anchor_collision": "NoCollision candidate detail",
    "new_anchor_navigation": "neutral",
    "line_boss_in_world": False,
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_unchanged": True,
    "rejected_pr008_v076_v078_v080_unchanged": True,
    "retained_v079_unchanged": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR008_V081_ANCHORED_INSTALLATION_BUILD_PASS anchors={len(assemblies)}")
unreal.SystemLibrary.quit_editor()
