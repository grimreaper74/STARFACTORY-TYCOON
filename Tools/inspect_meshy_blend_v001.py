"""Report what is actually inside a Meshy .blend, without guessing.

Run headless:
  blender.exe -b <file.blend> -P inspect_meshy_blend_v001.py

Prints object names, triangle counts and the world-space bounding box in
metres. Two reasons this exists rather than trusting the filename:

  1. Meshy names its output for itself ("Titan Forge Station"), not for
     this project's stations. A drop must be identified by the owner,
     not inferred from a filename.
  2. Provenance requires a DECLARED TRIANGLE BUDGET. Generated geometry
     is permitted as a master asset; what it has to prove is its record.
     The measurement belongs in the manifest, so it is taken here.

Dimensions are the other half of identification: a hangar is long and
low, a forge is tall and narrow. Numbers settle it faster than a name.
"""
import bpy
import sys
from mathutils import Vector


def report():
    scene = bpy.context.scene
    meshes = [o for o in scene.objects if o.type == "MESH"]
    print("BLEND_REPORT_BEGIN")
    print("  objects_total   : %d" % len(scene.objects))
    print("  mesh_objects    : %d" % len(meshes))

    total_tris = 0
    total_verts = 0
    lo = Vector((1e18, 1e18, 1e18))
    hi = Vector((-1e18, -1e18, -1e18))

    for obj in meshes:
        mesh = obj.data
        # loop_triangles needs calculating before it is populated.
        mesh.calc_loop_triangles()
        tris = len(mesh.loop_triangles)
        total_tris += tris
        total_verts += len(mesh.vertices)
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            for axis in range(3):
                lo[axis] = min(lo[axis], world[axis])
                hi[axis] = max(hi[axis], world[axis])
        print("  MESH %-34s tris=%8d  verts=%8d"
              % (obj.name[:34], tris, len(mesh.vertices)))

    print("  triangles_total : %d" % total_tris)
    print("  vertices_total  : %d" % total_verts)
    if meshes:
        size = hi - lo
        print("  bounds_m        : X=%.2f  Y=%.2f  Z=%.2f"
              % (size.x, size.y, size.z))
        print("  bounds_cm       : X=%.0f  Y=%.0f  Z=%.0f"
              % (size.x * 100.0, size.y * 100.0, size.z * 100.0))
        print("  longest_axis_m  : %.2f" % max(size.x, size.y, size.z))

    mats = {m.name for o in meshes for m in o.data.materials if m}
    print("  materials       : %d  %s" % (len(mats), sorted(mats)[:6]))
    images = [i for i in bpy.data.images if i.source == "FILE" or i.packed_file]
    print("  images          : %d" % len(images))
    for img in images[:8]:
        print("    IMG %-28s %dx%d packed=%s"
              % (img.name[:28], img.size[0], img.size[1],
                 bool(img.packed_file)))
    print("BLEND_REPORT_END")


try:
    report()
except Exception as exc:  # noqa: BLE001 - headless, report and exit clean
    print("BLEND_REPORT_ERROR: %s" % exc)
    sys.exit(1)
