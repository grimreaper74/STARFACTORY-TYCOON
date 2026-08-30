"""Add sparse, reusable robot cues to the fresh 2126 press candidate.

The visual authority calls for a robot-rich but uncluttered factory.  This pass
uses a light existing robot arm (not a high-poly Coil AGV) at only the process
points where a player can read a clear automated task: laser tending, press
sample handling and vision/outfeed stacking.
"""

import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
MATERIAL_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Materials"
ROBOT = "/Game/Meshes/Robot/SM_RoboArm04"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_robotic_cues_v001.json"
TAG = unreal.Name("LB.PressShop.2126.RoboticCues.v001")

ROBOTS = (
    ("S01 | laser tend robot", (-7900.0, 3300.0, 0.0), 205.0, 1.10, "laser tending"),
    ("S02 | draw quality robot", (-4200.0, 3200.0, 0.0), 180.0, 1.00, "draw sample handling"),
    ("S04 | pierce handling robot", (-200.0, 3200.0, 0.0), 180.0, 1.00, "pierce panel handling"),
    ("S06 | vision stack robot", (4500.0, -3100.0, 0.0), -20.0, 1.20, "vision-gated outbound stacking"),
)


def fail(message):
    raise RuntimeError("PRESSSHOP_2126_ROBOTIC_CUES_FAIL: " + message)


if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("fresh candidate map missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load fresh candidate map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    fail("robotic-cue tag already exists; refusing duplicate pass")

robot_mesh = unreal.load_asset(ROBOT)
green = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_CairnwellGreen")
yellow = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_SafetyYellow")
if not isinstance(robot_mesh, unreal.StaticMesh):
    fail("lightweight existing robot arm unavailable")
if not isinstance(green, unreal.Material) or not isinstance(yellow, unreal.Material):
    fail("candidate B_stylized materials unavailable")
if int(robot_mesh.get_num_triangles(0)) > 20000:
    fail("robot asset exceeds the 20k screenshot-candidate guard")

placed = []
for index, (label, location, yaw, scale, role) in enumerate(ROBOTS):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    if actor is None:
        fail("could not place " + label)
    actor.set_actor_label("ROBOT | " + label)
    actor.tags = [TAG, unreal.Name("LB.Asset.Reused.Robot"), unreal.Name("LB.PressShop.Automation")]
    component = actor.static_mesh_component
    component.set_static_mesh(robot_mesh)
    component.set_world_scale3d(unreal.Vector(scale, scale, scale))
    component.set_material(0, green if index < 3 else yellow)
    component.set_mobility(unreal.ComponentMobility.STATIC)
    placed.append({
        "label": actor.get_actor_label(),
        "role": role,
        "location_cm": list(location),
        "yaw": yaw,
        "scale": scale,
        "triangles_lod0": int(robot_mesh.get_num_triangles(0)),
    })

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save robot-cue pass")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__SPARSE_REUSED_ROBOTIC_CUES_ADDED_TO_FRESH_2126_CANDIDATE",
    "map": MAP,
    "candidate_only": True,
    "reused_asset": ROBOT,
    "robot_triangles_lod0_each": int(robot_mesh.get_num_triangles(0)),
    "placed": placed,
    "not_used": {
        "high_poly_coil_agv": "Rejected for this screenshot candidate: 1,984,003 LOD0 triangles.",
        "meshy_generation": "No new Meshy asset generated or API credit used.",
    },
    "honest_status": "static visual automation cues only; no robot runtime, collision or gameplay claim",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_ROBOTIC_CUES_PASS robots=%d" % len(placed))
