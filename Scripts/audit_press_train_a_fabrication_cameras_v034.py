"""Read-only fixed-camera inventory for exact fabrication v034."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressTrainAFabricationCollisionSafeCandidate_v034"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressTrains/press_train_a_fabrication_cameras_v034.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
rows = []
for actor in actors_api.get_all_level_actors():
    if not isinstance(actor, unreal.CameraActor):
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    rows.append({
        "label": actor.get_actor_label(),
        "location_cm": [location.x, location.y, location.z],
        "rotation": [rotation.pitch, rotation.yaw, rotation.roll],
        "fov": actor.camera_component.field_of_view,
        "tags": [str(value) for value in actor.tags],
    })
payload = {"map": MAP, "read_only": True, "camera_count": len(rows), "cameras": rows}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
