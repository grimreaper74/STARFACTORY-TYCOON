"""Audit component material overrides in the isolated logistics bay."""

import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_FactoryLogistics_Candidate_v001"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/factory_logistics_validation_bindings_v001.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
rows = []
for actor in actors.get_all_level_actors():
    if not actor.get_actor_label().startswith("LB_LOGISTICS_") or not isinstance(actor, unreal.StaticMeshActor):
        continue
    component = actor.static_mesh_component
    rows.append({
        "actor": actor.get_actor_label(),
        "mesh": component.static_mesh.get_path_name() if component.static_mesh else None,
        "materials": [component.get_material(i).get_path_name() if component.get_material(i) else None
                      for i in range(component.get_num_materials())],
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"actors": rows}, indent=2), encoding="utf-8")

