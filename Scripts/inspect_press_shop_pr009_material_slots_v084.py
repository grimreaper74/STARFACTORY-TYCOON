"""Read-only Unreal inspection of PR-009 v084 imported and assigned material slots."""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009CorrectedIntegrationCandidate_v084"
PREFIX = "LB_PR009_V084_"
OUT = ROOT / "Saved/Audits/press_shop_pr009_material_slots_v084.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

slot_counts = Counter()
assigned_counts = Counter()
slot_examples = defaultdict(list)
actor_records = []

for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith(PREFIX) or not isinstance(actor, unreal.StaticMeshActor):
        continue
    component = actor.static_mesh_component
    mesh = component.static_mesh
    if not mesh:
        continue
    slots = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        imported = str(slot.get_editor_property("imported_material_slot_name") or "")
        logical = str(slot.get_editor_property("material_slot_name") or "")
        key = imported or logical
        assigned = component.get_material(index)
        assigned_path = assigned.get_path_name() if assigned else None
        slot_counts[key] += 1
        assigned_counts[assigned_path or "<none>"] += 1
        if len(slot_examples[key]) < 8:
            slot_examples[key].append(label)
        slots.append({
            "index": index,
            "imported_name": imported,
            "logical_name": logical,
            "assigned_material": assigned_path,
        })
    actor_records.append({"actor": label, "mesh": mesh.get_path_name(), "slots": slots})

payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-material-slots-v084/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PR009_V084_READ_ONLY_MATERIAL_SLOT_INSPECTION_COMPLETE",
    "map": MAP,
    "actor_count": len(actor_records),
    "unique_slot_count": len(slot_counts),
    "slot_counts": dict(sorted(slot_counts.items())),
    "assigned_material_counts": dict(sorted(assigned_counts.items())),
    "slot_examples": dict(sorted(slot_examples.items())),
    "actors": actor_records,
    "map_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(payload["status"])
unreal.SystemLibrary.quit_editor()
