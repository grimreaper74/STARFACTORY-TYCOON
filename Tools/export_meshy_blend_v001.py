"""Export a Meshy .blend to FBX + textures, scaled to a declared footprint.

Run headless:
  blender.exe -b <file.blend> -P export_meshy_blend_v001.py -- \
      <out_dir> <asset_name> <target_x_cm> <target_y_cm>

Two things this exists to do, neither of which should be done by hand:

SCALE. Meshy normalises every export to roughly a 2 m bounding box
regardless of what was asked for, so everything imports tiny. The
uniform scale is DERIVED here from the station's declared footprint in
the build catalogue, not typed in - the mesh and the data that says how
big the station is have to agree, or the game will tell a player a craft
fits and then clip it through the frame.

TEXTURES. Meshy packs its images into the .blend. Unpacked here beside
the FBX so the import lane has real files to bring in.

The scale is taken from the LONGER of the two footprint axes so the
model is never scaled up past its declared plan area on the other one.
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
    out_dir, name = argv[0], argv[1]
    target_x_cm, target_y_cm = float(argv[2]), float(argv[3])
    os.makedirs(out_dir, exist_ok=True)

    lo, hi = world_bounds()
    size = hi - lo
    print("SOURCE_BOUNDS_M X=%.3f Y=%.3f Z=%.3f" % (size.x, size.y, size.z))

    # Match the model's own long axis to the footprint's long axis, so a
    # model authored "long" is not squashed by a footprint written the
    # other way round.
    model_long = max(size.x, size.y)
    model_short = min(size.x, size.y)
    target_long = max(target_x_cm, target_y_cm) / 100.0
    target_short = min(target_x_cm, target_y_cm) / 100.0
    if model_long <= 0.0 or model_short <= 0.0:
        print("EXPORT_ERROR: degenerate source bounds")
        sys.exit(1)
    # Uniform, and the SMALLER of the two ratios, so the model always
    # fits inside its declared plan area rather than overhanging it.
    scale = min(target_long / model_long, target_short / model_short)
    print("SCALE_UNIFORM %.4f" % scale)

    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.scale = (obj.scale.x * scale, obj.scale.y * scale,
                         obj.scale.z * scale)
    bpy.context.view_layer.update()

    lo2, hi2 = world_bounds()
    scaled = hi2 - lo2
    print("SCALED_BOUNDS_CM X=%.0f Y=%.0f Z=%.0f"
          % (scaled.x * 100, scaled.y * 100, scaled.z * 100))

    # Every Meshy .blend names its one material "material", so importing
    # several assets made every FBX overwrite ONE shared material asset -
    # ten buildings wearing whichever import ran last, found by the first
    # sighted screenshot. Unique names end the collision.
    for material in bpy.data.materials:
        material.name = "%s_Mat" % name

    # Meshy packs its maps into the .blend; the import lane needs files.
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
