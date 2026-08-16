import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetNav_v20260809_v019"
TARGET = "/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetPaint_v20260809_v032"
OUT = ROOT / "Saved/Audits/PressShopIntegration/clean_full_floor_paint_v20260809_v032.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
PROTECTED_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

before = sha(PROTECTED)
assert before == PROTECTED_SHA
assert not unreal.EditorAssetLibrary.does_asset_exist(TARGET), f"Refusing to overwrite {TARGET}"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.new_level_from_template(TARGET, SOURCE), "Could not create child map from v019"

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assets = unreal.EditorAssetLibrary
cube = assets.load_asset("/Engine/BasicShapes/Cube.Cube")
mat_root = "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v001/Materials/"
palette = "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v026/FloorMaterials/"
grey = assets.load_asset(palette + "M_LB_PS_SealedFloorMidGrey_v026")
green = assets.load_asset(palette + "M_LB_PS_ProtectedWalkwayGreen_v026")
yellow = assets.load_asset(palette + "M_LB_PS_SafetyYellow_v026")
white = assets.load_asset(palette + "M_LB_PS_CrossingWhite_v026")
red = assets.load_asset(palette + "M_LB_PS_KeepClearRed_v026")
blue = assets.load_asset(palette + "M_LB_PS_AGVBlue_v026")
assert all((cube, grey, green, yellow, white, red, blue))

for existing in actors.get_all_level_actors():
    if isinstance(existing, unreal.StaticMeshActor) and existing.get_actor_label() == "LB_CLEAN_Floor_220m_x_120m":
        existing.static_mesh_component.set_material(0, grey)

# Remove the inherited placement-linked partial route pass. Retain the fixed shell
# perimeter/fire markings and the four robot-dock bay markings.
removed=[]
for existing in list(actors.get_all_level_actors()):
    label=existing.get_actor_label()
    if label.startswith("LB_PAINT_") and not label.startswith("LB_PAINT_Dock"):
        removed.append(label)
        actors.destroy_actor(existing)

created = []

def paint(label, loc, dims, material, category):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator())
    actor.set_actor_label(label)
    comp = actor.static_mesh_component
    comp.set_static_mesh(cube)
    comp.set_world_scale3d(unreal.Vector(dims[0] / 100.0, dims[1] / 100.0, dims[2] / 100.0))
    comp.set_material(0, material)
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    comp.set_editor_property("can_ever_affect_navigation", False)
    comp.set_cast_shadow(False)
    actor.tags = [unreal.Name("LB.CleanRebuild.v20260809.v032"), unreal.Name("LB.FloorPaint.FullShop"), unreal.Name(category)]
    created.append(actor)

# Connected protected pedestrian network. The main southern spine serves player construction,
# robot docks and every press train; the north spine serves inbound and coil handling.
walkways = [
    ("SouthSpine", (0, -5050, 3.0), (21400, 520, 2)),
    ("NorthSpine", (0, 5050, 3.0), (21400, 520, 2)),
    ("WestSpine", (-10450, 0, 3.0), (500, 9600, 2)),
    ("EastSpine", (10450, 0, 3.0), (500, 9600, 2)),
    ("InboundAisle", (-7900, 0, 3.0), (320, 8800, 2)),
    ("StorageAisleWest", (-5600, 0, 3.0), (260, 7000, 2)),
    ("StorageAisleEast", (800, 0, 3.0), (260, 7000, 2)),
]
for train, y in zip("ABCD", (-3000, -1000, 1000, 3000)):
    walkways.append((f"Train{train}Operator", (5000, y - 560, 3.0), (8500, 260, 2)))
for name, loc, dims in walkways:
    paint("LB_PAINT_FULL_Walkway_" + name, loc, dims, green, "LB.FloorPaint.Walkway")

# Yellow edges on every principal protected walkway.
for name, loc, dims in walkways:
    x, y, _ = loc
    if dims[0] >= dims[1]:
        for suffix, dy in (("N", dims[1] / 2), ("S", -dims[1] / 2)):
            paint(f"LB_PAINT_FULL_Edge_{name}_{suffix}", (x, y + dy, 4.2), (dims[0], 10, 2), yellow, "LB.FloorPaint.WalkwayEdge")
    else:
        for suffix, dx in (("E", dims[0] / 2), ("W", -dims[0] / 2)):
            paint(f"LB_PAINT_FULL_Edge_{name}_{suffix}", (x + dx, y, 4.2), (10, dims[1], 2), yellow, "LB.FloorPaint.WalkwayEdge")

