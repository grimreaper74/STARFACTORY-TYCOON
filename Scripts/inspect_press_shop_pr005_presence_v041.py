"""Read-only inventory of PR-005 geometry and native authority in the v041 full Press Shop candidate."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LuminaireCandidate_v041"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_presence_v041.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

matches = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    tags = [str(tag) for tag in actor.tags]
    class_path = actor.get_class().get_path_name()
    if "PR005" in label.upper() or "PR-005" in label.upper() or any("PR005" in tag.upper() or "PR-005" in tag.upper() for tag in tags) or "LBPR005Station" in class_path:
        matches.append({
            "label": label,
            "class": class_path,
            "location_cm": list(actor.get_actor_location().to_tuple()),
            "tags": tags,
        })

payload = {
    "$schema": "line-boss/audit/press-shop-pr005-presence-v041/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "match_count": len(matches),
    "native_station_count": sum("LBPR005Station" in row["class"] for row in matches),
    "matches": matches,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_PRESENCE_V041_AUDIT count={len(matches)}")
unreal.SystemLibrary.quit_editor()
