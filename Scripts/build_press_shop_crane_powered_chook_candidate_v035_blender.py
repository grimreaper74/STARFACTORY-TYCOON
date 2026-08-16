"""Build manufacturer-neutral powered C-hook Candidate v035.

Official manufacturer literature informs typology only. Project interfaces are
preserved; capacity, structure, drive performance and certification remain TBC.
"""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/IndustrialKit/BridgeCrane/PoweredCHook/Candidate_v035"
BLEND = OUT / "LB_Crane_PoweredCHook_Candidate_v035.blend"
FBX = OUT / "SM_LB_Crane_PoweredCHook_Candidate_v035.fbx"
PREVIEW = OUT / "LB_Crane_PoweredCHook_Candidate_v035_reference_oblique.png"
MANIFEST = OUT / "LB_Crane_PoweredCHook_Candidate_v035_manifest.json"
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1600, 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("PoweredCHookV035PreviewWorld")
scene.world.color = (0.012, 0.016, 0.022)


def material(name, colour, metallic=0.0, roughness=0.45, emission=None):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*colour, 1.0)
    value.metallic, value.roughness = metallic, roughness
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 4.0
    return value


YELLOW = material("LB_CHook_SafetyYellow_Worked", (0.62, 0.285, 0.012), 0.38, 0.42)
YELLOW_WEAR = material("LB_CHook_YellowEdgeWear", (0.22, 0.16, 0.075), 0.72, 0.31)
DARK = material("LB_CHook_FabricatedDarkSteel", (0.018, 0.024, 0.031), 0.82, 0.30)
STEEL = material("LB_CHook_WorkedSteel", (0.26, 0.30, 0.34), 0.94, 0.25)
WELD = material("LB_CHook_WeldMetal", (0.11, 0.13, 0.15), 0.88, 0.40)
RED = material("LB_CHook_ReplaceableContactRed", (0.39, 0.018, 0.012), 0.24, 0.56)
RUBBER = material("LB_CHook_LoadContactRubber", (0.008, 0.010, 0.012), 0.0, 0.82)
WHITE = material("LB_CHook_CairnwellPlate", (0.62, 0.65, 0.66), 0.48, 0.39)
GREEN = material("LB_CHook_SensorGreen", (0.008, 0.10, 0.018), 0.12, 0.28, (0.02, 0.85, 0.06))
AMBER = material("LB_CHook_StatusAmber", (0.52, 0.15, 0.005), 0.08, 0.30, (1.0, 0.20, 0.01))
parts = []


def finish(obj, mat, bevel=0.012):
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("ManufacturedEdge", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, 3, "ANGLE"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    parts.append(obj)
    return obj


def cube(name, location, dimensions, mat, bevel=0.012, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name, obj.dimensions = name, dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, mat, bevel)


def cylinder(name, location, radius, depth, mat, rotation=(0, 0, 0), vertices=64, bevel=0.008):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return finish(obj, mat, bevel)


def prism(name, points, depth, mat, bevel=0.018, y=0.0):
    count = len(points)
    verts = [(x, y-depth/2, z) for x, z in points] + [(x, y+depth/2, z) for x, z in points]
    faces = [tuple(range(count-1, -1, -1)), tuple(range(count, count*2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count+nxt, count+index))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(obj, mat, bevel)


def rod_between(name, start, end, radius, mat, vertices=32, bevel=0.004):
    a, b = Vector(start), Vector(end)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=delta.length,
                                       location=(a+b)*0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(delta.normalized())
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, mat, bevel)


def hose(name, points, radius=0.014, mat=DARK):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions, curve.bevel_depth, curve.bevel_resolution = "3D", radius, 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points)-1)
    for control, point in zip(spline.bezier_points, points):
        control.co = point
        control.handle_left_type = control.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    curve.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    parts.append(obj)
    return obj


