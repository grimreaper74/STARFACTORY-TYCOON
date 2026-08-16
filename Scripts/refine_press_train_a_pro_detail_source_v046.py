"""Refine v044 service interfaces and end cells without overwriting retained work."""
import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v044/CA_MW_PressTrainA_ProDetailModular_v044.blend"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v046"
BLEND = OUT / "CA_MW_PressTrainA_ProDetailModular_v046.blend"
FBX = OUT / "FBX/SM_CA_MW_PressTrainA_ProDetailModular_v046.fbx"
REPORT = OUT / "PRESS_TRAIN_A_PRO_DETAIL_MODULAR_REFINEMENT_v046.json"

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

for path in (BLEND, FBX, REPORT):
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite {path}")
OUT.mkdir(parents=True, exist_ok=True)
FBX.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC))
collection = bpy.data.collections.get("PTA_ProDetail_v042") or bpy.context.scene.collection

GREEN = bpy.data.materials["CAI_MainStructureGreen_v042"]
DARK = bpy.data.materials["CAI_ServiceCharcoal_v042"]
STEEL = bpy.data.materials["CAI_MachinedSteel_v042"]
YELLOW = bpy.data.materials["CAI_SafetyYellow_v042"]
GREY = bpy.data.materials.get("CAI_ElectricalGrey_v041") or bpy.data.materials.get("CAI_ElectricalGrey_v042")
if GREY is None:
    raise RuntimeError("Inherited electrical-grey material is missing")
BLUE = bpy.data.materials.get("CAI_VacuumCupBlue_v041") or bpy.data.materials.get("CAI_VacuumCupBlue_v042")
if BLUE is None:
    raise RuntimeError("Inherited blue sensor material is missing")

added = []
def finish(obj, mat, role="STATIC", collision="SIMPLE", pivot="OBJECT_ORIGIN_TBC"):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj["LB_MobilityRole"] = role
    obj["LB_CollisionRole"] = collision
    obj["LB_PivotAuthority"] = pivot
    obj["LB_EngineeringValues"] = "TBC_NOT_INVENTED"
    added.append(obj.name)
    return obj

def box(name, loc, dims, mat, bevel=0.04, **meta):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(obj, mat, **meta)
    if bevel:
        mod = obj.modifiers.new("FabricatedEdge", "BEVEL")
        mod.width, mod.segments = bevel, 2
    return obj

def cyl(name, loc, radius, depth, mat, rotation=(0, 0, 0), vertices=20, **meta):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return finish(obj, mat, **meta)

def rail(name, a, b, radius, mat, **meta):
    av, bv = Vector(a), Vector(b)
    delta = bv - av
    obj = cyl(name, (av + bv) / 2, radius, delta.length, mat, **meta)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(delta.normalized())
    return obj

# S04 and S05: make the service-side process path physically legible from the press
# throat to the removable collection equipment. Values are visual/TBC.
stage_y = {"S04": 25.4, "S05": 33.0}
for stage, y in stage_y.items():
    # Twin enclosed bridge chutes span the gap from press skirt to service module.
    for idx, dy in enumerate((-0.72, 0.72), 1):
        chute = box(f"SM_CA_MW_PTA_{stage}_ServiceBridgeChute_{idx:02d}_v046",
                    (-3.55, y + dy, 1.82), (2.35, 0.58, 0.52), GREEN, 0.07)
        chute.rotation_euler.y = math.radians(-12)
    # Fabricated support legs and crossbeam visibly carry the external module.
    for idx, sy in enumerate((y - 1.45, y + 1.45), 1):
        box(f"SM_CA_MW_PTA_{stage}_ServiceSupportLeg_{idx:02d}_v046",
            (-5.30, sy, 0.72), (0.22, 0.22, 1.44), DARK, 0.025)
        box(f"SM_CA_MW_PTA_{stage}_ServiceFoot_{idx:02d}_v046",
            (-5.30, sy, 0.08), (0.62, 0.62, 0.16), STEEL, 0.02)
    box(f"SM_CA_MW_PTA_{stage}_ServiceSupportCrossbeam_v046",
        (-5.30, y, 1.36), (0.28, 3.15, 0.28), DARK, 0.03)
    # Guarded docking outline grounds the removable bin and identifies access.
    for sy in (y - 1.75, y + 1.75):
        box(f"SM_CA_MW_PTA_{stage}_BinDockRail_{'A' if sy < y else 'B'}_v046",
            (-6.05, sy, 0.34), (1.65, 0.12, 0.42), YELLOW, 0.025)
    box(f"SM_CA_MW_PTA_{stage}_BinDockBackstop_v046",
        (-6.72, y, 0.55), (0.14, 3.55, 1.10), YELLOW, 0.025)
    box(f"SM_CA_MW_PTA_{stage}_ServiceInspectionPanel_v046",
        (-6.58, y + 1.82, 1.35), (0.20, 0.72, 1.25), GREY, 0.05,
        role="MOVABLE", collision="QUERY_ONLY", pivot="HINGE_TBC")

# S01: add centring rails, blank separator fingers, and a visible feed handoff.
s01_y = 0.0
for side, x in (("L", -1.68), ("R", 1.68)):
    box(f"SM_CA_MW_PTA_S01_CentringRail_{side}_v046", (x, s01_y + 0.15, 0.93),
        (0.14, 3.85, 0.28), STEEL, 0.025, role="MOVABLE", collision="QUERY_ONLY", pivot="RAIL_SLIDE_TBC")
