"""Dump an Unreal level's actors; target and output version come from env."""

import json
import os
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = os.environ["LB_AUDIT_MAP"]
NAME = os.environ.get("LB_AUDIT_NAME", "level_actor_inventory")
OUT = PROJECT / f"Saved/Audits/{NAME}.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

try:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    rows = []
    for actor in actors.get_all_level_actors():
        loc = actor.get_actor_location()
        mesh = ""
        if isinstance(actor, unreal.StaticMeshActor):
            value = actor.static_mesh_component.get_editor_property("static_mesh")
            mesh = value.get_path_name() if value else ""
        rows.append({
            "label": actor.get_actor_label(),
            "class": actor.get_class().get_name(),
            "mesh": mesh,
            "is_editor_only_actor": actor.get_editor_property("is_editor_only_actor"),
            "hidden_in_game": actor.get_editor_property("hidden"),
            "location_cm": [round(loc.x, 3), round(loc.y, 3), round(loc.z, 3)],
        })
    rows.sort(key=lambda row: row["label"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"map": MAP, "count": len(rows), "actors": rows}, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_LEVEL_ACTOR_AUDIT_PASS count={len(rows)} path={OUT}")
finally:
    unreal.SystemLibrary.quit_editor()
