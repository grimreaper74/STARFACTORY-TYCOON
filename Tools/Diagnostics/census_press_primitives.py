"""What do the press shop's raw primitives represent?

715 Cubes, 166 Cylinders and 30 Planes hide under PT_LB_ labels. Group
them by label family (digits stripped) with counts and size ranges so
the rebuild knows which families are walls (permitted) and which are
machine stand-ins to replace with authored models.
"""
import json
import re
from collections import defaultdict

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_press_primitives.json"

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

families = defaultdict(lambda: {"count": 0, "min_size": [1e9] * 3,
                                "max_size": [0.0] * 3, "example": ""})
for actor in ACTOR_SUB.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith("PT_LB_"):
        continue
    for component in actor.get_components_by_class(
            unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or mesh.get_name() not in ("Cube", "Cylinder",
                                                   "Plane"):
            continue
        origin, extent = actor.get_actor_bounds(False)
        family = re.sub(r"[\d_\-\.]+$", "", label)
        entry = families[family + "|" + mesh.get_name()]
        entry["count"] += 1
        entry["example"] = label
        for axis, size in enumerate((extent.x * 2.0, extent.y * 2.0,
                                     extent.z * 2.0)):
            entry["min_size"][axis] = min(entry["min_size"][axis], size)
            entry["max_size"][axis] = max(entry["max_size"][axis], size)

result = sorted(
    ({"family": key, **value} for key, value in families.items()),
    key=lambda row: -row["count"])
with open(OUT, "w") as handle:
    json.dump(result, handle, indent=1)
unreal.log("LINE_BOSS_PRESS_PRIMS families={}".format(len(result)))
