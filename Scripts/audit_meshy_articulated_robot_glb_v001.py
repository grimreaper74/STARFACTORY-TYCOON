"""Read-only geometry, articulation and rendered-view audit for a Meshy GLB."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def args() -> tuple[Path, Path]:
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(values) != 2:
        raise RuntimeError("usage: -- <source.glb> <output-directory>")
    return Path(values[0]).resolve(), Path(values[1]).resolve()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def rounded(values) -> list[float]:
    return [round(float(value), 6) for value in values]


def world_bounds(obj) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return low, high


def mesh_record(obj) -> dict:
    mesh = obj.data
    low, high = world_bounds(obj)
    triangle_count = sum(max(0, len(polygon.vertices) - 2) for polygon in mesh.polygons)
    face_sizes: dict[str, int] = {}
    for polygon in mesh.polygons:
        key = str(len(polygon.vertices))
        face_sizes[key] = face_sizes.get(key, 0) + 1
    return {
        "name": obj.name,
        "data_name": mesh.name,
        "parent": obj.parent.name if obj.parent else None,
        "parent_type": obj.parent_type,
        "hide_render": bool(obj.hide_render),
        "hide_viewport": bool(obj.hide_viewport),
        "visible_camera": bool(obj.visible_camera),
        "location_m": rounded(obj.location),
        "rotation_euler_rad": rounded(obj.rotation_euler),
        "scale": rounded(obj.scale),
        "world_origin_m": rounded(obj.matrix_world.translation),
        "world_bounds_min_m": rounded(low),
        "world_bounds_max_m": rounded(high),
        "world_dimensions_m": rounded(high - low),
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "polygons": len(mesh.polygons),
        "triangles_after_triangulation": triangle_count,
        "face_vertex_counts": face_sizes,
        "uv_layers": [layer.name for layer in mesh.uv_layers],
        "color_attributes": [attribute.name for attribute in mesh.color_attributes],
        "material_slots": [slot.material.name if slot.material else None
                           for slot in obj.material_slots],
        "modifiers": [{"name": modifier.name, "type": modifier.type}
                      for modifier in obj.modifiers],
        "shape_keys": ([key.name for key in mesh.shape_keys.key_blocks]
                       if mesh.shape_keys else []),
        "vertex_groups": [group.name for group in obj.vertex_groups],
    }


def material_record(material) -> dict:
    images = []
    node_types = []
    if material.use_nodes and material.node_tree:
        for node in material.node_tree.nodes:
            node_types.append(node.bl_idname)
            if node.type == "TEX_IMAGE" and node.image:
                images.append(node.image.name)
    return {
        "name": material.name,
        "use_nodes": bool(material.use_nodes),
        "blend_method": getattr(material, "surface_render_method", None),
        "node_types": node_types,
        "images": images,
    }


def add_render_context(low: Vector, high: Vector):
    center = (low + high) * 0.5
    span = max(high - low)

    bpy.ops.mesh.primitive_plane_add(size=span * 5.0,
                                     location=(center.x, center.y, low.z - span * 0.012))
    floor = bpy.context.object
    floor.name = "LB_Audit_Floor"
    floor_material = bpy.data.materials.new("LB_Audit_Floor_Material")
    floor_material.diffuse_color = (0.035, 0.045, 0.055, 1.0)
    floor_material.metallic = 0.05
    floor_material.roughness = 0.72
    floor.data.materials.append(floor_material)

    world = bpy.data.worlds.new("LB_Audit_World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.012, 0.016, 0.022, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.32
    bpy.context.scene.world = world

    for name, offset, energy, size in (
        ("Key", (span * 1.4, -span * 1.3, span * 1.9), 1_600.0, span * 0.9),
        ("Fill", (-span * 1.5, -span * 0.5, span * 1.0), 950.0, span * 1.1),
        ("Rim", (0.0, span * 1.5, span * 1.5), 1_250.0, span * 0.8),
    ):
        data = bpy.data.lights.new(f"LB_Audit_{name}", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(f"LB_Audit_{name}", data)
        bpy.context.scene.collection.objects.link(light)
        light.location = center + Vector(offset)
        light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()

    camera_data = bpy.data.cameras.new("LB_Audit_Camera")
    camera_data.lens = 58.0
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
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    return center, span, camera


def render_views(output: Path, center: Vector, span: float, camera) -> list[str]:
    views = {
        "01_isometric": Vector((span * 1.45, -span * 1.75, span * 1.15)),
        "02_front": Vector((0.0, -span * 2.2, span * 0.30)),
        "03_side": Vector((span * 2.2, 0.0, span * 0.30)),
        "04_top": Vector((0.0, -span * 0.01, span * 2.5)),
    }
    rendered = []
    for name, offset in views.items():
        camera.location = center + offset
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        target = output / f"{name}.png"
        bpy.context.scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(target))
    return rendered


def main() -> None:
    source, output = args()
    if not source.is_file() or source.suffix.lower() != ".glb":
        raise RuntimeError(f"GLB input is missing or invalid: {source}")
    output.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    bpy.context.view_layer.update()
    meshes = sorted((obj for obj in bpy.context.scene.objects if obj.type == "MESH"),
                    key=lambda obj: obj.name)
    if not meshes:
        raise RuntimeError("Imported candidate contains no mesh objects")
    records = [mesh_record(obj) for obj in meshes]
    lows, highs = zip(*(world_bounds(obj) for obj in meshes))
    low = Vector(tuple(min(point[index] for point in lows) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in highs) for index in range(3)))

    materials = sorted({material for obj in meshes for material in obj.data.materials if material},
                       key=lambda material: material.name)
    armatures = sorted((obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"),
                       key=lambda obj: obj.name)
    actions = sorted(bpy.data.actions, key=lambda action: action.name)
    center, span, camera = add_render_context(low, high)
    renders = render_views(output, center, span, camera)

    payload = {
        "$schema": "lineboss/audit/meshy-articulated-robot-glb-v001/v1",
        "source": str(source),
        "source_bytes": source.stat().st_size,
        "source_sha256": file_sha256(source),
        "object_count": len(bpy.context.scene.objects),
        "mesh_object_count": len(meshes),
        "armature_count": len(armatures),
        "bone_count": sum(len(obj.data.bones) for obj in armatures),
        "armatures": [
            {
                "name": obj.name,
                "location_m": rounded(obj.location),
                "rotation_euler_rad": rounded(obj.rotation_euler),
                "scale": rounded(obj.scale),
                "bones": [
                    {
                        "name": bone.name,
                        "parent": bone.parent.name if bone.parent else None,
                        "head_local_m": rounded(bone.head_local),
                        "tail_local_m": rounded(bone.tail_local),
                        "use_deform": bool(bone.use_deform),
                    }
                    for bone in obj.data.bones
                ],
            }
            for obj in armatures
        ],
        "action_count": len(actions),
        "animation_actions": [
            {"name": action.name,
             "frame_range": rounded(action.frame_range),
             "fcurve_count": len(action.fcurves),
             "keyframe_count": sum(len(curve.keyframe_points) for curve in action.fcurves)}
            for action in actions
        ],
        "envelope_min_m": rounded(low),
        "envelope_max_m": rounded(high),
        "envelope_size_m": rounded(high - low),
        "total_vertices": sum(record["vertices"] for record in records),
        "total_polygons": sum(record["polygons"] for record in records),
        "total_triangles_after_triangulation": sum(
            record["triangles_after_triangulation"] for record in records),
        "material_count": len(materials),
        "materials": [material_record(material) for material in materials],
        "images": [
            {"name": image.name, "size": list(image.size),
             "packed": bool(image.packed_file), "filepath": image.filepath}
            for image in bpy.data.images if image.name != "Render Result"
        ],
        "meshes": records,
        "renders": renders,
    }
    report = output / "audit.json"
    report.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("LINE_BOSS_MESHY_ARTICULATED_ROBOT_GLB_AUDIT_PASS", report)


if __name__ == "__main__":
    main()
