"""Read-only visibility/bounds probe for the four reused robot tenders."""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_robot_visibility_v046.json"
LABELS = (
    "ROBOT | S01 | laser tend robot",
    "ROBOT | S02 | draw quality robot",
    "ROBOT | S04 | pierce handling robot",
    "ROBOT | S06 | vision stack robot",
)

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
rows = []
for label in LABELS:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Robot actor missing: " + label)
    component = actor.static_mesh_component
    origin, extent = actor.get_actor_bounds(False, False)
    materials = [component.get_material(index).get_path_name() if component.get_material(index) else None for index in range(component.get_num_materials())]
    mesh = component.get_editor_property("static_mesh")
    rows.append({
        "label": label,
        "actor_location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "actor_rotation": [actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw, actor.get_actor_rotation().roll],
        "actor_scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z],
        "bounds_origin_cm": [origin.x, origin.y, origin.z],
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
        "mesh": mesh.get_path_name() if mesh else None,
        "component_visible": component.is_visible(),
        "editor_hidden": actor.is_temporarily_hidden_in_editor(),
        "materials": materials,
    })
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY_ROBOT_VISIBILITY_PROBE", "robots": rows, "map_saved": False}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_ROBOT_VISIBILITY_V046_PASS")
