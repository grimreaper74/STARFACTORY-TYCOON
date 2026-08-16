"""Build a non-overwriting Pro-led modular-detail successor from retained v037.

All dimensions are visual/TBC. Objects remain separated for later Unreal pivots,
collision roles and native runtime binding; no gameplay authority is authored here.
"""
import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v037/CA_MW_PressTrainA_ModularAssembly_v037.blend"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v041"
BLEND = OUT / "CA_MW_PressTrainA_ProDetailModular_v041.blend"
FBX = OUT / "FBX/SM_CA_MW_PressTrainA_ProDetailModular_v041.fbx"
REPORT = OUT / "PRESS_TRAIN_A_PRO_DETAIL_MODULAR_v041.json"
REF_DIR = ROOT / "SourceAssets/Reference/PressTrains/TrainA/ProDetailedPack_v20260807"

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

for p in (BLEND, FBX, REPORT):
    if p.exists():
        raise RuntimeError(f"Refusing to overwrite {p}")
OUT.mkdir(parents=True, exist_ok=True)
FBX.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC))

collection = bpy.data.collections.new("PTA_ProDetail_v041")
bpy.context.scene.collection.children.link(collection)

def material(name, colour, metallic=0.0, rough=0.45):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*colour, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    return mat

GREEN = material("CAI_MainStructureGreen_v041", (0.025, 0.18, 0.115), 0.55, 0.34)
DARK = material("CAI_ServiceCharcoal_v041", (0.025, 0.032, 0.035), 0.65, 0.32)
STEEL = material("CAI_MachinedSteel_v041", (0.34, 0.39, 0.40), 0.82, 0.22)
YELLOW = material("CAI_SafetyYellow_v041", (0.95, 0.55, 0.015), 0.45, 0.30)
BLUE = material("CAI_VacuumCupBlue_v041", (0.015, 0.12, 0.25), 0.30, 0.30)
RUBBER = material("CAI_Rubber_v041", (0.008, 0.010, 0.012), 0.05, 0.70)
GREY = material("CAI_ElectricalGrey_v041", (0.34, 0.36, 0.35), 0.45, 0.38)
RED = material("CAI_SafetyRed_v041", (0.55, 0.015, 0.008), 0.25, 0.35)

new_objects = []

def finish(obj, name, mat, role="STATIC", collision="SIMPLE", pivot="OBJECT_ORIGIN_TBC"):
    obj.name = name
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj["LB_MobilityRole"] = role
    obj["LB_CollisionRole"] = collision
    obj["LB_PivotAuthority"] = pivot
    obj["LB_EngineeringValues"] = "TBC_NOT_INVENTED"
    new_objects.append(obj)
    return obj

