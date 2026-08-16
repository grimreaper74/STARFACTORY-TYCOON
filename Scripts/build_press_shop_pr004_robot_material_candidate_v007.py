"""Create a non-destructive integrated PR-004 robot material candidate.

The accepted v009 geometry and its source static meshes are preserved.  This
script duplicates only the v006 integration map and applies per-component
material overrides to the robot_v002 actors in the duplicate.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
IMPORT_AUDIT = ROOT / "Saved/Audits/pr004_unreal_import_candidate_v003.json"
AUDIT = ROOT / "Saved/Audits/press_shop_pr004_robot_material_candidate_v007.json"
BASE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
DEST_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004MaterialCandidate_v007"
DEST_MATERIALS = "/Game/LineBoss/Stations/Press/PR004/Candidate_v009/MaterialsPBR_Robot_v001"
PREFIX = "LB_INT_PR004_V009_robot_v002_"
MASTER_ROOT = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003"

# Deliberately restrained texture influence: this is aged painted machinery,
# not concrete and not heavily corroded scrap.
SURFACES = {
    "CastIron": ("metal", (0.045, 0.060, 0.073, 1.0), 0.22, 7.0, 0.62, 0.25, 0.78, 0.20),
    "SafetyYellow": ("metal", (0.82, 0.42, 0.025, 1.0), 0.16, 8.0, 0.55, 0.20, 0.0, 0.14),
    "MachinedSteel": ("metal", (0.38, 0.44, 0.50, 1.0), 0.14, 9.0, 0.28, 0.18, 1.0, 0.12),
    "MachineDark": ("metal", (0.035, 0.045, 0.055, 1.0), 0.20, 8.0, 0.60, 0.22, 0.50, 0.16),
    "Rubber": ("nonmetal", (0.010, 0.014, 0.019, 1.0), 0.08, 9.0, 0.82, 0.10, 0.0, 0.08),
    "HoseCable": ("nonmetal", (0.012, 0.017, 0.023, 1.0), 0.08, 10.0, 0.72, 0.10, 0.0, 0.08),
    "GreaseResidue": ("nonmetal", (0.015, 0.011, 0.007, 1.0), 0.12, 8.0, 0.34, 0.12, 0.0, 0.10),
    "ServiceLabel": ("nonmetal", (0.48, 0.51, 0.54, 1.0), 0.04, 4.0, 0.68, 0.05, 0.0, 0.04),
    "WarningRed": ("metal", (0.60, 0.018, 0.012, 1.0), 0.08, 7.0, 0.48, 0.10, 0.0, 0.08),
    "ReadyGreen": ("metal", (0.025, 0.46, 0.09, 1.0), 0.08, 7.0, 0.48, 0.10, 0.0, 0.08),
    "SensorBlue": ("metal", (0.035, 0.18, 0.40, 1.0), 0.06, 7.0, 0.38, 0.08, 0.20, 0.06),
    "OpaqueSensorLens": ("nonmetal", (0.025, 0.075, 0.13, 1.0), 0.03, 6.0, 0.24, 0.04, 0.0, 0.03),
}


def vector(value):
    return [round(value.x, 5), round(value.y, 5), round(value.z, 5)]


def build_instance(key, spec):
    kind, tint, texture_influence, scale, roughness, rough_influence, metallic, normal_strength = spec
    parent_name = "MetalPBR" if kind == "metal" else "NonmetalPBR"
    parent = unreal.load_asset(f"{MASTER_ROOT}/M_LB_PR004_{parent_name}_Master_v003")
    if parent is None:
        raise RuntimeError(f"Missing PBR parent for {key}")
    name = f"MI_LB_PR004_Robot_{key}_PBR_v001"
    path = f"{DEST_MATERIALS}/{name}"
    instance = unreal.EditorAssetLibrary.load_asset(path)
    if instance is None:
        instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, DEST_MATERIALS, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew()
        )
    instance.set_editor_property("parent", parent)
    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_vector_parameter_value(instance, "SurfaceTint", unreal.LinearColor(*tint))
    for parameter, value in (
        ("TextureInfluence", texture_influence), ("TextureScale", scale),
        ("BaseRoughness", roughness), ("RoughTextureInfluence", rough_influence),
        ("Metallic", metallic), ("NormalStrength", normal_strength),
    ):
        mel.set_material_instance_scalar_parameter_value(instance, parameter, value)
    mel.update_material_instance(instance)
    unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


library = unreal.EditorAssetLibrary
if not library.does_asset_exist(BASE_MAP):
    raise RuntimeError(f"Missing base map {BASE_MAP}")
if library.does_asset_exist(DEST_MAP):
    if not library.delete_asset(DEST_MAP):
        raise RuntimeError(f"Could not replace existing candidate {DEST_MAP}")
if not library.duplicate_asset(BASE_MAP, DEST_MAP):
    raise RuntimeError(f"Could not duplicate {BASE_MAP}")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(DEST_MAP):
    raise RuntimeError(f"Could not load {DEST_MAP}")

source = json.loads(IMPORT_AUDIT.read_text(encoding="utf-8"))
robot_records = {
    item["asset"].rsplit("/", 1)[-1].split(".", 1)[0]: item
    for item in source["imported_assets"] if item["family"] == "robot_v002"
}
instances = {key: build_instance(key, spec) for key, spec in SURFACES.items()}

records = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith(PREFIX):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or component.static_mesh is None:
        continue
    mesh_path = component.static_mesh.get_path_name()
    mesh_name = component.static_mesh.get_name()
    imported = robot_records.get(mesh_name)
    if imported is None:
        raise RuntimeError(f"Robot actor uses unaudited mesh: {label}: {mesh_path}")
    before_location = actor.get_actor_location()
    before_rotation = actor.get_actor_rotation()
    before_scale = actor.get_actor_scale3d()
    assignments = imported["opaque_material_assignments"]
    if len(assignments) != component.get_num_materials():
        raise RuntimeError(f"Material slot count changed for {label}")
    applied = []
    for index, assignment in enumerate(assignments):
        key = assignment["material_key"]
        material = instances.get(key)
        if material is None:
            applied.append({"slot": index, "key": key, "status": "RETAINED_EXISTING"})
            continue
        component.set_material(index, material)
        applied.append({"slot": index, "key": key, "material": material.get_path_name(), "status": "ACTOR_OVERRIDE"})
    after_location = actor.get_actor_location()
    after_rotation = actor.get_actor_rotation()
    after_scale = actor.get_actor_scale3d()
    unchanged = (
        vector(before_location) == vector(after_location)
        and [round(before_rotation.roll, 5), round(before_rotation.pitch, 5), round(before_rotation.yaw, 5)]
        == [round(after_rotation.roll, 5), round(after_rotation.pitch, 5), round(after_rotation.yaw, 5)]
        and vector(before_scale) == vector(after_scale)
    )
    if not unchanged:
        raise RuntimeError(f"Transform changed while applying materials: {label}")
    records.append({"actor": label, "mesh": mesh_path, "transform_unchanged": unchanged, "assignments": applied})

if len(records) != 28:
    raise RuntimeError(f"Expected 28 integrated robot modules, found {len(records)}")
levels.save_current_level()

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-robot-material-candidate-v007/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "MAP_LOCAL_PBR_CONDITION_CANDIDATE_NOT_PROMOTED",
    "base_map": BASE_MAP,
    "candidate_map": DEST_MAP,
    "source_geometry_preserved": True,
    "accepted_layout_preserved": all(item["transform_unchanged"] for item in records),
    "robot_module_count": len(records),
    "materials": {key: value.get_path_name() for key, value in instances.items()},
    "actors": records,
    "collision_gate": "UNCHANGED__SOURCE_COMPLEX_AS_SIMPLE_RELEASE_FIX_STILL_REQUIRED",
    "visual_gate": "PENDING_FRESH_FIXED_CAMERA_REVIEW",
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_ROBOT_MATERIAL_V007_PASS actors={len(records)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
