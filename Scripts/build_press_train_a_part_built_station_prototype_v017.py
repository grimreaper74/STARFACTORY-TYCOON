"""Build one reusable press station deliberately, part by part, in Blender.

This is a source-only visual prototype. Dimensions are constrained to the retained
mid-train visual envelope but remain TBC engineering data. It creates no runtime,
collision, navigation, motion, safety or production authority.
"""

import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v017"
RENDERS = OUT / "Renders"
FBX_DIR = OUT / "FBX"
BLEND_OUT = OUT / "CA_MW_PressModulePrototype_v017.blend"
FBX_OUT = FBX_DIR / "SM_CA_MW_PressModulePrototype_v017.fbx"
MANIFEST = OUT / "PRESS_MODULE_PROTOTYPE_MANIFEST_v017.json"
VALIDATION = OUT / "PRESS_MODULE_PROTOTYPE_VALIDATION_v017.json"
for directory in (OUT, RENDERS, FBX_DIR):
    directory.mkdir(parents=True, exist_ok=True)
if any(path.exists() for path in (BLEND_OUT, FBX_OUT, MANIFEST, VALIDATION)):
    raise RuntimeError("Refusing to overwrite immutable PressModulePrototype_v017")

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.look = "AgX - Medium High Contrast"
if scene.world is None:
    scene.world = bpy.data.worlds.new("PressModulePrototypeWorld_v017")
scene.world.color = (0.018, 0.022, 0.026)

collection = bpy.data.collections.new("CA_MW_PressModulePrototype_v017")
scene.collection.children.link(collection)

def material(name, colour, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*colour, 1.0)
    mat.metallic = metallic
    mat.roughness = roughness
    node = mat.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (*colour, 1.0)
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = roughness
    return mat

GREEN = material("CA_MW_Press_CairnwellGreen_v017", (0.035, 0.20, 0.13), 0.32, 0.46)
GRAPHITE = material("CA_MW_Press_FabricatedGraphite_v017", (0.10, 0.12, 0.13), 0.50, 0.42)
STEEL = material("CA_MW_Press_MachinedSteel_v017", (0.38, 0.42, 0.45), 0.78, 0.29)
DARK = material("CA_MW_Press_DarkMachined_v017", (0.045, 0.052, 0.058), 0.63, 0.34)
YELLOW = material("CA_MW_Press_SafetyYellow_v017", (0.82, 0.39, 0.015), 0.18, 0.44)
COPPER = material("CA_MW_Press_CopperService_v017", (0.36, 0.12, 0.045), 0.66, 0.30)
parts = []

def relink(obj):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)

