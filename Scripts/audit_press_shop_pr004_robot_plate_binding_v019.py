"""Audit live v019 plate component/material/texture bindings."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004ReusableRobotPlateCandidate_v019"
OUT = ROOT / "Saved/Audits/press_shop_pr004_robot_plate_binding_v019.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
robot = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_INT_PR004_BP_ModularRobot_400kg_v005")
rows = []
for component in robot.get_components_by_class(unreal.StaticMeshComponent):
    if "Plate" not in component.get_name():
        continue
    materials = []
    for index in range(component.get_num_materials()):
        material = component.get_material(index)
        materials.append(material.get_path_name() if material else None)
    rows.append({
        "component": component.get_name(),
        "mesh": component.static_mesh.get_path_name() if component.static_mesh else None,
        "materials": materials,
        "relative_location": list(component.get_editor_property("relative_location")),
        "relative_rotation": list(component.get_editor_property("relative_rotation")),
        "relative_scale": list(component.get_editor_property("relative_scale3d")),
    })
texture = unreal.EditorAssetLibrary.load_asset("/Game/LineBoss/Brand/Cairnwell/Candidate_v005/RobotPlate/T_Cairnwell_PR004_RobotPlate_v001")
material = unreal.EditorAssetLibrary.load_asset("/Game/LineBoss/Brand/Cairnwell/Candidate_v005/RobotPlate/M_Cairnwell_PR004_RobotPlate_v001")
payload = {
    "map": MAP,
    "robot": robot.get_actor_label(),
    "plate_components": rows,
    "texture": texture.get_path_name() if texture else None,
    "texture_size": [texture.blueprint_get_size_x(), texture.blueprint_get_size_y()] if texture else None,
    "texture_srgb": texture.get_editor_property("srgb") if texture else None,
    "material": material.get_path_name() if material else None,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_ROBOT_PLATE_BINDING_V019_PASS audit={OUT}")
unreal.SystemLibrary.quit_editor()
