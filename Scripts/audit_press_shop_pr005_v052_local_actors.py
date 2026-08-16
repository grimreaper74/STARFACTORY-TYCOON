"""Read-only local actor inventory for safe PR-005 logistics placement."""

import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceIdentityCandidate_v052"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_v052_local_actors.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
rows = []
for actor in actors.get_all_level_actors():
    p = actor.get_actor_location()
    if -6500.0 <= p.x <= -1500.0 and -5000.0 <= p.y <= 500.0:
        rows.append({"label": actor.get_actor_label(), "class": actor.get_class().get_name(),
                     "location": [p.x, p.y, p.z]})
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"actors": sorted(rows, key=lambda row: row["label"])}, indent=2), encoding="utf-8")