def curved_shoe(name, x0, x1, y_half, base_z, crown, mat):
    profile = []
    segments = 10
    for i in range(segments + 1):
        y = -y_half + 2*y_half*i/segments
        z = base_z + crown * (1.0 - (y/y_half)**2)
        profile.append((y, z))
    profile += [(y_half, base_z-0.035), (-y_half, base_z-0.035)]
    verts = [(x0, y, z) for y, z in profile] + [(x1, y, z) for y, z in profile]
    n = len(profile)
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    for i in range(n):
        j = (i+1) % n
        faces.append((i, j, n+j, n+i))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(obj, mat, 0.008)


def text_mesh(name, body, location, size, extrude, mat, rotation=(math.pi/2, 0, 0)):
    curve = bpy.data.curves.new(name + "_Curve", "FONT")
    curve.body, curve.align_x, curve.align_y = body, "CENTER", "CENTER"
    curve.size, curve.extrude, curve.bevel_depth = size, extrude, 0.001
    obj = bpy.data.objects.new(name, curve)
    obj.location, obj.rotation_euler = location, rotation
    bpy.context.collection.objects.link(obj)
    curve.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    parts.append(obj)
    return obj


# Double-cheek fabricated C-frame. Opening is +X; suspension datum is Z=0.
outline = [
    (-0.61, 0.79), (-0.48, 1.01), (-0.20, 1.11), (0.09, 1.08),
    (0.34, 0.94), (0.49, 0.71), (0.50, 0.46), (0.39, 0.27),
    (0.17, 0.15), (-0.01, 0.08), (-0.10, -0.16), (-0.07, -0.38),
    (0.08, -0.51), (0.24, -0.55), (0.24, -0.73), (0.03, -0.82),
    (-0.25, -0.82), (-0.49, -0.69), (-0.64, -0.46), (-0.70, -0.13),
    (-0.69, 0.46)
]
prism("CH035_FrameWeb", outline, 0.34, YELLOW, 0.024)
for y in (-0.225, 0.225):
    prism(f"CH035_FrameCheek_{y:+.3f}", outline, 0.085, YELLOW, 0.018, y)

# External stiffeners and boxed curved transition evidence.
for y in (-0.285, 0.285):
    prism(f"CH035_UpperStiffener_{y:+.3f}", [(-0.49,0.76),(-0.31,0.95),(0.22,0.91),(0.39,0.69),(0.30,0.60),(-0.33,0.63)], 0.035, DARK, 0.006, y)
    prism(f"CH035_LowerGusset_{y:+.3f}", [(-0.47,-0.62),(-0.16,-0.71),(0.15,-0.68),(-0.03,-0.47),(-0.34,-0.40)], 0.035, STEEL, 0.006, y)
    for z in (-0.48, -0.17, 0.14, 0.45, 0.75):
        rod_between(f"CH035_WeldToe_{y:+.3f}_{z:+.2f}", (-0.62,y,z-0.09), (-0.59,y,z+0.09), 0.010, WELD, 20, 0.002)

# Long tapered arm through the bore, with bolted replaceable curved saddle.
prism("CH035_LoadArmBox", [(-0.04,-0.76),(2.15,-0.76),(2.35,-0.66),(2.35,-0.53),(2.19,-0.48),(-0.04,-0.48)], 0.38, STEEL, 0.020)
prism("CH035_LoadArmSidePlate_L", [(0.02,-0.77),(2.15,-0.77),(2.31,-0.67),(2.15,-0.61),(0.02,-0.61)], 0.035, YELLOW, 0.006, -0.215)
prism("CH035_LoadArmSidePlate_R", [(0.02,-0.77),(2.15,-0.77),(2.31,-0.67),(2.15,-0.61),(0.02,-0.61)], 0.035, YELLOW, 0.006, 0.215)
curved_shoe("CH035_ReplaceableCurvedSaddle", 0.08, 2.15, 0.205, -0.485, 0.050, RED)
curved_shoe("CH035_CurvedRubberContact", 0.16, 2.07, 0.185, -0.430, 0.036, RUBBER)
prism("CH035_ArmNose", [(2.13,-0.76),(2.38,-0.66),(2.38,-0.52),(2.15,-0.47)], 0.40, YELLOW_WEAR, 0.018)
for x in (0.22, 0.82, 1.42, 2.02):
    for y in (-0.225, 0.225):
        cylinder(f"CH035_SaddleBolt_{x:.2f}_{y:+.3f}", (x,y,-0.485), 0.026, 0.026, STEEL, rotation=(math.pi/2,0,0), vertices=32, bevel=0.003)

