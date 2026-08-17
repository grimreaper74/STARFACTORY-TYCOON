"""Roof any shop with Codex's authored 40 m wide-span truss.

Generalised from the weld pass, which is verified on screen. The grid is copied from
press's own 12 placements rather than invented: 4000 cm pitch in X, rows every 1500 cm
in Y, Z 1740, zero rotation, and scale 100 because the mesh is authored small - a
native-scale placement is invisible.

The asset path is read from the reference dump, not composed: an invented
CleanRebuild/PressTrains path failed to load on the first weld attempt.

Roof structure sits above the 900 cm roof-hide threshold, so it is deliberately absent
from overhead captures. Verify at a low pitch, e.g. <Shop>@0.14~8.

  LB_SHOP=Paint  UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=Tools/build_shop_trusses.py
"""
import io
import json
import os

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
TRUSS = ("/Game/LineBoss/Candidates/PressShop/Structure/WideSpanTruss_v373/"
         "SM_CA_MW_PressShop_WideSpanTruss_40m_TBC_v372")
SCALE = 100.0
Z = 1740.0
X_PITCH = 4000.0
Y_PITCH = 1500.0
MARGIN = 750.0

# Bays from MakeMoorcrossWorksShellLayout: centre then size.
BAYS = {
    "Press": ((-14500.0, 8000.0), (32000.0, 13000.0)),
    "Body": ((-11000.0, -8500.0), (18000.0, 10000.0)),
    "Paint": ((10000.0, -8500.0), (22000.0, 10000.0)),
    "Assembly": ((16500.0, 8500.0), (28000.0, 12000.0)),
}

SHOP = os.environ.get("LB_SHOP", "Paint")
if SHOP not in BAYS:
    raise RuntimeError("LB_SHOP must be one of {}".format(sorted(BAYS)))
TAG = "LB.{}.Truss".format(SHOP)
OUT = os.environ.get("LB_TRUSS_OUT", "C:/Temp/lb_truss.json")

(cx, cy), (sx, sy) = BAYS[SHOP]
min_x, max_x = cx - sx * 0.5, cx + sx * 0.5
min_y, max_y = cy - sy * 0.5, cy + sy * 0.5

LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT = {"shop": SHOP, "placed": 0, "cleared": 0}

if not LEVEL_SUB.load_level(TARGET):
    raise RuntimeError("could not load target")
w = unreal.EditorLevelLibrary.get_editor_world()
if w is None or TARGET.rsplit("/", 1)[-1] != w.get_name():
    raise RuntimeError("wrong world; use -ExecutePythonScript")

for a in ACTOR_SUB.get_all_level_actors():
    if a and unreal.Name(TAG) in a.tags:
        ACTOR_SUB.destroy_actor(a)
        REPORT["cleared"] += 1

asset = unreal.load_asset(TRUSS)
if asset is None:
    raise RuntimeError("truss not found at {}".format(TRUSS))

columns = int((max_x - min_x - MARGIN * 2) // X_PITCH)
rows = int((max_y - min_y - MARGIN * 2) // Y_PITCH)
for c in range(columns):
    x = min_x + MARGIN + X_PITCH * (c + 0.5)
    for r in range(rows):
        y = min_y + MARGIN + Y_PITCH * (r + 0.5)
        actor = ACTOR_SUB.spawn_actor_from_object(
            asset, unreal.Vector(x, y, Z), unreal.Rotator(0.0, 0.0, 0.0))
        if actor is None:
            continue
        actor.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
        actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                      unreal.Name("LB.NotProcessWIP")]
        actor.set_actor_label("{}_Truss_{:.0f}_{:.0f}".format(SHOP, x, y))
        REPORT["placed"] += 1

LEVEL_SUB.save_current_level()
REPORT["grid"] = [columns, rows]
with io.open(OUT, "w", encoding="utf-8") as h:
    h.write(json.dumps(REPORT, indent=1))
unreal.log("LINE_BOSS_SHOP_TRUSS shop={} placed={} grid={}x{} cleared={}".format(
    SHOP, REPORT["placed"], columns, rows, REPORT["cleared"]))
