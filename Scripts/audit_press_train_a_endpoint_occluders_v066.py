"""Read-only actor/bounds inventory for S01 and S07 endpoint occlusion diagnosis."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v066"
OUT = (Path(unreal.Paths.project_saved_dir()) /
       "Audits/PressTrains/press_train_a_endpoint_occluders_v066.json")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
for actor in actors_api.get_all_level_actors():
    tags = sorted(str(tag) for tag in actor.tags)
    label = actor.get_actor_label()
    if not ("S01" in label or "S07" in label or any(".S01." in tag or ".S07." in tag for tag in tags)):
        continue
    component = getattr(actor, "static_mesh_component", None)
    mesh = None
    if component is not None and component.static_mesh is not None:
        mesh = component.static_mesh.get_path_name()
    origin, extent = actor.get_actor_bounds(False)
    rows.append({
        "actor": label,
        "class": actor.get_class().get_name(),
        "mesh": mesh,
        "location_cm": [round(v, 3) for v in actor.get_actor_location().to_tuple()],
        "rotation_deg": [round(v, 3) for v in actor.get_actor_rotation().to_tuple()],
        "bounds_origin_cm": [round(v, 3) for v in origin.to_tuple()],
        "bounds_extent_cm": [round(v, 3) for v in extent.to_tuple()],
        "tags": tags,
    })

rows.sort(key=lambda row: row["actor"])
report = {
    "$schema": "cairnwell/audit/press-train-a-endpoint-occluders-v066/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_ENDPOINT_ACTOR_BOUNDS_INVENTORY__NOT_A_PROMOTION_GATE",
    "map": MAP,
    "actor_count": len(rows),
    "actors": rows,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"actor_count": len(rows), "output": str(OUT)}, indent=2))
