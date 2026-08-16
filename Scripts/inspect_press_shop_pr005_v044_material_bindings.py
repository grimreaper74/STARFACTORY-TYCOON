"""Inspect PR-005 v044 slot names and component overrides."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005MaterialCandidate_v044"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_material_bindings_v044.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
rows = []
for actor in actors_api.get_all_level_actors():
    if unreal.Name("LB.Station.PR-005") not in actor.tags or not isinstance(actor, unreal.StaticMeshActor):
        continue
    component = actor.static_mesh_component
    mesh = component.static_mesh
    slots = mesh.get_editor_property("static_materials") if mesh else []
    materials = []
    for index in range(component.get_num_materials()):
        current = component.get_material(index)
        slot = slots[index] if index < len(slots) else None
        materials.append({
            "index": index,
            "slot": str(slot.get_editor_property("imported_material_slot_name")) if slot else None,
            "mesh_default": slot.get_editor_property("material_interface").get_path_name()
                if slot and slot.get_editor_property("material_interface") else None,
            "component_material": current.get_path_name() if current else None,
        })
    rows.append({"actor": actor.get_actor_label(), "materials": materials})
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "actors": rows}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_V044_MATERIAL_BINDINGS_PASS actors={len(rows)}")
unreal.SystemLibrary.quit_editor()
