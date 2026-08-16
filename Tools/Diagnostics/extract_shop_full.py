"""Read-only: extract EVERY static-mesh component of the restored press shop.

The first extraction took only root StaticMeshActors and skipped 442 composed
actors - the PR-004 destrap cell, the decoiler/threader, the blanking line -
plus 776 engine-primitive actors carrying floor markings, plinths and kerbs.
This pass walks every non-train actor's StaticMeshComponents (instanced ones
per instance), records world transform, mesh and full slot material list, so
the shop can be rebuilt in Moorcross at reference density. The protected map
is only read.
"""
import json
import os

import unreal

OUT = os.environ["LB_SHOP_OUT"]
MAP = "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001"
DATUM = (3850.0, -4300.0, 0.0)

report = {"map": MAP, "datum": DATUM, "actors": [], "actor_count": 0,
          "component_count": 0, "instance_count": 0, "errors": []}


def record(mesh, transform, materials):
    location = transform.translation
    rotation = transform.rotation.rotator()
    scale = transform.scale3d
    report["actors"].append({
        "mesh": mesh.get_path_name().rsplit(".", 1)[0],
        "loc": [round(location.x - DATUM[0], 1),
                round(location.y - DATUM[1], 1),
                round(location.z - DATUM[2], 1)],
        "rot": [round(rotation.pitch, 3), round(rotation.yaw, 3),
                round(rotation.roll, 3)],
        "scale": [round(scale.x, 4), round(scale.y, 4), round(scale.z, 4)],
        "mats": materials,
    })


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
        if actor.hidden:
            continue
        components = actor.get_components_by_class(
            unreal.StaticMeshComponent)
        if not components:
            continue
        report["actor_count"] += 1
        for component in components:
            mesh = component.static_mesh
            if not mesh:
                continue
            if not component.is_visible():
                continue
            materials = []
            any_material = False
            for index in range(component.get_num_materials()):
                interface = component.get_material(index)
                if interface:
                    materials.append(
                        interface.get_path_name().rsplit(".", 1)[0])
                    any_material = True
                else:
                    materials.append(None)
            if not any_material:
                materials = []
            report["component_count"] += 1
            if isinstance(component, unreal.InstancedStaticMeshComponent):
                count = component.get_instance_count()
                for index in range(count):
                    transform = component.get_instance_transform(
                        index, world_space=True)
                    record(mesh, transform, materials)
                    report["instance_count"] += 1
            else:
                record(mesh, component.get_world_transform(), materials)
except Exception as error:  # noqa: BLE001
    import traceback
    report["errors"].append({"error": str(error),
                             "traceback": traceback.format_exc()})

with open(OUT, "w", encoding="utf-8") as handle:
    json.dump(report, handle)
unreal.log("LB_SHOP_FULL actors=%d components=%d instanced=%d recorded=%d"
           % (report["actor_count"], report["component_count"],
              report["instance_count"], len(report["actors"])))
