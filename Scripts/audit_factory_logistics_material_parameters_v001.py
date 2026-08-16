"""Inspect exposed parameters on contained vendor logistics materials."""

import json
from pathlib import Path

import unreal


ROOT = "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics/Materials"
NAMES = ("MI_ForkLift2", "MI_ForkLiftDetails", "MI_PalletCart", "MI_PlasticPallet01")
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/factory_logistics_material_parameters_v001.json"
rows = []
for name in NAMES:
    material = unreal.load_asset(f"{ROOT}/{name}")
    if material is None:
        raise RuntimeError(f"Missing {name}")
    row = {"asset": material.get_path_name(), "vectors": [], "scalars": [], "textures": []}
    for parameter in unreal.MaterialEditingLibrary.get_vector_parameter_names(material):
        value = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(material, parameter)
        row["vectors"].append({"name": str(parameter), "value": [value.r, value.g, value.b, value.a]})
    for parameter in unreal.MaterialEditingLibrary.get_scalar_parameter_names(material):
        value = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, parameter)
        row["scalars"].append({"name": str(parameter), "value": value})
    for parameter in unreal.MaterialEditingLibrary.get_texture_parameter_names(material):
        value = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(material, parameter)
        row["textures"].append({"name": str(parameter), "value": value.get_path_name() if value else None})
    rows.append(row)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"materials": rows}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_LOGISTICS_MATERIAL_PARAMETER_AUDIT_PASS materials={len(rows)}")

