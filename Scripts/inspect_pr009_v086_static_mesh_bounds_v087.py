"""Read-only v086 parent static-mesh bounds evidence for v087 collision authoring."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import unreal
sys.path.insert(0, str(Path(__file__).resolve().parent))
from press_shop_pr009_release_collision_v087_config import PARENT_MAP

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/PR009_InMap_v087/parent_static_mesh_bounds.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(PARENT_MAP):
    raise RuntimeError(f"Could not load {PARENT_MAP}")
rows = []
for actor in actors.get_all_level_actors():
    if unreal.Name("LB.Structure.PR009") not in actor.tags:
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = component.get_editor_property("static_mesh") if component else None
    box = mesh.get_bounding_box() if mesh else None
    rows.append({
        "actor": actor.get_actor_label(), "asset": mesh.get_path_name() if mesh else None,
        "mesh_min_cm": [box.min.x, box.min.y, box.min.z] if box else None,
        "mesh_max_cm": [box.max.x, box.max.y, box.max.z] if box else None,
        "actor_location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "actor_rotation": str(actor.get_actor_rotation()),
        "actor_scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z],
    })
payload = {"$schema": "cairnwell/audit/pr009-v086-parent-static-bounds/v1",
           "generated_utc": datetime.now(timezone.utc).isoformat(), "parent_map": PARENT_MAP,
           "groups": sorted(rows, key=lambda row: row["asset"] or ""), "promotion_authorized": False}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"PR009_V087_PARENT_BOUNDS count={len(rows)} output={out}")
unreal.SystemLibrary.quit_editor()
