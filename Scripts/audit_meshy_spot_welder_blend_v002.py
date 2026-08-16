"""Read-only Blender audit and evidence renders for a Meshy spot-welder candidate.

Run with Blender 5.2 in factory/background mode:
  blender.exe --factory-startup --background --python this_script.py -- \
      source.blend output_directory stage_label

The source file is opened but never saved. All audit lights, cameras, materials and
object edits exist only in the disposable Blender process.
"""

from __future__ import annotations

from array import array
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Iterable

import bpy
from mathutils import Vector


def parse_args() -> tuple[Path, Path, str]:
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(values) != 3:
        raise RuntimeError(
            "usage: -- <source.blend> <output-directory> <stage-label>"
        )
    return Path(values[0]).resolve(), Path(values[1]).resolve(), values[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def rounded(values: Iterable[float], digits: int = 6) -> list[float]:
    return [round(float(value), digits) for value in values]


def world_bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return low, high


def combined_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    bounds = [world_bounds(obj) for obj in objects]
    lows, highs = zip(*bounds)
    low = Vector(tuple(min(point[index] for point in lows) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in highs) for index in range(3)))
    return low, high


def connected_component_sizes(mesh: bpy.types.Mesh) -> list[int]:
    """Return exact vertex counts per edge-connected island, largest first."""
    count = len(mesh.vertices)
    if count == 0:
        return []
    parents = list(range(count))
    sizes = [1] * count

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for edge in mesh.edges:
        first, second = edge.vertices
        root_first = find(first)
        root_second = find(second)
        if root_first == root_second:
            continue
        if sizes[root_first] < sizes[root_second]:
            root_first, root_second = root_second, root_first
        parents[root_second] = root_first
        sizes[root_first] += sizes[root_second]

    totals: dict[int, int] = {}
    for index in range(count):
        root = find(index)
        totals[root] = totals.get(root, 0) + 1
    return sorted(totals.values(), reverse=True)


def mesh_geometry_sha256(mesh: bpy.types.Mesh) -> str:
    """Hash geometry values/topology independent of Blender datablock names."""
    digest = hashlib.sha256()
    sections = (
        (mesh.vertices, "co", "f", len(mesh.vertices) * 3),
        (mesh.edges, "vertices", "i", len(mesh.edges) * 2),
        (mesh.polygons, "loop_start", "i", len(mesh.polygons)),
        (mesh.polygons, "loop_total", "i", len(mesh.polygons)),
        (mesh.loops, "vertex_index", "i", len(mesh.loops)),
    )
    for collection, property_name, typecode, size in sections:
        values = array(typecode, [0]) * size
        if size:
            collection.foreach_get(property_name, values)
        digest.update(property_name.encode("ascii"))
        digest.update(values.tobytes())
    return digest.hexdigest().upper()


def uv_sha256(mesh: bpy.types.Mesh) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for layer in mesh.uv_layers:
        values = array("f", [0]) * (len(layer.data) * 2)
        if values:
            layer.data.foreach_get("uv", values)
        digest = hashlib.sha256(values.tobytes())
        hashes[layer.name] = digest.hexdigest().upper()
    return hashes


def uv_record(mesh: bpy.types.Mesh) -> list[dict]:
    layers: list[dict] = []
    for layer in mesh.uv_layers:
        coordinates = [loop.uv for loop in layer.data]
        finite = [
            uv for uv in coordinates if math.isfinite(uv.x) and math.isfinite(uv.y)
        ]
        if finite:
            low = (min(uv.x for uv in finite), min(uv.y for uv in finite))
            high = (max(uv.x for uv in finite), max(uv.y for uv in finite))
        else:
            low = high = (0.0, 0.0)
        layers.append(
            {
                "name": layer.name,
                "active": layer == mesh.uv_layers.active,
                "loop_count": len(layer.data),
                "finite_loop_count": len(finite),
                "nonfinite_loop_count": len(coordinates) - len(finite),
                "bounds_min": rounded(low),
                "bounds_max": rounded(high),
            }
        )
    return layers


