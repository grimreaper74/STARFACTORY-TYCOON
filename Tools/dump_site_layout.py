"""Dump the site-level layout of Moorcross Works to JSON: the four shop
bays from the shell layout, and every site actor (fence, gates, roads,
buildings, logistics dressing) with its bounds, for the site plan drawing.

Run with -ExecutePythonScript.
"""
import io
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_site_layout.json"

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

report = {"bays": [], "site": [], "shells": [], "counts": {}}

layout = unreal.LBOneFactoryLayoutLibrary.make_moorcross_works_shell_layout()
for bay in layout.get_editor_property("department_bays"):
    centre = bay.get_editor_property("world_transform").translation
    size = bay.get_editor_property("size_cm")
    report["bays"].append({
        "department": str(bay.get_editor_property("department")),
        "centre": [round(centre.x), round(centre.y)],
        "size": [round(size.x), round(size.y)]})

SITE_TOKENS = ("fence", "gate", "road", "kerb", "tarmac", "yard", "lorry",
               "truck", "container", "tower", "hangar", "background",
               "skyline", "car_", "parking", "tree", "wall", "roof",
               "shutter", "door", "sign", "bollard", "path", "grass",
               "apron", "slab", "floor")
for actor in ACTOR_SUB.get_all_level_actors():
    if not actor:
        continue
    label = actor.get_actor_label()
    lower = label.lower()
    if not any(token in lower for token in SITE_TOKENS):
        continue
    origin, extent = actor.get_actor_bounds(False)
    entry = {
        "label": label,
        "class": actor.get_class().get_name(),
        "centre": [round(origin.x), round(origin.y)],
        "extent": [round(extent.x), round(extent.y)],
        "z_top": round(origin.z + extent.z)}
    key = "shells" if ("wall" in lower or "roof" in lower
                       or "floor" in lower or "slab" in lower) else "site"
    report[key].append(entry)
    cls = entry["class"]
    report["counts"][cls] = report["counts"].get(cls, 0) + 1

with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_SITE_DUMP bays={} site={} shells={}".format(
    len(report["bays"]), len(report["site"]), len(report["shells"])))
