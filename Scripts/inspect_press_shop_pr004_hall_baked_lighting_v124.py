"""Read-only mobility/lightmap inspection for retained v124 hall surfaces and lights."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124"
OUT = ROOT / "Saved/Audits/press_shop_pr004_hall_baked_lighting_inspection_v124.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"could not load {MAP}")


def hall_role(label):
    if label == "LB_INT_FRONT_NorthWallLowerLiner":
        return "lower_liner"
    if label in ("LB_INT_FRONT_NorthWallUpperLiner", "LB_INT_FRONT_WestWallLiner"):
        return "upper_or_west_liner"
    if label.startswith("LB_INT_FRONT_NorthWallColumn_"):
        return "column"
    if label.startswith("LB_INT_FRONT_NorthWallBeam_"):
        return "beam"
    if label.startswith("LB_PR004_V028_SouthWallLiner_"):
        return "superseded_overlap"
    return None


surfaces = []
lights = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    role = hall_role(label)
    if role and isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        mesh = component.static_mesh
        surfaces.append({
            "actor": label,
            "role": role,
            "mobility": str(component.get_editor_property("mobility")),
            "override_light_map_res": bool(component.get_editor_property("override_light_map_res")),
            "overridden_light_map_res": int(component.get_editor_property("overridden_light_map_res")),
            "mesh": mesh.get_path_name() if mesh else None,
        })
    component = None
    for component_class in (
            unreal.PointLightComponent,
            unreal.SpotLightComponent,
            unreal.RectLightComponent,
            unreal.DirectionalLightComponent,
            unreal.SkyLightComponent):
        component = actor.get_component_by_class(component_class)
        if component is not None:
            break
    if component is not None:
        lights.append({
            "actor": label,
            "class": actor.get_class().get_name(),
            "mobility": str(component.get_editor_property("mobility")),
            "intensity": float(component.get_editor_property("intensity")),
            "affects_world": bool(component.get_editor_property("affects_world")),
            "cast_shadows": bool(component.get_editor_property("cast_shadows")),
            "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        })

report = {
    "$schema": "line-boss/audit/press-shop-pr004-hall-baked-lighting-inspection-v124/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_V124_HALL_MOBILITY_AND_LIGHTMAP_INSPECTION__NO_ASSETS_CHANGED",
    "map": MAP,
    "surface_count": len(surfaces),
    "light_count": len(lights),
    "surfaces": sorted(surfaces, key=lambda item: item["actor"]),
    "lights": sorted(lights, key=lambda item: item["actor"]),
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "surfaces": len(surfaces), "lights": len(lights)}, indent=2))
