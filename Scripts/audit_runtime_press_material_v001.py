"""Read-only inspection of the material used by the live five-press assembly."""
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
MATERIAL_PATHS = [
    "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/"
    "Cairnwell_S03_Movable_v632Controls_v735/Materials/material.material",
    "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/"
    "Cairnwell_S03_Movable_v632Controls_v735/Materials/Material_0.Material_0",
    "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/"
    "Cairnwell_S03_Movable_v632Controls_v735/Materials/Material_0_001.Material_0_001",
]
MESH_PATHS = [
    "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/"
    "Cairnwell_S03_Movable_v632Controls_v735/StaticMeshes/S03_STATIC_SHELL.S03_STATIC_SHELL",
    "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/"
    "Cairnwell_S03_Movable_v632Controls_v735/StaticMeshes/S03_RAM_SLIDE.S03_RAM_SLIDE",
    "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/"
    "Cairnwell_S03_Movable_v632Controls_v735/StaticMeshes/S03_UPPER_DIE.S03_UPPER_DIE",
    "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/"
    "Cairnwell_S03_Movable_v632Controls_v735/StaticMeshes/S03_LOWER_DIE_BOLSTER.S03_LOWER_DIE_BOLSTER",
    "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/"
    "Cairnwell_S03_Movable_v632Controls_v735/StaticMeshes/SM_CA_Factory_Elect_net_MeshyMaster_v632.SM_CA_Factory_Elect_net_MeshyMaster_v632",
    "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/"
    "Cairnwell_S03_Movable_v632Controls_v735/StaticMeshes/SM_CA_Factory_Opera_HMI_MeshyMaster_v632.SM_CA_Factory_Opera_HMI_MeshyMaster_v632",
]

def describe_input(material, prop):
    node = unreal.MaterialEditingLibrary.get_material_property_input_node(material, prop)
    row = {"node": node.get_class().get_name() if node else None}
    if node:
        for key in ("constant", "parameter_name", "texture", "sampler_type"):
            try:
                value = node.get_editor_property(key)
                if hasattr(value, "get_path_name"):
                    value = value.get_path_name()
                elif hasattr(value, "to_tuple"):
                    value = list(value.to_tuple())
                else:
                    value = str(value)
                row[key] = value
            except Exception:
                pass
    return row

records = []
for path in MATERIAL_PATHS:
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        records.append({"asset": path, "error": "missing"})
        continue
    if isinstance(asset, unreal.MaterialInstanceConstant):
        parent = asset.get_editor_property("parent")
        vector_values = {}
        texture_values = {}
        if parent:
            for name in unreal.MaterialEditingLibrary.get_vector_parameter_names(parent):
                vector_values[str(name)] = str(unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(asset, name))
            for name in unreal.MaterialEditingLibrary.get_texture_parameter_names(parent):
                value = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(asset, name)
                texture_values[str(name)] = value.get_path_name() if value else None
        records.append({
            "asset": asset.get_path_name(),
            "class": asset.get_class().get_name(),
            "parent": parent.get_path_name() if parent else None,
            "vector_overrides": [str(value) for value in asset.get_editor_property("vector_parameter_values")],
            "scalar_overrides": [str(value) for value in asset.get_editor_property("scalar_parameter_values")],
            "texture_overrides": [str(value) for value in asset.get_editor_property("texture_parameter_values")],
            "effective_vector_parameters": vector_values,
            "effective_texture_parameters": texture_values,
        })
        continue
    if not isinstance(asset, unreal.Material):
        records.append({"asset": path, "class": asset.get_class().get_name(), "error": "unsupported_material_type"})
        continue
    records.append({
        "asset": asset.get_path_name(),
        "base_color": describe_input(asset, unreal.MaterialProperty.MP_BASE_COLOR),
        "roughness": describe_input(asset, unreal.MaterialProperty.MP_ROUGHNESS),
        "metallic": describe_input(asset, unreal.MaterialProperty.MP_METALLIC),
        "normal": describe_input(asset, unreal.MaterialProperty.MP_NORMAL),
        "emissive": describe_input(asset, unreal.MaterialProperty.MP_EMISSIVE_COLOR),
        "expressions": [expression.get_class().get_name() for expression in asset.get_editor_property("expressions")],
    })

mesh_records = []
for path in MESH_PATHS:
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    mesh_records.append({
        "asset": path,
        "slots": [slot.get_editor_property("material_interface").get_path_name()
                  if slot.get_editor_property("material_interface") else None
                  for slot in mesh.get_editor_property("static_materials")] if isinstance(mesh, unreal.StaticMesh) else None,
    })

out = ROOT / "Saved" / "Audits" / "PressTrains" / "runtime_press_material_v001.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"generated_utc": datetime.now(timezone.utc).isoformat(), "records": records,
                           "meshes": mesh_records}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_RUNTIME_PRESS_MATERIAL_AUDIT_V001 PASS path={out}")
