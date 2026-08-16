"""Read-only probe of retained v301 cameras for a proven interior Train A sightline."""
import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/PressTrains/press_shop_v301_camera_probe_v331.json"
if out.exists():
    raise RuntimeError("Refusing to overwrite v331 probe")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level("/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301"):
    raise RuntimeError("Could not load v301")
rows = []
for actor in actors.get_all_level_actors():
    if isinstance(actor, unreal.CameraActor):
        loc = actor.get_actor_location()
        rot = actor.get_actor_rotation()
        rows.append({"label": actor.get_actor_label(), "location": [loc.x, loc.y, loc.z], "rotation": [rot.pitch, rot.yaw, rot.roll], "fov": actor.camera_component.get_editor_property("field_of_view")})
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"map": "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301", "cameras": rows}, indent=2), encoding="utf-8")
print(json.dumps(rows, indent=2))
unreal.SystemLibrary.quit_editor()
