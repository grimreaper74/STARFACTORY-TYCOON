"""Read-only transform audit for the fresh 2126 candidate camera actors."""

import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits" / "PressShopIntegration" / "pressshop_2126_camera_debug_v001.json"
LABELS = {
    "CAM | 2126 Steam hero overview",
    "CAM | 2126 operator line",
    "CAM | 2126 draw nexus",
}

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")

records = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if label in LABELS:
        loc = actor.get_actor_location()
        rot = actor.get_actor_rotation()
        component = actor.get_cine_camera_component()
        records.append({
            "label": label,
            "class": actor.get_class().get_name(),
            "location_cm": [loc.x, loc.y, loc.z],
            "rotation": [rot.pitch, rot.yaw, rot.roll],
            "forward": [actor.get_actor_forward_vector().x, actor.get_actor_forward_vector().y, actor.get_actor_forward_vector().z],
            "focal_length_mm": component.get_editor_property("current_focal_length"),
            "filmback": str(component.get_editor_property("filmback")),
        })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "cameras": records}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_CAMERA_DEBUG=" + json.dumps(records))
