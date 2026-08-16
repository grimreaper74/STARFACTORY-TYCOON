"""Read-only CR01 v053 component/material probe for the v054 visual correction."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v053/Blueprints/BP_LB_CR01_CleaningAMR_v053"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v053_material_branding_probe.json"

asset_library = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary

blueprint = asset_library.load_asset(BP_PATH)
if not isinstance(blueprint, unreal.Blueprint):
    raise RuntimeError(f"Missing blueprint {BP_PATH}")

rows = []
for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    name = str(data_library.get_variable_name(data))
    obj = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
    if not isinstance(obj, unreal.StaticMeshComponent):
        continue
    mesh = obj.get_editor_property("static_mesh")
    if mesh is None:
        continue
    slots = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        override = obj.get_material(index)
        slots.append({
            "index": index,
            "slot_name": str(slot.get_editor_property("material_slot_name")),
            "mesh_default": (slot.get_editor_property("material_interface").get_path_name()
                             if slot.get_editor_property("material_interface") else None),
            "component_material": override.get_path_name() if override else None,
        })
    rows.append({"component": name, "mesh": mesh.get_path_name(), "slots": slots})

material_paths = sorted({s["component_material"] for r in rows for s in r["slots"] if s["component_material"]})
materials = []
for path in material_paths:
    material = asset_library.load_asset(path)
    entry = {"path": path, "class": material.get_class().get_name() if material else None}
    if isinstance(material, unreal.MaterialInstanceConstant):
        scalar_names = unreal.MaterialEditingLibrary.get_scalar_parameter_names(material)
        vector_names = unreal.MaterialEditingLibrary.get_vector_parameter_names(material)
        entry["scalar_parameters"] = {
            str(n): unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, n)
            for n in scalar_names
        }
        entry["vector_parameters"] = {
            str(n): list(unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(material, n).to_tuple())
            for n in vector_names
        }
        entry["texture_parameters"] = [str(n) for n in unreal.MaterialEditingLibrary.get_texture_parameter_names(material)]
    materials.append(entry)

result = {
    "$schema": "line-boss/audit/lb-cr01-candidate-v053-material-branding-probe",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_PROBE_COMPLETE",
    "blueprint": BP_PATH,
    "component_count": len(rows),
    "components": rows,
    "materials": materials,
    "assets_modified": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V053_MATERIAL_BRANDING_PROBE_PASS audit={AUDIT}")
