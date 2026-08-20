"""List the ground, floor and wall actors with their bound materials.

The target frame wants warm cream shop floors, cream walls and green
surroundings; find which actors and material assets actually paint those
surfaces before retinting anything.
"""
import json
import re

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_surfaces.json"
PATTERN = re.compile(r"ground|floor|slab|wall|road|yard", re.IGNORECASE)

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

rows = {}
for actor in ACTOR_SUB.get_all_level_actors():
    label = actor.get_actor_label()
    if not PATTERN.search(label):
        continue
    for component in actor.get_components_by_class(
            unreal.StaticMeshComponent):
        for index in range(component.get_num_materials()):
            material = component.get_material(index)
            key = "{}|{}".format(
                re.sub(r"_?\d+$", "", label),
                material.get_path_name() if material else "none")
            entry = rows.setdefault(key, {"example": label, "count": 0})
            entry["count"] += 1

with open(OUT, "w") as handle:
    json.dump(rows, handle, indent=1)
unreal.log("LINE_BOSS_SURFACES groups={}".format(len(rows)))
