"""Build and apply isolated PBR surfaces to PR-004 Candidate_v003.

The material masters use the locally installed, licensed Factory Environment
texture maps only as generic repeatable surface inputs.  Custom PR-004 geometry,
slot identity and gameplay pivots remain Line Boss assets.  Writes are confined
to Candidate_v003 and the dedicated validation map remains unpromoted.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
IMPORT_AUDIT = ROOT / "Saved/Audits/pr004_unreal_import_candidate_v003.json"
AUDIT = ROOT / "Saved/Audits/pr004_packaging_pbr_candidate_v003.json"
DEST = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003"

TEXTURE_SETS = {
    "metal": {
        "base": "/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_Metalbeam01_BC.T_Metalbeam01_BC",
        "normal": "/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_Metalbeam01_N.T_Metalbeam01_N",
        "orm": "/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_Metalbeam01_ORM.T_Metalbeam01_ORM",
    },
    "nonmetal": {
        "base": "/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_ConcretePillar01_BC.T_ConcretePillar01_BC",
        "normal": "/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_ConcretePillar01_N.T_ConcretePillar01_N",
        "orm": "/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_ConcretePillar01_ORM.T_ConcretePillar01_ORM",
    },
}

# Linear-space tints.  TextureInfluence deliberately remains restrained on the
# wrap so it reads as mottled polyethylene, not concrete.
SURFACES = {
    "CoilSteel": ("metal", (0.32, 0.37, 0.43, 1.0), 0.48, 5.5, 0.36, 0.50, 1.0, 0.45),
    "BandSteel": ("metal", (0.018, 0.022, 0.029, 1.0), 0.30, 8.0, 0.28, 0.32, 1.0, 0.35),
    "DullGreyWrap": ("nonmetal", (0.38, 0.42, 0.47, 1.0), 0.16, 11.0, 0.82, 0.20, 0.0, 0.12),
    "RemovedFilm": ("nonmetal", (0.30, 0.34, 0.39, 1.0), 0.18, 12.0, 0.78, 0.18, 0.0, 0.18),
    "CompactedFilm": ("nonmetal", (0.23, 0.27, 0.32, 1.0), 0.28, 9.0, 0.88, 0.30, 0.0, 0.28),
    "EdgeProtector": ("nonmetal", (0.31, 0.13, 0.035, 1.0), 0.36, 8.0, 0.91, 0.42, 0.0, 0.42),
    "IdentityLabel": ("nonmetal", (0.64, 0.61, 0.51, 1.0), 0.10, 3.0, 0.74, 0.12, 0.0, 0.08),
    "SafetyYellow": ("metal", (0.82, 0.42, 0.025, 1.0), 0.30, 5.0, 0.48, 0.34, 0.0, 0.32),
    "MaintenanceOrange": ("metal", (0.74, 0.18, 0.018, 1.0), 0.28, 5.0, 0.51, 0.35, 0.0, 0.30),
    "CastIron": ("metal", (0.055, 0.068, 0.082, 1.0), 0.50, 5.5, 0.60, 0.56, 0.78, 0.52),
    "MachinedSteel": ("metal", (0.39, 0.45, 0.52, 1.0), 0.42, 6.0, 0.25, 0.34, 1.0, 0.45),
    "MachineDark": ("metal", (0.045, 0.058, 0.071, 1.0), 0.44, 5.0, 0.53, 0.48, 0.55, 0.42),
    "Rubber": ("nonmetal", (0.012, 0.016, 0.021, 1.0), 0.12, 7.0, 0.84, 0.12, 0.0, 0.18),
    "HoseCable": ("nonmetal", (0.014, 0.019, 0.026, 1.0), 0.12, 8.0, 0.70, 0.15, 0.0, 0.16),
    "ServiceLabel": ("nonmetal", (0.49, 0.52, 0.55, 1.0), 0.10, 3.0, 0.68, 0.10, 0.0, 0.08),
    "WarningRed": ("metal", (0.60, 0.018, 0.012, 1.0), 0.18, 5.0, 0.46, 0.22, 0.0, 0.20),
    "ReadyGreen": ("metal", (0.025, 0.46, 0.09, 1.0), 0.18, 5.0, 0.46, 0.22, 0.0, 0.20),
    "SensorBlue": ("metal", (0.035, 0.18, 0.40, 1.0), 0.16, 5.0, 0.36, 0.20, 0.20, 0.18),
    "OpaqueSensorLens": ("nonmetal", (0.025, 0.075, 0.13, 1.0), 0.08, 4.0, 0.22, 0.08, 0.0, 0.06),
    "GreaseResidue": ("nonmetal", (0.018, 0.013, 0.008, 1.0), 0.12, 7.0, 0.30, 0.10, 0.0, 0.12),
}


def load_texture(path: str) -> unreal.Texture:
    texture = unreal.load_asset(path)
    if not isinstance(texture, unreal.Texture):
        raise RuntimeError(f"Licensed PBR texture input missing: {path}")
    return texture


def expression(material, klass, x: int, y: int):
    return unreal.MaterialEditingLibrary.create_material_expression(material, klass, x, y)


def build_master(kind: str, paths: dict[str, str]):
    name = f"M_LB_PR004_{kind.title()}PBR_Master_v003"
    path = f"{DEST}/{name}"
    library = unreal.EditorAssetLibrary
    material = library.load_asset(path)
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, DEST, unreal.Material, unreal.MaterialFactoryNew()
        )
    if hasattr(unreal.MaterialEditingLibrary, "delete_all_material_expressions"):
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    material.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})

    uv = expression(material, unreal.MaterialExpressionTextureCoordinate, -1250, 0)
    scale = expression(material, unreal.MaterialExpressionScalarParameter, -1250, 130)
    scale.set_editor_properties({"parameter_name": "TextureScale", "default_value": 6.0})
    scaled_uv = expression(material, unreal.MaterialExpressionMultiply, -1030, 20)
    unreal.MaterialEditingLibrary.connect_material_expressions(uv, "", scaled_uv, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(scale, "", scaled_uv, "B")

    base = expression(material, unreal.MaterialExpressionTextureSample, -800, -180)
    base.set_editor_property("texture", load_texture(paths["base"]))
    unreal.MaterialEditingLibrary.connect_material_expressions(scaled_uv, "", base, "UVs")
    tint = expression(material, unreal.MaterialExpressionVectorParameter, -800, 20)
    tint.set_editor_properties({
        "parameter_name": "SurfaceTint",
        "default_value": unreal.LinearColor(0.35, 0.38, 0.42, 1.0),
    })
    textured_tint = expression(material, unreal.MaterialExpressionMultiply, -560, -80)
    unreal.MaterialEditingLibrary.connect_material_expressions(base, "RGB", textured_tint, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(tint, "", textured_tint, "B")
    texture_influence = expression(material, unreal.MaterialExpressionScalarParameter, -560, 90)
    texture_influence.set_editor_properties({"parameter_name": "TextureInfluence", "default_value": 0.35})
    base_lerp = expression(material, unreal.MaterialExpressionLinearInterpolate, -320, -20)
    unreal.MaterialEditingLibrary.connect_material_expressions(tint, "", base_lerp, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(textured_tint, "", base_lerp, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(texture_influence, "", base_lerp, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_property(base_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)

    normal = expression(material, unreal.MaterialExpressionTextureSample, -800, 280)
    normal.set_editor_properties({
        "texture": load_texture(paths["normal"]),
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
    })
    unreal.MaterialEditingLibrary.connect_material_expressions(scaled_uv, "", normal, "UVs")
    flat_normal = expression(material, unreal.MaterialExpressionVectorParameter, -800, 440)
    flat_normal.set_editor_properties({
        "parameter_name": "FlatNormal",
        "default_value": unreal.LinearColor(0.5, 0.5, 1.0, 1.0),
    })
    normal_strength = expression(material, unreal.MaterialExpressionScalarParameter, -560, 440)
    normal_strength.set_editor_properties({"parameter_name": "NormalStrength", "default_value": 0.35})
    normal_lerp = expression(material, unreal.MaterialExpressionLinearInterpolate, -320, 340)
    unreal.MaterialEditingLibrary.connect_material_expressions(flat_normal, "", normal_lerp, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(normal, "RGB", normal_lerp, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(normal_strength, "", normal_lerp, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_property(normal_lerp, "", unreal.MaterialProperty.MP_NORMAL)

    orm = expression(material, unreal.MaterialExpressionTextureSample, -800, 650)
    orm.set_editor_properties({
        "texture": load_texture(paths["orm"]),
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR,
    })
    unreal.MaterialEditingLibrary.connect_material_expressions(scaled_uv, "", orm, "UVs")
    roughness = expression(material, unreal.MaterialExpressionScalarParameter, -560, 680)
    roughness.set_editor_properties({"parameter_name": "BaseRoughness", "default_value": 0.55})
    rough_influence = expression(material, unreal.MaterialExpressionScalarParameter, -560, 810)
    rough_influence.set_editor_properties({"parameter_name": "RoughTextureInfluence", "default_value": 0.35})
    rough_lerp = expression(material, unreal.MaterialExpressionLinearInterpolate, -320, 680)
    unreal.MaterialEditingLibrary.connect_material_expressions(roughness, "", rough_lerp, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(orm, "G", rough_lerp, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(rough_influence, "", rough_lerp, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_property(rough_lerp, "", unreal.MaterialProperty.MP_ROUGHNESS)
    metallic = expression(material, unreal.MaterialExpressionScalarParameter, -320, 850)
    metallic.set_editor_properties({"parameter_name": "Metallic", "default_value": 0.0})
    unreal.MaterialEditingLibrary.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.connect_material_property(orm, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)

    unreal.MaterialEditingLibrary.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def build_instance(name: str, parent, values):
    _kind, tint, texture_influence, scale, roughness, rough_influence, metallic, normal_strength = values
    asset_name = f"MI_LB_PR004_{name}_PBR_v003"
    path = f"{DEST}/{asset_name}"
    library = unreal.EditorAssetLibrary
    instance = library.load_asset(path)
    if instance is None:
        instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            asset_name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew()
        )
    instance.set_editor_property("parent", parent)
    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_vector_parameter_value(instance, "SurfaceTint", unreal.LinearColor(*tint))
    for parameter, value in (
        ("TextureInfluence", texture_influence),
        ("TextureScale", scale),
        ("BaseRoughness", roughness),
        ("RoughTextureInfluence", rough_influence),
        ("Metallic", metallic),
        ("NormalStrength", normal_strength),
    ):
        mel.set_material_instance_scalar_parameter_value(instance, parameter, value)
    # Ensure the render resource sees scripted parameter changes before the
    # validation level is saved and captured.
    mel.update_material_instance(instance)
    library.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


import_audit = json.loads(IMPORT_AUDIT.read_text(encoding="utf-8"))
if import_audit.get("status") != "UNREAL_IMPORT_CANDIDATE_NOT_PROMOTED":
    raise RuntimeError("Candidate_v003 import audit is missing or not quarantined")

masters = {kind: build_master(kind, paths) for kind, paths in TEXTURE_SETS.items()}
instances = {
    name: build_instance(name, masters[values[0]], values)
    for name, values in SURFACES.items()
}

target_families = {"packaging_v003", "powered_cradle_v001"}
records = []
for imported in import_audit["imported_assets"]:
    if imported["family"] not in target_families:
        continue
    mesh = unreal.load_asset(imported["asset"])
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Imported static mesh missing: {imported['asset']}")
    assignments = imported.get("opaque_material_assignments", [])
    if len(assignments) != int(imported.get("source_material_slot_count", -1)):
        raise RuntimeError(f"Slot audit mismatch for {mesh.get_path_name()}")
    applied = []
    for slot_index, assignment in enumerate(assignments):
        key = assignment["material_key"]
        material = instances.get(key)
        if material is None:
            # A rare cradle service category can safely retain its controlled
            # opaque candidate material until it receives a dedicated PBR spec.
            applied.append({"slot": slot_index, "key": key, "status": "RETAINED_EXISTING"})
            continue
        mesh.set_material(slot_index, material)
        applied.append({
            "slot": slot_index,
            "source_slot": assignment["slot"],
            "key": key,
            "material": material.get_path_name(),
            "status": "PBR_REBOUND",
        })
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    records.append({"family": imported["family"], "mesh": mesh.get_path_name(), "assignments": applied})

payload = {
    "$schema": "line-boss/audit/pr004-packaging-pbr-candidate-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PBR_MATERIAL_CANDIDATE_APPLIED_NOT_PROMOTED",
    "destination": DEST,
    "licensed_texture_inputs": TEXTURE_SETS,
    "masters": {name: asset.get_path_name() for name, asset in masters.items()},
    "instances": {name: asset.get_path_name() for name, asset in instances.items()},
    "target_families": sorted(target_families),
    "mesh_count": len(records),
    "meshes": records,
    "blend_mode": "OPAQUE_ONLY",
    "visual_gate": "PENDING_FRESH_FIXED_CAMERA_REVIEW",
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_PBR_V003_PASS meshes={len(records)} audit={AUDIT}")
