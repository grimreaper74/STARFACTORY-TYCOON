"""Read-only material-slot inventory for the twelve PR003 coil presentations."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004HallContextCandidate_v138"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_pr003_coil_materials_v138.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

pattern = re.compile(r"CS-(0[1-9]|1[0-2])")
rows = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    tags = [str(value) for value in actor.tags]
    text = " ".join([label] + tags)
    if "Coil" not in label or not pattern.search(text):
        continue
    components = actor.get_components_by_class(unreal.StaticMeshComponent)
    for component in components:
        mesh = component.get_editor_property("static_mesh")
        if mesh is None:
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
    "$schema": "cairnwell/audit/press-shop-pr003-coil-materials-v138/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_MATERIAL_INVENTORY__NO_ASSETS_CHANGED",
    "map": MAP,
    "component_count": len(rows),
    "rows": rows,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({
    "component_count": len(rows),
    "actors": sorted(set(row["actor"] for row in rows)),
    "materials": sorted(set(material for row in rows for material in row["materials"] if material)),
}, indent=2))
