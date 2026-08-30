"""Read the saved outbound camera transform and component offsets; no mutation."""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_camera_v025.json"

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
camera = actors.get("CAM | 2126 outbound autonomy")
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Outbound camera missing")
component = camera.get_cine_camera_component()
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__READ_ONLY_CAMERA_TRANSFORM_AUDIT",
    "actor_location": str(camera.get_actor_location()),
    "actor_rotation": str(camera.get_actor_rotation()),
    "component_relative_location": str(component.get_editor_property("relative_location")),
    "component_relative_rotation": str(component.get_editor_property("relative_rotation")),
    "focal_length_mm": component.get_editor_property("current_focal_length"),
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_CAMERA_AUDIT_V025_PASS")
