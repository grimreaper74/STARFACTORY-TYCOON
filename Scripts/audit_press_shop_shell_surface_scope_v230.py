"""Read-only inventory of v230 whole-hall shell wall and roof-liner surfaces."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_shell_surface_scope_v230.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

rows = []
for actor in actors_api.get_all_level_actors():
    tags = [str(value) for value in actor.tags]
    label = actor.get_actor_label()
    scope = None
    if label in {"LB_PRESS_Wall_North", "LB_PRESS_Wall_South", "LB_PRESS_Wall_West", "LB_PRESS_Wall_East"}:
        scope = "primary_perimeter_wall"
    elif "LB.Module.FactoryRoofLiner" in tags:
        scope = "front_end_roof_liner"
    if scope is None:
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        continue
    location = actor.get_actor_location()
    scale = actor.get_actor_scale3d()
    rows.append({
        "scope": scope,
        "label": label,
        "location_cm": [location.x, location.y, location.z],
        "scale": [scale.x, scale.y, scale.z],
        "materials": [
            component.get_material(index).get_path_name() if component.get_material(index) else None
            for index in range(component.get_num_materials())
        ],
        "collision": str(component.get_collision_enabled()),
        "tags": tags,
    })

payload = {
    "$schema": "cairnwell/audit/press-shop-shell-surface-scope-v230/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY__NO_ASSETS_CHANGED",
    "map": MAP,
    "counts": {
        "primary_perimeter_wall": sum(row["scope"] == "primary_perimeter_wall" for row in rows),
        "front_end_roof_liner": sum(row["scope"] == "front_end_roof_liner" for row in rows),
    },
    "rows": sorted(rows, key=lambda row: (row["scope"], row["label"])),
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
