"""Read-only renderer for the PR005 v012 Blender art-review derivative."""
import bpy
import math
import os
from mathutils import Vector


PROJECT = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
OUT = os.path.join(PROJECT, "SourceAssets", "Candidate", "PressShop", "PR005", "ArtSkin_v012_ValidatedDetailDressCorrected", "Renders")


def material(name, colour, roughness=0.55):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*colour, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    return mat


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_stage(scene):
    stage = bpy.data.collections.new("TEMP_PR005_V012_RENDER_STAGE")
    scene.collection.children.link(stage)
    floor_mat = material("TEMP_PR005_V012_Floor", (0.56, 0.56, 0.53), 0.74)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.04))
    floor = bpy.context.object
    floor.name = "TEMP_PR005_V012_Floor"
    floor.data.materials.append(floor_mat)
    for coll in list(floor.users_collection):
        coll.objects.unlink(floor)
    stage.objects.link(floor)
    for name, loc, energy, size, col in (
        ("TEMP_Key", (-9, 8, 12), 2000, 6.0, (1.0, 0.97, 0.91)),
        ("TEMP_Fill", (8, 5, 8), 1450, 5.0, (0.80, 0.90, 1.0)),
        ("TEMP_Back", (0, -9, 9), 1650, 5.0, (1.0, 0.88, 0.70)),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, col
        light = bpy.data.objects.new(name, data)
        stage.objects.link(light)
        light.location = loc
        aim(light, (0, 0, 1.6))
    cam_data = bpy.data.cameras.new("TEMP_PR005_V012_REVIEW_CAMERA")
    cam_data.type, cam_data.lens = "ORTHO", 50
    camera = bpy.data.objects.new("TEMP_PR005_V012_REVIEW_CAMERA", cam_data)
    stage.objects.link(camera)
    scene.camera = camera
    return camera


def set_core_visible(value):
    for obj in bpy.context.scene.objects:
        collections = {coll.name for coll in obj.users_collection}
        is_core = (obj.name.startswith("CTX_") or any(name.startswith(("00_", "10_", "20_", "25_", "30_", "40_")) for name in collections))
        if is_core:
            obj.hide_render = not value


def point(camera, location, target, ortho):
    camera.location = location
    camera.data.ortho_scale = ortho
    aim(camera, target)


def render(scene, camera, name, pose):
    point(camera, *pose)
    scene.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    print("RENDERED|" + scene.render.filepath)


def main():
    os.makedirs(OUT, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.035, 0.042, 0.045)
    for obj in scene.objects:
        if obj.name.startswith("CLR_") or obj.name in {"RenderFloor", "STAGE_PR005_Floor"}:
            obj.hide_render = True
        if obj.type == "LIGHT":
            obj.hide_render = True
    camera = add_stage(scene)
    set_core_visible(False)
    views = {
        "01_PR005_v012_SkinOnly_Front.png": ((0, 16, 4.0), (0, 0, 1.65), 12.0),
        "02_PR005_v012_SkinOnly_Rear.png": ((0, -16, 4.0), (0, 0, 1.65), 12.0),
        "03_PR005_v012_SkinOnly_OperatorSide.png": ((-16, 0, 3.8), (0, 0, 1.65), 12.0),
        "04_PR005_v012_SkinOnly_UtilitiesSide.png": ((16, 0, 3.8), (0, 0, 1.65), 12.0),
        "05_PR005_v012_SkinOnly_ThreeQuarter.png": ((-12, 12, 8.5), (0, 0, 1.65), 13.0),
    }
    for name, pose in views.items():
        render(scene, camera, name, pose)
    set_core_visible(True)
    render(scene, camera, "06_PR005_v012_SkinOverEngineering_Diagnostic.png", ((-12, 12, 8.5), (0, 0, 1.65), 13.0))
    print("SOURCE_NOT_SAVED")


if __name__ == "__main__":
    main()
