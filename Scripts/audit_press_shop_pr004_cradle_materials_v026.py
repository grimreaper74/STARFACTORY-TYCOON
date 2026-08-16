"""Read-only audit of the powered PR-004 cradle material bindings."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_cradle_materials_v026.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
for actor in actors.get_all_level_actors():
    if not actor.get_actor_label().startswith("LB_INT_PR004_V009_powered_cradle_v001_"):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = component.get_editor_property("static_mesh") if component else None
    slots = []
    if component and mesh:
        names = [str(name) for name in component.get_material_slot_names()]
        for index, name in enumerate(names):
            material = component.get_material(index)
            slots.append({"index": index, "name": name,
                          "material": material.get_path_name() if material else None})
    rows.append({"actor": actor.get_actor_label(), "mesh": mesh.get_path_name() if mesh else None,
                 "slots": slots})

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "actor_count": len(rows), "actors": rows}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRADLE_MATERIAL_AUDIT_PASS count={len(rows)}")
unreal.SystemLibrary.quit_editor()
