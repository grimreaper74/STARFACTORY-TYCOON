"""Author the four missing shop models, Blender-native, family conventions.

Owner commission (2026-08-16): the weld closure turntable, the paint ED dip
tunnel, the press certified coil-scale platform and the press scrap baler.
Modelled in metres (1 BU = 1 m, the PR004 family convention), floor pivots at
the origin, brand-named material slots, one FBX per asset. No Meshy, no
external geometry: primitives, bevels and booleans only.
"""
import math
import os
import sys

import bpy

OUT_ROOT = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/SourceAssets/Candidate"

MATERIALS = {}


def material(name, rgba):
    if name in MATERIALS:
        return MATERIALS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.55
    MATERIALS[name] = mat
    return mat


GREEN = ("MAT_CairnwellGreen", (0.047, 0.153, 0.137, 1.0))
CHARCOAL = ("MAT_FoundryCharcoal", (0.055, 0.063, 0.071, 1.0))
STEEL = ("MAT_MachinedSteel", (0.44, 0.46, 0.48, 1.0))
YELLOW = ("MAT_SafetyYellow", (0.83, 0.68, 0.0, 1.0))
RUBBER = ("MAT_DarkRubber", (0.02, 0.02, 0.022, 1.0))


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATERIALS.clear()


def add_box(name, size, location, mat, bevel=0.008):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0] * 0.5, size[1] * 0.5, size[2] * 0.5)
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0.0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    obj.data.materials.append(material(*mat))
    return obj


def add_cylinder(name, radius, depth, location, mat, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=radius, depth=depth, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material(*mat))
    return obj


def export(asset_name, folder):
    directory = os.path.join(OUT_ROOT, folder)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, asset_name + ".fbx")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True,
        apply_scale_options="FBX_SCALE_UNITS",
        object_types={"MESH"}, add_leaf_bones=False,
        bake_space_transform=True)
    print("EXPORTED", path)


# ---------------------------------------------------------------------------
# 1. Weld closure turntable: a two-post panel positioner on a driven deck.
# ---------------------------------------------------------------------------
reset_scene()
add_cylinder("Skirt", 1.40, 0.20, (0, 0, 0.10), CHARCOAL)
add_cylinder("Deck", 1.30, 0.25, (0, 0, 0.325), STEEL)
add_cylinder("DeckRim", 1.32, 0.06, (0, 0, 0.47), YELLOW)
add_cylinder("Hub", 0.30, 0.12, (0, 0, 0.51), CHARCOAL)
for side in (-1.0, 1.0):
    add_box("FixturePost", (0.30, 0.30, 0.95), (side * 0.85, 0.0, 0.925),
        GREEN)
    add_box("FixtureHead", (0.44, 0.20, 0.16), (side * 0.85, 0.0, 1.48),
        STEEL)
    add_box("ClampFinger", (0.10, 0.34, 0.10), (side * 0.85, 0.0, 1.60),
        RUBBER)
add_box("DriveCabinet", (0.45, 0.32, 0.85), (0.0, 1.55, 0.425), GREEN)
add_box("CabinetPanel", (0.34, 0.05, 0.40), (0.0, 1.38, 0.60), CHARCOAL)
export("SM_LB_BodyShop_ClosureTurntable_v001", "WeldShop/ClosureTurntable_v001")

# ---------------------------------------------------------------------------
# 2. Paint ED dip tunnel: drive-through shell over a visible dip basin.
# ---------------------------------------------------------------------------
reset_scene()
# Basin and bath.
add_box("Basin", (7.0, 4.6, 2.2), (0, 0, 1.10), CHARCOAL)
add_box("Bath", (6.6, 4.2, 0.10), (0, 0, 2.16), GREEN, bevel=0.0)
add_box("BasinRim", (7.2, 4.8, 0.12), (0, 0, 2.26), YELLOW)
# Portal frames at each end and the roof gantry the carriers hang from.
for endx in (-4.0, 4.0):
    add_box("PortalLeg", (0.25, 0.25, 5.0), (endx, -2.6, 2.5), GREEN)
    add_box("PortalLeg", (0.25, 0.25, 5.0), (endx, 2.6, 2.5), GREEN)
    add_box("PortalBeam", (0.25, 5.45, 0.30), (endx, 0.0, 5.05), GREEN)
add_box("GantryRail", (8.5, 0.22, 0.28), (0, -1.0, 5.15), STEEL)
add_box("GantryRail", (8.5, 0.22, 0.28), (0, 1.0, 5.15), STEEL)
for hx in (-2.6, -0.9, 0.9, 2.6):
    add_box("HangerFrame", (0.16, 2.3, 0.16), (hx, 0.0, 4.95), CHARCOAL)
    add_box("HangerDrop", (0.12, 0.12, 1.6), (hx, 0.0, 4.05), CHARCOAL)
# Side service platform with rails, and the extraction stacks.
add_box("Platform", (7.4, 0.9, 0.08), (0, 3.05, 2.60), STEEL)
add_box("PlatformRail", (7.4, 0.06, 0.90), (0, 3.48, 3.10), YELLOW)
for lx in (-3.4, 0.0, 3.4):
    add_box("PlatformLeg", (0.14, 0.14, 2.56), (lx, 3.05, 1.28), CHARCOAL)
add_cylinder("Stack", 0.30, 1.6, (-1.6, 1.6, 6.0), STEEL, verts=24)
add_cylinder("Stack", 0.30, 1.6, (1.6, 1.6, 6.0), STEEL, verts=24)
export("SM_LB_Paint_EDDipTunnel_v001", "PaintShop/EDDipTunnel_v001")

# ---------------------------------------------------------------------------
# 3. Press certified coil-scale platform: flush deck, load pads, HMI post.
# ---------------------------------------------------------------------------
reset_scene()
add_box("Deck", (4.0, 3.0, 0.25), (0, 0, 0.125), STEEL)
add_box("DeckBorder", (4.2, 3.2, 0.10), (0, 0, 0.05), YELLOW)
for cx in (-1.7, 1.7):
    for cy in (-1.2, 1.2):
        add_box("LoadCell", (0.30, 0.30, 0.10), (cx, cy, 0.30), CHARCOAL)
add_box("HMIPost", (0.35, 0.35, 1.30), (2.35, -1.35, 0.65), GREEN)
add_box("HMIHead", (0.45, 0.12, 0.35), (2.35, -1.48, 1.35), CHARCOAL)
export("SM_LB_Press_CoilScalePlatform_v001", "PressShop/CoilScale_v001")

# ---------------------------------------------------------------------------
# 4. Press scrap baler: body, hopper, ram housing, discharge, cabinet.
# ---------------------------------------------------------------------------
reset_scene()
add_box("Body", (3.5, 2.2, 2.6), (0, 0, 1.30), CHARCOAL)
add_box("Hopper", (1.6, 1.6, 1.1), (-0.7, 0, 3.10), GREEN)
add_box("HopperRim", (1.75, 1.75, 0.12), (-0.7, 0, 3.62), YELLOW)
add_box("RamHousing", (1.2, 2.24, 1.8), (1.75, 0, 0.90), GREEN)
add_box("Discharge", (1.0, 0.9, 0.8), (2.55, 0, 0.40), STEEL)
add_box("Cabinet", (0.45, 0.30, 1.20), (-1.55, 1.35, 0.60), GREEN)
add_box("WarnStripe", (3.52, 2.22, 0.10), (0, 0, 0.05), YELLOW)
export("SM_LB_Press_ScrapBaler_v001", "PressShop/ScrapBaler_v001")

print("ALL_MODELS_BUILT")
sys.exit(0)
