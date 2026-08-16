"""Read-only PR-005 validation-level actor/layout audit."""
import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/pr005_actor_layout_v002.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

records = []
for actor in actor_system.get_all_level_actors():
    label = actor.get_actor_label()
    if not (label.startswith("LB_PR005_") or label.startswith("LB_CAM_PR005_")):
        continue
    origin, extent = actor.get_actor_bounds(False, False)
    record = {
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "bounds_origin_cm": [origin.x, origin.y, origin.z],
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
    }
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.get_editor_property("static_mesh_component")
        mesh = component.get_editor_property("static_mesh")
        record["mesh"] = mesh.get_path_name() if mesh else None
        record["scale"] = list(actor.get_actor_scale3d().to_tuple())
    records.append(record)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"status": "PASS_READ_ONLY", "map": MAP, "actor_count": len(records), "actors": records}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_LAYOUT_AUDIT_PASS actors={len(records)} path={OUT}")
