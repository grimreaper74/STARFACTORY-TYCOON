"""Render every GLB in a Meshy drop folder, so a drop can be JUDGED.

The standing rule is that a Meshy drop is identified by its RENDER and
never by its filename - a generator returns what it felt like returning,
and this project has already wired up the wrong thing once by trusting a
name. Importing straight into Unreal to look is slow and pollutes
Content with assets that may be rejected, so the look happens here
first, outside the engine.

Also reports TRIANGLE COUNT and real-world DIMENSIONS for each drop.
Both are needed by the intake manifest anyway (a declared triangle
budget is part of what an asset must prove), and the dimensions are the
check that a scale anchor actually landed - the prompts ask for "about
the size of a washing machine" precisely because a generator ignores a
number, so whether it obeyed is worth measuring rather than assuming.

Run:
  blender --background --python render_meshy_drop_v001.py -- <in> <out>
"""

import math
import os
import sys

import bpy  # noqa: E402  (only available inside Blender)


def argv_after_dashes():
    if "--" not in sys.argv:
        raise SystemExit("usage: ... -- <glb_dir> <out_dir>")
    return sys.argv[sys.argv.index("--") + 1:]


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def scene_bounds():
    """World-space bounds of every mesh, in metres."""
    lo = [1e9, 1e9, 1e9]
    hi = [-1e9, -1e9, -1e9]
    found = False
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        found = True
        for corner in obj.bound_box:
            world = obj.matrix_world @ __import__("mathutils").Vector(corner)
            for axis in range(3):
                lo[axis] = min(lo[axis], world[axis])
                hi[axis] = max(hi[axis], world[axis])
    if not found:
        return None, None
    return lo, hi


def triangle_count():
    total = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        total += len(mesh.loop_triangles)
        evaluated.to_mesh_clear()
    return total


def render_one(glb_path, out_png):
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=glb_path)

    lo, hi = scene_bounds()
    if lo is None:
        return None
    centre = [(lo[i] + hi[i]) * 0.5 for i in range(3)]
    size = [hi[i] - lo[i] for i in range(3)]
    radius = max(max(size) * 0.5, 0.001)
    tris = triangle_count()

    # A three-quarter view from roughly the game's own camera pitch, so
    # what is judged here resembles what will be seen in game rather
    # than a flattering hero angle.
    pitch = math.radians(35.0)
    yaw = math.radians(38.0)
    distance = radius * 3.4
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 50.0
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (
        centre[0] + distance * math.cos(pitch) * math.cos(yaw),
        centre[1] - distance * math.cos(pitch) * math.sin(yaw),
        centre[2] + distance * math.sin(pitch),
    )
    direction = (
        centre[0] - cam.location[0],
        centre[1] - cam.location[1],
        centre[2] - cam.location[2],
    )
    rot = __import__("mathutils").Vector(direction).to_track_quat("-Z", "Y")
    cam.rotation_euler = rot.to_euler()
    bpy.context.scene.camera = cam

    # Bright and even. These are draft previews with no materials worth
    # showing, so the job of the light is to reveal SHAPE.
    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 4.0
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(50), 0.0, math.radians(35))
    bpy.context.scene.collection.objects.link(sun)
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.1
    bpy.context.scene.world = world

    scene = bpy.context.scene
    # Engine name by AVAILABILITY, not by guess: Blender has renamed
    # EEVEE between versions and a wrong literal throws rather than
    # falling back, which is how this failed the first time.
    engines = {item.identifier for item in
               type(scene.render).bl_rna.properties["engine"].enum_items}
    scene.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT"
                           in engines else "BLENDER_EEVEE")
    scene.render.resolution_x = 900
    scene.render.resolution_y = 700
    scene.render.film_transparent = False
    scene.render.filepath = out_png
    bpy.ops.render.render(write_still=True)

    return {
        "triangles": tris,
        "size_cm": [round(s * 100.0, 1) for s in size],
    }


def main():
    args = argv_after_dashes()
    in_dir, out_dir = args[0], args[1]
    os.makedirs(out_dir, exist_ok=True)
    for name in sorted(os.listdir(in_dir)):
        if not name.lower().endswith(".glb"):
            continue
        stem = os.path.splitext(name)[0]
        info = render_one(os.path.join(in_dir, name),
                          os.path.join(out_dir, stem + ".png"))
        if info is None:
            print("DROP %s NO MESH" % stem)
        else:
            print("DROP %s tris=%d size_cm=%s"
                  % (stem, info["triangles"], info["size_cm"]))


main()
