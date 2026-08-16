"""Preserve RP01 v001 and build a corrected reusable visual parent candidate."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_BP = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Blueprints/BP_LB_RP01_MobileBase"
BP_PATH = "/Game/LineBoss/Robots/Shared/RP01/Candidate_v002/Blueprints/BP_LB_RP01_MobileBase"
AUDIT = ROOT / "Saved/Audits/lb_rp01_mobile_base_candidate_v002_build.json"
SHARED_PAINT = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v002"
CR_SUPPORT = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v052/Materials"

asset_library = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary


def require(path, cls=None):
    asset = asset_library.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


if asset_library.does_asset_exist(BP_PATH) or asset_library.does_directory_exist("/Game/LineBoss/Robots/Shared/RP01/Candidate_v002"):
    raise RuntimeError("Refusing to overwrite preserved RP01 Candidate v002")
require(SOURCE_BP, unreal.Blueprint)
if not asset_library.duplicate_asset(SOURCE_BP, BP_PATH):
    raise RuntimeError(f"Could not duplicate {SOURCE_BP} -> {BP_PATH}")
blueprint = require(BP_PATH, unreal.Blueprint)

components = {}
for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    name = str(data_library.get_variable_name(data))
    if name and name != "None" and name not in components:
        components[name] = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)

corrected_locations = {}
for suffix in ("DriveWheel", "DriveRim", "DriveHubCap", "DriveBearing"):
    corrected_locations[f"Visual_{suffix}_L"] = (10.0, 40.5, -17.0)
    corrected_locations[f"Visual_{suffix}_R"] = (10.0, -40.5, -17.0)
for suffix in ("CasterForkArmA", "CasterForkArmB", "CasterSwivelBearing"):
    corrected_locations[f"Visual_{suffix}_F"] = (-47.0, 0.0, -16.0)
    corrected_locations[f"Visual_{suffix}_R"] = (53.0, 0.0, -16.0)
for suffix in ("CasterWheel", "CasterRim"):
    corrected_locations[f"Visual_{suffix}_F"] = (-47.0, 0.0, -8.0)
    corrected_locations[f"Visual_{suffix}_R"] = (53.0, 0.0, -8.0)
for suffix in ("DockAlignmentPlate", "DockGuideCone_L", "DockGuideCone_R", "ChargingContact_N45", "ChargingContact_P45"):
    corrected_locations[f"Visual_{suffix}"] = (73.5, 0.0, -31.0)

transform_rows = []
for name, location in corrected_locations.items():
    component = components.get(name)
    if not isinstance(component, unreal.SceneComponent):
        raise RuntimeError(f"Missing RP01 correction target {name}")
    old = list(component.get_editor_property("relative_location").to_tuple())
    component.set_editor_property("relative_location", unreal.Vector(*location))
    transform_rows.append({"component": name, "old_relative_location_cm": old, "new_relative_location_cm": list(location)})

materials = {
    "body": require(f"{SHARED_PAINT}/MI_LB_Robot_BodyCharcoal_Mothballed_v002", unreal.MaterialInterface),
    "yellow": require(f"{SHARED_PAINT}/MI_LB_Robot_SafetyYellow_Mothballed_v002", unreal.MaterialInterface),
    "rubber": require(f"{CR_SUPPORT}/M_LB_CR01_Bristle", unreal.MaterialInterface),
    "steel": require(f"{CR_SUPPORT}/M_LB_CR01_BrushedSteel_v013", unreal.MaterialInterface),
    "sensor": require(f"{CR_SUPPORT}/M_LB_CR01_SensorGlass", unreal.MaterialInterface),
}


def choose(slot_name):
    if "BodyCharcoal" in slot_name or "FrameAnthracite" in slot_name:
        return materials["body"], "shared_mothballed_charcoal"
    if "SafetyYellow" in slot_name:
        return materials["yellow"], "shared_mothballed_yellow"
    if "RubberBlack" in slot_name:
        return materials["rubber"], "dark_rubber_proxy"
    if "BrushedSteel" in slot_name:
        return materials["steel"], "brushed_steel"
    if "SensorGlass" in slot_name or "LensVertexTint" in slot_name:
        return materials["sensor"], "sensor_lens"
    return None, "unmapped"


binding_rows = []
unmapped = []
for name, component in sorted(components.items()):
    if not name.startswith("Visual_") or not isinstance(component, unreal.StaticMeshComponent):
        continue
    mesh = component.get_editor_property("static_mesh")
    if mesh is None:
        continue
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        material, role = choose(slot_name)
        if material is None:
            unmapped.append({"component": name, "slot": index, "slot_name": slot_name})
            continue
        component.set_material(index, material)
        binding_rows.append({
            "component": name, "slot": index, "slot_name": slot_name,
            "material": material.get_path_name(), "role": role,
        })

if unmapped:
    raise RuntimeError(f"RP01 v002 has unmapped material slots: {unmapped}")
bp_library.compile_blueprint(blueprint)
generated_class = bp_library.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("RP01 v002 generated class missing")
default_object = unreal.get_default_object(generated_class)
default_object.set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.Platform.LB-RP01"),
    unreal.Name("LB.Asset.Candidate.v002"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.RP01.VisualAnchorCorrection"),
])
bp_library.compile_blueprint(blueprint)
if not asset_library.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

result = {
    "$schema": "line-boss/audit/lb-rp01-mobile-base-candidate-v002-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PRESERVED_PARENT_VISUAL_CORRECTION_BUILT__FRESH_RELOAD_AND_CAMERA_GATES_REQUIRED__NOT_PROMOTED",
    "source_blueprint_preserved": SOURCE_BP,
    "candidate_blueprint": BP_PATH,
    "corrected_root_space_visual_count": len(transform_rows),
    "corrected_transforms": transform_rows,
    "material_binding_count": len(binding_rows),
    "material_bindings": binding_rows,
    "unmapped_material_slots": unmapped,
    "geometry_duplicated": False,
    "source_meshes_modified": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_RP01_V002_BUILD_PASS transforms={len(transform_rows)} bindings={len(binding_rows)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
