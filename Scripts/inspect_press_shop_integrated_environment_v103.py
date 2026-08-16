"""Read-only whole-map scene inspection prompted by the 2026-08-05 user walkthrough.

This script never saves the level or assets. It records exact light conflicts,
large floor/pad actors and hall-shell candidates before any v103 successor is
authored.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103"
OUT = ROOT / "Saved/Audits/PressShopIntegration/integrated_environment_inspection_v103.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"could not load {MAP}")


def tags(actor):
    return [str(value) for value in actor.tags]


def vector(value):
    return [round(float(value.x), 3), round(float(value.y), 3), round(float(value.z), 3)]


def bounds(actor):
    origin, extent = actor.get_actor_bounds(False)
    return {
        "origin_cm": vector(origin),
        "extent_cm": vector(extent),
        "size_cm": [round(float(extent.x * 2), 3), round(float(extent.y * 2), 3), round(float(extent.z * 2), 3)],
    }


def safe(component, name, default=None):
    try:
        value = component.get_editor_property(name)
        if isinstance(value, unreal.LinearColor):
            return [round(float(value.r), 5), round(float(value.g), 5), round(float(value.b), 5), round(float(value.a), 5)]
        if hasattr(value, "value"):
            return str(value)
        return value
    except Exception:
        return default


all_actors = actors_api.get_all_level_actors()
lights = []
directional = []
skylights = []
for actor in all_actors:
    component = None
    kind = None
    if isinstance(actor, unreal.DirectionalLight):
        kind = "DirectionalLight"
        component = actor.get_component_by_class(unreal.DirectionalLightComponent)
    elif isinstance(actor, unreal.SkyLight):
        kind = "SkyLight"
        component = actor.get_component_by_class(unreal.SkyLightComponent)
    elif isinstance(actor, unreal.RectLight):
        kind = "RectLight"
        component = actor.get_component_by_class(unreal.RectLightComponent)
    elif isinstance(actor, unreal.PointLight):
        kind = "PointLight"
        component = actor.get_component_by_class(unreal.PointLightComponent)
    elif isinstance(actor, unreal.SpotLight):
        kind = "SpotLight"
        component = actor.get_component_by_class(unreal.SpotLightComponent)
    if component is None:
        continue
    row = {
        "label": actor.get_actor_label(),
        "class": kind,
        "location_cm": vector(actor.get_actor_location()),
        "rotation": str(actor.get_actor_rotation()),
        "tags": tags(actor),
        "visible": not actor.is_hidden_ed(),
        "intensity": safe(component, "intensity"),
        "light_color": safe(component, "light_color"),
        "mobility": safe(component, "mobility"),
        "cast_shadows": safe(component, "cast_shadows"),
        "affects_world": safe(component, "affects_world"),
        "forward_shading_priority": safe(component, "forward_shading_priority"),
    }
    if kind == "SkyLight":
        row.update({
            "real_time_capture": safe(component, "real_time_capture"),
            "source_type": safe(component, "source_type"),
            "cubemap": str(safe(component, "cubemap", "")),
        })
        skylights.append(row)
    if kind == "DirectionalLight":
        directional.append(row)
    lights.append(row)

large_surfaces = []
hall_structure = []
for actor in all_actors:
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    b = bounds(actor)
    sx, sy, sz = b["size_cm"]
    label = actor.get_actor_label()
    lower = label.lower()
    component = actor.static_mesh_component
    mesh = component.get_editor_property("static_mesh")
    material_paths = []
    for index in range(component.get_num_materials()):
        material = component.get_material(index)
        material_paths.append(material.get_path_name() if material else None)
    row = {
        "label": label,
        "mesh": mesh.get_path_name() if mesh else None,
        "location_cm": vector(actor.get_actor_location()),
        "rotation": str(actor.get_actor_rotation()),
        "scale": vector(actor.get_actor_scale3d()),
        "bounds": b,
        "tags": tags(actor),
        "materials": material_paths,
        "collision_enabled": str(safe(component, "collision_enabled")),
        "can_ever_affect_navigation": safe(component, "can_ever_affect_navigation"),
        "visible": not actor.is_hidden_ed(),
    }
    floor_word = any(token in lower for token in ("floor", "pad", "walk", "aisle", "zone", "slab", "foundation", "route"))
    if (sx >= 500 and sy >= 500 and sz <= 250) or floor_word:
        large_surfaces.append(row)
    structure_word = any(token in lower for token in ("wall", "roof", "ceiling", "column", "beam", "truss", "hall", "shell"))
    if structure_word or max(sx, sy, sz) >= 5000:
        hall_structure.append(row)

atmosphere_classes = {
    "SkyAtmosphere": 0,
    "VolumetricCloud": 0,
    "ExponentialHeightFog": 0,
}
for actor in all_actors:
    class_name = actor.get_class().get_name()
    for key in atmosphere_classes:
        if key.lower() in class_name.lower():
            atmosphere_classes[key] += 1

real_time_skylights = [row for row in skylights if row.get("real_time_capture") is True and row.get("visible")]
active_directionals = [row for row in directional if row.get("visible") and row.get("affects_world") is not False]
findings = []
if real_time_skylights and atmosphere_classes["SkyAtmosphere"] == 0 and atmosphere_classes["VolumetricCloud"] == 0:
    findings.append("real-time skylight has no SkyAtmosphere or VolumetricCloud actor")
if len(active_directionals) > 1:
    findings.append(f"{len(active_directionals)} visible world-affecting directional lights compete for the forward-light role")
if not large_surfaces:
    findings.append("no large floor/pad candidates were identified")

payload = {
    "$schema": "cairnwell/audit/press-shop-integrated-environment-inspection-v103/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_INSPECTION__USER_WALKTHROUGH_VISUAL_FAILURES_REQUIRE_ISOLATED_SUCCESSOR__V103_UNCHANGED",
    "map": MAP,
    "actor_count": len(all_actors),
    "light_count": len(lights),
    "directional_light_count": len(directional),
    "active_directional_light_count": len(active_directionals),
    "sky_light_count": len(skylights),
    "real_time_sky_light_count": len(real_time_skylights),
    "atmosphere_actor_counts": atmosphere_classes,
    "findings": findings,
    "directional_lights": directional,
    "sky_lights": skylights,
    "all_lights": lights,
    "large_floor_pad_and_route_candidates": large_surfaces,
    "hall_structure_candidates": hall_structure,
    "accepted_map_saved_or_modified": False,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
print(json.dumps({
    "status": payload["status"],
    "actor_count": payload["actor_count"],
    "light_count": payload["light_count"],
    "findings": findings,
    "large_surface_count": len(large_surfaces),
    "hall_structure_count": len(hall_structure),
    "audit": str(OUT),
}, indent=2))
