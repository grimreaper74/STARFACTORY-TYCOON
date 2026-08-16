"""Inventory exact v035 stage/crown/facade material slots before calibration."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainAFacadeMaterialCandidate_v035"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_v035_material_roles.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

records = []
for actor in actors_api.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    tags = {str(tag) for tag in actor.tags}
    if "LB.PressTrain.TrainA.Isolated" not in tags:
        continue
    if not (
        any(tag.startswith("LB.PressTrain.Stage.S") for tag in tags)
        or "LB.PressTrain.Fixed.ExteriorDetail" in tags
        or "LB.PressTrain.Fixed.EnclosedFacade" in tags
        or "LB.PressTrain.Fixed.MechanicalBay" in tags
    ):
        continue
    component = actor.static_mesh_component
    slots = []
    for index, slot_name in enumerate(component.get_material_slot_names()):
        material = component.get_material(index)
        slots.append({
            "index": index, "slot": str(slot_name),
            "material": material.get_path_name() if material else None,
        })
    mesh = component.get_editor_property("static_mesh")
    records.append({
        "actor": actor.get_actor_label(),
        "mesh": mesh.get_path_name() if mesh else None,
        "location_cm": [round(value, 3) for value in (
            actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z)],
        "tags": sorted(tags), "slots": slots,
    })

report = {
    "$schema": "cairnwell/inspection/press-train-a-v035-material-roles/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP, "actor_count": len(records), "actors": sorted(records, key=lambda row: row["actor"]),
    "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": "PASS__PRESS_TRAIN_A_V035_MATERIAL_ROLE_INVENTORY", "actor_count": len(records), "output": str(OUT)}, indent=2))