# Rear replaceable coil-face pad and inspection witness fasteners.
cube("CH035_RearPadCarrier", (-0.705, 0, -0.17), (0.075, 0.66, 0.92), RED, 0.014)
cube("CH035_RearRubberPad", (-0.750, 0, -0.17), (0.026, 0.59, 0.78), RUBBER, 0.007)
for z in (-0.46, -0.17, 0.12):
    for y in (-0.265, 0.265):
        cylinder(f"CH035_RearPadBolt_{z:+.2f}_{y:+.2f}", (-0.767,y,z), 0.025, 0.022, STEEL, rotation=(0,math.pi/2,0), vertices=32, bevel=0.002)

# Slewing housing, hoist clevis, guarded ring gear and structural pins.
cylinder("CH035_SlewRingHousing", (-0.20,0,1.18), 0.30, 0.58, DARK, rotation=(math.pi/2,0,0), bevel=0.012)
cylinder("CH035_SlewRingGuard", (-0.20,0,1.18), 0.245, 0.62, YELLOW, rotation=(math.pi/2,0,0), bevel=0.010)
cylinder("CH035_SlewHub", (-0.20,0,1.18), 0.145, 0.67, STEEL, rotation=(math.pi/2,0,0), bevel=0.008)
for y in (-0.27, 0.27):
    cube(f"CH035_HoistClevisCheek_{y:+.2f}", (-0.20,y,1.50), (0.70,0.10,0.47), YELLOW, 0.024)
cylinder("CH035_HoistClevisPin", (-0.20,0,1.61), 0.105, 0.72, STEEL, rotation=(math.pi/2,0,0), bevel=0.008)
cube("CH035_HoistSuspensionInterface", (-0.20,0,1.84), (0.52,0.48,0.20), YELLOW, 0.024)
cylinder("CH035_TopSwivel", (-0.20,0,1.70), 0.145, 0.30, DARK, bevel=0.010)

# Powered upper rotator: finned motor, reducer, brake and encoder.
cylinder("CH035_RotatorMotorBody", (-0.20,0.49,1.39), 0.16, 0.40, DARK, rotation=(math.pi/2,0,0), bevel=0.010)
for x in (-0.31,-0.25,-0.19,-0.13,-0.07):
    cylinder(f"CH035_MotorCoolingFin_{x:+.2f}", (x,0.49,1.39), 0.178, 0.018, STEEL, rotation=(0,math.pi/2,0), vertices=48, bevel=0.002)
cylinder("CH035_MotorBrake", (-0.20,0.72,1.39), 0.13, 0.075, RED, rotation=(math.pi/2,0,0), bevel=0.008)
cube("CH035_PlanetaryGearbox", (0.12,0.34,1.25), (0.34,0.31,0.34), DARK, 0.020)
cylinder("CH035_GearboxOutput", (-0.02,0.18,1.21), 0.12, 0.12, STEEL, rotation=(math.pi/2,0,0), bevel=0.006)
cylinder("CH035_AbsoluteEncoder", (-0.20,-0.36,1.18), 0.095, 0.13, WHITE, rotation=(math.pi/2,0,0), bevel=0.006)
cylinder("CH035_EncoderGuard", (-0.20,-0.44,1.18), 0.12, 0.035, DARK, rotation=(math.pi/2,0,0), bevel=0.006)