def mesh_record(obj: bpy.types.Object) -> dict:
    mesh = obj.data
    low, high = world_bounds(obj)
    center = (low + high) * 0.5
    origin = obj.matrix_world.translation
    diagonal = max((high - low).length, 1.0e-9)
    face_sizes: dict[str, int] = {}
    triangle_count = 0
    material_face_counts: dict[str, int] = {}
    for polygon in mesh.polygons:
        count = len(polygon.vertices)
        face_sizes[str(count)] = face_sizes.get(str(count), 0) + 1
        triangle_count += max(0, count - 2)
        key = str(polygon.material_index)
        material_face_counts[key] = material_face_counts.get(key, 0) + 1
    islands = connected_component_sizes(mesh)
    return {
        "name": obj.name,
        "data_name": mesh.name,
        "parent": obj.parent.name if obj.parent else None,
        "parent_type": obj.parent_type,
        "children": sorted(child.name for child in obj.children),
        "collection_names": sorted(collection.name for collection in obj.users_collection),
        "hide_render": bool(obj.hide_render),
        "hide_viewport": bool(obj.hide_viewport),
        "location": rounded(obj.location),
        "rotation_mode": obj.rotation_mode,
        "rotation_euler_rad": rounded(obj.rotation_euler),
        "scale": rounded(obj.scale),
        "matrix_world": [rounded(row) for row in obj.matrix_world],
        "matrix_determinant": round(float(obj.matrix_world.determinant()), 8),
        "world_origin": rounded(origin),
        "world_bounds_min": rounded(low),
        "world_bounds_max": rounded(high),
        "world_dimensions": rounded(high - low),
        "bounds_center": rounded(center),
        "pivot_to_bounds_center": rounded(origin - center),
        "pivot_offset_fraction_of_diagonal": round((origin - center).length / diagonal, 8),
        "pivot_inside_axis_aligned_bounds": all(
            low[index] <= origin[index] <= high[index] for index in range(3)
        ),
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "polygons": len(mesh.polygons),
        "triangles_after_triangulation": triangle_count,
        "face_vertex_counts": face_sizes,
        "material_face_counts_by_slot": material_face_counts,
        "edge_connected_island_count": len(islands),
        "edge_connected_island_vertex_counts": islands,
        "loose_edge_count": sum(1 for edge in mesh.edges if edge.is_loose),
        "geometry_sha256": mesh_geometry_sha256(mesh),
        "uv_sha256": uv_sha256(mesh),
        "uv_layers": uv_record(mesh),
        "color_attributes": [attribute.name for attribute in mesh.color_attributes],
        "material_slots": [
            slot.material.name if slot.material else None for slot in obj.material_slots
        ],
        "modifiers": [
            {
                "name": modifier.name,
                "type": modifier.type,
                "show_render": bool(modifier.show_render),
            }
            for modifier in obj.modifiers
        ],
        "constraints": [
            {
                "name": constraint.name,
                "type": constraint.type,
                "mute": bool(constraint.mute),
                "influence": round(float(constraint.influence), 6),
            }
            for constraint in obj.constraints
        ],
        "shape_keys": [
            key.name for key in mesh.shape_keys.key_blocks
        ]
        if mesh.shape_keys
        else [],
        "vertex_groups": [group.name for group in obj.vertex_groups],
        "has_animation_data": obj.animation_data is not None,
        "custom_properties": sorted(
            key for key in obj.keys() if key != "_RNA_UI"
        ),
    }


def material_record(material: bpy.types.Material) -> dict:
    nodes = []
    if material.use_nodes and material.node_tree:
        for node in material.node_tree.nodes:
            record = {
                "name": node.name,
                "label": node.label,
                "type": node.bl_idname,
            }
            if node.type == "TEX_IMAGE":
                record["image"] = node.image.name if node.image else None
                record["interpolation"] = node.interpolation
                record["extension"] = node.extension
            nodes.append(record)
    return {
        "name": material.name,
        "use_nodes": bool(material.use_nodes),
        "surface_render_method": getattr(
            material, "surface_render_method", None
        ),
        "diffuse_color": rounded(material.diffuse_color),
        "metallic": round(float(material.metallic), 6),
        "roughness": round(float(material.roughness), 6),
        "node_count": len(nodes),
        "nodes": nodes,
        "links": [
            {
                "from_node": link.from_node.name,
                "from_socket": link.from_socket.name,
                "to_node": link.to_node.name,
                "to_socket": link.to_socket.name,
            }
            for link in material.node_tree.links
        ]
        if material.use_nodes and material.node_tree
        else [],
    }


