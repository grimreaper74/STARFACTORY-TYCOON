"""Read-only actor survey around the accepted PR-004 close camera target."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/lb_cr01_pr004_v006_integration_site.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

centre = unreal.Vector(-4750.0, -2050.0, 0.0)
rows = []
for actor in actors.get_all_level_actors():
    loc = actor.get_actor_location()
    distance_xy = ((loc.x - centre.x) ** 2 + (loc.y - centre.y) ** 2) ** 0.5
    if distance_xy <= 2200.0:
        rows.append({
            "label": actor.get_actor_label(),
            "class": actor.get_class().get_name(),
            "location_cm": [loc.x, loc.y, loc.z],
            "distance_xy_cm": distance_xy,
        })
rows.sort(key=lambda row: (row["distance_xy_cm"], row["label"]))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "survey_centre_cm": [centre.x, centre.y, centre.z],
    "radius_cm": 2200.0,
    "actors": rows,
    "map_modified": False,
}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_PR004_SITE_AUDIT_PASS actors={len(rows)} audit={OUT}")
