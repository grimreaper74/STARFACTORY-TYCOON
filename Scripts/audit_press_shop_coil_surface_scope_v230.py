"""Read-only v230 inventory for packaged PR003 and AGV-loaded coil surfaces."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_coil_surface_scope_v230.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
for actor in actors_api.get_all_level_actors():
    tags = [str(value) for value in actor.tags]
    label = actor.get_actor_label()
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or "MasterCoil" not in mesh.get_path_name():
            continue
        location = actor.get_actor_location()
        rows.append({
            "actor": label,
            "component": component.get_name(),
            "mesh": mesh.get_path_name(),
            "location_cm": [round(float(location.x), 3), round(float(location.y), 3), round(float(location.z), 3)],
            "materials": [
                component.get_material(index).get_path_name() if component.get_material(index) else None
                for index in range(component.get_num_materials())
            ],
            "tags": tags,
        })

payload = {
    "$schema": "cairnwell/audit/press-shop-coil-surface-scope-v230/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY__NO_ASSETS_CHANGED",
    "map": MAP,
    "component_count": len(rows),
    "rows": sorted(rows, key=lambda row: (row["location_cm"][0], row["location_cm"][1], row["actor"])),
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({
    "component_count": len(rows),
    "actors": [row["actor"] for row in payload["rows"]],
    "material_sets": sorted({tuple(row["materials"]) for row in rows}),
}, indent=2))
