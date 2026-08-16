"""Read-only scene inventory for the shared HMI v004 validation map."""

from pathlib import Path
import json
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_HMI04_ModelingValidation"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/hmi_v004_scene_layout.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

rows = []
for actor in actors.get_all_level_actors():
    origin, extent = actor.get_actor_bounds(False)
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    rows.append({
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location_cm": [loc.x, loc.y, loc.z],
        "rotation_deg": [rot.roll, rot.pitch, rot.yaw],
        "scale": [scale.x, scale.y, scale.z],
        "bounds_origin_cm": [origin.x, origin.y, origin.z],
        "bounds_extent_cm": [extent.x, extent.y, extent.z],
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "actors": rows}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_HMI04_LAYOUT_AUDIT_PASS actors={len(rows)} path={OUT}")
