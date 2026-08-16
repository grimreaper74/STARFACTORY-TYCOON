"""Read-only inventory of v180 hall shell actors for the next visual branch."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_v180_hall_surface_inventory.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"could not load {MAP}")

tokens = ("wall", "roof", "column", "portal", "frame", "structure", "hall", "cladding", "beam", "truss")
rows = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    tags = [str(value) for value in actor.tags]
    if not (any(token in label.lower() for token in tokens)
            or any("Environment" in value or "Hall" in value for value in tags)):
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    row = {
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.pitch, rotation.yaw, rotation.roll],
        "scale": [scale.x, scale.y, scale.z],
        "tags": tags,
    }
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        mesh = component.static_mesh
        row["mesh"] = mesh.get_path_name() if mesh else None
        row["materials"] = [material.get_path_name() if material else None for material in component.get_materials()]
        origin, extent = actor.get_actor_bounds(False)
        row["bounds_origin_cm"] = [origin.x, origin.y, origin.z]
        row["bounds_extent_cm"] = [extent.x, extent.y, extent.z]
    rows.append(row)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "actor_count": len(rows), "actors": rows}, indent=2), encoding="utf-8")
print(f"WROTE {OUT} actors={len(rows)}")
