"""Derive a coil-free Meshy hero press without modifying the approved source.

The source contains one visually confirmed coil-and-cradle loose component.  It
is removed only when its topology signature matches exactly; the separately
authored clean rollers and all other press geometry remain intact.
"""
import hashlib
import json
import shutil
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE_ROOT = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "HeroPressCell_MeshyOneCoil_v002"
SOURCE = SOURCE_ROOT / "HeroPressCell_MeshyOneCoil_v002_Cleaned.blend"
OUT = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "HeroPressCell_MeshyNoCoil_v001"
OUT_BLEND = OUT / "HeroPressCell_MeshyNoCoil_v001_Cleaned.blend"
OUT_FBX = OUT / "Runtime" / "SM_LB_PS_HeroPressCell_MeshyNoCoil_v001.fbx"
OUT_GLB = OUT / "Runtime" / "SM_LB_PS_HeroPressCell_MeshyNoCoil_v001.glb"
OUT_RENDER = OUT / "Evidence" / "hero_press_cell_nocoil_v001_review.png"
OUT_MANIFEST = OUT / "Evidence" / "hero_press_cell_nocoil_cleanup_manifest_v001.json"
BUILD_COPY = OUT / "Build" / "derive_hero_press_cell_no_coil_v001.py"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def components(mesh):
    faces_by_vertex = [[] for _ in mesh.vertices]
    for face_index, face in enumerate(mesh.polygons):
        for vertex_index in face.vertices:
            faces_by_vertex[vertex_index].append(face_index)
    seen, result = set(), []
    for start in range(len(mesh.polygons)):
        if start in seen:
            continue
        seen.add(start)
        pending, faces, vertices = [start], [], set()
        while pending:
            face_index = pending.pop()
            faces.append(face_index)
            for vertex_index in mesh.polygons[face_index].vertices:
                vertices.add(vertex_index)
                for neighbour in faces_by_vertex[vertex_index]:
                    if neighbour not in seen:
                        seen.add(neighbour)
                        pending.append(neighbour)
        points = [mesh.vertices[index].co for index in vertices]
        low = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
        high = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
        result.append({"faces": faces, "low": low, "high": high, "centre": (low + high) * 0.5, "dimensions": high - low})
    return result


def is_confirmed_coil_and_cradle(component):
    """Exact loose-island gate from the read-only v002 topology audit."""
    dim, centre = component["dimensions"], component["centre"]
    return (
        len(component["faces"]) == 556
        and all(abs(actual - expected) <= tolerance for actual, expected, tolerance in zip(dim, (2.208, 2.408, 2.140), (0.02, 0.02, 0.02)))
        and all(abs(actual - expected) <= tolerance for actual, expected, tolerance in zip(centre, (-7.088, 0.988, 2.542), (0.02, 0.02, 0.02)))
    )


