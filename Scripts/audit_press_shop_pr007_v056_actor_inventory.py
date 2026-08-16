"""Inventory PR-007 v056 actors before runtime binding."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR007StripGuardHMICandidate_v056"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    tags = [str(tag) for tag in actor.tags]
    if "PR007" not in label.upper() and not any("PR007" in tag.upper() for tag in tags):
        continue
    loc = actor.get_actor_location()
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [loc.x, loc.y, loc.z],
        "tags": tags,
    })

out = ROOT / "Saved/Audits/press_shop_pr007_v056_actor_inventory.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "$schema": "line-boss/audit/pr007-v056-actor-inventory/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "actor_count": len(rows),
    "actors": sorted(rows, key=lambda row: row["label"]),
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR007_V056_INVENTORY_PASS count={len(rows)}")
unreal.SystemLibrary.quit_editor()
