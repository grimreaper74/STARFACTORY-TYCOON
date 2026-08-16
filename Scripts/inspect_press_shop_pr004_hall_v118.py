"""Read-only v118 hall-surface and active-light inventory for the next visual slice."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_hall_inspection_v118.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)


def vec(value):
    return [round(float(value.x), 3), round(float(value.y), 3), round(float(value.z), 3)]


surfaces = []
lights = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if isinstance(actor, unreal.StaticMeshActor):
        origin, extent = actor.get_actor_bounds(False)
        size = [float(extent.x * 2), float(extent.y * 2), float(extent.z * 2)]
        lower = label.lower()
        vertical = size[2] >= 500.0 and min(size[0], size[1]) <= 300.0
        named = any(token in lower for token in ("wall", "column", "pillar", "roof", "ceiling", "hall", "shell"))
        if vertical or named:
            component = actor.static_mesh_component
            surfaces.append({
                "label": label,
                "location_cm": vec(actor.get_actor_location()),
                "bounds_size_cm": [round(value, 3) for value in size],
                "materials": [(component.get_material(i).get_path_name() if component.get_material(i) else None)
                              for i in range(component.get_num_materials())],
                "tags": [str(value) for value in actor.tags],
            })
    component = None
    if isinstance(actor, unreal.DirectionalLight):
        component = actor.get_component_by_class(unreal.DirectionalLightComponent)
    elif isinstance(actor, unreal.SkyLight):
        component = actor.get_component_by_class(unreal.SkyLightComponent)
    elif isinstance(actor, unreal.RectLight):
        component = actor.get_component_by_class(unreal.RectLightComponent)
    elif isinstance(actor, unreal.PointLight):
        component = actor.get_component_by_class(unreal.PointLightComponent)
    elif isinstance(actor, unreal.SpotLight):
        component = actor.get_component_by_class(unreal.SpotLightComponent)
    if component is not None:
        try:
            intensity = float(component.get_editor_property("intensity"))
        except Exception:
            intensity = None
        try:
            affects_world = bool(component.get_editor_property("affects_world"))
        except Exception:
            affects_world = True
        lights.append({"label": label, "class": actor.get_class().get_name(), "location_cm": vec(actor.get_actor_location()),
                       "intensity": intensity, "affects_world": affects_world, "hidden": actor.is_hidden_ed(),
                       "tags": [str(value) for value in actor.tags]})

payload = {
    "$schema": "cairnwell/audit/press-shop-pr004-hall-inspection-v118/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_V118_HALL_AND_LIGHT_INVENTORY__NO_ASSETS_CHANGED",
    "map": MAP,
    "surface_count": len(surfaces),
    "light_count": len(lights),
    "surfaces": sorted(surfaces, key=lambda row: row["label"]),
    "lights": sorted(lights, key=lambda row: row["label"]),
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "surface_count": len(surfaces), "light_count": len(lights)}, indent=2))
