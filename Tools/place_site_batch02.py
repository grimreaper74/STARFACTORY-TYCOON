"""Site batch 02: roads and yard slabs per SITE_PLAN_2026-08-19.

Ring road, central spine road, the two north links, and the four working
yards (coil intake, dispatch compound, chemical dock, container yard),
tiled from the largest vendor concrete floor mesh at native size so the
texture never stretches. Idempotent via LB.Site02. Run with
-ExecutePythonScript.
"""
import io
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_site02.json"
TAG = "LB.Site02"

# (label, centre_x, centre_y, size_x, size_y) in cm.
ROADS = [
    ("RoadNorth", 0, 17250, 70000, 900),
    ("RoadSouth", 0, -16750, 70000, 900),
    ("RoadWest", -34250, 500, 900, 34400),
    ("RoadEast", 34250, 500, 900, 34400),
    ("RoadSpine", 0, -500, 63000, 900),
    ("RoadLinkEast", 24800, 8500, 900, 16600),
    ("RoadLinkWest", -26000, 8000, 900, 17600),
]
YARDS = [
    ("YardCoil", -32200, 8000, 4800, 12000),
    ("YardDispatch", 16500, 16600, 20000, 3600),
    ("YardChemical", 15000, -15200, 8000, 2600),
    ("YardContainer", -12000, -15400, 10000, 2800),
]

report = {"floor_mesh": None, "placed": 0, "cleared": 0, "family": {}}

best = (None, None, 0.0, 0.0, 0.0)
for asset in unreal.EditorAssetLibrary.list_assets("/Game/Meshes",
                                                   recursive=True):
    name = asset.split(".")[-1] if "." in asset else asset.rsplit("/", 1)[-1]
    lower = name.lower()
    if not ("floor" in lower or "concrete" in lower) or "drain" in lower:
        continue
    loaded = unreal.load_asset(asset.split(".")[0])
    if not isinstance(loaded, unreal.StaticMesh):
        continue
    box = loaded.get_bounding_box()
    sx = box.max.x - box.min.x
    sy = box.max.y - box.min.y
    sz = box.max.z - box.min.z
    # A slab, not a wall: wide, flat, thin.
    if sz > 60.0 or sx < 150.0 or sy < 150.0:
        continue
    report["family"][name] = [round(sx), round(sy), round(sz)]
    if sx * sy > best[2] * best[3]:
        best = (loaded, name, sx, sy, sz)
floor_mesh, floor_name, tile_x, tile_y, tile_z = best
report["floor_mesh"] = floor_name
if floor_mesh is None:
    with io.open(OUT, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(report))
    raise RuntimeError("no suitable vendor floor slab found")

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target map")
w = unreal.EditorLevelLibrary.get_editor_world()
if w is None or TARGET.rsplit("/", 1)[-1] != w.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")
for a in ACTOR_SUB.get_all_level_actors():
    if a and unreal.Name(TAG) in a.tags:
        ACTOR_SUB.destroy_actor(a)
        report["cleared"] += 1

count = 0


def tile_rect(label, cx, cy, sx, sy):
    """Tile the slab over the rect, scaling each tile to fit its cell."""
    global count
    import math
    nx = max(1, int(math.ceil(sx / tile_x)))
    ny = max(1, int(math.ceil(sy / tile_y)))
    cell_x = sx / nx
    cell_y = sy / ny
    for ix in range(nx):
        for iy in range(ny):
            x = cx - sx / 2 + cell_x * (ix + 0.5)
            y = cy - sy / 2 + cell_y * (iy + 0.5)
            actor = ACTOR_SUB.spawn_actor_from_object(
                floor_mesh, unreal.Vector(x, y, 2.0),
                unreal.Rotator(0.0, 0.0, 0.0))
            if actor is None:
                continue
            actor.set_actor_scale3d(unreal.Vector(
                cell_x / tile_x, cell_y / tile_y, 1.0))
            actor.tags = [unreal.Name(TAG),
                          unreal.Name("LB.Environment.VisualOnly"),
                          unreal.Name("LB.NotProcessWIP")]
            actor.set_actor_label("Site_{}_{:d}".format(label, count))
            count += 1


for label, cx, cy, sx, sy in ROADS + YARDS:
    tile_rect(label, cx, cy, sx, sy)
report["placed"] = count

LEVEL_SUB.save_current_level()
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_SITE02 {}".format(json.dumps(
    {"floor": floor_name, "placed": count})))
