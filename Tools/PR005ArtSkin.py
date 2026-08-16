"""PR005 non-destructive Cairnwell visual skin review derivative.

Input: immutable v812 engineering Blender source.
Output: separately versioned skin-only review derivative and renders.
Rule: inherited objects are never renamed, transformed, parented, deleted, or modified.
"""

import math
import os

import bpy
from mathutils import Vector


PROJECT = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
OUT_DIR = os.path.join(PROJECT, "SourceAssets", "Candidate", "PressShop", "PR005", "ArtSkin_v001")
OUT_BLEND = os.path.join(OUT_DIR, "PR005_CairnwellVisualSkin_v001.blend")
RENDER_DIR = os.path.join(OUT_DIR, "Renders")
SKIN = "97_PR005_CAIRNWELL_VISUAL_SKIN_V001"
STAGE = "98_PR005_ART_SKIN_REVIEW_STAGE"


def state(obj):
    return (obj.type, obj.parent.name if obj.parent else "", tuple(round(v, 5) for v in obj.location),
            tuple(round(v, 5) for v in obj.rotation_euler), tuple(round(v, 5) for v in obj.scale))


def source_snapshot():
    return {obj.name: state(obj) for obj in bpy.context.scene.objects}


def unchanged(snapshot):
    changed = [name for name, value in snapshot.items() if state(bpy.data.objects[name]) != value]
    if changed:
        raise RuntimeError("Engineering source changed: " + ", ".join(changed))


def coll(name):
    found = bpy.data.collections.get(name)
    if not found:
        found = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(found)
    return found


def move_to(obj, destination):
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    destination.objects.link(obj)


def mat(name, rgb, metallic, roughness):
    item = bpy.data.materials.new(name)
    item.use_nodes = True
    bsdf = item.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return item


