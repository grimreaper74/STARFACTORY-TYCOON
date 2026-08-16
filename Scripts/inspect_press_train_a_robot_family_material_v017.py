"""Read-only inspection of the isolated v017 robot-family materials."""

import json
from pathlib import Path

import unreal

root = Path(unreal.Paths.project_dir())
library = unreal.EditorAssetLibrary
material_paths = [
    "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyRobotFamily_v017/Materials/M_CA_MW_PTA_Charcoal_AssemblyStudyRobotFamily_v017",
    "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyRobotFamily_v017/Materials/M_CA_MW_PTA_RobotSafetyYellow_AssemblyStudyRobotFamily_v017",
]
rows = []
for path in material_paths:
    asset = library.load_asset(path)
    row = {"path": path, "class": asset.get_class().get_name() if asset else None}
    if isinstance(asset, unreal.MaterialInstanceConstant):
        row["parent"] = asset.get_editor_property("parent").get_path_name()
        row["scalar_parameters"] = {
            str(name): unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(asset, name)
            for name in unreal.MaterialEditingLibrary.get_scalar_parameter_names(asset)
        }
        row["vector_parameters"] = {
            str(name): str(unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(asset, name))
            for name in unreal.MaterialEditingLibrary.get_vector_parameter_names(asset)
        }
    rows.append(row)
out = root / "Saved/Audits/PressTrains/press_train_a_robot_family_material_inspection_v017.json"
out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(json.dumps(rows, indent=2))
