"""Read-only exact-map diagnostic for imported/overridden material slot identities."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainAMechanicalBayCandidate_v008"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_material_slot_diagnostic_v008.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

labels = (
    "CA_MW_PTA_S02_DRAW_PRESS",
    "CA_MW_PTA_S02_MechanicalBayDress",
)
records = []
for label in labels:
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        records.append({"actor": label, "error": f"expected one actor, found {len(matches)}"})
        continue
    actor = matches[0]
    component = actor.static_mesh_component
    mesh = component.get_editor_property("static_mesh")
    slots = []
    for index, entry in enumerate(mesh.get_editor_property("static_materials")):
        mesh_material = entry.get_editor_property("material_interface")
        override = component.get_material(index)
        slots.append({
            "index": index,
            "slot_name": str(entry.get_editor_property("material_slot_name")),
            "imported_material": mesh_material.get_path_name() if mesh_material else None,
            "component_material": override.get_path_name() if override else None,
        })
    records.append({"actor": label, "mesh": mesh.get_path_name(), "slots": slots})

report = {
    "$schema": "cairnwell/diagnostic/press-train-a-material-slots-v008/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "records": records,
    "mutated_map": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
