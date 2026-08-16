"""Record exact imported actor bounds for the failed isolated Train A v001 assembly."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_actor_bounds_v001.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
records = []
for actor in actors_api.get_all_level_actors():
    values = {str(tag) for tag in actor.tags}
    if not isinstance(actor, unreal.StaticMeshActor) or "LB.PressTrain.TrainA.Isolated" not in values or "LB.Validation.Environment" in values:
        continue
    origin, extent = actor.get_actor_bounds(False, False)
    records.append({
        "label": actor.get_actor_label(),
        "location_cm": [round(value, 3) for value in (actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)],
        "rotation_deg": [round(value, 3) for value in (actor.get_actor_rotation().roll, actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw)],
        "bounds_origin_cm": [round(value, 3) for value in (origin.x, origin.y, origin.z)],
        "bounds_size_cm": [round(value * 2, 3) for value in (extent.x, extent.y, extent.z)],
        "tags": sorted(values),
    })
records.sort(key=lambda item: item["label"])
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "actor_count": len(records), "records": records}, indent=2), encoding="utf-8")
print(json.dumps({"actor_count": len(records), "output": str(OUT)}, indent=2))
