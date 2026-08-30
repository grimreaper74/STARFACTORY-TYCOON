"""Complete the readable control and outbound endpoints of the 2126 candidate.

Only proven lightweight project meshes are placed: one HMI at each press, then
one vision gate, an inspected stillage and an outbound dunnage beyond S06.
This creates a legible end-to-end line without using small decorative clutter.
"""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_controls_outbound_v001.json"
TAG = unreal.Name("LB.PressShop.2126.ControlsOutbound.v001")
HMI = "/Game/LineBoss/Candidates/PressShop/OperatorHMIStand_v001/SM_LB_OperatorHMIStand_v001"
VISION = "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001"
STILLAGE = "/Game/LineBoss/Candidates/PressTrains/Shared/ExteriorDetail_v002/SM_CA_MW_PT_S07InspectionStillageDress_v002"
DUNNAGE = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07OutboundDunnage_v001"


def fail(message):
    raise RuntimeError("PRESSSHOP_2126_CONTROLS_OUTBOUND_FAIL: " + message)


def ground(mesh):
    return -mesh.get_bounding_box().min.z


def spawn(label, mesh, location, rotation, scale, role):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation))
    if actor is None:
        fail("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, unreal.Name("LB.Asset.Reused.ControlsOutbound"), unreal.Name(role)]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_world_scale3d(unreal.Vector(*scale))
    component.set_mobility(unreal.ComponentMobility.STATIC)
    return actor


if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("fresh candidate map missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load fresh candidate map")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    fail("controls/outbound tag already exists; refusing duplicate pass")

assets = {"hmi": unreal.load_asset(HMI), "vision": unreal.load_asset(VISION), "stillage": unreal.load_asset(STILLAGE), "dunnage": unreal.load_asset(DUNNAGE)}
if not all(isinstance(mesh, unreal.StaticMesh) for mesh in assets.values()):
    fail("approved controls/outbound reuse asset missing")
if any(int(mesh.get_num_triangles(0)) > 50000 for mesh in assets.values()):
    fail("reuse asset exceeds candidate 50k triangle guard")

placed = []
for station, x in (("S02 Draw", -4200.0), ("S03 Trim", -2100.0), ("S04 Pierce", -200.0), ("S05 Flange", 1600.0), ("S06 Vision", 3500.0)):
    actor = spawn("CONTROL | %s operator HMI" % station, assets["hmi"],
                  (x, -3450.0, ground(assets["hmi"])), (0.0, -90.0, 0.0), (1.0, 1.0, 1.0), "LB.PressShop.OperatorControl")
    placed.append(actor.get_actor_label())

actor = spawn("OUTBOUND | real vision inspection gate", assets["vision"],
              (8300.0, 0.0, ground(assets["vision"])), (0.0, 90.0, 0.0), (1.0, 1.0, 1.0), "LB.PressShop.Inspection")
placed.append(actor.get_actor_label())
actor = spawn("OUTBOUND | inspected panel stillage", assets["stillage"],
              (11750.0, 0.0, ground(assets["stillage"])), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), "LB.PressShop.InspectedBuffer")
placed.append(actor.get_actor_label())
actor = spawn("OUTBOUND | real dunnage dispatch", assets["dunnage"],
              (15800.0, 0.0, ground(assets["dunnage"])), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), "LB.PressShop.Dispatch")
placed.append(actor.get_actor_label())

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save controls/outbound pass")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__REUSED_CONTROLS_VISION_AND_OUTBOUND_COMPLETE_FRESH_2126_CANDIDATE",
    "map": MAP,
    "candidate_only": True,
    "placed": placed,
    "assets": {key: {"path": mesh.get_path_name(), "triangles_lod0": int(mesh.get_num_triangles(0))} for key, mesh in assets.items()},
    "no_new_meshy_generation": True,
    "no_roof_or_wall_mesh_created": True,
    "honest_status": "static presentation / interaction cues only; no runtime control, inventory or motion claim",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_CONTROLS_OUTBOUND_PASS pieces=%d" % len(placed))
