"""Clean-room M1 Moorcross 2042 design-authority v002; source-only Blender output."""
import bpy
import math
from pathlib import Path

OUT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Vehicles\M1_Moorcross\CleanAuthoredAuthority_v002")
OUT.mkdir(parents=True, exist_ok=True)


def mat(name, color, metallic, roughness):
    value = bpy.data.materials.new(name)
    value.use_nodes = True
    node = value.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (*color, 1.0)
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = roughness
    return value


paint = mat("M1_2042_ElectricBlue", (0.025, 0.20, 0.46), 0.55, 0.22)
glass = mat("M1_2042_SmokedGlass", (0.007, 0.014, 0.027), 0.18, 0.12)
trim = mat("M1_2042_Graphite", (0.012, 0.014, 0.018), 0.45, 0.34)
tyre = mat("M1_2042_Tyre", (0.005, 0.005, 0.006), 0.0, 0.56)
alloy = mat("M1_2042_Alloy", (0.28, 0.30, 0.33), 0.9, 0.19)
lamp = mat("M1_2042_LED", (0.72, 0.95, 1.0), 0.15, 0.08)


def rounded_box(name, loc, dims, material, bevel):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    modifier = obj.modifiers.new("Production_Radii", 'BEVEL')
    modifier.width = bevel
    modifier.segments = 5
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.data.materials.append(material)
    return obj


def ellipsoid(name, loc, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def wheel(axle, side):
    y = 0.86 if side == "Left" else -0.86
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.365, depth=0.20,
        location=(axle, y, 0.365), rotation=(math.pi / 2, 0, 0))
    wheel = bpy.context.object
    wheel.name = f"M1_Tyre_{side}_{'Front' if axle > 0 else 'Rear'}"
    wheel.data.materials.append(tyre)
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.235, depth=0.205,
        location=(axle, y * 1.01, 0.365), rotation=(math.pi / 2, 0, 0))
    rim = bpy.context.object
    rim.name = f"M1_AeroRim_{side}_{'Front' if axle > 0 else 'Rear'}"
    rim.data.materials.append(alloy)
    for i in range(5):
        spoke = rounded_box(f"M1_Spoke_{axle}_{side}_{i}", (axle, y * 1.02, 0.365),
            (0.29, 0.026, 0.036), alloy, 0.012)
        spoke.rotation_euler[1] = i * math.tau / 5


bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Grounded 4.38m x 1.82m x 1.45m low five-door hatch: all dimensions are metres.
rounded_box("M1_LowerBody", (0, 0, 0.57), (4.38, 1.82, 0.48), paint, 0.18)
ellipsoid("M1_UpperShoulder", (-0.04, 0, 0.79), (2.06, 0.85, 0.29), paint)
ellipsoid("M1_HoodCrown", (1.17, 0, 0.94), (0.94, 0.82, 0.13), paint)
ellipsoid("M1_Greenhouse", (-0.28, 0, 1.12), (1.28, 0.73, 0.34), glass)

# The blue painted roof cap leaves a clean glass band below it.
rounded_box("M1_RoofCap", (-0.33, 0, 1.41), (1.72, 1.45, 0.08), paint, 0.07)
rounded_box("M1_FrontBumper", (2.07, 0, 0.50), (0.20, 1.77, 0.15), trim, 0.07)
rounded_box("M1_RearBumper", (-2.07, 0, 0.49), (0.20, 1.77, 0.15), trim, 0.07)
for y in (-0.91, 0.91):
    rounded_box("M1_Sill_" + str(y), (0, y, 0.43), (3.38, 0.045, 0.11), trim, 0.025)

# Four correctly separated door skins, a short front overhang and a tall rear hatch.
for x, label, width in ((0.55, "Front", 0.92), (-0.54, "Rear", 0.92)):
    for y, side in ((0.914, "Left"), (-0.914, "Right")):
        door = rounded_box(f"M1_Door_{label}_{side}", (x, y, 0.73), (width, 0.026, 0.42), paint, 0.035)
        rounded_box(f"M1_Handle_{label}_{side}", (x + 0.12, y * 1.015, 0.82),
            (0.13, 0.018, 0.020), trim, 0.007)

rounded_box("M1_TailgatePanel", (-1.71, 0, 0.87), (0.37, 1.70, 0.55), paint, 0.10)
rounded_box("M1_FrontLightBlade", (2.18, 0, 0.84), (0.028, 1.40, 0.035), lamp, 0.014)
rounded_box("M1_RearLightBlade", (-2.18, 0, 0.85), (0.028, 1.40, 0.035), lamp, 0.014)
rounded_box("M1_ClosedNose", (2.19, 0, 0.69), (0.025, 0.54, 0.12), trim, 0.012)

wheel(1.36, "Left")
wheel(1.36, "Right")
wheel(-1.36, "Left")
wheel(-1.36, "Right")

# Neutral review lighting and a wheel-level hero angle.
bpy.ops.object.camera_add(location=(6.3, -7.4, 2.65))
camera = bpy.context.object
camera.name = "M1_ReviewCamera"
bpy.context.scene.camera = camera
import mathutils
camera.rotation_euler = (mathutils.Vector((0, 0, 0.78)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
for loc, energy, size in (((3.0, -3.0, 5.5), 1100, 5.0), ((-3.0, 3.0, 3.0), 800, 4.0)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT / 'M1_Moorcross_2042_CleanAuthored_hero_v002.png')
scene.world.color = (0.018, 0.022, 0.030)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'M1_Moorcross_2042_CleanAuthoredAuthority_v002.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT / 'M1_Moorcross_2042_CleanAuthoredAuthority_v002.glb'), export_format='GLB', use_selection=False)
bpy.ops.render.render(write_still=True)
