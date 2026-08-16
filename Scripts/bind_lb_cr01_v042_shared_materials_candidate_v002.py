"""Bind corrected shared paint Candidate v002 to quarantined CR01 v042.

Only Blueprint component overrides and isolated candidate support-material
duplicates are changed.  Source FBXs, imported meshes and RP01 parent assets
remain untouched.  The result is still unpromoted visual evidence.
"""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v042/Blueprints/BP_LB_CR01_CleaningAMR_v042"
MATERIAL_ROOT = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v042/Materials"
SHARED_PAINT_ROOT = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v002"
RP_MATERIAL_ROOT = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Materials"
LEGACY_SOURCE_ROOT = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v038_ModularRig"
AUDIT = ROOT / "Saved/Audits/lb_cr01_v042_shared_material_bindings_v002.json"

asset_library = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary

SUPPORT_MATERIALS = [
    "M_LB_Condition_Oxide_v013",
    "M_LB_CR01_Bristle",
    "M_LB_CR01_BrushedSteel_v013",
    "M_LB_CR01_CertificationMark_v019",
    "M_LB_CR01_DormantDust_v015",
    "M_LB_CR01_DormantOxide_v015",
    "M_LB_CR01_MothballedGrime_v037",
    "M_LB_CR01_RecessBlack",
    "M_LB_CR01_RenewedRubber_v015",
    "M_LB_CR01_SensorGlass",
    "M_LB_CR01_ServiceFastener_v019",
    "M_LB_CR01_ServicePlate_Engrave_v019",
    "M_LB_CR01_ServicePlate_SS304_v019",
]


def require(path, cls=unreal.MaterialInterface):
    asset = asset_library.load_asset(path)
    if asset is None or not isinstance(asset, cls):
        raise RuntimeError(f"Missing required {cls.__name__}: {path}")
    return asset


if asset_library.does_directory_exist(MATERIAL_ROOT):
    raise RuntimeError(f"Refusing to overwrite existing v042 material candidate directory {MATERIAL_ROOT}")
blueprint = require(BP_PATH, unreal.Blueprint)

support = {}
duplicates = []
for name in SUPPORT_MATERIALS:
    source = f"{LEGACY_SOURCE_ROOT}/{name}"
    destination = f"{MATERIAL_ROOT}/{name}"
    require(source)
    if not asset_library.duplicate_asset(source, destination):
        raise RuntimeError(f"Could not duplicate support material {source} -> {destination}")
    material = require(destination)
    if not asset_library.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save duplicated support material {destination}")
    support[name] = material
    duplicates.append({"source": source, "candidate": material.get_path_name()})

shared_paint = {}
for semantic in ("BodyCharcoal", "SafetyYellow", "CairnwellGreen", "ServiceGrey"):
    for condition in ("Restored", "Mothballed"):
        key = f"{semantic}_{condition}"
        shared_paint[key] = require(
            f"{SHARED_PAINT_ROOT}/MI_LB_Robot_{semantic}_{condition}_v002",
            unreal.MaterialInstanceConstant,
        )

rp_materials = {
    "rubber": require(f"{RP_MATERIAL_ROOT}/M_LB_RP01_RubberBlack"),
    "lens": require(f"{RP_MATERIAL_ROOT}/M_LB_RP01_LensVertexTint"),
    "sensor": require(f"{RP_MATERIAL_ROOT}/M_LB_RP01_SensorGlass"),
}


