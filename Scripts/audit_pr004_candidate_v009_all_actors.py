"""Inventory every actor in PR-004 v009 before full-map candidate integration."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v009"
OUT = PROJECT / "Saved/Audits/pr004_v009_all_actor_inventory.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

try:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    rows = []
    for actor in actors.get_all_level_actors():
        mesh = ""
        if isinstance(actor, unreal.StaticMeshActor):
            value = actor.static_mesh_component.get_editor_property("static_mesh")
            mesh = value.get_path_name() if value else ""
        loc = actor.get_actor_location()
        rot = actor.get_actor_rotation()
        scale = actor.get_actor_scale3d()
        rows.append({
            "label": actor.get_actor_label(),
            "class": actor.get_class().get_name(),
            "mesh": mesh,
            "location_cm": [loc.x, loc.y, loc.z],
            "rotation_deg": [rot.roll, rot.pitch, rot.yaw],
            "scale": [scale.x, scale.y, scale.z],
        })
    rows.sort(key=lambda row: row["label"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"map": MAP, "count": len(rows), "actors": rows}, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_PR004_V009_ALL_ACTOR_AUDIT_PASS count={len(rows)} path={OUT}")
finally:
    unreal.SystemLibrary.quit_editor()
