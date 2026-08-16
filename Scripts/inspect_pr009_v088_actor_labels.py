import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
target = "/Game/LineBoss/Maps/LB_PressShop_PR009TracePortalClearanceCandidate_v088"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(target):
    raise RuntimeError(target)
rows = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if "PR009" in label and ("07" in label or "Trace" in label):
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        rows.append({
            "label": label,
            "tags": [str(tag) for tag in actor.tags],
            "mesh": component.get_editor_property("static_mesh").get_path_name() if component and component.get_editor_property("static_mesh") else None,
        })
out = root / "Saved/Audits/PR009_InMap_v088/actor_label_probe.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
unreal.SystemLibrary.quit_editor()