def material_for(slot_name, condition):
    if "BodyCharcoal" in slot_name or "FrameAnthracite" in slot_name:
        return shared_paint[f"BodyCharcoal_{condition}"], "shared_paint_body"
    if "SafetyYellow" in slot_name:
        return shared_paint[f"SafetyYellow_{condition}"], "shared_paint_safety"
    if "CairnwellGreen" in slot_name:
        return shared_paint[f"CairnwellGreen_{condition}"], "shared_paint_brand"
    if "CairnwellWarmWhite" in slot_name:
        return shared_paint[f"ServiceGrey_{condition}"], "shared_paint_warm_white_proxy"
    if "RubberBlack" in slot_name or "RenewedRubber" in slot_name:
        return rp_materials["rubber"], "shared_rp01_rubber"
    if "LensVertexTint" in slot_name:
        return rp_materials["lens"], "shared_rp01_lens"
    if "SensorGlass" in slot_name:
        return rp_materials["sensor"], "shared_rp01_sensor_glass"
    exact = {
        "M_LB_Condition_Oxide_v013": "M_LB_Condition_Oxide_v013",
        "M_LB_CR01_Bristle": "M_LB_CR01_Bristle",
        "M_LB_CR01_BrushedSteel_v013": "M_LB_CR01_BrushedSteel_v013",
        "M_LB_CR01_CertificationMark_v019": "M_LB_CR01_CertificationMark_v019",
        "M_LB_CR01_DormantDust_v015": "M_LB_CR01_DormantDust_v015",
        "M_LB_CR01_DormantOxide_v015": "M_LB_CR01_DormantOxide_v015",
        "M_LB_CR01_MothballedGrime_v037": "M_LB_CR01_MothballedGrime_v037",
        "M_LB_CR01_RecessBlack": "M_LB_CR01_RecessBlack",
        "M_LB_CR01_ServiceFastener_v019": "M_LB_CR01_ServiceFastener_v019",
        "M_LB_CR01_ServicePlate_Engrave_v019": "M_LB_CR01_ServicePlate_Engrave_v019",
        "M_LB_CR01_ServicePlate_SS304_v019": "M_LB_CR01_ServicePlate_SS304_v019",
    }
    key = exact.get(slot_name)
    if key:
        return support[key], "isolated_candidate_support"
    return None, "unmapped"


components = {}
for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    name = str(data_library.get_variable_name(data))
    if not name or name == "None" or name in components:
        continue
    component = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
    if isinstance(component, unreal.StaticMeshComponent):
        components[name] = component

binding_rows = []
unmapped = []
shared_paint_binding_count = 0
for component_name, component in sorted(components.items()):
    mesh = component.get_editor_property("static_mesh")
    if mesh is None or not mesh.get_path_name().startswith("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v042/Meshes/"):
        continue
    condition = "Restored" if "Restored" in component_name else "Mothballed"
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        material, role = material_for(slot_name, condition)
        if material is None:
            unmapped.append({"component": component_name, "mesh": mesh.get_path_name(), "slot": index, "slot_name": slot_name})
            continue
        component.set_material(index, material)
        if role.startswith("shared_paint"):
            shared_paint_binding_count += 1
        binding_rows.append({
            "component": component_name,
            "mesh": mesh.get_path_name(),
            "condition": condition,
            "slot": index,
            "slot_name": slot_name,
            "material": material.get_path_name(),
            "role": role,
        })

if unmapped:
    raise RuntimeError(f"Unmapped CR01 v042 semantic material slots: {unmapped}")
bp_library.compile_blueprint(blueprint)
if not asset_library.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save bound Blueprint {BP_PATH}")

result = {
    "$schema": "line-boss/audit/lb-cr01-v042-shared-material-bindings-v002",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SHARED_PAINT_V002_BOUND_TO_QUARANTINED_CR01__FRESH_RENDER_GATE_REQUIRED__NOT_PROMOTED",
    "blueprint": BP_PATH,
    "shared_paint_root": SHARED_PAINT_ROOT,
    "shared_paint_binding_count": shared_paint_binding_count,
    "total_binding_count": len(binding_rows),
    "bindings": binding_rows,
    "isolated_support_materials": duplicates,
    "unmapped_slots": unmapped,
    "source_meshes_modified": False,
    "rp01_parent_modified": False,
    "open_gates": [
        "fresh reload component material audit",
        "robot-scale texture/normal tuning",
        "mothballed/restored state-switch implementation",
        "fresh fixed-camera Unreal Pro comparison",
        "all collision, runtime, navigation, docking and SaveGame gates"
    ],
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(
    f"LINE_BOSS_CR01_V042_SHARED_MATERIALS_V002_BIND_PASS total={len(binding_rows)} "
    f"shared_paint={shared_paint_binding_count} audit={AUDIT}"
)
unreal.SystemLibrary.quit_editor()
