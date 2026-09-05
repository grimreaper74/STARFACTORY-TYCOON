"""Export a Meshy .blend to FBX at a DECLARED REAL-WORLD SIZE, scaled by
ONE defining axis rather than a footprint.

export_meshy_blend_v001.py already covers buildings/stations, whose
plan is two numbers (X and Y). A PART - a thruster pod, a fitting - is
defined by ONE length (how long it is), the same convention
export_meshy_glb_v001.py already uses for GLB drops. This is that
tool's sibling for a .blend drop, so an asset saved straight out of a
local generator (no GLB round trip) still gets an imposed, declared
size rather than whatever arbitrary box the generator normalised to.

Run headless:
  blender.exe -b <file.blend> -P export_meshy_blend_axis_v001.py -- \
      <out_dir> <asset_name> <axis> <target_cm>
where axis is one of x, y, z, longest.
"""
import bpy
import os
import sys
from mathutils import Vector


def world_bounds():
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
    out_dir, name, axis, target_cm = argv[0], argv[1], argv[2].lower(), float(argv[3])
    os.makedirs(out_dir, exist_ok=True)

    lo, hi = world_bounds()
    size = hi - lo
    print("SOURCE_BOUNDS_M X=%.3f Y=%.3f Z=%.3f" % (size.x, size.y, size.z))
    source = {"x": size.x, "y": size.y, "z": size.z,
              "longest": max(size.x, size.y, size.z)}[axis]
    if source <= 0.0:
        print("EXPORT_ERROR: degenerate source bounds")
        sys.exit(1)
    scale = (target_cm / 100.0) / source
    print("SCALE_UNIFORM %.4f (axis %s -> %.0f cm)" % (scale, axis, target_cm))

    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.scale = (obj.scale.x * scale, obj.scale.y * scale,
                         obj.scale.z * scale)
    bpy.context.view_layer.update()

    lo2, hi2 = world_bounds()
    scaled = hi2 - lo2
    print("SCALED_BOUNDS_CM X=%.0f Y=%.0f Z=%.0f"
          % (scaled.x * 100, scaled.y * 100, scaled.z * 100))

    # Every Meshy drop names its one material "material" - unique names
    # so importing several assets never overwrites one shared asset.
    for material in bpy.data.materials:
        material.name = "%s_Mat" % name

    # Meshy packs its maps into the .blend; the import lane needs files
    # (even though this project imports geometry only, unpacked here for
    # parity with export_meshy_blend_v001.py and so nothing is silently
    # dropped if a future import DOES want them).
    tex_dir = os.path.join(out_dir, "Textures")
    os.makedirs(tex_dir, exist_ok=True)
    written = []
    for img in bpy.data.images:
        if not img.packed_file or img.size[0] == 0:
            continue
        path = os.path.join(tex_dir, "%s_%s.png" % (name, img.name))
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        written.append(os.path.basename(path))
    print("TEXTURES %d %s" % (len(written), written))

    fbx = os.path.join(out_dir, "%s.fbx" % name)
    bpy.ops.export_scene.fbx(
        filepath=fbx,
        use_selection=False,
        apply_unit_scale=True,
        global_scale=1.0,
        apply_scale_options="FBX_SCALE_NONE",
        object_types={"MESH"},
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        path_mode="COPY",
        embed_textures=False,
        axis_forward="-Z",
        axis_up="Y")
    print("FBX_WRITTEN %s (%d bytes)" % (fbx, os.path.getsize(fbx)))
    print("EXPORT_OK")


try:
    main()
except Exception as exc:  # noqa: BLE001
    print("EXPORT_ERROR: %s" % exc)
    sys.exit(1)
