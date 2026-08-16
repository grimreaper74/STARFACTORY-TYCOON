"""Render CR01 v005 with the retained v014 source robot as fit evidence only."""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        raise SystemExit("Usage: -- retained_cr01_v014.blend output_directory")
    robot_path = Path(args[0]).resolve()
    output = Path(args[1]).resolve()
    output.mkdir(parents=True, exist_ok=True)

    names = [
        "10_LB_RP01_SHARED_STATIC", "11_LB_RP01_SHARED_MOVING", "20_LB_CR01_STATIC",
        "21_LB_CR01_MOVING", "LB_CR01_BUILD",
    ]
    with bpy.data.libraries.load(str(robot_path), link=False) as (source, target):
        target.collections = [name for name in names if name in source.collections]
    for collection in target.collections:
        if collection:
            bpy.context.scene.collection.children.link(collection)
    robot_root = bpy.data.objects.get("ROOT_LB_CR01")
    if not robot_root:
        raise RuntimeError("Retained CR01 v014 root missing")
    robot_root.location = (0.0, 0.0, 0.0)
    robot_root["lb_evidence_only"] = "CR01_V014_SOURCE_AT_V005_ROBOT_CENTRED_CFR"

    floor_mat = bpy.data.materials.get("M_CA_CR01_ReviewConcrete") or bpy.data.materials.new("M_CA_CR01_ReviewConcrete")
    floor_mat.diffuse_color = (0.12, 0.13, 0.135, 1.0)
    floor_mat.use_nodes = True
    floor_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = floor_mat.diffuse_color
    floor_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.74
    bpy.ops.mesh.primitive_plane_add(size=14.0, location=(0.0, 0.8, -0.015))
    bpy.context.object.data.materials.append(floor_mat)

    for name, location, energy, size, colour in (
        ("REVIEW_CR01_Key", (-4.0, -4.0, 5.2), 1400.0, 4.0, (0.86, 0.94, 1.0)),
        ("REVIEW_CR01_Fill", (4.2, -1.0, 3.5), 950.0, 3.2, (1.0, 0.8, 0.58)),
        ("REVIEW_CR01_Top", (0.0, 2.5, 5.4), 1200.0, 3.5, (0.82, 0.9, 1.0)),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = colour
        light = bpy.data.objects.new(name, data)
        light.location = location
        bpy.context.scene.collection.objects.link(light)
        look_at(light, (0.0, 0.7, 0.65))

    camera_data = bpy.data.cameras.new("CAM_CR01_DockV005Review")
    camera = bpy.data.objects.new("CAM_CR01_DockV005Review", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene["lb_review_only"] = True
    scene["lb_promotion_authorized"] = False
    world = scene.world or bpy.data.worlds.new("CR01_DockV005_ReviewWorld")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.025, 0.03, 0.035, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45

    views = {
        "01_cr01_v014_dock_v005_front_oblique.png": ((-4.3, -5.5, 3.25), (0.0, 0.45, 0.65), 52.0),
        "02_cr01_v014_dock_v005_service_side.png": ((4.5, -3.3, 2.65), (0.4, 0.75, 0.68), 55.0),
    }
    for filename, (location, target_location, lens) in views.items():
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target_location)
        scene.render.filepath = str(output / filename)
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {scene.render.filepath}")


if __name__ == "__main__":
    main()
