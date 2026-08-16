import bpy
import bmesh
import json
import math
import os
import sys
from mathutils import Vector


def args_after_double_dash():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def parse_args():
    values = args_after_double_dash()
    result = {}
    for index in range(0, len(values), 2):
        result[values[index].lstrip("-")] = values[index + 1]
    return result


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def mesh_islands_and_boundaries(obj):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    remaining = set(bm.verts)
    islands = 0
    while remaining:
        islands += 1
        stack = [remaining.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
    boundaries = sum(1 for edge in bm.edges if len(edge.link_faces) != 2)
    bm.free()
    return islands, boundaries


def main():
    arguments = parse_args()
    source = os.path.abspath(arguments["source"])
    output = os.path.abspath(arguments["output"])
    os.makedirs(output, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=source)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("Meshy GLB imported with no mesh objects")

    raw_corners = []
    total_vertices = 0
    total_triangles = 0
    total_polygons = 0
    total_material_slots = 0
    total_islands = 0
    total_boundary_edges = 0
    object_rows = []
    for obj in meshes:
        obj.data.calc_loop_triangles()
        islands, boundary_edges = mesh_islands_and_boundaries(obj)
        world_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        raw_corners.extend(world_corners)
        row = {
            "name": obj.name,
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "triangles": len(obj.data.loop_triangles),
            "material_slots": len(obj.material_slots),
            "connected_islands": islands,
            "non_two_manifold_edges": boundary_edges,
        }
        object_rows.append(row)
        total_vertices += row["vertices"]
        total_polygons += row["polygons"]
        total_triangles += row["triangles"]
        total_material_slots += row["material_slots"]
        total_islands += islands
        total_boundary_edges += boundary_edges

    raw_min = Vector((min(v.x for v in raw_corners), min(v.y for v in raw_corners), min(v.z for v in raw_corners)))
    raw_max = Vector((max(v.x for v in raw_corners), max(v.y for v in raw_corners), max(v.z for v in raw_corners)))
    raw_dimensions = raw_max - raw_min
    longest_horizontal = max(raw_dimensions.x, raw_dimensions.y)
    target_length_m = 4.38
    target_scale = target_length_m / longest_horizontal if longest_horizontal > 0.0 else 1.0

    # Centre and ground only in the disposable audit scene; never save over the source GLB.
    centre_xy = Vector(((raw_min.x + raw_max.x) * 0.5, (raw_min.y + raw_max.y) * 0.5, 0.0))
    for obj in meshes:
        obj.location -= centre_xy
        obj.location.z -= raw_min.z

    clay = bpy.data.materials.new("M_Audit_Clay")
    clay.diffuse_color = (0.07, 0.22, 0.18, 1.0)
    clay.metallic = 0.15
    clay.roughness = 0.38
    for obj in meshes:
        obj.data.materials.clear()
        obj.data.materials.append(clay)

    floor_mat = bpy.data.materials.new("M_Audit_Floor")
    floor_mat.diffuse_color = (0.18, 0.18, 0.18, 1.0)
    floor_mat.roughness = 0.85
    floor_size = max(raw_dimensions.x, raw_dimensions.y) * 3.0
    bpy.ops.mesh.primitive_plane_add(size=floor_size, location=(0.0, 0.0, -0.002))
    bpy.context.object.data.materials.append(floor_mat)

    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World_Audit")
        bpy.context.scene.world = world
    world.color = (0.035, 0.035, 0.035)
    bpy.ops.object.light_add(type="AREA", location=(-3.0, -4.0, 6.0))
    bpy.context.object.data.energy = 1100.0
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = 5.0
    bpy.ops.object.light_add(type="AREA", location=(4.0, 2.0, 3.0))
    bpy.context.object.data.energy = 650.0
    bpy.context.object.data.size = 4.0

    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    bpy.context.scene.camera = camera
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"

    centre_z = raw_dimensions.z * 0.5
    distance = max(raw_dimensions.x, raw_dimensions.y) * 2.2
    views = {
        "01_end_negative_x": Vector((-distance, 0.0, centre_z)),
        "02_end_positive_x": Vector((distance, 0.0, centre_z)),
        "03_side_negative_y": Vector((0.0, -distance, centre_z)),
        "04_side_positive_y": Vector((0.0, distance, centre_z)),
        "05_hero": Vector((-distance * 0.75, -distance * 0.75, raw_dimensions.z * 1.15)),
    }
    for name, location in views.items():
        camera.location = location
        look_at(camera, (0.0, 0.0, centre_z))
        if "end" in name:
            camera.data.ortho_scale = max(raw_dimensions.y, raw_dimensions.z) * 1.35
        elif "side" in name:
            camera.data.ortho_scale = max(raw_dimensions.x, raw_dimensions.z) * 1.20
        else:
            camera.data.type = "PERSP"
            camera.data.lens = 58.0
        scene.render.filepath = os.path.join(output, name + ".png")
        bpy.ops.render.render(write_still=True)
        camera.data.type = "ORTHO"

    audit = {
        "schema": "line-boss/audit/vehicle-meshy-text-preview/v1",
        "status": "BLENDER_GEOMETRY_AUDIT_COMPLETE__VISUAL_APPROVAL_PENDING",
        "source": source,
        "mesh_objects": len(meshes),
        "vertices": total_vertices,
        "polygons": total_polygons,
        "triangles": total_triangles,
        "material_slots_before_clay_override": total_material_slots,
        "connected_islands": total_islands,
        "non_two_manifold_edges": total_boundary_edges,
        "raw_bounds_min_m": list(raw_min),
        "raw_bounds_max_m": list(raw_max),
        "raw_dimensions_m": list(raw_dimensions),
        "longest_horizontal_axis": "X" if raw_dimensions.x >= raw_dimensions.y else "Y",
        "scale_to_4_38m_length": target_scale,
        "target_dimensions_m": [component * target_scale for component in raw_dimensions],
        "expected_dimensions_m": [4.38, 1.82, 1.45],
        "refine_or_texture_submitted": False,
        "objects": object_rows,
        "renders": [name + ".png" for name in views],
    }
    with open(os.path.join(output, "blender_geometry_audit_v974.json"), "w", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
