"""Dump PR-004 v008 process actor transforms and bounds for pivot repair."""

import json
import os
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
VERSION = os.environ.get("LB_PR004_AUDIT_VERSION", "v008")
MAP = os.environ.get(
    "LB_PR004_AUDIT_MAP",
    "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v008",
)
OUT = PROJECT / f"Saved/Audits/pr004_{VERSION}_actor_transforms.json"
TOKENS = (
    "packaging", "cradle", "coil", "robot_v002", "tool", "hmi08",
    "perimeter_gate", "film_dewrap",
)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

try:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    rows = []
    for actor in actors.get_all_level_actors():
        label = actor.get_actor_label()
        if not any(token in label.lower() for token in TOKENS):
            continue
        location = actor.get_actor_location()
        rotation = actor.get_actor_rotation()
        origin, extent = actor.get_actor_bounds(False)
        mesh = ""
        if isinstance(actor, unreal.StaticMeshActor):
            value = actor.static_mesh_component.get_editor_property("static_mesh")
            mesh = value.get_path_name() if value else ""
        rows.append({
            "label": label,
            "class": actor.get_class().get_name(),
            "mesh": mesh,
            "location_cm": [round(location.x, 3), round(location.y, 3), round(location.z, 3)],
            "rotation_deg": [round(rotation.roll, 3), round(rotation.pitch, 3), round(rotation.yaw, 3)],
            "bounds_origin_cm": [round(origin.x, 3), round(origin.y, 3), round(origin.z, 3)],
            "bounds_extent_cm": [round(extent.x, 3), round(extent.y, 3), round(extent.z, 3)],
        })
    rows.sort(key=lambda row: row["label"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"map": MAP, "count": len(rows), "actors": rows}, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_PR004_V008_TRANSFORM_AUDIT_PASS count={len(rows)} path={OUT}")
finally:
    unreal.SystemLibrary.quit_editor()
