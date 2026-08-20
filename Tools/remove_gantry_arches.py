"""Remove the light-gantry arches from all three shops.

Owner, 2026-08-21: "get rid of the arches with the lights in" - with
the machine lines rebuilt to full detail the decorative arch rows
read as clutter. Deletes every saved actor whose label starts with
<Shop>_Gantry (arches and their lamp fittings share the prefix).
Process portals (PF track, framing gates, vision tunnels) are placed
by the line scripts under different names and are untouched.
"""
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_remove_gantries.json"
PREFIXES = ("Weld_Gantry", "Assembly_Gantry", "Paint_Gantry")

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

report = {"removed": 0, "by_prefix": {}, "meshes": {}}
doomed = []
for actor in ACTOR_SUB.get_all_level_actors():
    label = actor.get_actor_label()
    prefix = next((p for p in PREFIXES if label.startswith(p)), None)
    if not prefix:
        continue
    report["by_prefix"][prefix] = report["by_prefix"].get(prefix, 0) + 1
    for component in actor.get_components_by_class(
            unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh:
            name = mesh.get_name()
            report["meshes"][name] = report["meshes"].get(name, 0) + 1
    doomed.append(actor)

for actor in doomed:
    ACTOR_SUB.destroy_actor(actor)
report["removed"] = len(doomed)

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")
with open(OUT, "w") as handle:
    json.dump(report, handle, indent=1)
unreal.log("LINE_BOSS_REMOVE_GANTRIES removed={} prefixes={}".format(
    report["removed"], report["by_prefix"]))
