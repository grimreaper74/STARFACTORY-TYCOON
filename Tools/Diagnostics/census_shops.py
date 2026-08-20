"""Census of every shop's actors: mesh, count, position spread.

Groundwork for rebuilding weld, paint and assembly to press's process
standard (owner, 2026-08-20). Per shop prefix: which meshes stand in it,
how many of each, their X/Y extents - plus every actor whose mesh name
suggests a robot, so assembly's foreign robots can be identified against
the project's canonical six-axis units.
"""
import json
import re
from collections import defaultdict

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_census.json"
PREFIXES = ("Press_", "PT_LB_", "Weld_", "Paint_", "Assembly_", "Zone_",
            "LB_OF_")

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

census = defaultdict(lambda: defaultdict(lambda: {
    "count": 0, "min": [1e9, 1e9], "max": [-1e9, -1e9]}))
robots = defaultdict(lambda: defaultdict(int))

for actor in ACTOR_SUB.get_all_level_actors():
    label = actor.get_actor_label()
    prefix = next((p for p in PREFIXES if label.startswith(p)), None)
    if prefix is None:
        continue
    where = actor.get_actor_location()
    for component in actor.get_components_by_class(
            unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None:
            continue
        name = mesh.get_name()
        entry = census[prefix][name]
        entry["count"] += 1
        entry["min"][0] = min(entry["min"][0], round(where.x))
        entry["min"][1] = min(entry["min"][1], round(where.y))
        entry["max"][0] = max(entry["max"][0], round(where.x))
        entry["max"][1] = max(entry["max"][1], round(where.y))
        if re.search(r"robot|sixaxis|six_axis|arm", name, re.IGNORECASE):
            robots[prefix][name] += 1

result = {"census": {}, "robots": {k: dict(v) for k, v in robots.items()}}
for prefix, meshes in census.items():
    ranked = sorted(meshes.items(), key=lambda kv: -kv[1]["count"])
    result["census"][prefix] = [
        {"mesh": name, **info} for name, info in ranked[:40]]

with open(OUT, "w") as handle:
    json.dump(result, handle, indent=1)
unreal.log("LINE_BOSS_CENSUS prefixes={}".format(list(census)))
