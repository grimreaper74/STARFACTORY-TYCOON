"""Compare overhead structure bounds against each shop's wall envelope.

Yaws are all clean, so 'arches out of position' means XY/Z placement:
beams overhanging their building, arches off their line or at the wrong
height. Dump per-family positions plus each shop's wall envelope so the
offenders are identifiable by number, not by squinting at a screenshot.
"""
import json
import re

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_overhead_bounds.json"
FAMILIES = re.compile(
    r"RoofBeam|WallBeam|Gantry|LampArch|OpenRoof|Truss", re.IGNORECASE)
WALLS = re.compile(r"Wall", re.IGNORECASE)

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

frames = []
wall_boxes = []
for actor in ACTOR_SUB.get_all_level_actors():
    label = actor.get_actor_label()
    origin, extent = actor.get_actor_bounds(False)
    row = {
        "label": label,
        "min": [round(origin.x - extent.x), round(origin.y - extent.y),
                round(origin.z - extent.z)],
        "max": [round(origin.x + extent.x), round(origin.y + extent.y),
                round(origin.z + extent.z)],
    }
    if FAMILIES.search(label):
        frames.append(row)
    elif WALLS.search(label):
        wall_boxes.append(row)

with open(OUT, "w") as handle:
    json.dump({"frames": frames, "walls": wall_boxes}, handle, indent=1)
unreal.log("LINE_BOSS_OVERHEAD_BOUNDS frames={} walls={}".format(
    len(frames), len(wall_boxes)))
