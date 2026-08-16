"""Build a detailed powered C-hook coil grab from the owner-supplied real reference.

The reference establishes equipment typology only. Geometry is fitted to the
verified Line Boss master-coil envelope and the existing -0.590 m bore datum.
Capacity, structure, clearances, controls and certification remain TBC.
"""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/IndustrialKit/BridgeCrane/PoweredCHook/Candidate_v034"
BLEND = OUT / "LB_Crane_PoweredCHook_Candidate_v034.blend"
FBX = OUT / "SM_LB_Crane_PoweredCHook_Candidate_v034.fbx"
PREVIEW = OUT / "LB_Crane_PoweredCHook_Candidate_v034_reference_oblique.png"
MANIFEST = OUT / "LB_Crane_PoweredCHook_Candidate_v034_manifest.json"
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("PoweredCHookPreviewWorld")
scene.world.color = (0.018, 0.022, 0.028)


def mat(name, colour, metallic=0.0, roughness=0.45, emission=None):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*colour, 1.0)
    value.metallic = metallic
    value.roughness = roughness
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 5.0
    return value


YELLOW = mat("LB_CHook_SafetyYellow_Aged", (0.78, 0.39, 0.015), 0.28, 0.38)
DARK = mat("LB_CHook_FabricatedDarkSteel", (0.025, 0.032, 0.040), 0.75, 0.30)
STEEL = mat("LB_CHook_MachinedSteel", (0.31, 0.35, 0.39), 0.92, 0.22)
RED = mat("LB_CHook_ReplaceableContactRed", (0.48, 0.025, 0.018), 0.18, 0.50)
RUBBER = mat("LB_CHook_LoadContactElastomer", (0.012, 0.014, 0.017), 0.0, 0.76)
WHITE = mat("LB_CHook_IdentityPlate", (0.72, 0.75, 0.76), 0.38, 0.34)
GREEN = mat("LB_CHook_SensorGreen", (0.01, 0.12, 0.025), 0.1, 0.25, (0.02, 1.0, 0.08))
parts = []


def finish(obj, material, bevel=0.018):
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("ManufacturedEdge", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    parts.append(obj)
    return obj


def cube(name, location, dimensions, material, bevel=0.018):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, material, bevel)


def cylinder(name, location, radius, depth, material, rotation=(0, 0, 0), vertices=48, bevel=0.012):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return finish(obj, material, bevel)


def cylinder_between(name, start, end, radius, material, vertices=48, bevel=0.012):
    a, b = Vector(start), Vector(end)
    delta = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=delta.length, location=(a + b) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(delta.normalized())
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, material, bevel)


def prism(name, points, depth, material, bevel=0.026):
    count = len(points)
    verts = [(x, -depth/2, z) for x, z in points] + [(x, depth/2, z) for x, z in points]
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(obj, material, bevel)


def torus(name, location, major, minor, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=64, minor_segments=16, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return finish(obj, material, 0.006)


def hose(name, points, radius=0.016):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points)-1)
    for control, point in zip(spline.bezier_points, points):
        control.co = point
        control.handle_left_type = "AUTO"
        control.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    curve.materials.append(DARK)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    parts.append(obj)
    return obj


# Thick fabricated C-spine. Opening faces +X; hook datum is Z=0.
side = [
    (-0.58, 0.87), (-0.40, 1.07), (-0.05, 1.13), (0.25, 1.03),
    (0.43, 0.79), (0.45, 0.52), (0.30, 0.33), (0.06, 0.23),
    (-0.10, 0.15), (-0.15, -0.16), (-0.12, -0.37), (0.02, -0.48),
    (0.22, -0.53), (0.22, -0.76), (-0.08, -0.82), (-0.40, -0.72),
    (-0.60, -0.48), (-0.67, -0.12), (-0.66, 0.50)]
prism("PoweredCHook_LoadSpine", side, 0.48, YELLOW, 0.035)

