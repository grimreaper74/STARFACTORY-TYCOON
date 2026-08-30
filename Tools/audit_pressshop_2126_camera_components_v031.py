"""Read-only camera-transform audit after live render discrepancy."""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_camera_components_v031.json"
LABELS = ("CAM | 2126 Steam hero overview", "CAM | 2126 operator line", "CAM | 2126 draw nexus", "CAM | 2126 outbound autonomy")

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
rows = []
for label in LABELS:
    actor = actors.get(label)
    if not isinstance(actor, unreal.CineCameraActor):
        raise RuntimeError("Missing cine camera: " + label)
    component = actor.get_cine_camera_component()
    relative_location = component.get_editor_property("relative_location")
    relative_rotation = component.get_editor_property("relative_rotation")
    actor_location = actor.get_actor_location()
    actor_rotation = actor.get_actor_rotation()
    rows.append({
        "label": label,
        "actor_location": [actor_location.x, actor_location.y, actor_location.z],
        "actor_rotation": [actor_rotation.pitch, actor_rotation.yaw, actor_rotation.roll],
        "component_relative_location": [relative_location.x, relative_location.y, relative_location.z],
        "component_relative_rotation": [relative_rotation.pitch, relative_rotation.yaw, relative_rotation.roll],
        "focal_length": component.get_editor_property("current_focal_length"),
        "look_at_tracking": str(actor.get_editor_property("lookat_tracking_settings")),
    })
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status": "PASS__READ_ONLY_CAMERA_COMPONENT_AUDIT", "rows": rows}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_CAMERA_COMPONENTS_V031_PASS")
