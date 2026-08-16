import bpy
import bmesh
import json
import sys
from pathlib import Path
from mathutils import Vector


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :]
    source = Path(argv[0])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    report = {
        "source": str(source),
        "objects": len(bpy.context.scene.objects),
        "mesh_objects": len(meshes),
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "edges": sum(len(obj.data.edges) for obj in meshes),
        "polygons": sum(len(obj.data.polygons) for obj in meshes),
        "materials": sorted({slot.material.name for obj in meshes for slot in obj.material_slots if slot.material}),
        "mesh_names": [obj.name for obj in meshes],
        "bounds": {},
        "connected_components": [],
    }

    if meshes:
        corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
        mins = [min(c[i] for c in corners) for i in range(3)]
        maxs = [max(c[i] for c in corners) for i in range(3)]
        report["bounds"] = {
            "min": mins,
            "max": maxs,
            "size": [maxs[i] - mins[i] for i in range(3)],
        }

        for obj in meshes:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            unseen = set(bm.verts)
            sizes = []
            while unseen:
                seed = unseen.pop()
                stack = [seed]
                size = 1
                while stack:
                    vert = stack.pop()
                    for edge in vert.link_edges:
                        other = edge.other_vert(vert)
                        if other in unseen:
                            unseen.remove(other)
                            stack.append(other)
                            size += 1
                sizes.append(size)
            bm.free()
            report["connected_components"].append({
                "mesh": obj.name,
                "count": len(sizes),
                "largest_vertex_counts": sorted(sizes, reverse=True)[:20],
            })

    print("LB_MESHY_AUDIT=" + json.dumps(report, separators=(",", ":")))


if __name__ == "__main__":
    main()
