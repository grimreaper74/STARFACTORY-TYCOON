"""Export Meshy GLB drops to FBX at a DECLARED REAL-WORLD SIZE.

Meshy normalises every result to a ~2 m box whatever was asked for, so
scale has to be imposed here. Its sibling for .blend drops derives the
scale from a station's declared FOOTPRINT; site furniture is different -
a lighting mast is defined by its HEIGHT and a fence panel by its
LENGTH - so this takes the target size on the axis that defines the
object, named explicitly per asset.

Run headless:
  blender.exe -b -P export_meshy_glb_v001.py -- <glb> <out_dir> <name> <axis> <target_cm>
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


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    glb, out_dir, name, axis, target_cm = (
        argv[0], argv[1], argv[2], argv[3].lower(), float(argv[4]))
    os.makedirs(out_dir, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.ops.import_scene.gltf(filepath=glb)

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
    # on import - ten assets wearing whichever landed last.
    for material in bpy.data.materials:
        material.name = "%s_Mat" % name

    # UNPACK THE MAPS. A refined GLB carries its textures INSIDE the
    # file, and an FBX export cannot copy what has no path on disk -
    # the refined assets exported as bare geometry, silently, until
    # this was added. Written beside the FBX so the import lane has
    # real files to bring in.
    tex_dir = os.path.join(out_dir, "Textures")
    os.makedirs(tex_dir, exist_ok=True)
    written = []
    for img in bpy.data.images:
        if img.size[0] == 0:
            continue
        safe = img.name.replace("/", "_").replace("\\", "_")
        path = os.path.join(tex_dir, "%s_%s.png" % (name, safe))
        img.filepath_raw = path
        img.file_format = "PNG"
        try:
            img.save()
            written.append(os.path.basename(path))
        except Exception as exc:  # noqa: BLE001
            print("TEXTURE_SKIPPED %s: %s" % (safe, exc))
    print("TEXTURES %d %s" % (len(written), written))

    fbx = os.path.join(out_dir, "%s.fbx" % name)
    bpy.ops.export_scene.fbx(
        filepath=fbx, use_selection=False, apply_unit_scale=True,
        global_scale=1.0, apply_scale_options="FBX_SCALE_NONE",
        object_types={"MESH"}, mesh_smooth_type="FACE",
        use_mesh_modifiers=True, path_mode="COPY", embed_textures=False,
        axis_forward="-Z", axis_up="Y")
    print("FBX_WRITTEN %s (%d bytes)" % (fbx, os.path.getsize(fbx)))
    print("EXPORT_OK")


try:
    main()
except Exception as exc:  # noqa: BLE001
    print("EXPORT_ERROR: %s" % exc)
    sys.exit(1)