# Lower bore-entering load arm: structural steel core plus replaceable red pad.
prism("PoweredCHook_BoreArmCore", [(-0.08,-0.77),(1.78,-0.77),(1.93,-0.67),(1.93,-0.53),(-0.08,-0.53)], 0.34, STEEL, 0.026)
cube("PoweredCHook_BoreContactPad", (0.92, 0, -0.505), (1.66, 0.39, 0.105), RED, 0.030)
cube("PoweredCHook_BoreContactElastomer", (0.92, 0, -0.445), (1.48, 0.36, 0.030), RUBBER, 0.012)
prism("PoweredCHook_ArmNose", [(1.76,-0.77),(1.96,-0.68),(1.96,-0.52),(1.76,-0.48)], 0.36, YELLOW, 0.028)

# Rear sacrificial contact face protects the coil OD during pickup.
cube("PoweredCHook_RearContactCarrier", (-0.675, 0, -0.19), (0.08, 0.62, 0.96), RED, 0.022)
cube("PoweredCHook_RearContactElastomer", (-0.725, 0, -0.19), (0.028, 0.55, 0.79), RUBBER, 0.010)
for z in (-0.47, -0.17, 0.13):
    cube(f"PoweredCHook_RearPadBoltBand_{z:+.2f}", (-0.747, 0, z), (0.016, 0.60, 0.035), STEEL, 0.004)

# Powered rotator and suspension, recognisably distinct from a simple lifting eye.
cylinder("PoweredCHook_RotatorBearing", (-0.22, 0, 1.17), 0.27, 0.44, DARK, rotation=(math.pi/2,0,0), bevel=0.018)
cylinder("PoweredCHook_RotatorHub", (-0.22, 0, 1.17), 0.17, 0.50, STEEL, rotation=(math.pi/2,0,0), bevel=0.012)
cube("PoweredCHook_RotatorYoke", (-0.22, 0, 1.43), (0.68, 0.54, 0.24), YELLOW, 0.034)
cylinder("PoweredCHook_TopSwivel", (-0.22, 0, 1.69), 0.18, 0.34, DARK, bevel=0.015)
cube("PoweredCHook_HoistInterface", (-0.22, 0, 1.92), (0.46, 0.40, 0.18), YELLOW, 0.026)

# Side drive motor, gearbox, encoder and guarded service box.
cylinder("PoweredCHook_RotationMotor", (-0.22, 0.47, 1.34), 0.15, 0.34, DARK, rotation=(math.pi/2,0,0), bevel=0.015)
cylinder("PoweredCHook_MotorEndBell", (-0.22, 0.66, 1.34), 0.12, 0.07, STEEL, rotation=(math.pi/2,0,0), bevel=0.010)
cube("PoweredCHook_Gearbox", (0.04, 0.29, 1.22), (0.30, 0.28, 0.31), YELLOW, 0.027)
cylinder("PoweredCHook_Encoder", (-0.22, -0.29, 1.17), 0.095, 0.12, DARK, rotation=(math.pi/2,0,0), bevel=0.008)
cube("PoweredCHook_JunctionBox", (-0.53, 0.30, 0.67), (0.26, 0.12, 0.30), WHITE, 0.018)

# Visible pins, fasteners, proximity sensor and status lamp.
for x, z in ((-0.48,0.84),(0.08,0.84),(-0.50,1.46),(0.06,1.46)):
    cylinder(f"PoweredCHook_Pin_{x:+.2f}_{z:+.2f}", (x,-0.265,z), 0.045, 0.055, STEEL, rotation=(math.pi/2,0,0), bevel=0.005)
cylinder("PoweredCHook_LoadPresenceSensor", (-0.69,-0.24,-0.30), 0.035, 0.06, GREEN, rotation=(math.pi/2,0,0), bevel=0.003)
cylinder("PoweredCHook_StatusLamp", (-0.53,-0.28,0.64), 0.033, 0.06, GREEN, rotation=(math.pi/2,0,0), bevel=0.003)

