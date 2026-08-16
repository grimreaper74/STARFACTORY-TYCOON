"""Read-only spatial audit for adding the validated inbound cell to clean v767."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_Trains_S01_S07_v767"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/v767_inbound_capacity_v769.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    loc = actor.get_actor_location()
    origin, extent = actor.get_actor_bounds(False)
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)],
        "bounds_min_cm": [round(origin.x-extent.x, 2), round(origin.y-extent.y, 2), round(origin.z-extent.z, 2)],
        "bounds_max_cm": [round(origin.x+extent.x, 2), round(origin.y+extent.y, 2), round(origin.z+extent.z, 2)],
        "tags": [str(t) for t in actor.tags],
    })

payload = {
    "status": "PASS__READ_ONLY",
    "map": MAP,
    "actor_count": len(rows),
    "hall_shell": [r for r in rows if r["label"] in {
        "LB_PRESS_FinishedFloor", "LB_PRESS_Wall_West", "LB_PRESS_Wall_East",
        "LB_PRESS_Wall_North", "LB_PRESS_Wall_South"}],
    "press_shop_content_bounds_cm": {
        "min": [min(r["bounds_min_cm"][i] for r in rows) for i in range(3)],
        "max": [max(r["bounds_max_cm"][i] for r in rows) for i in range(3)],
    },
    "west_side_actors": sorted(
        [r for r in rows if r["bounds_min_cm"][0] < -9000],
        key=lambda r: r["bounds_min_cm"][0]
    ),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_V767_INBOUND_CAPACITY_AUDIT_V769_PASS")
