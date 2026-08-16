"""Read-only: record material overrides for every non-train static mesh actor
of the restored press shop.

For each actor whose component overrides differ from the mesh's default
material list, emit the mesh path, datum-relative location (to join against
shop_manifest.json) and the full slot-by-slot material list. Also dump the
default material list of every unique mesh so 'no override' cases can still be
compared against what the reference map showed.
"""
import json
import os
from collections import defaultdict

import unreal

OUT = os.environ["LB_MATS_OUT"]
MAP = "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001"
DATUM = (3850.0, -4300.0, 0.0)

report = {"map": MAP, "datum": DATUM, "overrides": [], "mesh_defaults": {},
          "skipped": 0, "errors": []}
try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
    actors = unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem).get_all_level_actors()
    for actor in actors:
        if not actor:
            continue
        tags = [str(t) for t in actor.tags]
        if any("PressTrain.Installed" in t for t in tags):
            continue
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        component = actor.static_mesh_component
        mesh = component.static_mesh if component else None
        if not mesh:
            report["skipped"] += 1
            continue
        mesh_path = mesh.get_path_name().rsplit(".", 1)[0]
        if mesh_path not in report["mesh_defaults"]:
            defaults = []
            for static_material in mesh.static_materials:
                interface = static_material.material_interface
                defaults.append(interface.get_path_name().rsplit(".", 1)[0]
                                if interface else None)
            report["mesh_defaults"][mesh_path] = defaults
        defaults = report["mesh_defaults"][mesh_path]
        slots = []
        differs = False
        for index in range(component.get_num_materials()):
            interface = component.get_material(index)
            path = (interface.get_path_name().rsplit(".", 1)[0]
                    if interface else None)
            slots.append(path)
            default = defaults[index] if index < len(defaults) else None
            if path != default:
                differs = True
        if differs:
            location = actor.get_actor_location()
            report["overrides"].append({
                "mesh": mesh_path,
                "loc": [round(location.x - DATUM[0], 1),
                        round(location.y - DATUM[1], 1),
                        round(location.z - DATUM[2], 1)],
                "mats": slots,
            })
except Exception as error:  # noqa: BLE001
    import traceback
    report["errors"].append({"error": str(error),
                             "traceback": traceback.format_exc()})

with open(OUT, "w", encoding="utf-8") as handle:
    json.dump(report, handle)
unreal.log("LB_MATS_EXTRACT overrides=%d meshes=%d skipped=%d"
           % (len(report["overrides"]), len(report["mesh_defaults"]),
              report["skipped"]))