def box(name, location, dimensions, mat, bevel=0.05, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    relink(obj)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("ManufacturedEdge", "BEVEL")
        mod.width = min(bevel, min(dimensions) * 0.20)
        mod.segments = 3
    parts.append(obj)
    return obj

def cylinder(name, location, radius, depth, mat, rotation=(math.pi / 2, 0, 0), vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    relink(obj)
    obj.data.materials.append(mat)
    mod = obj.modifiers.new("MachinedEdge", "BEVEL")
    mod.width = min(0.025, radius * 0.12)
    mod.segments = 3
    parts.append(obj)
    return obj

def pipe(name, points, radius, mat):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points):
        point.co = (*xyz, 1.0)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    parts.append(obj)
    return obj

# Retained mid-train visual envelope target: 4.60 m wide x 2.30 m deep x 8.20 m high.
# Foundation and bed are layered assemblies rather than single blocks.
box("S03_Foundation_Plate", (0, 0, 0.16), (4.55, 2.25, 0.32), GRAPHITE, 0.09)
box("S03_Lower_Frame", (0, 0, 0.52), (4.20, 1.95, 0.42), GREEN, 0.08)
box("S03_Bolster_Base", (0, 0, 1.05), (3.70, 1.72, 0.52), DARK, 0.06)
box("S03_Bolster_Machined", (0, 0, 1.39), (3.42, 1.55, 0.18), STEEL, 0.025)
for x in (-1.42, -0.72, 0, 0.72, 1.42):
    box(f"S03_Bolster_TSlot_{x:+.2f}", (x, -0.79, 1.50), (0.055, 0.04, 0.035), DARK, 0.006)

# Four built-up uprights with separate face plates, inner wear plates and foot gussets.
for side in (-1, 1):
    x = side * 1.72
    for depth_side in (-1, 1):
        y = depth_side * 0.68
        box(f"S03_Upright_{side}_{depth_side}", (x, y, 4.15), (0.50, 0.56, 5.55), GREEN, 0.10)
        box(f"S03_UprightFace_{side}_{depth_side}", (x - side * 0.263, y, 4.15), (0.055, 0.43, 4.92), GRAPHITE, 0.018)
        box(f"S03_InnerWearPlate_{side}_{depth_side}", (x - side * 0.295, y, 3.58), (0.025, 0.34, 1.70), STEEL, 0.010)
        box(f"S03_FootGusset_{side}_{depth_side}", (x - side * 0.18, y, 1.14), (0.64, 0.46, 0.88), GRAPHITE, 0.11, rotation=(0, side * 0.11, 0))
        for z in (2.10, 3.40, 4.70, 5.95):
            cylinder(f"S03_FrameBolt_{side}_{depth_side}_{z:.2f}", (x - side * 0.295, y, z), 0.055, 0.045, STEEL, rotation=(0, math.pi / 2, 0), vertices=24)

# Crown: stepped fabricated box, inset panel, transverse ribs and rounded drive housings.
box("S03_Crown_Lower", (0, 0, 6.95), (4.38, 2.14, 0.62), GREEN, 0.12)
box("S03_Crown_Main", (0, 0, 7.50), (4.10, 1.98, 0.76), GREEN, 0.15)
box("S03_Crown_Top", (0, 0, 8.02), (3.65, 1.70, 0.28), GRAPHITE, 0.10)
box("S03_Crown_ServicePanel", (0, -1.006, 7.47), (2.15, 0.045, 0.46), GRAPHITE, 0.025)
for x in (-1.40, -0.70, 0, 0.70, 1.40):
    box(f"S03_Crown_Rib_{x:+.2f}", (x, -1.035, 7.48), (0.075, 0.06, 0.64), STEEL, 0.018)
for side in (-1, 1):
    cylinder(f"S03_Crown_Bearing_{side}", (side * 1.18, -1.10, 7.72), 0.36, 0.22, DARK, rotation=(math.pi / 2, 0, 0))
    cylinder(f"S03_Crown_BearingCap_{side}", (side * 1.18, -1.225, 7.72), 0.22, 0.05, STEEL, rotation=(math.pi / 2, 0, 0))

# Ram/slide and guides, visually separated from the fixed frame.
box("S03_RamBody", (0, 0, 5.55), (2.88, 1.42, 0.62), GRAPHITE, 0.08)
box("S03_RamMachinedFace", (0, 0, 5.19), (2.62, 1.27, 0.16), STEEL, 0.025)
for side in (-1, 1):
    box(f"S03_RamGuide_{side}", (side * 1.54, 0, 5.55), (0.18, 1.18, 1.18), DARK, 0.035)
    cylinder(f"S03_TieRod_{side}", (side * 1.18, 0, 6.18), 0.095, 1.20, STEEL, rotation=(0, 0, 0))

# Top drive group: motor, gearbox, flywheel guards and hydraulic services.
box("S03_DrivePlinth", (0.60, 0, 8.20), (1.95, 1.35, 0.22), DARK, 0.07)
cylinder("S03_MainMotor", (0.72, 0, 8.55), 0.44, 1.16, GRAPHITE, rotation=(0, math.pi / 2, 0))
for x in (0.30, 0.72, 1.14):
    cylinder(f"S03_MotorCoolingRib_{x:.2f}", (x, 0, 8.55), 0.49, 0.055, DARK, rotation=(0, math.pi / 2, 0), vertices=48)
cylinder("S03_FlywheelGuard", (-0.95, 0, 8.52), 0.69, 0.46, YELLOW, rotation=(0, math.pi / 2, 0), vertices=64)
cylinder("S03_FlywheelHub", (-1.19, 0, 8.52), 0.20, 0.06, DARK, rotation=(0, math.pi / 2, 0))

# Operator/service side: cabinet, HMI, manifold, pipes, vents and access ladder.
box("S03_ServiceCabinet", (2.02, -0.74, 3.05), (0.40, 0.64, 1.55), GRAPHITE, 0.06)
box("S03_ServiceCabinetDoor", (2.227, -0.74, 3.05), (0.025, 0.53, 1.38), GREEN, 0.018)
box("S03_HMI_Arm", (2.18, -1.02, 4.35), (0.16, 0.52, 0.16), GRAPHITE, 0.035)
box("S03_HMI_Panel", (2.18, -1.30, 4.35), (0.52, 0.12, 0.72), DARK, 0.055)
box("S03_HMI_Screen", (2.18, -1.365, 4.43), (0.35, 0.025, 0.38), STEEL, 0.02)
box("S03_Manifold", (-2.02, -0.72, 3.40), (0.40, 0.70, 1.20), GRAPHITE, 0.07)
for i, z in enumerate((3.10, 3.40, 3.70)):
    cylinder(f"S03_Valve_{i}", (-2.25, -0.72, z), 0.09, 0.10, YELLOW, rotation=(0, math.pi / 2, 0), vertices=32)
pipe("S03_HydraulicSupply", [(-2.10, -0.70, 3.75), (-2.10, -0.70, 6.65), (-1.50, -0.70, 7.02)], 0.045, COPPER)
pipe("S03_HydraulicReturn", [(-1.92, -0.50, 3.75), (-1.92, -0.50, 6.48), (-1.28, -0.50, 6.95)], 0.038, DARK)
for z in (2.15, 2.72, 3.29, 3.86, 4.43, 5.00, 5.57):
    box(f"S03_LadderRung_{z:.2f}", (-2.20, 0.66, z), (0.44, 0.07, 0.055), YELLOW, 0.018)
for x in (-2.38, -2.02):
    box(f"S03_LadderRail_{x:.2f}", (x, 0.66, 3.86), (0.055, 0.07, 3.86), YELLOW, 0.018)

# Safety and identity details.
box("S03_OperatorGuardRail", (0, -1.36, 1.80), (3.25, 0.07, 0.10), YELLOW, 0.025)
for x in (-1.58, 0, 1.58):
    box(f"S03_GuardPost_{x:+.2f}", (x, -1.36, 1.38), (0.08, 0.08, 0.92), YELLOW, 0.022)
box("S03_CairnwellIdentityPlate", (0, -1.085, 7.87), (1.32, 0.035, 0.22), STEEL, 0.022)

# Preserve individual objects in the Blend for inspection, plus a joined export copy.
for obj in parts:
    obj["engineering_status"] = "VISUAL_PROTOTYPE_TBC"
    obj["runtime_authority"] = "NONE_SOURCE_ONLY"
    obj["collision_intent"] = "NoCollision"

bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.duplicate()
export_parts = list(bpy.context.selected_objects)
for obj in export_parts:
    if obj.type == "CURVE":
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
bpy.ops.object.join()
export_obj = bpy.context.object
export_obj.name = "SM_CA_MW_PressModulePrototype_v017"
export_obj["engineering_status"] = "VISUAL_PROTOTYPE_TBC"
export_obj["collision_intent"] = "NoCollision"
export_obj["runtime_authority"] = "RETAINED_PRESS_STATION_ONLY"
export_obj.hide_render = True

bpy.ops.object.select_all(action="DESELECT")
export_obj.select_set(True)
bpy.context.view_layer.objects.active = export_obj
bpy.ops.export_scene.fbx(filepath=str(FBX_OUT), use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False, use_custom_props=True, object_types={"MESH"})

# Ground and studio lighting are render-only.
ground_mat = material("StudioGround", (0.055, 0.06, 0.065), 0.05, 0.78)
ground = box("StudioGround", (0, 0, -0.04), (13, 11, 0.08), ground_mat, 0)
ground["render_only"] = True

def look(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

camera_data = bpy.data.cameras.new("PressModule_v017_Camera")
camera = bpy.data.objects.new("PressModule_v017_Camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
for name, location, energy, size, colour in (
    ("Key", (7, -8, 11), 1250, 6.0, (1.0, 0.90, 0.78)),
    ("Fill", (-7, -4, 7), 900, 5.0, (0.62, 0.78, 1.0)),
    ("Roof", (0, 2, 13), 1450, 5.0, (1.0, 1.0, 1.0)),
    ("Rim", (5, 6, 8), 850, 4.0, (0.65, 0.85, 1.0)),
):
    data = bpy.data.lights.new("PressModule_v017_" + name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = colour
    light = bpy.data.objects.new("PressModule_v017_" + name, data)
    scene.collection.objects.link(light)
    light.location = location
    look(light, (0, 0, 4.2))

def render(filename, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look(camera, target)
    scene.render.filepath = str(RENDERS / filename)
    bpy.ops.render.render(write_still=True)

render("01_operator_three_quarter_v017.png", (8.8, -10.5, 6.2), (0, 0, 4.15), 58)
render("02_service_three_quarter_v017.png", (-8.4, -9.0, 6.8), (0, 0, 4.25), 60)
render("03_front_orthographic_v017.png", (0, -13.0, 4.25), (0, 0, 4.25), 70)

# Remove render-only ground from source collection contract before save/export accounting.
bpy.data.objects.remove(ground, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT), check_existing=False)

mesh_corners = [export_obj.matrix_world @ Vector(corner) for corner in export_obj.bound_box]
bounds = {
    "min": [min(point[i] for point in mesh_corners) for i in range(3)],
    "max": [max(point[i] for point in mesh_corners) for i in range(3)],
}
dimensions = [bounds["max"][i] - bounds["min"][i] for i in range(3)]
failures = []
if len(parts) < 75:
    failures.append(f"part count too low: {len(parts)}")
if dimensions[0] > 4.70 or dimensions[1] > 2.85 or dimensions[2] > 9.35:
    failures.append(f"prototype escaped retained visual envelope allowance: {dimensions}")
if not FBX_OUT.exists() or FBX_OUT.stat().st_size < 100000:
    failures.append("FBX export missing or implausibly small")

manifest = {
    "$schema": "cairnwell/source/press-module-prototype-v017/v1",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_ONLY_PART_BUILT_PRESS_MODULE__UNREAL_INTAKE_REQUIRED__NOT_PROMOTED",
    "method": "deliberate component-by-component hard-surface modelling in Blender 5.2",
    "asset_name": export_obj.name,
    "authored_part_count": len(parts),
    "joined_vertices": len(export_obj.data.vertices),
    "joined_polygons": len(export_obj.data.polygons),
    "bounds_m": bounds,
    "dimensions_m": dimensions,
    "dimensions_authority": "TBC_VISUAL_ENVELOPE_ONLY",
    "collision_intent": "NoCollision",
    "runtime_authority_added": False,
    "retained_assets_edited": False,
    "fbx": {"file": "FBX/" + FBX_OUT.name, "bytes": FBX_OUT.stat().st_size, "sha256": sha(FBX_OUT)},
    "renders": ["Renders/01_operator_three_quarter_v017.png", "Renders/02_service_three_quarter_v017.png", "Renders/03_front_orthographic_v017.png"],
}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
validation = {
    "status": "PASS__PART_BUILT_SOURCE_PROTOTYPE__FRESH_VISUAL_REVIEW_AND_ISOLATED_UNREAL_INTAKE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__SOURCE_PROTOTYPE_NOT_RETAINED",
    "authored_part_count": len(parts),
    "joined_vertices": len(export_obj.data.vertices),
    "joined_polygons": len(export_obj.data.polygons),
    "dimensions_m": dimensions,
    "retained_assets_edited": False,
    "promotion_authorized": False,
    "failures": failures,
}
VALIDATION.write_text(json.dumps(validation, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
print(json.dumps(validation, indent=2))
