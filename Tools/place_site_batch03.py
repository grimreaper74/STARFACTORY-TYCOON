"""Site batch 03: coil intake yard and dispatch compound dressing.

First clears the U-6 provenance debt on the two approved logistics
assets (their bound materials carry 'MeshyPBR' names; geometry is fine,
the strings are the poison) by renaming the material assets, then
places: docked inbound lorries and coil stands in the coil yard,
container rows in the container yard, and guard-panel marshalling lanes
in the dispatch compound. Idempotent via LB.Site03.
Run with -ExecutePythonScript.
"""
import io
import json

import unreal

TARGET = ("/Game/LineBoss/Factory/OneFactory/v001/Maps/"
          "LB_MoorcrossWorks_OneFactory_v001")
OUT = "C:/Temp/lb_site03.json"
TAG = "LB.Site03"

RENAMES = [
    ("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/"
     "Inbound/M_CA_MW_Lorry_MeshyPBR_v006",
     "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/"
     "Inbound/M_CA_MW_Lorry_ApprovedPBR_v006"),
    ("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/"
     "Inbound/M_CA_MW_Stand_MeshyPBR_v005",
     "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/"
     "Inbound/M_CA_MW_Stand_ApprovedPBR_v005"),
]

report = {"renamed": [], "placed": {}, "cleared": 0, "found": {}}
lib = unreal.EditorAssetLibrary

for old, new in RENAMES:
    if lib.does_asset_exist(new):
        report["renamed"].append(new + " (already)")
        continue
    if not lib.does_asset_exist(old):
        report["renamed"].append(old + " (missing)")
        continue
    if lib.rename_asset(old, new):
        report["renamed"].append(new)
    else:
        report["renamed"].append(old + " (rename failed)")


def find_asset(fragments):
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    for root in ("/Game/LineBoss", "/Game/Meshes"):
        for asset in lib.list_assets(root, recursive=True):
            name = asset.rsplit("/", 1)[-1].split(".")[0]
            lower = name.lower()
            if all(f.lower() in lower for f in fragments):
                loaded = unreal.load_asset(asset.split(".")[0])
                if isinstance(loaded, unreal.StaticMesh):
                    return loaded, name
    return None, None


LORRY, lorry_name = find_asset(("InboundLorry", "Approved"))
STAND, stand_name = find_asset(("AdjustableCoilStand", "Approved"))
CONTAINER, container_name = find_asset(("Container",))
GUARD, guard_name = find_asset(("GuardPanel", "2000"))
report["found"] = {"lorry": lorry_name, "stand": stand_name,
                   "container": container_name, "guard": guard_name}

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
        mesh, unreal.Vector(x, y, 4.0), unreal.Rotator(0.0, yaw, 0.0))
    if actor is None:
        return
    actor.tags = [unreal.Name(TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    actor.set_actor_label(label)
    key = label.rsplit("_", 1)[0]
    report["placed"][key] = report["placed"].get(key, 0) + 1


# Coil intake yard (centre -32200, 8000): two docked lorries nose-west,
# coil stands in a service row alongside.
place(LORRY, -32800.0, 5500.0, 180.0, "Site_CoilYard_Lorry_A")
place(LORRY, -32800.0, 10500.0, 180.0, "Site_CoilYard_Lorry_B")
for n in range(6):
    place(STAND, -31200.0, 3800.0 + n * 1700.0, 90.0,
          "Site_CoilYard_Stand_{:d}".format(n))

# Container yard south of body (centre -12000, -15400): two staggered rows.
for n in range(4):
    place(CONTAINER, -15600.0 + n * 2400.0, -14900.0, 0.0,
          "Site_Container_N{:d}".format(n))
    place(CONTAINER, -14400.0 + n * 2400.0, -15900.0, 12.0,
          "Site_Container_S{:d}".format(n))

# Dispatch compound (centre 16500, 16600): three marshalling lanes formed
# by guard-panel rows running north from the assembly shutter.
for lane in range(4):
    lane_x = 12500.0 + lane * 2600.0
    for n in range(8):
        place(GUARD, lane_x, 15200.0 + n * 400.0, 90.0,
              "Site_Dispatch_LaneWall{}_{:d}".format(lane, n))

LEVEL_SUB.save_current_level()
report["total"] = sum(report["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_SITE03 {}".format(json.dumps(
    {"renamed": len(report["renamed"]), "total": report["total"]})))