def remove_confirmed_coil(body):
    selected = [component for component in components(body.data) if is_confirmed_coil_and_cradle(component)]
    if len(selected) != 1:
        raise RuntimeError("Expected exactly one confirmed coil/cradle island; found %d" % len(selected))
    component = selected[0]
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for face_index in component["faces"]:
        body.data.polygons[face_index].select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="FACE")
    bpy.ops.object.mode_set(mode="OBJECT")
    body.data.update()
    return {
        "triangles": len(component["faces"]),
        "centre_m": [round(value, 4) for value in component["centre"]],
        "dimensions_m": [round(value, 4) for value in component["dimensions"]],
    }


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_review(scene, meshes):
    for obj in list(scene.objects):
        if obj.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)
    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[axis] for point in corners) for axis in range(3)))
    high = Vector(tuple(max(point[axis] for point in corners) for axis in range(3)))
    centre, span = (low + high) * 0.5, max((high - low).length, 0.1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1600, 1000, 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT_RENDER)
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.055, 0.065, 0.075, 1.0)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.35
    bpy.ops.object.camera_add(location=centre + Vector((span * 1.08, -span * 1.48, span * 0.88)))
    camera = bpy.context.object
    camera.data.lens = 54
    look_at(camera, centre + Vector((0.0, 0.0, span * 0.05)))
    scene.camera = camera
    for location, energy, size, colour in (
        (centre + Vector((span * 0.7, -span * 0.9, span * 1.35)), 36000, span * 1.3, (1.0, 0.82, 0.64)),
        (centre + Vector((-span * 1.1, -span * 0.15, span * 0.75)), 16000, span, (0.55, 0.72, 1.0)),
        (centre + Vector((span * 0.25, span * 1.2, span * 1.25)), 44000, span, (1.0, 0.94, 0.82)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy, light.data.shape, light.data.size, light.data.color = energy, "DISK", size, colour
        look_at(light, centre)
    bpy.ops.mesh.primitive_plane_add(size=span * 7.0, location=(centre.x, centre.y, low.z - 0.01))
    floor = bpy.context.object
    floor.name = "ReviewFloor_Temporary"
    material = bpy.data.materials.new("ReviewFloor")
    material.diffuse_color = (0.055, 0.065, 0.075, 1.0)
    floor.data.materials.append(material)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(floor, do_unlink=True)
    for obj in list(scene.objects):
        if obj.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError("Run only against the immutable one-coil v002 source")
    if any(path.exists() for path in (OUT_BLEND, OUT_FBX, OUT_GLB, OUT_MANIFEST)):
        raise RuntimeError("Refusing to overwrite an existing no-coil derivative")
    for folder in (OUT / "Runtime", OUT / "Evidence", OUT / "Build"):
        folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), BUILD_COPY)
    source_hash = sha256(SOURCE)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(meshes) != 2:
        raise RuntimeError("Expected v002 body and clean-rollers meshes, found %d" % len(meshes))
    body = next((obj for obj in meshes if obj.name.endswith("_Body")), None)
    rollers = next((obj for obj in meshes if obj.name.endswith("_CleanRollers")), None)
    if body is None or rollers is None:
        raise RuntimeError("Expected body and clean-rollers names in v002 source")
    source_triangles = sum(len(face.vertices) - 2 for face in body.data.polygons) + sum(len(face.vertices) - 2 for face in rollers.data.polygons)
    removed = remove_confirmed_coil(body)
    body.name = "SM_LB_PS_HeroPressCell_MeshyNoCoil_v001_Body"
    body.data.name = body.name + "_Mesh"
    rollers.name = "SM_LB_PS_HeroPressCell_MeshyNoCoil_v001_CleanRollers"
    rollers.data.name = rollers.name + "_Mesh"
    old_roots = [obj for obj in bpy.context.scene.objects if obj.type == "EMPTY"]
    for root in old_roots:
        if root in {body.parent, rollers.parent}:
            bpy.data.objects.remove(root, do_unlink=True)
    root = bpy.data.objects.new("SM_LB_PS_HeroPressCell_MeshyNoCoil_v001_Root", None)
    bpy.context.scene.collection.objects.link(root)
    body.parent, rollers.parent = root, root
    body.data.calc_loop_triangles()
    rollers.data.calc_loop_triangles()
    render_review(bpy.context.scene, [body, rollers])
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND), check_existing=False)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in (body, rollers, root):
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.export_scene.fbx(filepath=str(OUT_FBX), use_selection=True, object_types={"MESH", "EMPTY"}, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS", bake_space_transform=False, add_leaf_bones=False, use_mesh_modifiers=True, mesh_smooth_type="FACE", path_mode="COPY", embed_textures=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format="GLB", use_selection=True, export_apply=True, export_materials="EXPORT", export_yup=True)
    output_triangles = len(body.data.loop_triangles) + len(rollers.data.loop_triangles)
    manifest = {
        "status": "source-candidate-derived-no-coil-v001; no Unreal map was touched",
        "input_onecoil_v002_blend": {"path": str(SOURCE), "sha256": source_hash},
        "outputs": {"blend": str(OUT_BLEND), "fbx": str(OUT_FBX), "glb": str(OUT_GLB), "review_render": str(OUT_RENDER)},
        "removed_component": removed,
        "geometry": {"input_triangles": source_triangles, "output_triangles": output_triangles, "removed_triangles": source_triangles - output_triangles, "body": body.name, "rollers": rollers.name, "root": root.name},
        "source_unchanged_after_build": sha256(SOURCE) == source_hash,
        "next_gate": "separate Unreal import candidate and in-engine visual review; no production map import.",
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("PRESSSHOP_HERO_NOCOIL_V001_PASS|removed_triangles={}|output_triangles={}".format(source_triangles - output_triangles, output_triangles))


main()
