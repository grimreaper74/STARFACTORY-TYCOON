"""Diagnostic: where is press, really? Dumps (a) the bounds of the
transplanted PT_* visual content, (b) the runtime press station
transforms from the configured route, (c) the press bay rectangle, and
(d) the press wall dimensions, so the correction transform is computed
from measurements. Read-only. Run with -ExecutePythonScript.
"""
import io
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_press_alignment.json"

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")

report = {"pt_bounds": None, "pt_count": 0, "press_stations": [],
          "bay": None, "walls": {}, "batch02": None, "cutaway": None}

lo = [1e12, 1e12]
hi = [-1e12, -1e12]
b02_lo = [1e12, 1e12]
b02_hi = [-1e12, -1e12]
for actor in ACTOR_SUB.get_all_level_actors():
    if not actor:
        continue
    label = actor.get_actor_label()
    origin, extent = actor.get_actor_bounds(False)
    if label.startswith("PT_"):
        report["pt_count"] += 1
        lo[0] = min(lo[0], origin.x - extent.x)
        lo[1] = min(lo[1], origin.y - extent.y)
        hi[0] = max(hi[0], origin.x + extent.x)
        hi[1] = max(hi[1], origin.y + extent.y)
        if "PRESS_Wall" in label or "FinishedFloor" in label:
            report["walls"][label] = {
                "centre": [round(origin.x), round(origin.y)],
                "extent": [round(extent.x), round(extent.y),
                           round(extent.z)]}
    if unreal.Name("LB.Batch02") in actor.tags:
        b02_lo[0] = min(b02_lo[0], origin.x - extent.x)
        b02_lo[1] = min(b02_lo[1], origin.y - extent.y)
        b02_hi[0] = max(b02_hi[0], origin.x + extent.x)
        b02_hi[1] = max(b02_hi[1], origin.y + extent.y)
    if "CutawayWalls" in label:
        report["cutaway"] = {"centre": [round(origin.x), round(origin.y)],
                             "extent": [round(extent.x), round(extent.y),
                                        round(extent.z)]}
report["pt_bounds"] = {"min": [round(v) for v in lo],
                       "max": [round(v) for v in hi]}
report["batch02"] = {"min": [round(v) for v in b02_lo],
                     "max": [round(v) for v in b02_hi]}

coordinator = None
for actor in ACTOR_SUB.get_all_level_actors():
    if actor and actor.get_class().get_name() == \
            "LBOneFactoryRuntimeCoordinator":
        coordinator = actor
        break
if coordinator:
    route, topology, reason = coordinator.get_configured_station_route()
    for step in route:
        if str(step.get_editor_property("department")).endswith("PRESS"):
            loc = step.get_editor_property("world_transform").translation
            report["press_stations"].append({
                "id": str(step.get_editor_property("station_id")),
                "at": [round(loc.x), round(loc.y)]})

layout = unreal.LBOneFactoryLayoutLibrary.make_moorcross_works_shell_layout()
for bay in layout.get_editor_property("department_bays"):
    if str(bay.get_editor_property("department")).endswith("PRESS"):
        centre = bay.get_editor_property("world_transform").translation
        size = bay.get_editor_property("size_cm")
        report["bay"] = {"centre": [round(centre.x), round(centre.y)],
                         "size": [round(size.x), round(size.y)]}

with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_PRESS_ALIGN pt={} stations={}".format(
    report["pt_count"], len(report["press_stations"])))
