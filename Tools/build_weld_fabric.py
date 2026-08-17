"""Place the weld shop's building fabric from assets the project already owns.

The weld bay reads sparse because of its layout, not its station count: two 32 m
rows plus a 24 m aisle consume 88 of the bay's 100 m, so there is no receiving lane,
no service corridor, no subassembly space - and no mezzanine anywhere in the whole
project. This wires the idle vendor kit into those strips.

Every pitch below is MEASURED (Tools/Diagnostics/probe_weld_kit.py), not assumed -
the plan's own figures were specified from process reasoning and two were wrong:
  * SM_HeavyArch01 is 6.0 m tall against 22 m walls, so it is a PER-CELL gantry, not
    the shop-scale hall gantry the plan described. Shop steelwork is an authoring item.
  * SM_LargeWindowFramed_02 does not exist; only the base version does.
Two vendor meshes extend below their origin and sink into the slab at Z=0, so they
are offset by -minZ: SM_FloorStairs01 (-176.7) and SM_ElectricalPanel_01 (-79.4).
The SM_LB_* family uses floor pivots; the vendor pack does not.

Idempotent: clears everything tagged LB.Weld.Fabric before placing.

Run headless with -ExecutePythonScript (a commandlet has no editor world, so spawns
silently no-op and the script still exits 0):
  UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=Tools/build_weld_fabric.py
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TAG = "LB.Weld.Fabric"
OUT = os.environ.get("LB_WELD_FABRIC_OUT", "C:/Temp/lb_weld_fabric.json")

# Body bay from MakeMoorcrossWorksShellLayout: centre (-11000,-8500), 18000 x 10000.
BAY_MIN_X, BAY_MAX_X = -20000.0, -2000.0
BAY_MIN_Y, BAY_MAX_Y = -13500.0, -3500.0

# The re-layout's two runs and the strips they free.
RUN_A_Y = -7000.0
RUN_B_Y = -11200.0
AISLE_Y = (RUN_A_Y + RUN_B_Y) * 0.5      # mezzanine over the central service aisle
RECEIVING_Y = -4400.0                      # north marshalling lane
SWITCHROOM_Y = -13150.0                    # south service corridor

M = {
    "deck": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_IndustrialPlatform01",
    "rail": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_PlatformRailing_01",
    "pillar": "/Game/Meshes/SM_PlatformPillar_01",
    "stairs": "/Game/Meshes/SM_FloorStairs01",
    "arch": "/Game/Meshes/SM_HeavyArch01",
    "window": "/Game/Meshes/SM_LargeWindowFramed",
    "rack_bottom": "/Game/Meshes/SM_StorageShelvesBottom01",
    "rack_middle": "/Game/Meshes/SM_StorageShelvesMiddle01",
    "rack_top": "/Game/Meshes/SM_StorageShelvesTop01",
    "switchboard": "/Game/Meshes/SM_ElectricalSupply_Switchboard01",
}

# Measured sizes, cm.
DECK_X, DECK_Y, DECK_Z = 700.0, 300.0, 71.5
RAIL_LEN_Y = 352.1            # runs along Y, so needs a 90 degree yaw
PILLAR_Z = 282.0              # deck sits on top: a 2.8 m walkway beneath
STAIRS_MIN_Z = -176.7
WINDOW_X = 830.6
RACK_X = 300.0
RACK_H = (200.0, 209.7, 229.7)
SWITCH_X = 140.0

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT = {"placed": {}, "cleared": 0}

if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load {}".format(TARGET))
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or TARGET.rsplit("/", 1)[-1] != world.get_name():
    raise RuntimeError("wrong world open; use -ExecutePythonScript")

for actor in ACTOR_SUB.get_all_level_actors():
    if actor and unreal.Name(TAG) in actor.tags:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1

LOADED = {}


def mesh(key):
    if key not in LOADED:
        asset = unreal.load_asset(M[key])
        if asset is None:
            raise RuntimeError("missing {}: {}".format(key, M[key]))
        LOADED[key] = asset
    return LOADED[key]


def place(kind, key, x, y, z, yaw=0.0, label=None):
    actor = ACTOR_SUB.spawn_actor_from_object(
        mesh(key), unreal.Vector(x, y, z), unreal.Rotator(0.0, yaw, 0.0))
    if actor is None:
        return None
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    if label:
        actor.set_actor_label(label)
    REPORT["placed"][kind] = REPORT["placed"].get(kind, 0) + 1
    return actor


# ---- mezzanine over the central service aisle -----------------------------
# The first mezzanine anywhere in the project. Two 3 m deck lanes give a 6 m
# walkway; pillars at 282 leave the aisle passable beneath.
DECK_FROM_X, DECK_TO_X = -17800.0, -3800.0
deck_count = int((DECK_TO_X - DECK_FROM_X) // DECK_X)
lane_offsets = (-DECK_Y * 0.5, DECK_Y * 0.5)
for index in range(deck_count):
    x = DECK_FROM_X + DECK_X * (index + 0.5)
    for lane in lane_offsets:
        place("mezz_deck", "deck", x, AISLE_Y + lane, PILLAR_Z,
              label="Weld_Mezz_Deck")
    # Pillars just outside each deck edge.
    for edge in (-DECK_Y, DECK_Y):
        place("mezz_pillar", "pillar", x, AISLE_Y + edge, 0.0,
              label="Weld_Mezz_Pillar")

rail_count = int((DECK_TO_X - DECK_FROM_X) // RAIL_LEN_Y)
for index in range(rail_count):
    x = DECK_FROM_X + RAIL_LEN_Y * (index + 0.5)
    for edge in (-DECK_Y, DECK_Y):
        place("mezz_rail", "rail", x, AISLE_Y + edge, PILLAR_Z + DECK_Z,
              yaw=90.0, label="Weld_Mezz_Rail")

# Stairs at both ends. minZ is -176.7, so lift by that or they sink.
for x, yaw in ((DECK_FROM_X - 200.0, 0.0), (DECK_TO_X + 200.0, 180.0)):
    # The mesh hangs entirely below its origin (bounds -176.7..0), so placing at
    # -minZ puts its foot on the slab. It climbs 176.7 of the 282 to the deck; the
    # remainder needs a second flight or a landing, noted rather than fudged by
    # stretching the mesh.
    place("mezz_stairs", "stairs", x, AISLE_Y, -STAIRS_MIN_Z,
          yaw=yaw, label="Weld_Mezz_Stairs")

# ---- per-cell gantries over the 18 re-laid station positions -------------
# Yawed 90 so the 400 cm span crosses the line rather than running along it.
RUN_A_X = [-3200.0 - 1800.0 * n for n in range(9)]
RUN_B_X = [-17600.0 + 1800.0 * n for n in range(9)]
for x in RUN_A_X:
    place("cell_gantry", "arch", x, RUN_A_Y, 0.0, yaw=90.0,
          label="Weld_CellGantry_A")
for x in RUN_B_X:
    place("cell_gantry", "arch", x, RUN_B_Y, 0.0, yaw=90.0,
          label="Weld_CellGantry_B")

# ---- clerestory glazing on the north and south walls ---------------------
# Real framed glazing instead of the tinted opaque cube band, set just below the
# 2200 cm eaves.
GLAZE_Z = 1330.0
glaze_count = int((BAY_MAX_X - 1000.0 - (BAY_MIN_X + 1000.0)) // WINDOW_X)
for index in range(glaze_count):
    x = BAY_MIN_X + 1000.0 + WINDOW_X * (index + 0.5)
    place("clerestory", "window", x, BAY_MAX_Y, GLAZE_Z, yaw=0.0,
          label="Weld_Clerestory_N")
    place("clerestory", "window", x, BAY_MIN_Y, GLAZE_Z, yaw=180.0,
          label="Weld_Clerestory_S")

# ---- marshalling racks in the north receiving lane -----------------------
# Bottom is the only tier wired today; stack all three to 640 cm per bay.
rack_bays = 14
for bay in range(rack_bays):
    x = BAY_MIN_X + 1400.0 + RACK_X * bay * 1.15
    z = 0.0
    for tier, key in enumerate(("rack_bottom", "rack_middle", "rack_top")):
        place("rack", key, x, RECEIVING_Y, z, label="Weld_MarshallingRack")
        z += RACK_H[tier]

# ---- switchroom line on the south service corridor ----------------------
switch_count = 24
for index in range(switch_count):
    x = BAY_MIN_X + 1200.0 + SWITCH_X * index * 2.6
    if x > BAY_MAX_X - 800.0:
        break
    place("switchboard", "switchboard", x, SWITCHROOM_Y, 0.0,
          label="Weld_Switchboard")

LEVEL_SUB.save_current_level()

REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_WELD_FABRIC placed {} (cleared {}) {} -> {}".format(
    REPORT["total"], REPORT["cleared"], json.dumps(REPORT["placed"]), OUT))