# Electrical enclosure, protected cable tray, glands, sensors and limit flags.
cube("CH035_JunctionBox", (-0.54,0.34,0.66), (0.30,0.16,0.38), DARK, 0.016)
cube("CH035_JunctionBoxDoor", (-0.54,0.428,0.66), (0.25,0.025,0.32), WHITE, 0.006)
for z in (0.54,0.78):
    cylinder(f"CH035_CableGland_{z:.2f}", (-0.54,0.445,z), 0.022, 0.035, STEEL, rotation=(math.pi/2,0,0), bevel=0.002)
prism("CH035_CableGuard", [(-0.60,1.62),(-0.39,1.72),(-0.30,1.49),(-0.50,1.34)], 0.14, YELLOW, 0.010, 0.36)
hose("CH035_PowerCable", [(-0.35,0.34,1.78),(-0.66,0.43,1.56),(-0.63,0.43,1.02),(-0.55,0.43,0.82)], 0.018)
hose("CH035_ControlCable", [(-0.27,0.38,1.75),(-0.57,0.48,1.51),(-0.54,0.48,1.06),(-0.48,0.47,0.84)], 0.012)
hose("CH035_BrakeCable", [(-0.12,0.44,1.67),(0.10,0.49,1.52),(0.12,0.49,1.38)], 0.010)
cylinder("CH035_LoadPresenceProximity", (-0.70,-0.34,-0.32), 0.032, 0.07, GREEN, rotation=(math.pi/2,0,0), bevel=0.002)
cylinder("CH035_RotationHomeSensor", (-0.42,-0.34,1.03), 0.032, 0.07, GREEN, rotation=(math.pi/2,0,0), bevel=0.002)
cube("CH035_RotationLimitFlag", (-0.37,-0.31,1.12), (0.12,0.035,0.08), STEEL, 0.003)
cylinder("CH035_AmberStatusLamp", (-0.56,-0.33,0.78), 0.038, 0.07, AMBER, rotation=(math.pi/2,0,0), bevel=0.003)

# Guarded pinch zone, inspection covers, grease points and restrained identity.
for y in (-0.322, 0.322):
    cube(f"CH035_PinGuardRail_{y:+.3f}", (-0.20,y,1.04), (0.72,0.025,0.055), DARK, 0.005)
    cube(f"CH035_PinGuardLower_{y:+.3f}", (-0.20,y,0.88), (0.72,0.025,0.055), DARK, 0.005)
    for x in (-0.52,-0.28,-0.04,0.12):
        rod_between(f"CH035_PinGuardBar_{y:+.3f}_{x:+.2f}", (x,y,0.90), (x,y,1.02), 0.010, DARK, 20, 0.002)
for y in (-0.292,0.292):
    cube(f"CH035_InspectionCover_{y:+.3f}", (-0.33,y,0.35), (0.36,0.025,0.34), DARK, 0.010)
    for x,z in ((-0.47,0.21),(-0.19,0.21),(-0.47,0.49),(-0.19,0.49)):
        cylinder(f"CH035_CoverFastener_{y:+.3f}_{x:+.2f}_{z:+.2f}", (x,y*1.035,z), 0.018, 0.018, STEEL, rotation=(math.pi/2,0,0), vertices=24, bevel=0.002)
for x,z in ((-0.53,0.83),(0.12,0.83),(-0.53,-0.53),(0.05,-0.62)):
    cylinder(f"CH035_InspectionPoint_{x:+.2f}_{z:+.2f}", (x,-0.305,z), 0.022, 0.035, RED, rotation=(math.pi/2,0,0), vertices=24, bevel=0.002)
cube("CH035_CairnwellIdentityPlate", (-0.56,-0.315,0.68), (0.30,0.024,0.16), WHITE, 0.006)
text_mesh("CH035_CairnwellRaisedText", "CAIRNWELL", (-0.56,-0.331,0.68), 0.045, 0.0025, DARK, rotation=(math.pi/2,0,math.pi/2))

