"""Read-only inventory of effective PR-008 v075 static-mesh material bindings."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008VisualCleanupCandidate_v075"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_material_bindings_v075.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
material_counts = Counter()
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    tags = sorted(str(tag) for tag in actor.tags)
    if "PR008" not in label and not any("PR008" in tag for tag in tags):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or component.static_mesh is None:
        continue
    slots = []
    static_materials = component.static_mesh.get_editor_property("static_materials")
    for index in range(component.get_num_materials()):
        material = component.get_material(index)
        path = material.get_path_name() if material else None
        material_counts[path or "<None>"] += 1
        slots.append({
            "index": index,
            "slot_name": str(static_materials[index].material_slot_name),
            "effective_material": path,
        })
    rows.append({
        "actor": label,
        "class": actor.get_class().get_name(),
        "tags": tags,
        "mesh": component.static_mesh.get_path_name(),
        "materials": slots,
    })

rows.sort(key=lambda row: row["actor"])
payload = {
    "$schema": "line-boss/audit/press-shop-pr008-material-bindings-v075/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_EFFECTIVE_MATERIAL_INVENTORY",
    "map": MAP,
    "actor_count": len(rows),
    "slot_count": sum(len(row["materials"]) for row in rows),
    "material_counts": dict(sorted(material_counts.items())),
    "actors": rows,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_PR008_V075_MATERIAL_INVENTORY_PASS actors={payload['actor_count']} "
    f"slots={payload['slot_count']} unique={len(material_counts)}"
)
unreal.SystemLibrary.quit_editor()