def armature_record(obj: bpy.types.Object) -> dict:
    return {
        "name": obj.name,
        "parent": obj.parent.name if obj.parent else None,
        "world_origin": rounded(obj.matrix_world.translation),
        "bone_count": len(obj.data.bones),
        "bones": [
            {
                "name": bone.name,
                "parent": bone.parent.name if bone.parent else None,
                "head_local": rounded(bone.head_local),
                "tail_local": rounded(bone.tail_local),
                "use_deform": bool(bone.use_deform),
            }
            for bone in obj.data.bones
        ],
    }


def create_material(name: str, color: tuple[float, float, float, float],
                    metallic: float = 0.05, roughness: float = 0.48):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.metallic = metallic
    material.roughness = roughness
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Metallic"].default_value = metallic
        principled.inputs["Roughness"].default_value = roughness
    return material


def aim(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_render_context(low: Vector, high: Vector):
    center = (low + high) * 0.5
    dimensions = high - low
    span = max(dimensions.x, dimensions.y, dimensions.z)

    floor_material = create_material(
        "LB_Audit_Floor_Material", (0.025, 0.032, 0.041, 1.0), 0.03, 0.72
    )
    bpy.ops.mesh.primitive_plane_add(
        size=span * 5.0,
        location=(center.x, center.y, low.z - span * 0.012),
    )
    floor = bpy.context.object
    floor.name = "LB_Audit_Floor"
    floor.data.materials.append(floor_material)

    world = bpy.data.worlds.new("LB_Audit_World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.008,
        0.012,
        0.018,
        1.0,
    )
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.28
    bpy.context.scene.world = world

    lights = (
        ("Key", (1.35, -1.25, 1.75), 1450.0, 0.85),
        ("Fill", (-1.30, -0.55, 0.95), 900.0, 1.05),
        ("Rim", (0.30, 1.45, 1.40), 1200.0, 0.75),
    )
    for name, normalized_offset, energy, normalized_size in lights:
        data = bpy.data.lights.new(f"LB_Audit_{name}", "AREA")
        # Scale photometric power with the candidate envelope so a Meshy file
        # authored at centimetre scale is not blown out relative to the metre
        # scale texture/generate files.
        data.energy = energy * max((span * span) / 4.0, 0.005)
        data.shape = "DISK"
        data.size = span * normalized_size
        light = bpy.data.objects.new(f"LB_Audit_{name}", data)
        bpy.context.scene.collection.objects.link(light)
        light.location = center + Vector(normalized_offset) * span
        aim(light, center)

    camera_data = bpy.data.cameras.new("LB_Audit_Camera")
    camera_data.lens = 56.0
    camera = bpy.data.objects.new("LB_Audit_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    return center, dimensions, span, camera


def render_views(
    output: Path,
    center: Vector,
    dimensions: Vector,
    span: float,
    camera: bpy.types.Object,
    prefix: str,
) -> list[str]:
    focus = Vector((center.x, center.y, center.z + dimensions.z * 0.04))
    views = {
        "isometric": Vector((1.55, -1.85, 1.15)) * span,
        "front": Vector((0.0, -2.70, 0.20)) * span,
        "side": Vector((2.70, 0.0, 0.20)) * span,
        "top": Vector((0.0, -0.01, 3.05)) * span,
    }
    rendered: list[str] = []
    for name, offset in views.items():
        camera.location = focus + offset
        aim(camera, focus)
        target = output / f"{prefix}_{name}.png"
        bpy.context.scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(target))
    return rendered


def assign_fallback_materials(meshes: list[bpy.types.Object]) -> None:
    fallback = create_material(
        "LB_Audit_Fallback_Cream", (0.72, 0.68, 0.56, 1.0), 0.16, 0.42
    )
    for obj in meshes:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(fallback)


def assign_segmentation_palette(meshes: list[bpy.types.Object]) -> None:
    palette = (
        (0.84, 0.18, 0.16, 1.0),
        (0.15, 0.55, 0.92, 1.0),
        (0.16, 0.76, 0.38, 1.0),
        (0.92, 0.62, 0.12, 1.0),
        (0.63, 0.28, 0.88, 1.0),
        (0.12, 0.76, 0.76, 1.0),
        (0.92, 0.30, 0.62, 1.0),
        (0.70, 0.74, 0.18, 1.0),
        (0.40, 0.46, 0.92, 1.0),
        (0.90, 0.44, 0.14, 1.0),
        (0.18, 0.70, 0.60, 1.0),
        (0.78, 0.24, 0.36, 1.0),
    )
    for index, obj in enumerate(meshes):
        material = create_material(
            f"LB_Audit_Part_{index:02d}", palette[index % len(palette)], 0.08, 0.40
        )
        obj.data.materials.clear()
        obj.data.materials.append(material)


def render_part_catalog(
    output: Path,
    meshes: list[bpy.types.Object],
    low: Vector,
    high: Vector,
    camera: bpy.types.Object,
) -> str:
    """Render a labelled, scale-preserving front catalogue of segmented parts."""
    span = max(high - low)
    columns = 5
    rows = math.ceil(len(meshes) / columns)
    cell_width = span * 1.18
    cell_height = span * 1.12
    originals = {obj.name: obj.matrix_world.copy() for obj in meshes}
    text_material = create_material(
        "LB_Audit_Catalog_Label", (0.92, 0.96, 1.0, 1.0), 0.0, 0.34
    )
    for index, obj in enumerate(meshes):
        row = index // columns
        column = index % columns
        target = Vector(
            (
                (column - (columns - 1) * 0.5) * cell_width,
                0.0,
                ((rows - 1) * 0.5 - row) * cell_height,
            )
        )
        part_low, part_high = world_bounds(obj)
        delta = target - (part_low + part_high) * 0.5
        obj.matrix_world.translation += delta

        font_curve = bpy.data.curves.new(f"LB_Audit_Label_{index:02d}", "FONT")
        font_curve.body = obj.name.replace("model_part", "part ")
        font_curve.align_x = "CENTER"
        font_curve.align_y = "CENTER"
        font_curve.size = span * 0.075
        font_curve.extrude = 0.0
        label = bpy.data.objects.new(f"LB_Audit_Label_{index:02d}", font_curve)
        bpy.context.scene.collection.objects.link(label)
        label.location = target + Vector((0.0, -span * 0.22, cell_height * 0.40))
        label.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        font_curve.materials.append(text_material)

    for obj in bpy.context.scene.objects:
        if obj.name == "LB_Audit_Floor":
            obj.hide_render = True
    grid_width = columns * cell_width
    grid_height = rows * cell_height
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = max(grid_height * 1.12, grid_width * 0.75)
    camera.location = Vector((0.0, -grid_width * 1.1, 0.0))
    # Bias the catalogue framing upward so labels above the first row remain
    # visible without wasting the larger margin below the last row.
    aim(camera, Vector((0.0, 0.0, cell_height * 0.25)))
    target_path = output / "03_part_catalog_front.png"
    bpy.context.scene.render.filepath = str(target_path)
    bpy.ops.render.render(write_still=True)
    camera.data.type = "PERSP"
    for obj in meshes:
        obj.matrix_world = originals[obj.name]
    return str(target_path)


def main() -> None:
    source, output, stage_label = parse_args()
    if not source.is_file() or source.suffix.lower() != ".blend":
        raise RuntimeError(f"BLEND input missing or invalid: {source}")
    output.mkdir(parents=True, exist_ok=True)
    source_bytes_before = source.stat().st_size
    source_hash_before = sha256(source)

    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
    bpy.context.view_layer.update()
    meshes = sorted(
        (obj for obj in bpy.context.scene.objects if obj.type == "MESH"),
        key=lambda obj: obj.name,
    )
    if not meshes:
        raise RuntimeError("Candidate has no mesh objects")
    armatures = sorted(
        (obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"),
        key=lambda obj: obj.name,
    )
    mesh_records = [mesh_record(obj) for obj in meshes]
    low, high = combined_bounds(meshes)
    dimensions = high - low
    source_materials = sorted(
        {material for obj in meshes for material in obj.data.materials if material},
        key=lambda material: material.name,
    )
    source_images = sorted(bpy.data.images, key=lambda image: image.name)
    actions = sorted(bpy.data.actions, key=lambda action: action.name)

    assign_fallback_materials(meshes)
    center, render_dimensions, span, camera = add_render_context(low, high)
    renders = render_views(
        output, center, render_dimensions, span, camera, "01_material"
    )
    if len(meshes) > 1:
        assign_segmentation_palette(meshes)
        renders.extend(
            render_views(output, center, render_dimensions, span, camera, "02_parts")
        )
        renders.append(render_part_catalog(output, meshes, low, high, camera))

    unique_origins = {
        tuple(round(float(value), 8) for value in obj.matrix_world.translation)
        for obj in meshes
    }
    payload = {
        "$schema": "lineboss/audit/meshy-spot-welder-blend-v002/v1",
        "stage_label": stage_label,
        "source": str(source),
        "source_bytes_before": source_bytes_before,
        "source_sha256_before": source_hash_before,
        "blender_version": bpy.app.version_string,
        "scene_name": bpy.context.scene.name,
        "scene_unit_system": bpy.context.scene.unit_settings.system,
        "scene_unit_scale_length": bpy.context.scene.unit_settings.scale_length,
        "scene_frame_start": bpy.context.scene.frame_start,
        "scene_frame_end": bpy.context.scene.frame_end,
        "source_object_count": len(
            [obj for obj in bpy.context.scene.objects if not obj.name.startswith("LB_Audit_")]
        ),
        "mesh_object_count": len(meshes),
        "mesh_object_names": [obj.name for obj in meshes],
        "unique_mesh_origin_count": len(unique_origins),
        "all_mesh_origins_coincident": len(meshes) > 1 and len(unique_origins) == 1,
        "mesh_origins": [list(origin) for origin in sorted(unique_origins)],
        "root_object_names": sorted(
            obj.name
            for obj in meshes
            if obj.parent is None
        ),
        "envelope_min": rounded(low),
        "envelope_max": rounded(high),
        "envelope_dimensions": rounded(dimensions),
        "envelope_diagonal": round(float(dimensions.length), 6),
        "total_vertices": sum(record["vertices"] for record in mesh_records),
        "total_edges": sum(record["edges"] for record in mesh_records),
        "total_polygons": sum(record["polygons"] for record in mesh_records),
        "total_triangles_after_triangulation": sum(
            record["triangles_after_triangulation"] for record in mesh_records
        ),
        "total_edge_connected_islands": sum(
            record["edge_connected_island_count"] for record in mesh_records
        ),
        "meshes": mesh_records,
        "material_count": len(source_materials),
        "materials": [material_record(material) for material in source_materials],
        "image_count": len(source_images),
        "images": [
            {
                "name": image.name,
                "size": list(image.size),
                "packed": bool(image.packed_file),
                "filepath": image.filepath,
                "filepath_resolved": bpy.path.abspath(image.filepath),
                "source": image.source,
                "colorspace": image.colorspace_settings.name,
            }
            for image in source_images
        ],
        "armature_count": len(armatures),
        "armatures": [armature_record(obj) for obj in armatures],
        "action_count": len(actions),
        "actions": [
            {
                "name": action.name,
                "frame_range": rounded(action.frame_range),
                "slot_count": len(action.slots),
            }
            for action in actions
        ],
        "scene_markers": [
            {"name": marker.name, "frame": marker.frame}
            for marker in bpy.context.scene.timeline_markers
        ],
        "renders": renders,
    }
    source_bytes_after = source.stat().st_size
    source_hash_after = sha256(source)
    payload["source_bytes_after"] = source_bytes_after
    payload["source_sha256_after"] = source_hash_after
    payload["source_unchanged"] = (
        source_bytes_before == source_bytes_after
        and source_hash_before == source_hash_after
    )
    report = output / "audit.json"
    report.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("LINE_BOSS_MESHY_SPOT_WELDER_BLEND_V002_AUDIT_PASS", report)


if __name__ == "__main__":
    main()
