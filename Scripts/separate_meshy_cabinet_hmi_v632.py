import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector


SPLIT_X = 0.225


def bounds(objects):
    corners = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    lo = Vector(tuple(min(c[i] for c in corners) for i in range(3)))
    hi = Vector(tuple(max(c[i] for c in corners) for i in range(3)))
    return lo, hi


def center_of(obj):
    lo, hi = bounds([obj])
    return (lo + hi) * 0.5


def join_group(objects, name):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = max(objects, key=lambda obj: len(obj.data.polygons))
    bpy.ops.object.join()
    result = bpy.context.object
    result.name = name
    result.data.name = name
    return result


def bottom_center_origin(obj):
    lo, hi = bounds([obj])
    origin = Vector(((lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5, lo.z))
    cursor = bpy.context.scene.cursor
    cursor.location = origin
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    obj.location -= origin


def export_glb(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_materials="EXPORT",
    )


def material_summary(obj):
    images = set()
    for slot in obj.material_slots:
        material = slot.material
        if material and material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    images.add(node.image.name)
    return {
        "materials": [slot.material.name for slot in obj.material_slots if slot.material],
        "images": sorted(images),
    }


def render_asset(obj, output):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    lo, hi = bounds([obj])
    center = (lo + hi) * 0.5
    extent = max(hi - lo)

    bpy.ops.mesh.primitive_plane_add(size=extent * 5, location=(center.x, center.y, lo.z - extent * 0.006))
    floor = bpy.context.object
    floor.name = "StudioFloor"
    floor_mat = bpy.data.materials.get("StudioFloorMaterial") or bpy.data.materials.new("StudioFloorMaterial")
    floor_mat.diffuse_color = (0.055, 0.065, 0.075, 1.0)
    floor_mat.metallic = 0.0
    floor_mat.roughness = 0.72
    floor.data.materials.append(floor_mat)

    camera_data = bpy.data.cameras.new("StudioCamera")
    camera = bpy.data.objects.new("StudioCamera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = center + Vector((extent * 1.35, -extent * 1.7, extent * 0.9))
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.lens = 58

    def area(name, location, energy, size, colour):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = colour
        light = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(light)
        light.location = location
        light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
        return light

    key = area("Key", center + Vector((extent * 1.3, -extent * 1.2, extent * 1.8)), 1500, extent * 1.2, (1.0, 0.92, 0.82))
    fill = area("Fill", center + Vector((-extent * 1.6, -extent * 0.6, extent * 0.9)), 900, extent * 1.5, (0.72, 0.84, 1.0))
    rim = area("Rim", center + Vector((0.0, extent * 1.5, extent * 1.5)), 1200, extent, (0.82, 0.92, 1.0))

    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.camera = camera
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("StudioWorld")
    scene.world.color = (0.025, 0.035, 0.055)
    scene.view_settings.look = "AgX - Medium High Contrast"
    bpy.ops.render.render(write_still=True)

    bpy.data.objects.remove(floor, do_unlink=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    for light in (key, fill, rim):
        bpy.data.objects.remove(light, do_unlink=True)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    source = Path(args[0])
    output_dir = Path(args[1])
    output_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one Meshy mesh, found {len(meshes)}")

    bpy.context.view_layer.objects.active = meshes[0]
    meshes[0].select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    loose = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    cabinet_parts = [obj for obj in loose if center_of(obj).x < SPLIT_X]
    hmi_parts = [obj for obj in loose if center_of(obj).x >= SPLIT_X]
    if len(cabinet_parts) != 440 or len(hmi_parts) != 80:
        raise RuntimeError(f"Unexpected grouping: cabinet={len(cabinet_parts)}, hmi={len(hmi_parts)}")

    cabinet = join_group(cabinet_parts, "SM_CA_Factory_ElectricalCabinet_MeshyMaster_v632")
    hmi = join_group(hmi_parts, "SM_CA_Factory_OperatorHMI_MeshyMaster_v632")
    bottom_center_origin(cabinet)
    bottom_center_origin(hmi)

    cabinet_glb = output_dir / "SM_CA_Factory_ElectricalCabinet_MeshyMaster_v632.glb"
    hmi_glb = output_dir / "SM_CA_Factory_OperatorHMI_MeshyMaster_v632.glb"
    export_glb(cabinet, cabinet_glb)
    export_glb(hmi, hmi_glb)

    render_asset(cabinet, output_dir / "SM_CA_Factory_ElectricalCabinet_MeshyMaster_v632.png")
    render_asset(hmi, output_dir / "SM_CA_Factory_OperatorHMI_MeshyMaster_v632.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(output_dir / "CA_Factory_Cabinet_HMI_MeshyMasters_v632.blend"))

    manifest = {
        "source": str(source),
        "source_preserved": True,
        "split_axis": "X",
        "split_threshold_source_units": SPLIT_X,
        "assets": [
            {
                "name": cabinet.name,
                "loose_parts": 440,
                "vertices": len(cabinet.data.vertices),
                "triangles": sum(len(poly.vertices) - 2 for poly in cabinet.data.polygons),
                "glb": str(cabinet_glb),
                **material_summary(cabinet),
            },
            {
                "name": hmi.name,
                "loose_parts": 80,
                "vertices": len(hmi.data.vertices),
                "triangles": sum(len(poly.vertices) - 2 for poly in hmi.data.polygons),
                "glb": str(hmi_glb),
                **material_summary(hmi),
            },
        ],
        "status": "SOURCE_MASTERS_ONLY__NOT_UNREAL_READY__OPTIMIZATION_COLLISION_AND_VISUAL_GATES_OPEN",
    }
    (output_dir / "manifest_v632.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"LB_CABINET_HMI_OUTPUT={output_dir}")


if __name__ == "__main__":
    main()
