"""Render Codex's weld robot twice: unbound slots vs brand materials.

Left  - every semantic slot left at a default grey, which is how the robot
        currently renders in Unreal: the import lane sets import_materials=False
        and nothing is bound to the six named slots.
Right - the same geometry with each named slot given the material its own name
        already asks for, from BRAND_IDENTITY_AUTHORITY.md.

Geometry is identical in both. Only the material bindings differ.
"""
import math
import os

import bpy
from mathutils import Vector

GLB = os.environ["LB_ROBOT_GLB"]
OUT = os.environ["LB_ROBOT_OUT"]

# name fragment -> (hex, roughness, metallic)
BRAND = {
    "CreamPaint":      ("F3F1E9", 0.45, 0.00),  # Warm White housings
    "EmeraldPanel":    ("1F4B44", 0.38, 0.00),  # Cairnwell Green accents
    "GraphiteTooling": ("202428", 0.55, 0.25),  # Foundry Charcoal tooling
    "SafetyYellow":    ("F2C300", 0.50, 0.00),  # Safety Yellow, functional
    "BlackMotor":      ("14171A", 0.45, 0.30),  # motor housings
    "BrushedSteel":    ("70777C", 0.30, 0.85),  # Steel Grey, metallic
}
NEUTRAL = ("8C8C8C", 0.60, 0.0)


def srgb_to_linear(v):
    v = v / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def rgba(h):
    return (srgb_to_linear(int(h[0:2], 16)),
            srgb_to_linear(int(h[2:4], 16)),
            srgb_to_linear(int(h[4:6], 16)), 1.0)


def make_material(name, h, roughness, metallic):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba(h)
        bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
    return mat


def import_robot():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=GLB)
    return [o for o in bpy.data.objects if o not in before]


def bounds(objects):
    lo = Vector((1e18, 1e18, 1e18))
    hi = Vector((-1e18, -1e18, -1e18))
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            w = obj.matrix_world @ Vector(corner)
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo, hi


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    left = import_robot()
    grey = make_material("UNBOUND_SLOT_GREY", *NEUTRAL)
    for obj in left:
        if obj.type != "MESH":
            continue
        if not obj.data.materials:
            obj.data.materials.append(grey)
        for i in range(len(obj.data.materials)):
            obj.data.materials[i] = grey

    bpy.context.view_layer.update()
    lo, hi = bounds(left)
    size = hi - lo
    print("LB_ROBOT_SIZE: %.1f x %.1f x %.1f" % (size.x, size.y, size.z))
    gap = max(size.x, size.y) * 1.25

    right = import_robot()
    for obj in right:
        if obj.parent is None:
            obj.location.x += gap
    bpy.context.view_layer.update()

    cache, unmatched = {}, set()
    for obj in right:
        if obj.type != "MESH":
            continue
        for i, slot in enumerate(obj.data.materials):
            name = slot.name if slot else ""
            chosen = None
            for frag, spec in BRAND.items():
                if frag.lower() in name.lower():
                    chosen = cache.setdefault(frag,
                        make_material("BRAND_" + frag, *spec))
                    break
            if chosen is None:
                unmatched.add(name)
                chosen = cache.setdefault("FALLBACK",
                    make_material("BRAND_FALLBACK", *BRAND["CreamPaint"]))
            obj.data.materials[i] = chosen
    print("LB_SLOTS_MATCHED:", sorted(k for k in cache if k != "FALLBACK"))
    print("LB_SLOTS_UNMATCHED:", sorted(unmatched))

    allobj = left + right
    bpy.context.view_layer.update()
    lo, hi = bounds(allobj)
    print("LB_PAIR_SPAN: %.2f x %.2f x %.2f" % (hi.x-lo.x, hi.y-lo.y, hi.z-lo.z))
    size = hi - lo
    centre = (lo + hi) * 0.5

    # Studio floor sized to the pair.
    bpy.ops.mesh.primitive_plane_add(size=1.0,
        location=(centre.x, centre.y, lo.z - size.z * 0.002))
    floor = bpy.context.active_object
    floor.scale = (size.x * 3.0, max(size.y, size.z) * 4.0, 1.0)
    floor.data.materials.append(make_material("FLOOR", "CFCDC6", 0.72, 0.0))

    # Sun lights: irradiance is independent of scene unit scale, so this is
    # robust whether the export is in metres or centimetres.
    bpy.ops.object.light_add(type="SUN", location=(centre.x, centre.y, hi.z))
    key = bpy.context.active_object
    key.data.energy = 3.1
    key.data.angle = math.radians(9.0)
    key.rotation_euler = (math.radians(48), math.radians(6), math.radians(34))

    bpy.ops.object.light_add(type="SUN", location=(centre.x, centre.y, hi.z))
    fill = bpy.context.active_object
    fill.data.energy = 1.15
    fill.data.angle = math.radians(28.0)
    fill.rotation_euler = (math.radians(64), 0, math.radians(-58))

    world = bpy.data.worlds.new("LBWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.62, 0.66, 0.71, 1.0)
        bg.inputs[1].default_value = 0.75

    # Camera framed by solving for the distance that fits the pair.
    res_x, res_y = 1800, 820
    lens, sensor = 55.0, 36.0
    hfov = 2.0 * math.atan(sensor / (2.0 * lens))
    vfov = 2.0 * math.atan(math.tan(hfov / 2.0) * (res_y / res_x))

    fit_w = size.x * 1.10
    fit_h = max(size.z, size.y) * 1.35
    dist = max(fit_w / (2.0 * math.tan(hfov / 2.0)),
               fit_h / (2.0 * math.tan(vfov / 2.0))) * 1.06

    target = Vector((centre.x, centre.y, lo.z + size.z * 0.45))
    # Slight three-quarter so silhouettes read, not a flat elevation.
    yaw, pitch = math.radians(-19.0), math.radians(15.0)
    offset = Vector((math.sin(yaw) * math.cos(pitch),
                     -math.cos(yaw) * math.cos(pitch),
                     math.sin(pitch))) * dist
    eye = target + offset

    bpy.ops.object.camera_add(location=eye)
    cam = bpy.context.active_object
    cam.data.lens = lens
    cam.rotation_euler = (target - eye).normalized().to_track_quat(
        "-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scene.render.engine = engine
            print("LB_ENGINE:", engine)
            break
        except Exception:
            continue
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = 64
    try:
        scene.view_settings.view_transform = "AgX"
    except Exception:
        try:
            scene.view_settings.view_transform = "Filmic"
        except Exception:
            pass
    scene.view_settings.exposure = 0.35
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("LB_RENDER_DONE:", OUT)


main()
