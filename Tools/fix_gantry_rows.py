"""Recentre the gantry arches onto their production lines.

Measured (Tools/Diagnostics/dump_shop_rows.py): weld machine lines run at
y=-13067/-9099/-5192 but the gantry rows stand at -11200/-7000 - exactly
midway, straddling empty aisles. Assembly likewise (lines 3609/7391/9609/
13391, gantries 5500/11500). Paint's single row already sits on its line.
Move each gantry row (arches and their lamp actors) onto the nearest
line, so the arches span conveyors the way process gantries should.
"""
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_fix_gantries.json"

# old row y -> measured line y (nearest line; outer pairs, symmetric).
MOVES = {
    "Weld_": {-11200.0: -13067.0, -7000.0: -5192.0},
    "Assembly_": {5500.0: 3609.0, 11500.0: 13391.0},
}
TOLERANCE = 300.0

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

report = {"moved": 0, "rows": []}
for actor in ACTOR_SUB.get_all_level_actors():
    label = actor.get_actor_label()
    prefix = next((p for p in MOVES if label.startswith(p + "Gantry")), None)
    if not prefix:
        continue
    where = actor.get_actor_location()
    for old_y, new_y in MOVES[prefix].items():
        if abs(where.y - old_y) <= TOLERANCE:
            offset = new_y - old_y
            actor.set_actor_location(
                unreal.Vector(where.x, where.y + offset, where.z),
                False, False)
            report["moved"] += 1
            report["rows"].append([label, round(where.y), round(
                where.y + offset)])
            break

if not LEVEL_SUB.save_current_level():
    raise RuntimeError("could not save the level")

with open(OUT, "w") as handle:
    json.dump(report, handle, indent=1)
unreal.log("LINE_BOSS_FIX_GANTRIES moved={}".format(report["moved"]))
