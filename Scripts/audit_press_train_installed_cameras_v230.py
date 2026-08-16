"""Read-only camera inventory for the four installed trains in v230."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_train_installed_cameras_v230.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

records = []
for actor in actors_api.get_all_level_actors():
    if not isinstance(actor, unreal.CameraActor):
        continue
    tags = [str(tag) for tag in actor.tags]
    train = next((tag for tag in tags if tag.startswith("LB.PressTrain.Installed.TRAIN_")), None)
    label = actor.get_actor_label()
    if train is None and not ("PTA" in label or "PTB" in label or "PTC" in label or "PTD" in label):
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    records.append({"label": label, "train_tag": train,
                    "location_cm": [location.x, location.y, location.z],
                    "rotation_deg": [rotation.pitch, rotation.yaw, rotation.roll],
                    "fov": actor.camera_component.field_of_view, "tags": tags})

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(records, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
