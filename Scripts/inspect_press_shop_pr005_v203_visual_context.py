"""Read-only v203 camera/service-bay transform inspection."""

import json
from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
map_path = "/Game/LineBoss/Maps/LB_PressShop_PR005ReleaseArtCandidate_v203"
out = root / "Saved/Audits/PressShopIntegration/press_shop_pr005_v203_visual_context.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)

labels = {
    "LB_PR005_V053_CAM_LogisticsPlayer",
    "LB_PR005_V053_CAM_LogisticsElevated",
    "LB_PR005_V053_CAM_LogisticsWholeLine",
    "LB_PR005_V203_ServiceBayInstalled_Static_v009",
}
rows = []
for actor in actors_api.get_all_level_actors():
    if actor.get_actor_label() not in labels:
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    origin, extent = actor.get_actor_bounds(False)
    rows.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.pitch, rotation.yaw, rotation.roll],
        "bounds_min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "bounds_max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
    })
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"map": map_path, "actors": rows}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PR005_V203_VISUAL_CONTEXT_INSPECTION_PASS")
unreal.SystemLibrary.quit_editor()
