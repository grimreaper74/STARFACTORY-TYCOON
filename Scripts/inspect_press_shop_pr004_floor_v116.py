"""Read-only inventory of the surfaces making the v116 floor read as planks."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CarryContextCandidate_v116"
OUT = ROOT / "Saved/Audits/press_shop_pr004_floor_inspection_v116.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"could not load {MAP}")


def vec(value):
    return [round(float(value.x), 3), round(float(value.y), 3), round(float(value.z), 3)]


rows = []
for actor in actors_api.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    label = actor.get_actor_label()
    lower = label.lower()
    origin, extent = actor.get_actor_bounds(False)
    size = [float(extent.x * 2), float(extent.y * 2), float(extent.z * 2)]
    floor_named = any(token in lower for token in ("floor", "slab", "zone", "walk", "route", "pad", "joint"))
    broad_flat = size[0] >= 500.0 and size[1] >= 500.0 and size[2] <= 250.0
    if not (floor_named or broad_flat):
        continue
    component = actor.static_mesh_component
    mesh = component.get_editor_property("static_mesh")
    materials = []
    for index in range(component.get_num_materials()):
        material = component.get_material(index)
        materials.append(material.get_path_name() if material else None)
    rows.append({
        "label": label,
        "location_cm": vec(actor.get_actor_location()),
        "scale": vec(actor.get_actor_scale3d()),
        "bounds_origin_cm": vec(origin),
        "bounds_size_cm": [round(value, 3) for value in size],
        "mesh": mesh.get_path_name() if mesh else None,
        "materials": materials,
        "tags": [str(value) for value in actor.tags],
        "hidden_in_game": bool(actor.get_editor_property("hidden")),
    })

payload = {
    "$schema": "cairnwell/audit/press-shop-pr004-floor-inspection-v116/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_V116_FLOOR_INVENTORY__NO_ASSETS_CHANGED",
    "map": MAP,
    "surface_count": len(rows),
    "surfaces": sorted(rows, key=lambda row: row["label"]),
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "surface_count": len(rows), "audit": str(OUT)}, indent=2))
