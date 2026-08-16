"""Read-only camera-planning inventory for the retained v438 press shop."""
from pathlib import Path
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_capture_layout_v452.json"

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actor_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows = []
for actor in actor_api.get_all_level_actors():
    label = actor.get_actor_label()
    tags = [str(tag) for tag in actor.tags]
    search = (label + " " + " ".join(tags)).lower()
    if not any(token in search for token in (
        "presstrain", "press_train", "traina", "factoryroofliner", "roof", "ceiling"
    )):
        continue
    origin, extent = actor.get_actor_bounds(False)
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "bounds_origin_cm": [origin.x, origin.y, origin.z],
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
        "tags": tags,
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "actors": rows}, indent=2), encoding="utf-8")
unreal.log(f"CAPTURE_LAYOUT_V452 {OUT} actors={len(rows)}")
unreal.SystemLibrary.quit_editor()
