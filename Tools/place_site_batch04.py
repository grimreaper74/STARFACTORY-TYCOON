"""Site batch 04: the skyline beyond the fence - background towers,
box buildings and the hangar to the NW and NE, so the works sits in a
wider industrial landscape instead of a void. Idempotent via LB.Site04.
Run with -ExecutePythonScript.
"""
import io
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_site04.json"
TAG = "LB.Site04"

lib = unreal.EditorAssetLibrary
report = {"placed": {}, "cleared": 0, "found": {}}


def find_asset(fragment):
    for asset in lib.list_assets("/Game/Meshes", recursive=True):
        name = asset.rsplit("/", 1)[-1].split(".")[0]
        if fragment.lower() in name.lower():
            loaded = unreal.load_asset(asset.split(".")[0])
            if isinstance(loaded, unreal.StaticMesh):
                return loaded, name
    return None, None


TOWER1, t1 = find_asset("Background1_Tower")
ANTENNA, t2 = find_asset("AntennaTower")
HANGAR, t3 = find_asset("Background2_Hangar")
TOWER2, t4 = find_asset("Background2_Tower")
BOXB, t5 = find_asset("BoxBuilding")
report["found"] = {"tower1": t1, "antenna": t2, "hangar": t3, "tower2": t4,
                   "box": t5}

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


def place(mesh, x, y, yaw, label):
    if mesh is None:
        return
    actor = ACTOR_SUB.spawn_actor_from_object(
        mesh, unreal.Vector(x, y, 0.0), unreal.Rotator(0.0, yaw, 0.0))
    if actor is None:
        return
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label(label)
    key = label.rsplit("_", 1)[0]
    report["placed"][key] = report["placed"].get(key, 0) + 1


# NW industrial cluster beyond the fence.
place(HANGAR, -46000.0, 26000.0, 20.0, "Site_Skyline_Hangar_A")
place(TOWER1, -38000.0, 28000.0, 0.0, "Site_Skyline_Tower_A")
place(TOWER1, -34000.0, 30000.0, 45.0, "Site_Skyline_Tower_B")
place(ANTENNA, -42000.0, 24500.0, 0.0, "Site_Skyline_Antenna_A")
place(BOXB, -28000.0, 27500.0, 10.0, "Site_Skyline_Box_A")
# NE cluster past the main gate.
place(TOWER2, 44000.0, 24000.0, -15.0, "Site_Skyline_Tower_C")
place(BOXB, 47000.0, 19000.0, 80.0, "Site_Skyline_Box_B")
place(TOWER1, 50000.0, 26000.0, 0.0, "Site_Skyline_Tower_D")
# Southern horizon.
place(BOXB, -6000.0, -27000.0, 0.0, "Site_Skyline_Box_C")
place(TOWER2, 14000.0, -28000.0, 30.0, "Site_Skyline_Tower_E")

LEVEL_SUB.save_current_level()
report["total"] = sum(report["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_SITE04 {}".format(json.dumps(report["placed"])))
