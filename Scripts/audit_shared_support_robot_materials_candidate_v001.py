"""Fresh-process reload audit for shared support-robot material Candidate v001."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
DEST = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v001"
MASTER_PATH = f"{DEST}/M_LB_SupportRobot_LayeredPaint_v001"
OUT = ROOT / "Saved/Audits/lb_support_robot_shared_materials_candidate_v001.json"

EXPECTED = {
    "MI_LB_Robot_BodyCharcoal_Restored_v001": {"DustAmount": 0.08, "PaintCoverageBias": 0.86, "BaseRoughness": 0.56},
    "MI_LB_Robot_BodyCharcoal_Mothballed_v001": {"DustAmount": 0.42, "PaintCoverageBias": 0.67, "BaseRoughness": 0.72},
    "MI_LB_Robot_SafetyYellow_Restored_v001": {"DustAmount": 0.10, "PaintCoverageBias": 0.88, "BaseRoughness": 0.54},
    "MI_LB_Robot_SafetyYellow_Mothballed_v001": {"DustAmount": 0.38, "PaintCoverageBias": 0.69, "BaseRoughness": 0.70},
    "MI_LB_Robot_CairnwellGreen_Restored_v001": {"DustAmount": 0.08, "PaintCoverageBias": 0.87, "BaseRoughness": 0.55},
    "MI_LB_Robot_CairnwellGreen_Mothballed_v001": {"DustAmount": 0.40, "PaintCoverageBias": 0.68, "BaseRoughness": 0.71},
    "MI_LB_Robot_ServiceGrey_Restored_v001": {"DustAmount": 0.07, "PaintCoverageBias": 0.90, "BaseRoughness": 0.52},
    "MI_LB_Robot_ServiceGrey_Mothballed_v001": {"DustAmount": 0.36, "PaintCoverageBias": 0.72, "BaseRoughness": 0.69},
}

TEXTURE_PACKAGES = {
    "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_Base_Color_Metal_Paint_Chips",
    "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_Normal_Metal_Paint_Chips",
    "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_ORD_Metal_Paint_Chips",
}

lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
failures = []

master = lib.load_asset(MASTER_PATH)
if not isinstance(master, unreal.Material):
    failures.append(f"Missing master material {MASTER_PATH}")
    raise RuntimeError(failures[-1])

mel.recompile_material(master)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

registry = unreal.AssetRegistryHelpers.get_asset_registry()
options = unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=True,
    include_hard_package_references=True,
    include_searchable_names=False,
    include_soft_management_references=False,
    include_hard_management_references=False,
)
dependencies = {str(value) for value in registry.get_dependencies(MASTER_PATH, options)}
missing_textures = sorted(TEXTURE_PACKAGES - dependencies)
if missing_textures:
    failures.append(f"Master is missing required Surface Forge texture dependencies: {missing_textures}")

rows = []
for name, expected_scalars in EXPECTED.items():
    path = f"{DEST}/{name}"
    instance = lib.load_asset(path)
    if not isinstance(instance, unreal.MaterialInstanceConstant):
        failures.append(f"Missing material instance {path}")
        continue
    parent = instance.get_editor_property("parent")
    parent_path = parent.get_path_name().split(".", 1)[0] if parent else None
    if parent_path != MASTER_PATH:
        failures.append(f"{name} parent is {parent_path}, expected {MASTER_PATH}")
    scalars = {}
    for parameter, expected in expected_scalars.items():
        actual = float(mel.get_material_instance_scalar_parameter_value(instance, parameter))
        scalars[parameter] = actual
        if abs(actual - expected) > 1.0e-4:
            failures.append(f"{name}.{parameter}={actual}, expected {expected}")
    rows.append({"asset": path, "parent": parent_path, "scalar_parameters": scalars})

all_asset_objects = lib.list_assets(DEST, recursive=False, include_folder=False)
all_assets = sorted({path.split(".", 1)[0] for path in all_asset_objects})
unexpected_assets = sorted(set(all_assets) - {MASTER_PATH, *[f"{DEST}/{name}" for name in EXPECTED]})
if unexpected_assets:
    failures.append(f"Unexpected assets in isolated candidate path: {unexpected_assets}")

result = {
    "$schema": "line-boss/audit/lb-support-robot-shared-materials-candidate-v001",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FRESH_RELOAD_TECHNICAL_GATE_PASS__ROBOT_BINDING_AND_VISUAL_GATES_OPEN__NOT_PROMOTED" if not failures else "FRESH_RELOAD_TECHNICAL_GATE_FAIL__NOT_PROMOTED",
    "master": MASTER_PATH,
    "asset_count": len(all_assets),
    "instances": rows,
    "dependencies": sorted(dependencies),
    "required_surface_forge_texture_packages": sorted(TEXTURE_PACKAGES),
    "missing_surface_forge_texture_packages": missing_textures,
    "initial_build_log": "Saved/Logs/LB_SupportRobot_Materials_v001.log",
    "initial_build_log_note": "Assets saved and content-validated; the first audit-write step failed on a lowercase Python boolean. This fresh process is the authoritative technical reload result.",
    "material_compile_requested": True,
    "source_assets_modified": False,
    "maps_modified": False,
    "open_gates": [
        "semantic material-slot binding on CR01 and MR01",
        "mesh/UV-specific condition masks",
        "fresh fixed-camera Unreal comparison against both Pro sheets",
        "performance and packaged-runtime validation"
    ],
    "failures": failures,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
if failures:
    unreal.log_error(f"LINE_BOSS_SHARED_SUPPORT_ROBOT_MATERIALS_V001_AUDIT_FAIL failures={len(failures)} audit={OUT}")
    raise RuntimeError("; ".join(failures))
unreal.log(f"LINE_BOSS_SHARED_SUPPORT_ROBOT_MATERIALS_V001_AUDIT_PASS assets={len(all_assets)} audit={OUT}")
unreal.SystemLibrary.quit_editor()
