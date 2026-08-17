"""Dump the complete actor inventory of Codex's reference press-shop map.

Read-only. The reference map is the protected authority for what a finished press
shop contains, and it must never be modified - this loads it, records everything
the OneFactory bootstrap guards inspect, and saves nothing.

Recorded per actor: name, label, class (and its ancestry), tags, every static mesh
path, every bound material path, and light details. That is exactly the surface
ALBOneFactoryBootstrap inspects when deciding whether a world may commission a
factory, so the dump is sufficient to predict - offline, without another editor
run - whether level-instancing this map into Moorcross would be rejected.

Run headless (an editor world is required):
  UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=Tools/Diagnostics/dump_reference_press_actors.py
"""
import io
import json
import os

import unreal

LEVEL = "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001"
OUT = os.environ.get("LB_REF_DUMP_OUT", "C:/Temp/lb_reference_press.json")

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not LEVEL_SUB.load_level(LEVEL):
    raise RuntimeError("could not load {}".format(LEVEL))
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or LEVEL.rsplit("/", 1)[-1] != world.get_name():
    raise RuntimeError(
        "expected world '{}' but got '{}'. Use -ExecutePythonScript.".format(
            LEVEL.rsplit("/", 1)[-1],
            "<none>" if world is None else world.get_name()))

actors = ACTOR_SUB.get_all_level_actors()
report = {"level": LEVEL, "actor_total": len(actors), "actors": []}

min_x = min_y = min_z = float("inf")
max_x = max_y = max_z = float("-inf")

for actor in actors:
    if actor is None:
        continue
    entry = {
        "name": actor.get_name(),
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "tags": [str(t) for t in actor.tags],
    }

    # IsMapOwnedProductionActorClassName walks the superclass chain, so record the
    # full class path as well as the leaf name. Walking the chain from Python is
    # unreliable across engine versions; the path is unambiguous and the offline
    # analysis can resolve ancestry from the C++ class list instead.
    entry["class_path"] = actor.get_class().get_path_name()

    location = actor.get_actor_location()
    entry["loc"] = [round(location.x, 1), round(location.y, 1),
                    round(location.z, 1)]
    rotation = actor.get_actor_rotation()
    entry["rot"] = [round(rotation.pitch, 2), round(rotation.yaw, 2),
                    round(rotation.roll, 2)]
    scale = actor.get_actor_scale3d()
    entry["scale"] = [round(scale.x, 4), round(scale.y, 4), round(scale.z, 4)]

    min_x = min(min_x, location.x); max_x = max(max_x, location.x)
    min_y = min(min_y, location.y); max_y = max(max_y, location.y)
    min_z = min(min_z, location.z); max_z = max(max_z, location.z)

    meshes = []
    materials = []
    components = actor.get_components_by_class(unreal.StaticMeshComponent)
    for component in components:
        if component is None:
            continue
        asset = component.static_mesh
        if asset:
            meshes.append(asset.get_path_name())
        for slot in range(component.get_num_materials()):
            bound = component.get_material(slot)
            if bound:
                materials.append(bound.get_path_name())
    if meshes:
        entry["meshes"] = sorted(set(meshes))
    if materials:
        entry["materials"] = sorted(set(materials))
    entry["static_mesh_components"] = len(components)

    # Lights are the part a mesh-only manifest can never carry, so record them
    # in full: they are most of why the reference shop reads as a real shop.
    if isinstance(actor, unreal.Light):
        component = actor.light_component
        light = {}
        if component:
            for prop in ("intensity", "attenuation_radius", "cast_shadows",
                         "intensity_units", "temperature", "use_temperature",
                         "source_width", "source_height", "outer_cone_angle"):
                try:
                    light[prop] = str(component.get_editor_property(prop))
                except Exception:  # noqa: BLE001 - varies by light class
                    pass
            try:
                colour = component.get_editor_property("light_color")
                light["light_color"] = [colour.r, colour.g, colour.b]
            except Exception:  # noqa: BLE001
                pass
        entry["light"] = light

    report["actors"].append(entry)

report["bounds"] = {
    "min": [round(min_x, 1), round(min_y, 1), round(min_z, 1)],
    "max": [round(max_x, 1), round(max_y, 1), round(max_z, 1)],
    "size_m": [round((max_x - min_x) / 100.0, 1),
               round((max_y - min_y) / 100.0, 1),
               round((max_z - min_z) / 100.0, 1)],
}

with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_REF_DUMP {} actors, bounds {} m -> {}".format(
    report["actor_total"], report["bounds"]["size_m"], OUT))
