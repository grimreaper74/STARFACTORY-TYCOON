"""Read-only installed four-train material usage inventory."""

import json
from collections import Counter
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v229"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_train_installed_materials_v229.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

usage = Counter()
actors_by_material = {}
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if not any(tag.startswith("LB.PressTrain.Installed.TRAIN_") for tag in tags):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or component.static_mesh is None:
        continue
    for index in range(component.get_num_materials()):
        material = component.get_material(index)
        path = material.get_path_name() if material else "NONE"
        usage[path] += 1
        actors_by_material.setdefault(path, []).append(actor.get_actor_label())

payload = {
    "map": MAP,
    "read_only": True,
    "material_slot_usage": dict(usage.most_common()),
    "sample_actors_by_material": {key: value[:12] for key, value in actors_by_material.items()},
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
