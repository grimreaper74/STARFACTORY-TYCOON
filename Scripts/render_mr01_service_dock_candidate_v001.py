"""Render fixed visual-review views of the MR01 service/tool dock source."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def material(name: str, rgba: tuple[float, float, float, float], metallic: float, roughness: float) -> bpy.types.Material:
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.use_nodes = True
    bsdf = result.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return result


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area(name: str, location: tuple[float, float, float], energy: float, size: float,
         target: tuple[float, float, float], colour: tuple[float, float, float]) -> None:
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = colour
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)
    look_at(obj, target)


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if not args:
        raise SystemExit("Output directory required")
    output = Path(args[0]).resolve()
    output.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass

    world = scene.world or bpy.data.worlds.new("MR01_Dock_ReviewWorld")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.028, 0.032, 0.035, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45

    floor_mat = material("M_CA_Review_SealedConcrete", (0.12, 0.13, 0.135, 1.0), 0.02, 0.74)
    bpy.ops.mesh.primitive_plane_add(size=14.0, location=(0.0, 1.0, -0.012))
    floor = bpy.context.object
    floor.name = "STAGE_SealedConcrete"
    floor.data.materials.append(floor_mat)

    area("STAGE_Key", (-3.2, -2.2, 5.0), 1150.0, 4.0, (0.0, 1.35, 0.8), (0.88, 0.94, 1.0))
    area("STAGE_Fill", (4.0, -0.5, 3.2), 850.0, 3.2, (0.0, 1.35, 0.8), (1.0, 0.78, 0.55))
    area("STAGE_Top", (0.0, 2.0, 5.5), 1050.0, 3.5, (0.0, 1.3, 0.6), (0.82, 0.9, 1.0))
    area("STAGE_Rim", (-4.5, 3.0, 2.7), 700.0, 2.5, (0.0, 1.4, 1.0), (0.45, 0.7, 1.0))

    camera_data = bpy.data.cameras.new("CAM_MR01_DockReview")
    camera_data.lens = 52.0
    camera = bpy.data.objects.new("CAM_MR01_DockReview", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera

    views = {
        "01_mr01_dock_front_oblique_v001.png": ((3.8, -4.5, 2.7), (0.0, 1.35, 0.78), 52.0),
        "02_mr01_dock_front_v001.png": ((0.0, -5.4, 1.55), (0.0, 1.35, 0.78), 58.0),
        "03_mr01_dock_tool_side_v001.png": ((4.4, -1.5, 2.35), (0.45, 1.45, 0.85), 56.0),
        "04_mr01_dock_consumables_side_v001.png": ((-4.4, -1.5, 2.35), (-0.45, 1.45, 0.85), 56.0),
    }
    for filename, (position, target, lens) in views.items():
        camera.location = position
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(output / filename)
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {scene.render.filepath}")

    # Separate deterministic service-open evidence; source default remains closed.
    rack_pivot = bpy.data.objects.get("PVT_DockToolRackDoor")
    waste_pivot = bpy.data.objects.get("PVT_DockWasteDrawer")
    calibration_pivot = bpy.data.objects.get("PVT_DockCalibrationProbe")
    if rack_pivot and waste_pivot and calibration_pivot:
        rack_pivot.rotation_euler.z = math.radians(92.0)
        waste_pivot.location.x -= 0.45
        calibration_pivot.location.y -= 0.18
        service_views = {
            "05_mr01_dock_service_open_v001.png": ((4.5, -1.9, 2.3), (0.5, 1.45, 0.8), 52.0),
            "06_mr01_dock_tool_rack_open_v001.png": ((3.2, -0.1, 1.75), (0.82, 1.55, 0.92), 62.0),
        }
        for filename, (position, target, lens) in service_views.items():
            camera.location = position
            camera.data.lens = lens
            look_at(camera, target)
            scene.render.filepath = str(output / filename)
            bpy.ops.render.render(write_still=True)
            print(f"Rendered {scene.render.filepath}")


if __name__ == "__main__":
    main()