# Hose loop and protected run to the actuator/sensor package.
hose("PoweredCHook_ServiceHose_A", [(-0.35,0.30,1.77),(-0.70,0.38,1.58),(-0.66,0.36,1.03),(-0.52,0.35,0.80)], 0.017)
hose("PoweredCHook_ServiceHose_B", [(-0.28,0.34,1.75),(-0.61,0.43,1.54),(-0.58,0.41,1.09),(-0.46,0.39,0.84)], 0.013)

# Reference-inspired hazard panels; identity plate deliberately carries no copied brand/load rating.
for z in (-0.56, -0.30, -0.04, 0.22):
    panel = cube(f"PoweredCHook_HazardPanel_{z:+.2f}", (-0.723,-0.322,z), (0.026,0.016,0.16), DARK, 0.003)
    panel.rotation_euler.y = math.radians(-25)
cube("PoweredCHook_CairnwellIdentityPlate", (-0.665,-0.260,0.62), (0.028,0.22,0.24), WHITE, 0.008)

# Join into a stable single static mesh with explicit UVs for Unreal import.
bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
hook = bpy.context.object
hook.name = "SM_LB_Crane_PoweredCHook_Candidate_v034"
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")
hook["asset_id"] = "LB-CRANE-POWERED-CH-CANDIDATE-v034"
hook["reference_type"] = "owner_supplied_real_powered_coil_c_hook"
hook["capacity_status"] = "TBC_NOT_CERTIFIED"
hook["bore_arm_centre_below_datum_m"] = 0.59
hook["verified_coil_od_m"] = 1.90
hook["verified_coil_width_m"] = 1.50
hook["promotion_status"] = "CANDIDATE_NOT_PROMOTED"

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.object.select_all(action="DESELECT")
hook.select_set(True)
bpy.context.view_layer.objects.active = hook
bpy.ops.export_scene.fbx(filepath=str(FBX), use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                         apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="FACE", use_mesh_modifiers=True,
                         add_leaf_bones=False, bake_anim=False, axis_forward="-Y", axis_up="Z")

# Studio preview with the open side and powered suspension visible.
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.mesh.primitive_plane_add(size=12, location=(0,0,-0.86))
floor = bpy.context.object
floor.data.materials.append(mat("PreviewFloor", (0.055,0.065,0.075), 0.2, 0.55))
bpy.ops.object.camera_add(location=(4.6,-5.1,3.25))
camera = bpy.context.object
scene.camera = camera
direction = Vector((0.35,0,0.48)) - camera.location
camera.rotation_euler = direction.to_track_quat("-Z","Y").to_euler()
camera.data.lens = 58
for location, energy, size in [((-2.8,-3.0,5.4),1600,4.0),((4.5,-1.0,3.6),1100,3.0),((-1.0,4.0,2.2),900,2.5)]:
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.rotation_euler = (Vector((0.2,0,0.4))-light.location).to_track_quat("-Z","Y").to_euler()
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)

manifest = {
    "$schema": "line-boss/source/bridge-crane-powered-chook-candidate-v034/v1",
    "status": "SOURCE_BUILT__REFERENCE_LED_REDIRECT__INDEPENDENT_IMPORT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "reference": "owner-supplied photograph of a real powered C-hook coil grab",
    "blend": str(BLEND), "fbx": str(FBX), "preview": str(PREVIEW), "object": hook.name,
    "dimensions_m": [round(v,6) for v in hook.dimensions],
    "verified_interface": {"coil_outer_diameter_m":1.90,"coil_width_m":1.50,"bore_arm_centre_below_hook_datum_m":0.59},
    "unverified_tbc": ["rated capacity","structural sizing","load centre limit","contact pressure","drive torque","clearances","controls","safety performance","certification"],
    "copied_reference_branding": False, "copied_reference_16t_marking": False,
    "material_slots": [slot.material.name for slot in hook.material_slots],
    "promotion_authorized": False
}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
