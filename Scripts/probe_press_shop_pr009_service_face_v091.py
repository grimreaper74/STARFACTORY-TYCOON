"""Measure visible plate-like actors on the PR-009 south service face."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009ServiceIdentityCandidate_v091"
OUT = ROOT / "Saved/Audits/PR009_InMap_v091/service_face_plate_probe.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
for actor in actors_api.get_all_level_actors():
    origin, extent = actor.get_actor_bounds(False)
    dimensions = [2.0 * extent.x, 2.0 * extent.y, 2.0 * extent.z]
    if not (-400.0 <= origin.x <= 1200.0 and -2500.0 <= origin.y <= -1650.0 and 20.0 <= origin.z <= 400.0):
        continue
    plate_like = min(dimensions) <= 40.0 and sorted(dimensions)[1] >= 45.0
    identity = "IDENTITY" in actor.get_actor_label().upper()
    if not (plate_like or identity or isinstance(actor, unreal.TextRenderActor)):
        continue
    rows.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "origin_cm": [origin.x, origin.y, origin.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "dimensions_cm": dimensions,
        "rotation": [actor.get_actor_rotation().roll, actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw],
        "tags": [str(tag) for tag in actor.tags],
    })

rows.sort(key=lambda row: (row["origin_cm"][1], row["origin_cm"][0], row["label"]))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "candidate_count": len(rows), "actors": rows}, indent=2), encoding="utf-8")
unreal.log(f"PR009_V091_SERVICE_FACE_PLATE_PROBE output={OUT} candidates={len(rows)}")