# Full AGV route lanes: broad grey running surface with blue edge guidance, plus handoff bays.
agv_segments = [
    ("South", (0, -4450, 3.2), (19600, 520, 2)),
    ("North", (0, 4450, 3.2), (19600, 520, 2)),
    ("West", (-9500, 0, 3.2), (520, 8400, 2)),
    ("East", (9500, 0, 3.2), (520, 8400, 2)),
    ("StorageLoopWest", (-6200, 0, 3.2), (420, 6800, 2)),
    ("StorageLoopEast", (1400, 0, 3.2), (420, 6800, 2)),
]
for name, loc, dims in agv_segments:
    paint("LB_PAINT_FULL_AGVSurface_" + name, loc, dims, grey, "LB.FloorPaint.AGVSurface")
    x, y, _ = loc
    if dims[0] >= dims[1]:
        paint("LB_PAINT_FULL_AGVBlue_" + name + "_N", (x, y + dims[1]/2, 4.5), (dims[0], 12, 2), blue, "LB.FloorPaint.AGVRoute")
        paint("LB_PAINT_FULL_AGVBlue_" + name + "_S", (x, y - dims[1]/2, 4.5), (dims[0], 12, 2), blue, "LB.FloorPaint.AGVRoute")
    else:
        paint("LB_PAINT_FULL_AGVBlue_" + name + "_E", (x + dims[0]/2, y, 4.5), (12, dims[1], 2), blue, "LB.FloorPaint.AGVRoute")
        paint("LB_PAINT_FULL_AGVBlue_" + name + "_W", (x - dims[0]/2, y, 4.5), (12, dims[1], 2), blue, "LB.FloorPaint.AGVRoute")

# Inbound, storage, process-cell and press-train safety boundaries.
zones = [
    ("LorryUnload", (-9000, -500, 5.0), (1800, 7600), yellow),
    ("CoilStorage", (-2400, 0, 5.0), (6000, 7000), yellow),
    ("CoilPrep", (2500, 0, 5.0), (1800, 7000), yellow),
]
for train, y in zip("ABCD", (-3000, -1000, 1000, 3000)):
    zones.append((f"Train{train}", (5000, y, 5.0), (8500, 1100), yellow))
for name, loc, size, material in zones:
    x, y, z = loc; sx, sy = size
    for suffix, ploc, pdims in (
        ("N", (x, y+sy/2, z), (sx, 12, 2)), ("S", (x, y-sy/2, z), (sx, 12, 2)),
        ("E", (x+sx/2, y, z), (12, sy, 2)), ("W", (x-sx/2, y, z), (12, sy, 2))):
        paint(f"LB_PAINT_FULL_Zone_{name}_{suffix}", ploc, pdims, material, "LB.FloorPaint.SafetyBoundary")

# Zebra crossings wherever pedestrian routes meet the AGV loop.
crossings = [(-7900,-4450), (-5600,-4450), (800,-4450), (5000,-4450), (9500,-3000), (9500,-1000), (9500,1000), (9500,3000)]
for ci, (x, y) in enumerate(crossings, 1):
    horizontal = abs(y) == 4450
    for stripe in range(-3, 4):
        loc = (x + stripe*55, y, 6.0) if horizontal else (x, y + stripe*55, 6.0)
        dims = (28, 500, 2) if horizontal else (500, 28, 2)
        paint(f"LB_PAINT_FULL_Crossing_{ci:02d}_{stripe+4:02d}", loc, dims, white, "LB.FloorPaint.PedestrianCrossing")

# Red crane keep-clear boundary around inbound lift envelope.
for suffix, loc, dims in (
    ("N", (-8600, 3900, 6.2), (3200, 14, 2)), ("S", (-8600, -3900, 6.2), (3200, 14, 2)),
    ("E", (-7000, 0, 6.2), (14, 7800, 2)), ("W", (-10200, 0, 6.2), (14, 7800, 2))):
    paint("LB_PAINT_FULL_CraneExclusion_" + suffix, loc, dims, red, "LB.FloorPaint.CraneExclusion")

assert levels.save_current_level(), "Could not save full floor paint map"
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetPaint_v20260809_v032.umap"
after = sha(PROTECTED)
assert after == before
counts = {}
for actor in created:
    for tag in actor.tags:
        key = str(tag)
        if key.startswith("LB.FloorPaint.") and key not in ("LB.FloorPaint.FullShop",):
            counts[key] = counts.get(key, 0) + 1
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS_BUILD__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source": SOURCE, "map": TARGET, "map_sha256": sha(map_file),
    "paint_actor_count": len(created), "paint_counts": counts,
    "removed_inherited_partial_paint_count": len(removed),
    "coverage": ["main slab finish retained", "connected perimeter walkways", "inbound unloading", "coil storage", "coil preparation", "press trains A-D", "AGV loop and handoffs", "robot dock access", "pedestrian crossings", "crane exclusion"],
    "meshy_credits_used": 0,
    "protected_v438_before": before, "protected_v438_after": after
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_FULL_FLOOR_PAINT_V032_PASS")
