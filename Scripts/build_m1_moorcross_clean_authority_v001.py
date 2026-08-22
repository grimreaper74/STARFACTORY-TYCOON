"""Creates a clean-room, Blender-authored 2042 M1 Moorcross design candidate.

This is source-art only.  It does not import, cook, or promote anything into Unreal.
"""
import bpy
import math
from pathlib import Path

OUT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\Vehicles\M1_Moorcross\CleanAuthoredAuthority_v001")
OUT.mkdir(parents=True, exist_ok=True)


def material(name, colour, metallic=0.0, roughness=0.4):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*colour, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


PAINT = material("M1_2042_SatinTeal", (0.035, 0.24, 0.20), 0.45, 0.23)
GLASS = material("M1_SmokedGlass", (0.012, 0.025, 0.04), 0.1, 0.16)
TRIM = material("M1_Graphite", (0.018, 0.022, 0.026), 0.55, 0.32)
LIGHT = material("M1_LED", (0.8, 0.95, 1.0), 0.1, 0.12)
RUBBER = material("M1_Rubber", (0.006, 0.006, 0.007), 0.0, 0.54)
ALLOY = material("M1_Alloy", (0.23, 0.26, 0.28), 0.85, 0.25)


def cube(name, loc, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("Soft production edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = 'ANGLE'
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.data.materials.append(mat)
    return obj


def cylinder(name, loc, radius, depth, mat, rotation=(math.pi / 2, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Tyre edge", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


# Clear the design scene.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Exact overall envelope: 4.38m x 1.82m x 1.45m.  X is vehicle length.
body = cube("M1_Moorcross_2042_BodyShell", (0, 0, 0.66), (2.19, 0.91, 0.34), PAINT, 0.18)
hood = cube("M1_Hood", (1.18, 0, 0.98), (0.86, 0.86, 0.085), PAINT, 0.09)
hood.rotation_euler[1] = math.radians(-4)
roof = cube("M1_Roof", (-0.30, 0, 1.31), (1.18, 0.79, 0.12), PAINT, 0.16)
roof.rotation_euler[1] = math.radians(2)

# The smoked greenhouse is deliberately broken into windscreen, roof and hatch glass
# so the body reads as a mass-producible five-door hatch rather than a single blob.
screen = cube("M1_Windscreen", (0.57, 0, 1.25), (0.42, 0.785, 0.095), GLASS, 0.06)
screen.rotation_euler[1] = math.radians(-29)
side_glass = cube("M1_SideGlass", (-0.30, 0, 1.18), (0.95, 0.805, 0.11), GLASS, 0.08)
hatch_glass = cube("M1_HatchGlass", (-1.52, 0, 1.11), (0.42, 0.785, 0.09), GLASS, 0.07)
hatch_glass.rotation_euler[1] = math.radians(28)
hatch = cube("M1_Tailgate", (-1.62, 0, 0.90), (0.40, 0.86, 0.28), PAINT, 0.12)
hatch.rotation_euler[1] = math.radians(15)

# Graphite sill and bumpers make the body appear grounded without UV textures.
cube("M1_FrontBumper", (2.03, 0, 0.52), (0.20, 0.89, 0.14), TRIM, 0.08)
cube("M1_RearBumper", (-2.03, 0, 0.51), (0.19, 0.89, 0.13), TRIM, 0.08)
cube("M1_LeftSill", (0, 0.88, 0.43), (1.66, 0.045, 0.10), TRIM, 0.04)
cube("M1_RightSill", (0, -0.88, 0.43), (1.66, 0.045, 0.10), TRIM, 0.04)

# Thin full-width light blades, plus a plain closed EV nose.
cube("M1_FrontLightBlade", (2.145, 0, 0.86), (0.026, 0.72, 0.025), LIGHT, 0.02)
cube("M1_RearLightBlade", (-2.145, 0, 0.87), (0.026, 0.72, 0.025), LIGHT, 0.02)
cube("M1_FrontSensorBand", (2.16, 0, 0.72), (0.022, 0.27, 0.04), TRIM, 0.02)

# Four ordinary doors and flush handle strips.
for x, label in ((0.56, "Front"), (-0.55, "Rear")):
    for y, side in ((0.912, "Left"), (-0.912, "Right")):
        cube(f"M1_Door_{label}_{side}", (x, y, 0.74), (0.49, 0.018, 0.26), PAINT, 0.025)
        cube(f"M1_Handle_{label}_{side}", (x + 0.10, y * 1.02, 0.82), (0.11, 0.012, 0.012), TRIM, 0.008)

# Separate grounded wheels: 2.72m wheelbase, 0.34m radius, 1.82m exact width.
for x, axle in ((1.36, "Front"), (-1.36, "Rear")):
    for y, side in ((0.80, "Left"), (-0.80, "Right")):
        tyre = cylinder(f"M1_Tyre_{axle}_{side}", (x, y, 0.34), 0.34, 0.18, RUBBER)
        rim = cylinder(f"M1_Rim_{axle}_{side}", (x, y * 1.0125, 0.34), 0.225, 0.186, ALLOY)
        # Five simple spokes make the wheel read at gameplay distance.
        for spoke in range(5):
            angle = math.tau * spoke / 5
            bar = cube(f"M1_Spoke_{axle}_{side}_{spoke}", (x, y * 1.018, 0.34), (0.17, 0.013, 0.018), ALLOY, 0.008)
            bar.rotation_euler[1] = angle

# One neutral, rendered source view for review.
bpy.ops.object.camera_add(location=(6.5, -7.2, 4.4))
camera = bpy.context.object
camera.name = "M1_ReviewCamera"
bpy.context.scene.camera = camera
def track(obj, point):
    direction = mathutils.Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
import mathutils
track(camera, (0, 0, 0.75))
bpy.ops.object.light_add(type='AREA', location=(2.5, -3.0, 5.0))
bpy.context.object.data.energy = 900
bpy.context.object.data.shape = 'DISK'
bpy.context.object.data.size = 5
bpy.ops.object.light_add(type='AREA', location=(-3.5, 3.5, 2.5))
bpy.context.object.data.energy = 650
bpy.context.object.data.size = 4

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT / 'M1_Moorcross_2042_CleanAuthored_hero_v001.png')
scene.world.color = (0.025, 0.028, 0.035)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'M1_Moorcross_2042_CleanAuthoredAuthority_v001.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT / 'M1_Moorcross_2042_CleanAuthoredAuthority_v001.glb'), export_format='GLB', use_selection=False)
bpy.ops.render.render(write_still=True)
