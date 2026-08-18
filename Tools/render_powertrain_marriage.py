"""Render the marriage station in Blender so it can be reviewed without Unreal.

Per the owner's 2026-08-18 preference: Blender answers "does this model look right?"
in seconds, where the Unreal round trip costs several minutes and two editor launches.
Rebuilds the mesh from the authoring script, then sets a three-quarter camera, a key
and fill light and a ground plane, and writes a PNG.
"""
import os
import runpy
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PNG = (r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
           r"/SourceAssets/Candidate/AssemblyShop/PowertrainMarriage_v001"
           r"/SM_LB_Assembly_PowertrainMarriage_v001_preview.png")

# Build the geometry by running the authoring script in this same Blender session.
runpy.run_path(os.path.join(HERE, "build_powertrain_marriage.py"),
               run_name="__main__")

# Ground plane so the machine reads as standing on a floor, not floating.
bpy.ops.mesh.primitive_plane_add(size=30.0, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "PreviewFloor"
mat = bpy.data.materials.new("MAT_PreviewFloor")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.20, 0.20, 0.19, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
floor.data.materials.append(mat)

# Three-quarter view: high enough to read the deck layout, low enough to show height.
cam_data = bpy.data.cameras.new("PreviewCam")
cam_data.lens = 42.0
cam = bpy.data.objects.new("PreviewCam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (10.5, -9.0, 6.4)
cam.rotation_euler = (1.09, 0.0, 0.86)
bpy.context.scene.camera = cam

key = bpy.data.objects.new(
    "Key", bpy.data.lights.new("KeyData", type="AREA"))
key.data.energy = 4000.0
key.data.size = 12.0
key.location = (7.0, -7.0, 9.0)
key.rotation_euler = (0.85, 0.0, 0.8)
bpy.context.collection.objects.link(key)

fill = bpy.data.objects.new(
    "Fill", bpy.data.lights.new("FillData", type="AREA"))
fill.data.energy = 1200.0
fill.data.size = 16.0
fill.location = (-8.0, 5.0, 7.0)
fill.rotation_euler = (1.0, 0.0, -2.2)
bpy.context.collection.objects.link(fill)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("PreviewWorld")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0

os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
scene.render.filepath = OUT_PNG
bpy.ops.render.render(write_still=True)
print("RENDERED", OUT_PNG)
