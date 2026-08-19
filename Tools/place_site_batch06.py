"""Site batch 06: demolish the legacy one-building cutaway shell and
wall the three open shops.

The owner spotted that press looked misplaced and was the only walled
shop: measurement showed press sits inside its bay, and the false read
came from the old unified building's 620 x 310 m cutaway wall set still
standing around everything. This deletes that legacy shell (walls and
open roof frame; floors stay) and builds cube walls for Body, Paint and
Assembly on their bay perimeters - the sanctioned shell exception -
matched to the press walls' height, thickness and material, with
openings at the process links. Idempotent via LB.Site06.
Run with -ExecutePythonScript.
"""
import io
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_site06.json"
TAG = "LB.Site06"

# Bay rectangles (x_min, x_max, y_min, y_max) from the shell layout.
BAYS = {
    "Body": (-20000.0, -2000.0, -13500.0, -3500.0),
    "Paint": (-1000.0, 21000.0, -13500.0, -3500.0),
    "Assembly": (2500.0, 30500.0, 2500.0, 14500.0),
}
# Openings per bay: (edge, centre_along_edge, half_width).
OPENINGS = {
    "Body": [("north", -14500.0, 600.0),   # stillage feed from press
             ("east", -11200.0, 700.0)],   # BIW bridge to paint
    "Paint": [("west", -11200.0, 700.0),   # BIW bridge from body
              ("north", 15000.0, 600.0)],  # painted body link to assembly
    "Assembly": [("south", 15000.0, 600.0),  # painted body feed
                 ("north", 4700.0, 800.0)],  # dispatch shutter
}

report = {"legacy_removed": [], "walls": 0, "cleared": 0,
          "press_wall": None}

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
w = unreal.EditorLevelLibrary.get_editor_world()
if w is None or TARGET.rsplit("/", 1)[-1] != w.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

wall_height = 1100.0
wall_thickness = 40.0
wall_material = None
for actor in ACTOR_SUB.get_all_level_actors():
    if not actor:
        continue
    label = actor.get_actor_label()
    if unreal.Name(TAG) in actor.tags:
        ACTOR_SUB.destroy_actor(actor)
        report["cleared"] += 1
        continue
    if label in ("LB_OF_ENV_HISM_CutawayWalls_v001",
                 "LB_OF_ENV_HISM_OpenRoofFrame_v001"):
        report["legacy_removed"].append(label)
        ACTOR_SUB.destroy_actor(actor)
        continue
    if label == "PT_LB_PRESS_Wall_North" and report["press_wall"] is None:
        origin, extent = actor.get_actor_bounds(False)
        wall_height = extent.z * 2.0
        wall_thickness = min(extent.x, extent.y) * 2.0
        component = actor.get_component_by_class(
            unreal.StaticMeshComponent.static_class())
        if component:
            wall_material = component.get_material(0)
        report["press_wall"] = {"height": round(wall_height),
                                "thickness": round(wall_thickness)}

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")


def wall_segment(name, cx, cy, sx, sy):
    actor = ACTOR_SUB.spawn_actor_from_object(
        CUBE, unreal.Vector(cx, cy, wall_height / 2.0),
        unreal.Rotator(0.0, 0.0, 0.0))
    if actor is None:
        return
    actor.set_actor_scale3d(unreal.Vector(
        sx / 100.0, sy / 100.0, wall_height / 100.0))
    component = actor.get_component_by_class(
        unreal.StaticMeshComponent.static_class())
    if component and wall_material:
        component.set_material(0, wall_material)
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label(name)
    report["walls"] += 1


def run_with_openings(bay, edge, fixed, lo, hi, along_x):
    """One wall edge split around its openings."""
    cuts = sorted((c - h, c + h) for e, c, h in OPENINGS.get(bay, [])
                  if e == edge)
    spans = []
    cursor = lo
    for start, end in cuts:
        if start > cursor:
            spans.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < hi:
        spans.append((cursor, hi))
    for index, (a, b) in enumerate(spans):
        mid = (a + b) / 2.0
        size = b - a
        if along_x:
            wall_segment("Site_Wall_{}_{}_{:d}".format(bay, edge, index),
                         mid, fixed, size, wall_thickness)
        else:
            wall_segment("Site_Wall_{}_{}_{:d}".format(bay, edge, index),
                         fixed, mid, wall_thickness, size)


for bay, (x0, x1, y0, y1) in BAYS.items():
    run_with_openings(bay, "north", y1, x0, x1, True)
    run_with_openings(bay, "south", y0, x0, x1, True)
    run_with_openings(bay, "west", x0, y0, y1, False)
    run_with_openings(bay, "east", x1, y0, y1, False)

LEVEL_SUB.save_current_level()
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_SITE06 {}".format(json.dumps(report)))
