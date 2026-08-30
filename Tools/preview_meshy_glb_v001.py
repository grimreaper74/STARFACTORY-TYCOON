"""Render a contact sheet of Meshy GLB drops, one three-quarter view each.

The .blend preview tool's sibling for GLB output. Identity is confirmed
by LOOKING - a generator names its output for itself, and eight site
props are indistinguishable by filename.

Run headless:
  blender.exe -b -P preview_meshy_glb_v001.py -- <glb_dir> <out_dir>
"""
import bpy
import glob
import math
import os
import sys
from mathutils import Vector


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)


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


def render_one(path, out_png):
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=path)
    lo, hi = bounds()
    centre = (lo + hi) * 0.5
    size = max((hi - lo).length, 0.001)

    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    direction = Vector((1.0, -1.2, 0.75)).normalized()
    cam.location = centre + direction * size * 1.5
    track = cam.constraints.new(type="TRACK_TO")
    empty = bpy.data.objects.new("Target", None)
    empty.location = centre
    bpy.context.scene.collection.objects.link(empty)
    track.target = empty
    bpy.context.scene.camera = cam

    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 4.0
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(50), 0.0, math.radians(35))
    bpy.context.scene.collection.objects.link(sun)
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.2
    bpy.context.scene.world = world

    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scene.render.engine = engine
            break
        except Exception:
            continue
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    print("PREVIEW %s -> %s  size_m %.2f x %.2f x %.2f"
          % (os.path.basename(path), out_png,
             hi.x - lo.x, hi.y - lo.y, hi.z - lo.z))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    glb_dir, out_dir = argv[0], argv[1]
    os.makedirs(out_dir, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(glb_dir, "*.glb"))):
        name = os.path.splitext(os.path.basename(path))[0]
        render_one(path, os.path.join(out_dir, name + ".png"))
    print("PREVIEW_OK")


main()
