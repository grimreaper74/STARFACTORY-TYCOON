"""Read-only Blender review renderer for generic part-segmentation sources."""

import argparse
import colorsys
import os
import sys

import bpy
from mathutils import Vector


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    bpy.ops.wm.open_mainfile(filepath=args.source)
    meshes = sorted((obj for obj in bpy.context.scene.objects if obj.type == "MESH"), key=lambda obj: obj.name)
    for index, obj in enumerate(meshes):
        material = bpy.data.materials.new(f"AuditPart_{index:03d}")
        rgb = colorsys.hsv_to_rgb((index * 0.61803398875) % 1.0, 0.58, 0.82)
        material.diffuse_color = (*rgb, 1.0)
        obj.data.materials.clear()
        obj.data.materials.append(material)
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    center = (minimum + maximum) * 0.5
    span = max(maximum - minimum)
    bpy.ops.object.light_add(type="AREA", location=center + Vector((-span, -span, span * 1.6)))
    key = bpy.context.object
    key.data.energy = 1000
    key.data.size = span * 2.2
    point_at(key, center)
    bpy.ops.object.light_add(type="AREA", location=center + Vector((span * 1.5, span, span)))
    fill = bpy.context.object
    fill.data.energy = 550
    fill.data.size = span * 1.8
    point_at(fill, center)
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.location = center + Vector((span * 2.0, -span * 2.55, span * 1.45))
    camera.data.lens = 58
    point_at(camera, center)
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = args.output
    scene.world.color = (0.04, 0.04, 0.04)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
