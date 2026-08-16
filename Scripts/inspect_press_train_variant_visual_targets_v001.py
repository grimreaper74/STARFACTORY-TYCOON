"""Read-only inspection of B/C identity and transfer-gripper presentation targets."""

import json
import os
from pathlib import Path

import unreal


letter = os.environ.get("LB_PT_VARIANT", "C").upper()
if letter not in {"B", "C"}:
    raise RuntimeError(letter)
map_path = f"/Game/LineBoss/Maps/LB_PressTrain{letter}IsolatedVariantCandidate_v001"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)
rows = []
for actor in actors_api.get_all_level_actors():
    tags = {str(value) for value in actor.tags}
    roles = sorted(value for value in tags if value.startswith("LB.PressTrain.Role."))
    if not isinstance(actor, unreal.CameraActor) and not any(
            value.endswith("stage_identity") or value.endswith("transfer_gripper") for value in roles):
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    rows.append({
        "actor": actor.get_actor_label(), "roles": roles,
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.roll, rotation.pitch, rotation.yaw],
        "scale": [scale.x, scale.y, scale.z],
        "materials": [str(item) for item in actor.static_mesh_component.get_materials()]
            if isinstance(actor, unreal.StaticMeshActor) else [],
    })
output = Path(unreal.Paths.project_saved_dir()) / (
    f"Audits/PressTrains/press_train_{letter.lower()}_visual_targets_v001.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({"map": map_path, "rows": rows}, indent=2), encoding="utf-8")
print(json.dumps({"letter": letter, "rows": len(rows), "output": str(output)}, indent=2))