for idx, yoff in enumerate((-0.95, -0.30, 0.35, 1.0), 1):
    for side, x in (("L", -2.04), ("R", 2.04)):
        cyl(f"SM_CA_MW_PTA_S01_SeparatorFinger_{side}_{idx:02d}_v046",
            (x, s01_y + yoff, 1.34), 0.055, 0.78, YELLOW, vertices=16,
            role="MOVABLE", collision="QUERY_ONLY", pivot="FINGER_AXIS_TBC")
box("SM_CA_MW_PTA_S01_FeedHandoffBed_v046", (0, s01_y + 4.15, 0.72),
    (4.25, 1.65, 0.34), DARK, 0.04, role="MOVABLE", collision="QUERY_ONLY", pivot="BELT_AXIS")
for ix in (-1.55, -0.78, 0, 0.78, 1.55):
    cyl(f"SM_CA_MW_PTA_S01_HandoffRoller_{int((ix+2)*100):03d}_v046",
        (ix, s01_y + 4.15, 0.92), 0.10, 1.42, STEEL, rotation=(math.pi/2, 0, 0),
        role="MOVABLE", collision="QUERY_ONLY", pivot="ROLLER_AXIS")

# S07: replace the stick-like read with joint housings, a pedestal, wrist and cable.
s07_y = 45.0
box("SM_CA_MW_PTA_S07_RobotPedestal_v046", (0, s07_y + 0.15, 0.55), (1.35, 1.35, 1.10), DARK, 0.10)
for name, loc, radius, depth, rot in (
    ("Shoulder", (0, s07_y + 0.15, 1.55), 0.42, 0.62, (math.pi/2, 0, 0)),
    ("Elbow", (0, s07_y + 0.15, 2.78), 0.34, 0.54, (math.pi/2, 0, 0)),
    ("Wrist", (1.36, s07_y + 0.15, 3.56), 0.25, 0.46, (math.pi/2, 0, 0)),
):
    cyl(f"SM_CA_MW_PTA_S07_Robot{name}Housing_v046", loc, radius, depth, YELLOW,
        rotation=rot, role="MOVABLE", collision="QUERY_ONLY", pivot=f"{name.upper()}_AXIS_TBC")
rail("SM_CA_MW_PTA_S07_RobotCableUpper_v046", (-0.34, s07_y - 0.15, 1.55),
     (-0.34, s07_y - 0.15, 2.75), 0.055, DARK, collision="NO_COLLISION")
rail("SM_CA_MW_PTA_S07_RobotCableForearm_v046", (-0.34, s07_y - 0.15, 2.75),
     (1.38, s07_y - 0.15, 3.60), 0.050, DARK, collision="NO_COLLISION")
box("SM_CA_MW_PTA_S07_ClassificationHMI_v046", (-2.10, s07_y + 2.10, 1.45),
    (0.32, 0.72, 1.35), GREY, 0.05)
box("SM_CA_MW_PTA_S07_HMIScreen_v046", (-1.92, s07_y + 2.10, 1.62),
    (0.03, 0.48, 0.44), BLUE, 0.01, collision="NO_COLLISION")

renderables = [o for o in bpy.data.objects if o.type in {"MESH", "CURVE", "FONT"} and not o.hide_render]
minimum = Vector((float("inf"),) * 3)
maximum = Vector((float("-inf"),) * 3)
for obj in renderables:
    for corner in obj.bound_box:
        point = obj.matrix_world @ Vector(corner)
        for axis in range(3):
            minimum[axis] = min(minimum[axis], point[axis])
            maximum[axis] = max(maximum[axis], point[axis])
size = maximum - minimum
if size.x > 15.0:
    raise RuntimeError(f"Protected width exceeded: {size.x:.3f} m")

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
bpy.ops.object.select_all(action="DESELECT")
for obj in renderables:
    obj.select_set(True)
bpy.context.view_layer.objects.active = next(o for o in renderables if o.type == "MESH")
bpy.ops.export_scene.fbx(filepath=str(FBX), use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
    mesh_smooth_type="FACE", add_leaf_bones=False, use_custom_props=True,
    object_types={"MESH", "OTHER"})

payload = {
    "$schema": "cairnwell/source/press-train-a-pro-detail-modular-refinement-v046/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_ONLY_CONNECTED_SERVICE_AND_END_CELL_REFINEMENT__FRESH_REVIEW_REQUIRED__NOT_PROMOTED",
    "source_parent": str(SRC.relative_to(ROOT)).replace("\\", "/"),
    "source_parent_sha256": sha(SRC),
    "added_part_count": len(added),
    "added_parts": added,
    "bounds_size_m": [round(v, 6) for v in size],
    "protected_width_limit_m": 15.0,
    "protected_width_pass": bool(size.x <= 15.0),
    "engineering_values": "TBC_NOT_INVENTED",
    "runtime_authority_added": False,
    "promotion_authorized": False,
    "blend_sha256": sha(BLEND),
    "fbx_sha256": sha(FBX),
    "fbx_bytes": FBX.stat().st_size,
}
REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
