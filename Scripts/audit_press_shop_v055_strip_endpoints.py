"""Read-only endpoint audit for the unpromoted PR-005/007/006 strip line."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR007WasherLubeCandidate_v055"
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audits/press_shop_v055_strip_endpoints.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

records = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if "Strip" not in label and "Thread" not in label and "RollerBed" not in label:
        continue
    origin, extent = actor.get_actor_bounds(False)
    records.append({
        "actor": label,
        "origin_cm": list(origin.to_tuple()),
        "extent_cm": list(extent.to_tuple()),
        "min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
        "max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "records": records}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_V055_STRIP_ENDPOINT_AUDIT records={len(records)} output={OUT}")
