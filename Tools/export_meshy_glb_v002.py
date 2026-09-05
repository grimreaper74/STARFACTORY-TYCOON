"""Export a Meshy GLB to FBX at a declared real-world size, DECIMATED.

v001 does everything here except the decimation, and that omission is
why this exists: handed a raw Meshy generate (55 MB GLB -> 89 MB FBX),
Unreal's InterchangeFbxParser died with an access violation before the
import script got a look in (2026-09-04, the craft AGV). Every Meshy
asset this project has kept was reduced first - the Cargo-01 hull went
282,747 -> 38,940 triangles - so the reduction belongs IN the lane
rather than in whoever remembers to do it by hand.

It is also right on its own merits here: at this game's fixed -35
camera and its usual 6,500 cm boom, one centimetre of geometry is a
third of a pixel, so the sub-centimetre detail a generator lavishes on
a model cannot resolve at any zoom the player has.

v001 stays as it is - it is the lane every existing asset came through,
and superseding beats editing tested code in place.

Run headless:
  blender.exe -b -P export_meshy_glb_v002.py --
      <glb> <out_dir> <name> <axis> <target_cm> <target_tris>
where axis is one of x, y, z, longest.
"""
import bpy
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


def triangle_count():
    total = 0
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        mesh.calc_loop_triangles()
        total += len(mesh.loop_triangles)
    return total


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    glb, out_dir, name, axis, target_cm, target_tris = (
        argv[0], argv[1], argv[2], argv[3].lower(),
        float(argv[4]), int(argv[5]))
    os.makedirs(out_dir, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.ops.import_scene.gltf(filepath=glb)

    before = triangle_count()
    print("SOURCE_TRIS %d" % before)
    lo, hi = bounds()
    size = hi - lo
    print("SOURCE_BOUNDS_M X=%.3f Y=%.3f Z=%.3f" % (size.x, size.y, size.z))
    source = {"x": size.x, "y": size.y, "z": size.z,
              "longest": max(size.x, size.y, size.z)}[axis]
    if source <= 0.0:
        print("EXPORT_ERROR: degenerate bounds")
        sys.exit(1)
    scale = (target_cm / 100.0) / source
    print("SCALE_UNIFORM %.4f (axis %s -> %.0f cm)" % (scale, axis, target_cm))

    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.scale = (obj.scale.x * scale, obj.scale.y * scale,
                         obj.scale.z * scale)
    bpy.context.view_layer.update()

    # DECIMATE to the triangle budget, proportionally across objects so
    # a big part keeps its share and a small one is not annihilated.
    if before > target_tris:
        ratio = float(target_tris) / float(before)
        print("DECIMATE_RATIO %.4f (%d -> ~%d)" % (ratio, before, target_tris))
        for obj in bpy.context.scene.objects:
            if obj.type != "MESH":
                continue
            bpy.context.view_layer.objects.active = obj
            modifier = obj.modifiers.new(name="LBDecimate", type="DECIMATE")
            modifier.decimate_type = "COLLAPSE"
            modifier.ratio = ratio
            bpy.ops.object.modifier_apply(modifier="LBDecimate")
        print("DECIMATED_TRIS %d" % triangle_count())
    else:
        print("DECIMATE_SKIPPED already under budget")

    # SIT ON THE GROUND: a prop whose origin is its centre sinks half
    # into the floor when placed at Z=0.
    lo2, hi2 = bounds()
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.location.z -= lo2.z
    bpy.context.view_layer.update()
    lo3, hi3 = bounds()
    print("SCALED_BOUNDS_CM X=%.0f Y=%.0f Z=%.0f (base at %.1f)"
          % ((hi3.x - lo3.x) * 100, (hi3.y - lo3.y) * 100,
             (hi3.z - lo3.z) * 100, lo3.z * 100))

    # Unique material names: every Meshy export calls its material
    # "material", and identically-named materials overwrite each other
    # on import.
    for material in bpy.data.materials:
        material.name = "%s_Mat" % name

    fbx = os.path.join(out_dir, "%s.fbx" % name)
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=False,
                             apply_unit_scale=True, global_scale=1.0,
                             object_types={"MESH"},
                             mesh_smooth_type="FACE",
                             add_leaf_bones=False,
                             bake_anim=False,
                             path_mode="COPY", embed_textures=False)
    print("EXPORT_OK %s" % fbx)


main()
