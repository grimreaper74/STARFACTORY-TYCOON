"""Replace the remaining abstract material bridges with existing press assets.

Uses a single real roller bed for coil-to-blank handoff, a real exit conveyor,
and short reused transfer-rail spans between the actual Meshy presses.  It is a
candidate-only presentation pass; no protected map or source mesh is edited.
"""

import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_materialflow_reuse_v001.json"
TAG = unreal.Name("LB.PressShop.2126.MaterialFlowReuse.v001")
HIDDEN_TAG = unreal.Name("LB.PressShop.2126.AbstractBridge.Hidden")

ROLLER = "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/Cairnwell_RollerConveyor_Movable_v740/StaticMeshes/SM_CA_ROLLER_CONVEYO__TEXTURED_STATIC_v740"
EXIT_FRAME = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorFrame_v001"
EXIT_BELT = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorBelt_v001"
TRANSFER_RAIL = "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v003/SM_CA_MW_PT_TransferRail_v003"


def fail(message):
    raise RuntimeError("PRESSSHOP_2126_MATERIALFLOW_REUSE_FAIL: " + message)


def ground(mesh):
    return -mesh.get_bounding_box().min.z


def spawn(label, mesh, location, rotation, scale, role):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation))
    if actor is None:
        fail("could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, unreal.Name("LB.Asset.Reused.MaterialFlow"), unreal.Name(role)]
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
    fail("material-flow reuse tag already exists; refusing duplicate pass")

assets = {"roller": unreal.load_asset(ROLLER), "frame": unreal.load_asset(EXIT_FRAME), "belt": unreal.load_asset(EXIT_BELT), "rail": unreal.load_asset(TRANSFER_RAIL)}
if not all(isinstance(asset, unreal.StaticMesh) for asset in assets.values()):
    fail("one or more approved reusable material-flow meshes are unavailable")
if any(int(asset.get_num_triangles(0)) > 50000 for asset in assets.values()):
    fail("reuse asset exceeds the candidate 50k-triangle guard")

# The first build's plain stock bridge is preserved but no longer visible.
hidden = []
for actor in actors:
    if actor.get_actor_label() == "S01 | flat stock bridge":
        actor.set_actor_hidden_in_game(True)
        actor.tags = list(actor.tags) + [HIDDEN_TAG]
        for component in actor.get_components_by_class(unreal.PrimitiveComponent):
            component.set_visibility(False, True)
        hidden.append(actor.get_actor_label())
if hidden != ["S01 | flat stock bridge"]:
    fail("expected one first-pass stock bridge to supersede")

placed = []

# One real roller segment makes the laser-to-draw handoff legible without
# adding a repetitive roller forest. Its long axis is the production X flow.
roller = spawn("FLOW | S01-to-S02 real roller handoff", assets["roller"],
               (-6550.0, 0.0, ground(assets["roller"])),
               (0.0, 0.0, 0.0), (1.55, 1.0, 1.0), "LB.PressShop.Handoff")
placed.append(roller.get_actor_label())

# One actual low-poly exit conveyor carries the panel from vision/outfeed to
# the open dispatch space. Frame and belt stay separate per their source
# authoring, so later motion/material work has an honest seam.
frame = spawn("FLOW | S06 real exit conveyor frame", assets["frame"],
              (5050.0, 0.0, ground(assets["frame"])),
              (0.0, 90.0, 0.0), (1.0, 3.0, 1.0), "LB.PressShop.Outfeed")
belt = spawn("FLOW | S06 real exit conveyor belt", assets["belt"],
             (5050.0, 0.0, ground(assets["belt"]) + 100.0),
             (0.0, 90.0, 0.0), (1.0, 3.0, 1.0), "LB.PressShop.Outfeed")
placed.extend((frame.get_actor_label(), belt.get_actor_label()))

# Paired, short overhead rail spans replace the hidden primitive transfer bars
# over exactly the four gaps between the distinct Meshy press stations.
segments = ((-3150.0, 0.145), (-1150.0, 0.164), (700.0, 0.156), (2550.0, 0.150))
for segment_index, (x, y_scale) in enumerate(segments, start=1):
    for side in (-1, 1):
        actor = spawn("FLOW | reused transfer rail %d %s" % (segment_index, "L" if side < 0 else "R"),
                      assets["rail"], (x, side * 260.0, 950.0),
                      (0.0, 90.0, 0.0), (1.0, y_scale, 1.0), "LB.PressShop.Transfer")
        placed.append(actor.get_actor_label())

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save material-flow reuse pass")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__REAL_REUSED_MATERIAL_FLOW_REPLACES_ABSTRACT_BRIDGE_IN_FRESH_2126_CANDIDATE",
    "map": MAP,
    "candidate_only": True,
    "hidden_not_deleted": hidden,
    "placed": placed,
    "assets": {key: {"path": asset.get_path_name(), "triangles_lod0": int(asset.get_num_triangles(0))} for key, asset in assets.items()},
    "no_new_meshy_generation": True,
    "no_roof_or_wall_mesh_created": True,
    "honest_status": "static visual material-flow only; no conveyor motion, collision or gameplay claim",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_MATERIALFLOW_REUSE_PASS pieces=%d" % len(placed))