# Moderate wear at entry/contact edges without implying damage.
cube("CH035_NoseScuff", (2.355,-0.205,-0.61), (0.035,0.018,0.15), STEEL, 0.003)
for z in (-0.70,-0.43,0.00,0.42):
    cube(f"CH035_RearEdgeWear_{z:+.2f}", (-0.775,-0.20,z), (0.018,0.08,0.10), YELLOW_WEAR, 0.003)

# The loaded coil centre is +1.50 m from the hook-body datum. Move the whole
# powered suspension group toward that load line and bridge it back to the
# spine with a welded balance beam. A rear counterweight makes the unloaded
# pose visually credible; its actual mass and balance calculation remain TBC.
upper_prefixes = (
    "CH035_Slew", "CH035_Hoist", "CH035_TopSwivel", "CH035_Rotator",
    "CH035_Motor", "CH035_Planetary", "CH035_Gearbox", "CH035_Absolute",
    "CH035_Encoder", "CH035_CableGuard", "CH035_RotationHome",
    "CH035_RotationLimit", "CH035_PinGuard", "CH035_BrakeCable")
for obj in parts:
    if obj.name.startswith(upper_prefixes):
        obj.location.x += 1.35
cube("CH035_UpperBalanceBeam", (0.24,0,1.13), (2.42,0.58,0.38), YELLOW, 0.026)
prism("CH035_UpperBeamWeb_L", [(-0.92,0.96),(1.43,0.96),(1.43,1.29),(-0.92,1.29)], 0.045, YELLOW, 0.006, -0.325)
prism("CH035_UpperBeamWeb_R", [(-0.92,0.96),(1.43,0.96),(1.43,1.29),(-0.92,1.29)], 0.045, YELLOW, 0.006, 0.325)
cube("CH035_RearCounterweight", (-1.10,0,1.20), (0.72,0.76,0.82), YELLOW, 0.034)
cube("CH035_RearCounterweightWearCap", (-1.48,0,1.20), (0.045,0.66,0.68), YELLOW_WEAR, 0.008)
for y in (-0.405,0.405):
    for z in (0.94,1.20,1.46):
        cylinder(f"CH035_CounterweightFastener_{y:+.3f}_{z:.2f}",(-1.10,y,z),0.028,0.030,STEEL,rotation=(math.pi/2,0,0),vertices=32,bevel=0.003)
rod_between("CH035_UpperBeamWeld_A",(-0.72,-0.31,0.93),(1.28,-0.31,0.93),0.011,WELD,24,0.002)
rod_between("CH035_UpperBeamWeld_B",(-0.72,0.31,0.93),(1.28,0.31,0.93),0.011,WELD,24,0.002)
hose("CH035_PowerCableExtended", [(-0.53,0.45,0.84),(-0.25,0.48,1.48),(0.48,0.48,1.70),(0.99,0.46,1.74)], 0.016)
hose("CH035_ControlCableExtended", [(-0.48,0.49,0.82),(-0.18,0.52,1.39),(0.52,0.52,1.63),(1.06,0.50,1.69)], 0.011)

# Merge to one stable Unreal static mesh, author UVs, pivot at suspension datum.
bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
hook = bpy.context.object
hook.name = "SM_LB_Crane_PoweredCHook_Candidate_v035"
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.015)
bpy.ops.object.mode_set(mode="OBJECT")
hook["asset_id"] = "LB-CRANE-POWERED-CH-CANDIDATE-v035"
hook["source_typology"] = "manufacturer_neutral_powered_rotating_coil_c_hook"
hook["capacity_status"] = "TBC_NOT_CERTIFIED"
hook["bore_arm_centre_below_datum_m"] = 0.59
hook["coil_interface_od_range_m"] = "1.80-2.10"
hook["coil_interface_width_max_m"] = 1.55
hook["body_to_load_centre_m"] = 1.50
hook["promotion_status"] = "CANDIDATE_NOT_PROMOTED"

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.object.select_all(action="DESELECT")
hook.select_set(True)
bpy.context.view_layer.objects.active = hook
bpy.ops.export_scene.fbx(filepath=str(FBX), use_selection=True, object_types={"MESH"},
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                         mesh_smooth_type="FACE", use_mesh_modifiers=True,
                         add_leaf_bones=False, bake_anim=False, axis_forward="-Y", axis_up="Z")

