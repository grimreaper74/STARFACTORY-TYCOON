"""Cluster each shop's machine rows and compare gantry rows against them.

The gantry arches stand on the floor in two rows per shop; if a row's Y
doesn't match a machine-line Y, the arches straddle nothing - 'out of
position' as the owner reports. Dump machine-Y clusters per shop prefix
plus the gantry rows so the fix is a measured recentre, not a guess.
"""
import json
from collections import defaultdict

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_shop_rows.json"
PREFIXES = ("Weld_", "Assembly_", "Paint_", "Press_")

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

machines = defaultdict(list)
gantries = defaultdict(list)
for actor in ACTOR_SUB.get_all_level_actors():
    label = actor.get_actor_label()
    prefix = next((p for p in PREFIXES if label.startswith(p)), None)
    if not prefix:
        continue
    where = actor.get_actor_location()
    if "Gantry" in label and "Light" not in label:
        gantries[prefix].append((label, round(where.x), round(where.y)))
    elif "Gantry" not in label and "Wall" not in label \
            and "Roof" not in label:
        machines[prefix].append(round(where.y))

def cluster(values, gap=600):
    rows = []
    for v in sorted(values):
        if rows and v - rows[-1][-1] <= gap:
            rows[-1].append(v)
        else:
            rows.append([v])
    return [{"y": round(sum(r) / len(r)), "count": len(r)} for r in rows
            if len(r) >= 3]

result = {}
for prefix in PREFIXES:
    result[prefix] = {
        "machine_rows": cluster(machines[prefix]),
        "gantry_rows": sorted(set(y for _, _, y in gantries[prefix])),
        "gantry_count": len(gantries[prefix]),
    }

with open(OUT, "w") as handle:
    json.dump(result, handle, indent=1)
unreal.log("LINE_BOSS_SHOP_ROWS out={}".format(OUT))
