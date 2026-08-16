"""Read-only inventory of every PR-008 station static-mesh component in v075."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008VisualCleanupCandidate_v075"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_native_component_materials_v075.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

rows = []
for actor in actors_api.get_all_level_actors():
    if actor.get_class().get_name() != "LBPR008Station":
        continue
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.static_mesh
        slots = []
        for index in range(component.get_num_materials()):
            material = component.get_material(index)
            slots.append({
                "index": index,
                "effective_material": material.get_path_name() if material else None,
            })
        rows.append({
            "actor": actor.get_actor_label(),
            "component": component.get_name(),
            "component_tags": sorted(str(tag) for tag in component.component_tags),
            "mesh": mesh.get_path_name() if mesh else None,
            "visible": component.is_visible(),
            "materials": slots,
        })

rows.sort(key=lambda row: row["component"])
payload = {
    "$schema": "line-boss/audit/press-shop-pr008-native-component-materials-v075/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_NATIVE_PR008_COMPONENT_MATERIAL_INVENTORY",
    "map": MAP,
    "component_count": len(rows),
    "components": rows,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR008_V075_NATIVE_COMPONENT_INVENTORY_PASS components={len(rows)}")
unreal.SystemLibrary.quit_editor()
