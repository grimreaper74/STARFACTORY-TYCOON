"""Render a quick three-quarter preview of a Meshy .blend.

Run headless:
  blender.exe -b <file.blend> -P preview_meshy_blend_v001.py -- <out.png>

Exists so a drop can be identified by LOOKING at it rather than by
trusting a filename Meshy chose for itself. Frames the whole model from
a fixed three-quarter angle with flat neutral lighting - this is for
telling one building from another, not for looking pretty.
"""
import bpy
import math
import os
import sys
from mathutils import Vector


def bounds():
    lo = Vector((1e18, 1e18, 1e18))
    hi = Vector((-1e18, -1e18, -1e18))
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            for axis in range(3):
                lo[axis] = min(lo[axis], world[axis])
                hi[axis] = max(hi[axis], world[axis])
    return lo, hi


def main():
    out = sys.argv[sys.argv.index("--") + 1]
    scene = bpy.context.scene
    lo, hi = bounds()
    centre = (lo + hi) * 0.5
    radius = max((hi - lo).length * 0.5, 0.001)

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam)
    # Three-quarter view, slightly above - shows a long elevation and a
    # gable end at once, which is what distinguishes these buildings.
    ang = math.radians(35.0)
    dist = radius * 3.1
    cam.location = centre + Vector((math.cos(ang) * dist,
                                    -math.sin(ang) * dist,
                                    dist * 0.45))
    direction = centre - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    sun_data = bpy.data.lights.new("PreviewSun", type="SUN")
    sun_data.energy = 4.0
    sun = bpy.data.objects.new("PreviewSun", sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(55), 0.0, math.radians(35))

    world = bpy.data.worlds.new("PreviewWorld")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.1
    scene.world = world

    # Engine name moved between Blender versions; pick what exists.
    engines = scene.render.bl_rna.properties["engine"].enum_items.keys()
    for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
        if candidate in engines:
            scene.render.engine = candidate
            break
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 750
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = out
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print("PREVIEW_WRITTEN %s" % out)


try:
    main()
except Exception as exc:  # noqa: BLE001
    print("PREVIEW_ERROR: %s" % exc)
    sys.exit(1)
