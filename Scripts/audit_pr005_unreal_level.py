"""Record Unreal-side PR-005 actor transforms and bounds for camera debugging."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/pr005_unreal_level_bounds_v001.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

records = []
for actor in actors.get_all_level_actors():
    origin, extent = actor.get_actor_bounds(False)
    records.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": list(actor.get_actor_location().to_tuple()),
        "rotation_deg": list(actor.get_actor_rotation().to_tuple()),
        "bounds_origin_cm": list(origin.to_tuple()),
        "bounds_extent_cm": list(extent.to_tuple()),
        "hidden": actor.is_hidden_ed(),
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(records, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_LEVEL_AUDIT_PASS actors={len(records)} path={OUT}")