# Neutral oblique source preview.
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.mesh.primitive_plane_add(size=12, location=(0,0,-0.86))
floor = bpy.context.object
floor.data.materials.append(material("PreviewFloor", (0.045,0.052,0.060), 0.18, 0.62))
bpy.ops.object.camera_add(location=(4.5,-5.2,3.1))
camera = bpy.context.object
scene.camera = camera
camera.rotation_euler = (Vector((0.45,0,0.48))-camera.location).to_track_quat("-Z","Y").to_euler()
camera.data.lens = 58
for location, energy, size in [((-3.5,-3.0,5.2),1500,4.0),((4.5,-1.0,3.2),1100,3.0),((-1.0,4.0,2.8),1000,2.5)]:
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy, light.data.shape, light.data.size = energy, "DISK", size
    light.rotation_euler = (Vector((0.3,0,0.4))-light.location).to_track_quat("-Z","Y").to_euler()
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)

manifest = {
    "$schema": "line-boss/source/bridge-crane-powered-chook-candidate-v035/v1",
    "status": "SOURCE_BUILT__INDEPENDENT_ROUND_TRIP_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "reference_role": "official manufacturer typology and proportion reference only",
    "official_primary_sources": [
        {"manufacturer":"Bushman Equipment", "url":"https://www.bushman.com/below-the-hook-lifting-devices/c-hooks/", "applied":"tapered full-length carrying arm, coil saddle, motorized rotation, application-specific engineering"},
        {"manufacturer":"Winkle Industries", "url":"https://winkleindustries.com/en/c/hook", "applied":"replaceable curved support saddle, protective pads, motorized rotation option"},
        {"manufacturer":"WIMO Hebetechnik", "url":"https://wimo-ht.1kcloud.com/ep1imtqj/", "applied":"rounded supporting rail, motor/gear/brake typology, suspension and signal-light details"},
        {"manufacturer":"Bushman Equipment", "url":"https://www.bushman.com/news/recommendations-for-buying-and-inspecting-below-the-hook-lifting-devices/", "applied":"powered-lifter interlock sensors, control enclosure and electrical integration typology"}
    ],
    "blend": str(BLEND), "fbx": str(FBX), "preview": str(PREVIEW), "object": hook.name,
    "dimensions_m": [round(float(v),6) for v in hook.dimensions],
    "pivot_m": [round(float(v),6) for v in hook.location],
    "verified_project_interfaces": {"nominal_coil_od_m":1.90,"nominal_coil_width_m":1.50,"coil_od_range_m":[1.80,2.10],"coil_width_max_m":1.55,"bore_load_datum_below_hook_m":0.59,"hook_body_to_load_centre_m":1.50},
    "visible_systems": ["double-cheek fabricated C-frame","curved transitions","stiffening plates","weld seams","fasteners","long tapered bore arm","replaceable curved rubber saddle","slewing housing","motor","gearbox","brake","encoder","hoist clevis","junction box","protected cables","limit and proximity sensors","inspection covers","guarded pinch zone","restrained Cairnwell identity","moderate operational wear"],
    "engineering_values_tbc": ["safe working load","structural thicknesses","allowable stresses","fatigue life","contact pressure","drive torque","brake rating","stopping distance","clearances","control performance level","certification"],
    "copied_reference_branding": False, "copied_reference_capacity_marking": False,
    "material_slots": [slot.material.name for slot in hook.material_slots], "promotion_authorized": False
}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