def cube(name, loc, dim, material, collection, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dim
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("Folded edge radius", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    move_to(obj, collection)
    return obj


def cyl(name, loc, radius, depth, material, collection, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    modifier = obj.modifiers.new("Machined edge radius", "BEVEL")
    modifier.width = min(radius * 0.12, 0.02)
    modifier.segments = 3
    move_to(obj, collection)
    return obj


def hose(name, points, radius, material, collection):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = radius
    data.bevel_resolution = 3
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, co in zip(spline.bezier_points, points):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def label(name, body, loc, rotation, size, material, collection):
    data = bpy.data.curves.new(name, "FONT")
    data.body = body
    data.align_x = "CENTER"
    data.align_y = "CENTER"
    data.size = size
    data.extrude = 0.006
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    obj.rotation_euler = rotation
    obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def door(name, side, y, skin, mats):
    white, graphite, green, yellow, black, steel, glass = mats
    sx = 2.794 * side
    # A shallow, folded access cassette held inside the engineering 2.8815 m half-width.
    cube(name + "_Outer", (sx, y, 1.72), (0.045, 1.18, 2.46), white, skin, 0.025)
    cube(name + "_Inset", (sx + side * 0.024, y, 1.71), (0.013, 0.87, 1.62), green, skin, 0.018)
    cube(name + "_UpperVent", (sx + side * 0.025, y + 0.39, 2.46), (0.014, 0.44, 0.33), graphite, skin, 0.008)
    # Vent louvers use the common detail-kit profile.
    for offset in (-0.15, -0.05, 0.05, 0.15):
        cube(name + "_Louvre", (sx + side * 0.034, y + 0.39 + offset, 2.46), (0.015, 0.025, 0.20), black, skin, 0.004)
    for z in (1.05, 2.16):
        cyl(name + "_Hinge", (sx + side * 0.035, y - 0.51, z), 0.040, 0.095, graphite, skin, rot=(0, math.pi / 2, 0))
    cube(name + "_Handle", (sx + side * 0.035, y + 0.38, 1.69), (0.018, 0.12, 0.20), black, skin, 0.010)
    cube(name + "_SafetyDoorEdge", (sx + side * 0.036, y - 0.55, 1.70), (0.018, 0.035, 1.66), yellow, skin, 0.004)
    cube(name + "_LowerShadow", (sx + side * 0.028, y, 0.52), (0.018, 1.03, 0.08), graphite, skin, 0.004)


def panel_bay(name, side, y, skin, mats, green_panel=False):
    white, graphite, green, yellow, black, steel, glass = mats
    sx = 2.79 * side
    body = green if green_panel else white
    cube(name + "_Panel", (sx, y, 1.90), (0.042, 1.30, 1.64), body, skin, 0.022)
    cube(name + "_TopFold", (sx + side * 0.025, y, 2.70), (0.015, 1.15, 0.065), graphite, skin, 0.005)
    cube(name + "_LowerFold", (sx + side * 0.025, y, 1.10), (0.015, 1.15, 0.055), graphite, skin, 0.005)
    # Two recessed service labels give repeatable OEM panel language.
    cube(name + "_ServicePlate", (sx + side * 0.026, y - 0.31, 1.90), (0.016, 0.38, 0.20), graphite, skin, 0.009)
    cube(name + "_Gland", (sx + side * 0.027, y + 0.37, 1.72), (0.017, 0.13, 0.13), black, skin, 0.008)


def front_fascia(skin, mats):
    white, graphite, green, yellow, black, steel, glass = mats
    # y = + is process outfeed/front. The surround leaves the threader visibly readable.
    cube("SKIN_PR005_FrontHeader", (0, 5.12, 2.90), (5.48, 0.075, 0.47), graphite, skin, 0.025)
    cube("SKIN_PR005_FrontBrandPlate", (-0.98, 5.165, 2.90), (2.62, 0.018, 0.34), green, skin, 0.010)
    label("SKIN_PR005_FrontBrand", "CAIRNWELL  |  PR005", (-0.98, 5.185, 2.90), (math.radians(90), 0, math.pi), 0.155, white, skin)
    # Glazed process aperture gives a high-detail enclosure character without covering the strip exit.
    cube("SKIN_PR005_FrontProcessGlazing", (1.58, 5.16, 2.88), (1.42, 0.020, 0.29), glass, skin, 0.010)
    for x in (-2.68, -1.95, 1.95, 2.68):
        cube("SKIN_PR005_FrontUpright", (x, 5.13, 1.68), (0.065, 0.065, 2.58), graphite, skin, 0.018)
    cube("SKIN_PR005_FrontLowerPlinth", (0, 5.09, 0.32), (5.54, 0.12, 0.38), graphite, skin, 0.025)
    cube("SKIN_PR005_ThreaderFascia", (0, 4.88, 1.02), (2.58, 0.12, 0.22), graphite, skin, 0.02)
    # Safety yellow is confined to the exposed threader entry edges.
    for x in (-1.20, 1.20):
        cube("SKIN_PR005_ThreaderSafetyEdge", (x, 4.94, 1.04), (0.10, 0.035, 0.20), yellow, skin, 0.006)


def rear_headstock(skin, mats):
    white, graphite, green, yellow, black, steel, glass = mats
    cube("SKIN_PR005_RearHeader", (0, -5.11, 2.86), (5.48, 0.075, 0.53), graphite, skin, 0.025)
    cube("SKIN_PR005_RearHeadstockSkin", (0, -5.07, 1.70), (3.55, 0.095, 2.20), white, skin, 0.025)
    cube("SKIN_PR005_RearHeadstockAccess", (0, -5.125, 1.72), (1.52, 0.018, 1.30), green, skin, 0.018)
    cube("SKIN_PR005_RearServiceManifold", (2.51, -5.125, 1.24), (0.38, 0.026, 0.62), graphite, skin, 0.025)
    for x in (2.38, 2.51, 2.64):
        cyl("SKIN_PR005_RearCoupling", (x, -5.147, 1.24), 0.062, 0.025, steel, skin, rot=(math.pi / 2, 0, 0))
    # Visual-only circular headstock reveal; it does not alter the original mandrel or its pivot.
    cyl("SKIN_PR005_MandrelReveal", (0, -5.15, 1.78), 0.70, 0.024, graphite, skin, rot=(math.pi / 2, 0, 0))
    cyl("SKIN_PR005_MandrelSteelFace", (0, -5.17, 1.78), 0.46, 0.022, steel, skin, rot=(math.pi / 2, 0, 0))
    cube("SKIN_PR005_RearLowerPlinth", (0, -5.09, 0.32), (5.54, 0.12, 0.38), graphite, skin, 0.025)


def roof(skin, mats):
    white, graphite, green, yellow, black, steel, glass = mats
    # Thin roof cassette panels, all below the inherited 3.55m station height.
    for idx, y in enumerate((-4.15, -2.50, -0.85, 0.80, 2.45, 4.10)):
        cube("SKIN_PR005_RoofCassette_%02d" % idx, (0, y, 3.505), (5.40, 1.52, 0.045), white, skin, 0.014)
        cube("SKIN_PR005_RoofFold_%02d" % idx, (0, y - 0.70, 3.525), (5.35, 0.040, 0.035), graphite, skin, 0.005)
    cube("SKIN_PR005_RoofSpine", (0, 0, 3.53), (0.58, 9.72, 0.035), graphite, skin, 0.012)
    cube("SKIN_PR005_RoofServiceHatch", (1.52, -1.75, 3.54), (1.18, 0.95, 0.025), graphite, skin, 0.009)


def services(skin, mats):
    white, graphite, green, yellow, black, steel, glass = mats
    # Utility-side bundle and brackets. All objects stay inside the source half-width.
    for y in (-3.3, -2.35, -1.40, -0.45, 0.50):
        cube("SKIN_PR005_UtilityBracket", (2.80, y, 2.42), (0.055, 0.11, 0.24), graphite, skin, 0.012)
        cyl("SKIN_PR005_CableGland", (2.82, y, 2.26), 0.065, 0.055, black, skin, rot=(0, math.pi / 2, 0))
    hose("SKIN_PR005_Hose_A", [(2.79, -3.35, 2.35), (2.74, -2.65, 2.56), (2.79, -1.55, 2.12), (2.79, -0.42, 2.25)], 0.032, black, skin)
    hose("SKIN_PR005_Hose_B", [(2.79, -2.60, 2.15), (2.74, -1.85, 1.90), (2.79, -0.85, 1.72), (2.79, 0.30, 1.86)], 0.026, black, skin)
    cube("SKIN_PR005_UtilityServiceBox", (2.77, 1.72, 1.46), (0.055, 0.82, 0.92), white, skin, 0.025)
    cube("SKIN_PR005_UtilityServiceBoxDoor", (2.80, 1.72, 1.46), (0.015, 0.55, 0.60), green, skin, 0.013)


def build_skin(skin, mats):
    front_fascia(skin, mats)
    rear_headstock(skin, mats)
    roof(skin, mats)
    services(skin, mats)
    # Deliberately uneven spacing reads as access architecture rather than repeated toy blocks.
    for index, y in enumerate((-3.68, -2.18, -0.58, 1.15, 3.18)):
        if index in (1, 3):
            door("SKIN_PR005_UtilityDoor_%02d" % index, 1, y, skin, mats)
        else:
            panel_bay("SKIN_PR005_UtilityPanel_%02d" % index, 1, y, skin, mats, green_panel=(index == 4))
    for index, y in enumerate((-3.38, -1.76, -0.10, 1.62, 3.34)):
        if index in (0, 3):
            door("SKIN_PR005_OperatorDoor_%02d" % index, -1, y, skin, mats)
        else:
            panel_bay("SKIN_PR005_OperatorPanel_%02d" % index, -1, y, skin, mats, green_panel=(index == 2))


def set_engineering_visible(show):
    for obj in bpy.context.scene.objects:
        if obj.name.startswith("SKIN_PR005") or obj.name.startswith("STAGE_PR005"):
            continue
        obj.hide_render = not show
    # Previous render staging floor is an inherited presentational item; use it in diagnostic only.
    floor = bpy.data.objects.get("RenderFloor")
    if floor:
        floor.hide_render = not show


def stage(scene, stage_collection):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.008, 0.010, 0.012)
    floor_mat = mat("SKIN_PR005_ReviewFloor", (0.29, 0.30, 0.30), 0.0, 0.68)
    floor = cube("STAGE_PR005_Floor", (0, 0, -0.07), (18, 18, 0.10), floor_mat, stage_collection, 0.0)
    for old in [o for o in stage_collection.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(old, do_unlink=True)
    def light(name, loc, energy, size, color, target):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        obj = bpy.data.objects.new(name, data)
        stage_collection.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    light("STAGE_PR005_Key", (-7.0, 9.0, 10.0), 1500, 5.5, (0.94, 0.97, 1.0), (0, 0, 1.7))
    light("STAGE_PR005_Fill", (8.0, 2.0, 7.0), 1200, 5.0, (0.82, 0.90, 1.0), (0, 0, 1.5))
    light("STAGE_PR005_Rim", (0.0, -9.0, 8.0), 1400, 4.5, (1.0, 0.89, 0.72), (0, -0.6, 1.6))
    light("STAGE_PR005_Interior", (0.0, 1.0, 3.15), 550, 2.0, (0.92, 0.96, 1.0), (0, 1.0, 1.4))
    camera_data = bpy.data.cameras.new("STAGE_PR005_CAMERA")
    camera_data.lens = 52
    cam = bpy.data.objects.new("STAGE_PR005_CAMERA", camera_data)
    stage_collection.objects.link(cam)
    scene.camera = cam
    return cam


def aim(cam, loc, target):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()


def render_pack(scene, cam):
    os.makedirs(RENDER_DIR, exist_ok=True)
    beauty = {
        "01_PR005_ArtSkin_v001_Front.png": ((0.0, 13.4, 4.8), (0.0, 0.25, 1.65)),
        "02_PR005_ArtSkin_v001_Rear.png": ((0.0, -13.4, 4.9), (0.0, -0.35, 1.65)),
        "03_PR005_ArtSkin_v001_Left.png": ((-13.3, 0.2, 4.7), (0.0, 0.0, 1.65)),
        "04_PR005_ArtSkin_v001_Right.png": ((13.3, -0.1, 4.8), (0.0, -0.2, 1.65)),
        "05_PR005_ArtSkin_v001_ThreeQuarter.png": ((-11.6, 12.2, 8.1), (0.0, 0.1, 1.60)),
    }
    set_engineering_visible(False)
    for filename, (loc, target) in beauty.items():
        aim(cam, loc, target)
        scene.render.filepath = os.path.join(RENDER_DIR, filename)
        bpy.ops.render.render(write_still=True)
        print("RENDERED|" + scene.render.filepath)
    set_engineering_visible(True)
    aim(cam, (-11.6, 12.2, 8.1), (0.0, 0.1, 1.60))
    scene.render.filepath = os.path.join(RENDER_DIR, "06_PR005_ArtSkin_v001_Diagnostic_Overlay.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED|" + scene.render.filepath)


def main():
    original = source_snapshot()
    scene = bpy.context.scene
    skin = coll(SKIN)
    stage_collection = coll(STAGE)
    # New, clearly named derivative-only materials. Inherited source material slots are untouched.
    mats = (
        mat("SKIN_PR005_WarmWhite", (0.68, 0.70, 0.67), 0.25, 0.33),
        mat("SKIN_PR005_Graphite", (0.038, 0.048, 0.054), 0.74, 0.29),
        mat("SKIN_PR005_CairnwellGreen", (0.018, 0.19, 0.130), 0.26, 0.32),
        mat("SKIN_PR005_SafetyYellow", (0.92, 0.55, 0.045), 0.12, 0.36),
        mat("SKIN_PR005_ServiceBlack", (0.004, 0.006, 0.008), 0.30, 0.44),
        mat("SKIN_PR005_BrushedSteel", (0.35, 0.39, 0.41), 0.90, 0.23),
        mat("SKIN_PR005_InspectionGlass", (0.07, 0.20, 0.22), 0.15, 0.16),
    )
    build_skin(skin, mats)
    cam = stage(scene, stage_collection)
    unchanged(original)
    scene["skin_version"] = "PR005_CairnwellVisualSkin_v001"
    scene["engineering_authority"] = "PR005_ExteriorEnclosure_OwnerReview_v812.blend"
    scene["skin_scope"] = "Separate skin geometry; five beauty renders hide engineering core; sixth is diagnostic overlay."
    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, copy=False)
    render_pack(scene, cam)
    # Keep the derivative opening in diagnostic state: source and skin are both inspectable.
    set_engineering_visible(True)
    unchanged(original)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, copy=False)
    print("SKIN_DERIVATIVE_SAVED|" + OUT_BLEND)
    print("ENGINEERING_FINGERPRINT_PRESERVED|" + str(len(original)))


if __name__ == "__main__":
    main()
