"""Record known-valid PR-004 integration camera transforms."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_camera_transforms_v006.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if "CAM" not in label or "PR004" not in label:
        continue
    loc = actor.get_actor_location(); rot = actor.get_actor_rotation()
    comp = actor.get_component_by_class(unreal.CameraComponent)
    rows.append({"label": label, "location": [loc.x, loc.y, loc.z], "rotation": [rot.roll, rot.pitch, rot.yaw], "fov": comp.field_of_view if comp else None})
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "cameras": rows}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CAMERA_AUDIT_PASS count={len(rows)}")
unreal.SystemLibrary.quit_editor()
