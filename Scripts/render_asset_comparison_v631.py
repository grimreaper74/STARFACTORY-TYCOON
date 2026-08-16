import bpy
import math
import sys
from pathlib import Path
from mathutils import Vector


def import_asset(path: Path):
    suffix = path.suffix.lower()
    if suffix in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif suffix == ".fbx":
        bpy.ops.wm.fbx_import(filepath=str(path))
    elif suffix == ".blend":
        with bpy.data.libraries.load(str(path), link=False) as (src, dst):
            dst.objects = src.objects
        for obj in dst.objects:
            if obj is not None:
                bpy.context.scene.collection.objects.link(obj)
    else:
        raise RuntimeError(f"Unsupported source: {path}")


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :]
    source = Path(argv[0])
    output = Path(argv[1])
    colour_mode = argv[2].upper() if len(argv) > 2 else "MATERIAL"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_asset(source)

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh objects in {source}")

    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins = Vector(tuple(min(c[i] for c in corners) for i in range(3)))
    maxs = Vector(tuple(max(c[i] for c in corners) for i in range(3)))
    center = (mins + maxs) * 0.5
    extent = max(maxs - mins)

    # Neutral presentation floor; source meshes and materials remain untouched.
    bpy.ops.mesh.primitive_plane_add(size=extent * 5, location=(center.x, center.y, mins.z - extent * 0.012))
    floor = bpy.context.object
    floor_mat = bpy.data.materials.new("ComparisonFloor")
    floor_mat.diffuse_color = (0.055, 0.065, 0.075, 1.0)
    floor_mat.metallic = 0.05
    floor_mat.roughness = 0.72
    floor.data.materials.append(floor_mat)

    camera_data = bpy.data.cameras.new("ComparisonCamera")
    camera = bpy.data.objects.new("ComparisonCamera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = center + Vector((extent * 1.45, -extent * 1.75, extent * 0.92))
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.lens = 62
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.studio_light = "paint.sl"
    scene.display.shading.color_type = colour_mode
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.curvature_ridge_factor = 1.7
    scene.display.shading.curvature_valley_factor = 1.3
    scene.display.shading.background_type = "WORLD"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("ComparisonWorld")
    scene.world.color = (0.012, 0.015, 0.02)
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print(f"LB_COMPARISON_RENDER={output}")


if __name__ == "__main__":
    main()