def box(name, loc, dims, mat=GREEN, bevel=0.04, **meta):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("FabricatedEdge", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return finish(obj, name, mat, **meta)

def cyl(name, loc, radius, depth, mat=STEEL, axis="Z", vertices=24, **meta):
    rot = (0, 0, 0) if axis == "Z" else ((0, math.pi/2, 0) if axis == "X" else (math.pi/2, 0, 0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    return finish(bpy.context.object, name, mat, **meta)

def rail(name, start, end, radius=0.055, mat=DARK, **meta):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = cyl(name, (start + end) * 0.5, radius, delta.length, mat, axis="Z", **meta)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(delta.normalized())
    return obj

def safety_post(name, x, y, z=1.05):
    cyl(name, (x, y, z), 0.055, z * 2, YELLOW)
    box(name + "_Base", (x, y, 0.04), (0.28, 0.28, 0.08), DARK, 0.02)

STAGES = {"S01": 0.0, "S02": 7.5, "S03": 15.0, "S04": 22.5, "S05": 30.0, "S06": 37.5, "S07": 45.0}

# Shared inter-press transfer rails, carriage packs and grippers.
for side, x in (("L", -2.15), ("R", 2.15)):
    box(f"SM_CA_MW_PTA_TR_TransferRail_{side}_v041", (x, 24.0, 5.75), (0.24, 43.0, 0.32), DARK, 0.025)
for index, (stage, y) in enumerate(STAGES.items(), 1):
    box(f"SM_CA_MW_PTA_TR_ServoCarriage_{stage}_v041", (0, y, 5.72), (4.7, 0.48, 0.34), DARK, 0.04,
        role="MOVABLE", collision="QUERY_ONLY", pivot="CARRIAGE_CENTRE")
    box(f"SM_CA_MW_PTA_TR_Crossbar_{stage}_v041", (0, y, 5.20), (4.1, 0.16, 0.18), STEEL, 0.025,
        role="MOVABLE", collision="QUERY_ONLY", pivot="CROSSBAR_CENTRE")
    for cup_i, x in enumerate((-1.5, -0.75, 0, 0.75, 1.5), 1):
        rail(f"SM_CA_MW_PTA_TR_Arm_{stage}_{cup_i:02d}_v041", (x, y, 5.18), (x, y, 4.72), 0.035, STEEL,
             role="MOVABLE", collision="NO_COLLISION", pivot="ARM_TOP")
        cyl(f"SM_CA_MW_PTA_TR_VacuumCup_{stage}_{cup_i:02d}_v041", (x, y, 4.66), 0.10, 0.08, BLUE,
            role="MOVABLE", collision="QUERY_ONLY", pivot="CUP_CENTRE")
for y in (3.75, 11.25, 18.75, 26.25, 33.75, 41.25):
    box(f"SM_CA_MW_PTA_TR_SensorBracket_{int(y*100):04d}_v041", (2.45, y, 5.45), (0.14, 0.28, 0.50), YELLOW, 0.02)
    box(f"SM_CA_MW_PTA_TR_PositionSensor_{int(y*100):04d}_v041", (2.48, y, 5.62), (0.18, 0.18, 0.14), DARK, 0.02,
        collision="NO_COLLISION")

# S01 destack / blank-feed: fabricated frame, trolley, separators and vacuum head.
y = STAGES["S01"]
for x in (-3.1, 3.1):
    box(f"SM_CA_MW_PTA_S01_FramePost_{'L' if x < 0 else 'R'}_v041", (x, y, 2.55), (0.34, 0.42, 5.1), GREEN)
box("SM_CA_MW_PTA_S01_FrameCrosshead_v041", (0, y, 5.0), (6.5, 0.48, 0.50), GREEN)
box("SM_CA_MW_PTA_S01_BlankTrolley_v041", (0, y-1.05, 0.48), (4.5, 3.0, 0.52), GREEN, role="MOVABLE", collision="COMPLEX", pivot="TROLLEY_CARRIAGE")
for side, x in (("L", -2.45), ("R", 2.45)):
    box(f"SM_CA_MW_PTA_S01_SeparatorArm_{side}_v041", (x, y-0.4, 2.45), (0.22, 2.2, 0.22), STEEL, 0.04,
        role="MOVABLE", collision="QUERY_ONLY", pivot="ARM_BASE")
box("SM_CA_MW_PTA_S01_VacuumPickupFrame_v041", (0, y, 3.75), (4.8, 2.7, 0.20), DARK, role="MOVABLE", collision="QUERY_ONLY", pivot="HEAD_CENTRE")
for ix, x in enumerate((-1.8, -0.9, 0, 0.9, 1.8), 1):
    for iy, dy in enumerate((-0.8, 0, 0.8), 1):
        cyl(f"SM_CA_MW_PTA_S01_VacuumCup_{ix:02d}_{iy:02d}_v041", (x, y+dy, 3.55), 0.11, 0.10, BLUE,
            role="MOVABLE", collision="QUERY_ONLY", pivot="CUP_CENTRE")
box("SM_CA_MW_PTA_S01_FeedConveyor_v041", (0, y+3.0, 0.85), (4.4, 4.3, 0.45), DARK, role="MOVABLE", collision="QUERY_ONLY", pivot="BELT_AXIS")

# S02-S06 shared service packs and die-change interfaces.
for stage in ("S02", "S03", "S04", "S05", "S06"):
    y = STAGES[stage]
    box(f"SM_CA_MW_PTA_{stage}_HydraulicManifold_v041", (-4.85, y-1.35, 1.45), (0.42, 1.75, 1.75), DARK)
    for pipe_i, px in enumerate((-5.00, -4.82, -4.64), 1):
        rail(f"SM_CA_MW_PTA_{stage}_HydraulicPipe_{pipe_i:02d}_v041", (px, y-2.0, 0.8), (px, y+2.0, 3.8), 0.035, STEEL)
    box(f"SM_CA_MW_PTA_{stage}_ElectricalCabinet_v041", (4.95, y+1.65, 1.35), (0.62, 1.15, 2.7), GREY)
    box(f"SM_CA_MW_PTA_{stage}_HMIPedestal_v041", (5.05, y+0.55, 1.25), (0.40, 0.52, 1.75), DARK)
    box(f"SM_CA_MW_PTA_{stage}_HMIScreen_v041", (4.82, y+0.55, 1.72), (0.10, 0.42, 0.34), BLUE, 0.02, collision="NO_COLLISION")
    box(f"SM_CA_MW_PTA_{stage}_DieCart_v041", (-5.55, y, 0.45), (1.65, 4.6, 0.70), GREEN, role="MOVABLE", collision="COMPLEX", pivot="CART_CENTRE")
    for wheel_i, dy in enumerate((-1.65, 1.65), 1):
        cyl(f"SM_CA_MW_PTA_{stage}_DieCartWheel_{wheel_i:02d}_v041", (-6.0, y+dy, 0.28), 0.20, 0.22, RUBBER, axis="X",
            role="MOVABLE", collision="SIMPLE", pivot="WHEEL_AXIS")

# S04 trim/scrap gravity chutes, transition hopper, conveyor and removable bin.
y = STAGES["S04"]
for side, dy in (("L", -0.85), ("R", 0.85)):
    chute = box(f"SM_CA_MW_PTA_S04_ScrapChute_{side}_v041", (3.85, y+dy, 2.15), (2.7, 0.75, 0.50), GREEN, 0.08)
    chute.rotation_euler.y = math.radians(-24)
box("SM_CA_MW_PTA_S04_TransitionHopper_v041", (5.05, y, 1.15), (1.35, 2.45, 1.25), GREEN, 0.07)
box("SM_CA_MW_PTA_S04_ScrapConveyorHousing_v041", (5.75, y+2.2, 0.72), (1.25, 5.3, 0.95), DARK, 0.06)
cyl("SM_CA_MW_PTA_S04_ConveyorDrive_v041", (5.75, y+4.75, 0.72), 0.35, 1.32, STEEL, axis="X", role="MOVABLE", pivot="DRIVE_SHAFT")
box("SM_CA_MW_PTA_S04_RemovableScrapBin_v041", (5.75, y+5.85, 0.85), (1.35, 1.55, 1.65), GREY, 0.08,
    role="MOVABLE", collision="COMPLEX", pivot="BIN_CENTRE")
for px in (5.05, 6.45):
    safety_post(f"SM_CA_MW_PTA_S04_BinDockPost_{int(px*100)}_v041", px, y+5.85, 1.05)

# S05 pierce/slug chutes, hopper and removable bin.
y = STAGES["S05"]
for index, dy in enumerate((-1.2, -0.4, 0.4, 1.2), 1):
    cyl(f"SM_CA_MW_PTA_S05_SlugChute_{index:02d}_v041", (3.65, y+dy, 2.2), 0.16, 2.0, DARK, axis="X")
box("SM_CA_MW_PTA_S05_SlugHopper_v041", (4.75, y, 1.35), (1.8, 3.4, 1.25), GREEN, 0.08)
box("SM_CA_MW_PTA_S05_RemovableSlugBin_v041", (5.75, y, 0.75), (1.45, 2.7, 1.45), GREY, 0.08,
    role="MOVABLE", collision="COMPLEX", pivot="BIN_CENTRE")
box("SM_CA_MW_PTA_S05_LevelSensor_v041", (6.20, y, 1.65), (0.16, 0.20, 0.48), DARK, 0.02, collision="NO_COLLISION")

# S07 inspection/unload gantry, camera array, lighting, robot and stillage.
y = STAGES["S07"]
for x in (-4.7, 4.7):
    box(f"SM_CA_MW_PTA_S07_InspectGantryPost_{'L' if x < 0 else 'R'}_v041", (x, y, 2.7), (0.34, 0.44, 5.4), DARK)
box("SM_CA_MW_PTA_S07_InspectGantryTop_v041", (0, y, 5.25), (9.75, 0.48, 0.48), DARK)
for index, x in enumerate((-3.3, -1.1, 1.1, 3.3), 1):
    box(f"SM_CA_MW_PTA_S07_CameraBracket_{index:02d}_v041", (x, y, 4.78), (0.12, 0.35, 0.65), STEEL, 0.02)
    box(f"SM_CA_MW_PTA_S07_Camera_{index:02d}_v041", (x, y, 4.48), (0.30, 0.42, 0.24), DARK, 0.03,
        role="MOVABLE", collision="NO_COLLISION", pivot="CAMERA_TILT")
    box(f"SM_CA_MW_PTA_S07_Light_{index:02d}_v041", (x, y+0.28, 4.83), (0.62, 0.10, 0.16), YELLOW, 0.02, collision="NO_COLLISION")
# Six-axis visual robot assembled as separate links.
robot_x, robot_y = 0.0, y+1.4
cyl("SM_CA_MW_PTA_S07_RobotBase_v041", (robot_x, robot_y, 0.55), 0.55, 1.1, DARK, role="STATIC", collision="SIMPLE")
cyl("SM_CA_MW_PTA_S07_RobotTurntable_v041", (robot_x, robot_y, 1.12), 0.46, 0.28, YELLOW, role="MOVABLE", pivot="J1_Z")
link1 = rail("SM_CA_MW_PTA_S07_RobotUpperArm_v041", (0, robot_y, 1.25), (0, robot_y, 2.75), 0.28, YELLOW,
             role="MOVABLE", collision="QUERY_ONLY", pivot="J2")
link2 = rail("SM_CA_MW_PTA_S07_RobotForearm_v041", (0, robot_y, 2.75), (1.35, robot_y, 3.55), 0.24, YELLOW,
             role="MOVABLE", collision="QUERY_ONLY", pivot="J3")
box("SM_CA_MW_PTA_S07_EOATFrame_v041", (1.75, robot_y, 3.52), (1.25, 2.2, 0.16), DARK, 0.04,
    role="MOVABLE", collision="QUERY_ONLY", pivot="TOOL_CENTRE")
for ix, x in enumerate((1.3, 2.2), 1):
    for iy, dy in enumerate((-0.8, 0, 0.8), 1):
        cyl(f"SM_CA_MW_PTA_S07_EOATCup_{ix:02d}_{iy:02d}_v041", (x, robot_y+dy, 3.36), 0.11, 0.09, BLUE,
            role="MOVABLE", collision="QUERY_ONLY", pivot="CUP_CENTRE")
box("SM_CA_MW_PTA_S07_OutputConveyor_v041", (0, y+4.2, 0.82), (5.2, 4.4, 0.48), DARK, role="MOVABLE", collision="QUERY_ONLY", pivot="BELT_AXIS")
box("SM_CA_MW_PTA_S07_FinishedPanelStillage_v041", (0, y+6.6, 0.70), (4.4, 1.8, 1.4), GREEN, 0.06,
    role="MOVABLE", collision="COMPLEX", pivot="STILLAGE_CENTRE")

# Shared safety gates and local E-stops at service interfaces.
for stage in ("S01", "S02", "S03", "S04", "S05", "S06", "S07"):
    y = STAGES[stage]
    for side, x in (("L", -6.55), ("R", 6.55)):
        safety_post(f"SM_CA_MW_PTA_{stage}_SafetyPost_{side}_v041", x, y)
        box(f"SM_CA_MW_PTA_{stage}_EStop_{side}_v041", (x, y, 1.35), (0.18, 0.18, 0.26), RED, 0.03,
            role="INTERACT", collision="INTERACTION", pivot="BUTTON_CENTRE")

# Verify overall renderable envelope and protected-width rule.
renderables = [o for o in bpy.data.objects if o.type in {"MESH", "CURVE", "FONT"} and not o.hide_render]
minimum = Vector((float("inf"),) * 3)
maximum = Vector((float("-inf"),) * 3)
below_floor = []
for obj in renderables:
    object_min_z = float("inf")
    for corner in obj.bound_box:
        point = obj.matrix_world @ Vector(corner)
        object_min_z = min(object_min_z, point.z)
        minimum.x, minimum.y, minimum.z = min(minimum.x, point.x), min(minimum.y, point.y), min(minimum.z, point.z)
        maximum.x, maximum.y, maximum.z = max(maximum.x, point.x), max(maximum.y, point.y), max(maximum.z, point.z)
    if object_min_z < -0.01:
        below_floor.append({"name": obj.name, "min_z_m": object_min_z})
size = maximum - minimum
if size.x > 15.0:
    raise RuntimeError(f"Protected width exceeded: {size.x:.3f} m")
new_names = {o.name for o in new_objects}
new_below_floor = [row for row in below_floor if row["name"] in new_names]
if new_below_floor:
    raise RuntimeError(f"New below-floor geometry is forbidden: {new_below_floor}")

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
bpy.ops.object.select_all(action="DESELECT")
for obj in renderables:
    obj.select_set(True)
bpy.context.view_layer.objects.active = next(o for o in renderables if o.type == "MESH")
bpy.ops.export_scene.fbx(filepath=str(FBX), use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
    use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False,
    use_custom_props=True, object_types={"MESH", "OTHER"})

refs = {p.name: sha(p) for p in sorted(REF_DIR.glob("*.png"))}
payload = {
    "$schema": "cairnwell/source/press-train-a-pro-detail-modular-v041/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_ONLY_PRO_LED_MODULAR_DETAIL_SUCCESSOR__FRESH_RENDER_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "source_parent": str(SRC.relative_to(ROOT)).replace("\\", "/"),
    "source_parent_sha256": sha(SRC),
    "pro_references": refs,
    "new_object_count": len(new_objects),
    "total_renderable_count": len(renderables),
    "bounds_min_m": list(minimum), "bounds_max_m": list(maximum), "bounds_size_m": list(size),
    "inherited_below_floor_bounds": below_floor,
    "protected_width_limit_m": 15.0,
    "engineering_values": "TBC_NOT_INVENTED",
    "runtime_authority_added": False,
    "promotion_authorized": False,
    "blend_sha256": sha(BLEND), "fbx_sha256": sha(FBX), "fbx_bytes": FBX.stat().st_size,
}
REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
