"""Create a review-only Cairnwell art derivative from the immutable PR005 v812 source.

This script intentionally does not rename, transform, re-parent, delete, or apply modifiers to
the inherited engineering objects.  It adds only derivative-owned materials, presentation
lighting, and a separately tagged art-detail collection before saving to a new file.
"""

import math
import os
import sys
from mathutils import Vector

import bpy


PROJECT = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
OUT_DIR = os.path.join(
    PROJECT,
    "SourceAssets",
    "Candidate",
    "PressShop",
    "PR005",
    "ArtDerivative_v001",
)
OUT_BLEND = os.path.join(OUT_DIR, "PR005_CairnwellArtDerivative_v001.blend")
RENDER_DIR = os.path.join(OUT_DIR, "Renders")


def fmt(values):
    return tuple(round(v, 4) for v in values)


def source_fingerprint():
    """Record only inherited objects so we can prove their transforms/hierarchy survived."""
    return {
        obj.name: (
            obj.type,
            obj.parent.name if obj.parent else "",
            fmt(obj.location),
            fmt(obj.rotation_euler),
            fmt(obj.scale),
        )
        for obj in bpy.context.scene.objects
    }


def assert_source_unchanged(before):
    after = source_fingerprint()
    changed = [name for name, state in before.items() if after.get(name) != state]
    if changed:
        raise RuntimeError("Inherited source transform/hierarchy changed: " + ", ".join(changed))


def collection(name):
    found = bpy.data.collections.get(name)
    if found:
        return found
    found = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(found)
    return found


def material(name, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def remake_material(existing_name, name, color, metallic=0.0, roughness=0.45):
    """Replace an inherited material assignment inside the derivative only."""
    original = bpy.data.materials.get(existing_name)
    if not original:
        return
    derived = material(name, color, metallic, roughness)
    for obj in bpy.data.objects:
        if not hasattr(obj.data, "materials"):
            continue
        for index, slot in enumerate(obj.data.materials):
            if slot == original:
                obj.data.materials[index] = derived


def link_only(obj, target_collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    target_collection.objects.link(obj)


def box(name, location, dimensions, mat, bevel=0.025, target=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("Manufactured edge radius", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    obj.data.materials.append(mat)
    if target:
        link_only(obj, target)
    return obj


def cylinder(name, location, radius, depth, mat, rotation=(0, 0, 0), target=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    bevel = obj.modifiers.new("Machined edge radius", "BEVEL")
    bevel.width = min(radius * 0.14, 0.025)
    bevel.segments = 3
    obj.data.materials.append(mat)
    if target:
        link_only(obj, target)
    return obj


def cable(name, points, radius, mat, target):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    target.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def add_text(name, body, location, rotation, size, mat, target):
    curve = bpy.data.curves.new(name, "FONT")
    curve.body = body
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.008
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    obj.rotation_euler = rotation
    target.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def parent_preserving_world(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


def add_panel_bay(target, side, y, white, graphite, green, yellow, black):
    # Panel skins deliberately sit within a 30 mm visual tolerance of the inherited envelope.
    x = 2.872 * side
    panel = box("ART_PR005_%s_Panel_%+.1f" % ("Utilities" if side > 0 else "Operator", y), (x, y, 1.82), (0.05, 1.05, 1.56), white, 0.025, target)
    inset_x = 2.899 * side
    access = box("ART_PR005_%s_AccessDoor_%+.1f" % ("Utilities" if side > 0 else "Operator", y), (inset_x, y + 0.02, 1.72), (0.026, 0.72, 1.05), green, 0.018, target)
    # Horizontal panel seam and a narrow graphite plinth line.
    box("ART_PR005_%s_PanelSeam_%+.1f" % ("Utilities" if side > 0 else "Operator", y), (inset_x + 0.002 * side, y, 2.44), (0.029, 0.96, 0.028), graphite, 0.006, target)
    box("ART_PR005_%s_LowerPlinth_%+.1f" % ("Utilities" if side > 0 else "Operator", y), (inset_x + 0.002 * side, y, 0.47), (0.029, 0.98, 0.12), graphite, 0.008, target)
    # Door hinges, latch and a small genuine safety edge at the access opening.
    for z in (1.18, 2.18):
        cylinder("ART_PR005_DoorHinge", (2.918 * side, y - 0.63, z), 0.045, 0.12, graphite, rotation=(0, math.pi / 2, 0), target=target)
    box("ART_PR005_DoorLatch", (2.918 * side, y + 0.39, 1.72), (0.035, 0.10, 0.16), black, 0.012, target)
    box("ART_PR005_DoorSafetyEdge", (2.919 * side, y - 0.73, 1.72), (0.028, 0.035, 1.02), yellow, 0.005, target)
    return panel, access


def add_vent_bank(target, side, y, graphite, black):
    x = 2.917 * side
    box("ART_PR005_VentPlenum", (x, y, 2.64), (0.022, 0.88, 0.48), black, 0.01, target)
    for offset in (-0.30, -0.15, 0.0, 0.15, 0.30):
        box("ART_PR005_VentLouvre", (2.93 * side, y + offset, 2.64), (0.026, 0.075, 0.30), graphite, 0.008, target)


def art_detail(target, mats):
    white, graphite, green, yellow, steel, black, glass = mats
    # Lower fabricated plinth pieces keep all visual work tied to the inherited footprint.
    box("ART_PR005_FrontPlinth", (0, 5.105, 0.19), (5.58, 0.10, 0.34), graphite, 0.025, target)
    box("ART_PR005_RearPlinth", (0, -5.105, 0.19), (5.58, 0.10, 0.34), graphite, 0.025, target)
    box("ART_PR005_LeftPlinth", (-2.79, 0, 0.19), (0.10, 9.95, 0.34), graphite, 0.025, target)
    box("ART_PR005_RightPlinth", (2.79, 0, 0.19), (0.10, 9.95, 0.34), graphite, 0.025, target)

    # Roof panel break-up: flush cover strips and central raised but envelope-safe service spine.
    for y in (-3.75, -1.85, 0.0, 1.85, 3.75):
        box("ART_PR005_RoofSeam", (0, y, 3.525), (5.42, 0.075, 0.03), graphite, 0.008, target)
    box("ART_PR005_RoofServiceSpine", (0, -1.10, 3.53), (0.52, 5.55, 0.035), white, 0.016, target)
    box("ART_PR005_RoofVent", (1.55, -1.7, 3.535), (1.15, 0.78, 0.025), graphite, 0.006, target)

    # Service panels are alternated to break the source's broad side faces.
    for y in (-3.75, -2.05, -0.35, 1.35, 3.05):
        add_panel_bay(target, 1, y, white, graphite, green, yellow, black)
    for y in (-3.15, -1.45, 0.25, 1.95):
        add_panel_bay(target, -1, y, white, graphite, green, yellow, black)
    add_vent_bank(target, 1, -2.05, graphite, black)
    add_vent_bank(target, -1, 1.95, graphite, black)

    # Front access fascia, label, glazing and a restrained Cairnwell identity panel.
    box("ART_PR005_FrontFascia", (0, 5.155, 2.46), (3.70, 0.045, 0.66), white, 0.025, target)
    box("ART_PR005_FrontIdentityPanel", (-1.05, 5.185, 2.48), (1.78, 0.018, 0.36), green, 0.012, target)
    # Face the positive-Y front review camera; this is derivative-owned lettering only.
    add_text("ART_PR005_Identity", "CAIRNWELL  |  PR005  COIL PREPARATION", (-1.05, 5.205, 2.48), (math.radians(90), 0, math.pi), 0.145, white, target)
    box("ART_PR005_FrontProcessWindow", (1.35, 5.182, 2.45), (1.12, 0.020, 0.38), glass, 0.01, target)
    for x in (-1.84, 1.84):
        box("ART_PR005_FrontDoorFrame", (x, 5.19, 1.54), (0.055, 0.025, 1.72), graphite, 0.012, target)

    # Pinch rolls: derivative-only machined end caps parented to their existing movers.
    roller_data = [
        ("SM_CA_MW_PR005_PinchRollLower_ReadabilityMover_v002", 0.78),
        ("SM_CA_MW_PR005_PinchRollUpper_ReadabilityMover_v002", 1.27),
    ]
    for parent_name, z in roller_data:
        parent = bpy.data.objects.get(parent_name)
        for x in (-1.17, 1.17):
            cap = cylinder("ART_PR005_PinchRollMachinedCap", (x, 2.78, z), 0.24, 0.075, steel, rotation=(0, math.pi / 2, 0), target=target)
            if parent:
                parent_preserving_world(cap, parent)

    # Threader table end rails preserve the original mover as the only motion authority.
    threader_parent = bpy.data.objects.get("SM_CA_MW_PR005_ThreaderTable_ReadabilityMover_v002")
    for x in (-0.93, 0.93):
        rail = box("ART_PR005_ThreaderGuideRail", (x, 2.82, 1.01), (0.08, 1.32, 0.10), graphite, 0.02, target)
        if threader_parent:
            parent_preserving_world(rail, threader_parent)

    # External services: black flexible cables and stainless hard-line runs on the utility side.
    cable("ART_PR005_UtilityHose_A", [(2.91, -2.6, 2.9), (3.05, -2.0, 2.6), (2.93, -1.1, 2.1), (2.92, -0.4, 1.4)], 0.035, black, target)
    cable("ART_PR005_UtilityHose_B", [(2.91, -1.9, 2.95), (3.06, -1.0, 2.72), (2.93, 0.0, 2.25), (2.92, 0.8, 1.6)], 0.028, black, target)
    for y in (-2.4, -1.8, -1.2, -0.6):
        cylinder("ART_PR005_ServiceHardline", (2.90, y, 1.10), 0.028, 1.05, steel, target=target)

    # Detail around the rear headstock zone: a dense graphite service manifold and couplings.
    box("ART_PR005_HeadstockServiceManifold", (2.82, -3.75, 1.12), (0.12, 1.15, 0.56), graphite, 0.03, target)
    for y in (-4.10, -3.82, -3.54, -3.26):
        cylinder("ART_PR005_HeadstockCoupling", (2.90, y, 1.12), 0.075, 0.05, steel, rotation=(0, math.pi / 2, 0), target=target)


def stage(scene, mats):
    white, graphite, green, yellow, steel, black, glass = mats
    stage_collection = collection("98_ART_DERIVATIVE_RENDER_STAGE")
    for item in list(stage_collection.objects):
        bpy.data.objects.remove(item, do_unlink=True)
    # Hide original inspection clearance markers from review renders, without changing exports.
    for name in ("90_TBC_CLEARANCE_HELPERS_NOT_EXPORTED",):
        coll = bpy.data.collections.get(name)
        if coll:
            coll.hide_render = True
    floor = bpy.data.objects.get("RenderFloor")
    if floor and hasattr(floor.data, "materials"):
        floor.data.materials.clear()
        floor.data.materials.append(material("ART_PR005_Floor", (0.42, 0.43, 0.41), 0.0, 0.62))
    scene.world.color = (0.025, 0.03, 0.035)
    # Blender 5.2's Python enum is BLENDER_EEVEE (rather than the 4.x NEXT label).
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.image_settings.color_depth = "8"

    for existing in list(scene.objects):
        if existing.type == "LIGHT":
            existing.hide_render = True

    def area(name, location, energy, size, color):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = color
        obj = bpy.data.objects.new(name, data)
        stage_collection.objects.link(obj)
        obj.location = location
        obj.rotation_euler = (0, 0, 0)
        return obj

    key = area("ART_KEY", (-7.5, 8.0, 10.5), 1500, 6.0, (0.96, 0.98, 1.0))
    fill = area("ART_FILL", (7.0, 1.0, 6.8), 1050, 5.0, (0.82, 0.90, 1.0))
    rim = area("ART_RIM", (0.0, -8.5, 8.2), 1250, 5.0, (1.0, 0.92, 0.78))
    interior_a = area("ART_INTERIOR_A", (-1.8, 0.8, 3.25), 650, 2.0, (0.90, 0.96, 1.0))
    interior_b = area("ART_INTERIOR_B", (1.8, -2.8, 3.15), 700, 2.0, (0.95, 0.92, 0.84))
    for light, target in ((key, (0, 0, 1.5)), (fill, (0, 0, 1.3)), (rim, (0, -0.5, 1.7)), (interior_a, (-0.8, 1.4, 1.45)), (interior_b, (0.8, -2.1, 1.35))):
        light.rotation_euler = (Vector(target) - light.location).to_track_quat("-Z", "Y").to_euler()


def camera(scene, target_collection):
    existing = bpy.data.objects.get("ART_PR005_REVIEW_CAMERA")
    if existing:
        return existing
    data = bpy.data.cameras.new("ART_PR005_REVIEW_CAMERA")
    data.lens = 52
    data.sensor_width = 36
    obj = bpy.data.objects.new("ART_PR005_REVIEW_CAMERA", data)
    target_collection.objects.link(obj)
    scene.camera = obj
    return obj


def point_camera(cam, location, target=(0, 0, 1.65)):
    cam.location = location
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()


def render_review(scene, target_collection):
    os.makedirs(RENDER_DIR, exist_ok=True)
    cam = camera(scene, target_collection)
    views = {
        "01_PR005_Cairnwell_ArtDerivative_v001_Front.png": ((0.0, 13.4, 4.6), (0.0, 0.3, 1.55)),
        "02_PR005_Cairnwell_ArtDerivative_v001_Rear.png": ((0.0, -13.4, 4.9), (0.0, -0.4, 1.55)),
        "03_PR005_Cairnwell_ArtDerivative_v001_Left.png": ((-13.3, 0.2, 4.7), (0.0, 0.0, 1.58)),
        "04_PR005_Cairnwell_ArtDerivative_v001_Right.png": ((13.3, -0.1, 4.8), (0.0, -0.2, 1.58)),
        "05_PR005_Cairnwell_ArtDerivative_v001_ThreeQuarter.png": ((-11.4, 12.0, 8.0), (0.0, 0.1, 1.55)),
    }
    for filename, (location, target) in views.items():
        point_camera(cam, location, target)
        scene.render.filepath = os.path.join(RENDER_DIR, filename)
        bpy.ops.render.render(write_still=True)
        print("RENDERED|" + scene.render.filepath)


def build():
    before = source_fingerprint()
    scene = bpy.context.scene
    scene["art_derivative_version"] = "PR005_CairnwellArtDerivative_v001"
    scene["art_derivative_source"] = "OwnerApprovalPack_v20260809_v812/PR005_ExteriorEnclosure_OwnerReview_v812.blend"
    scene["art_derivative_scope"] = "Review renders only; no Unreal import; original source objects retained unchanged."
    detail_collection = collection("97_PR005_CAIRNWELL_ART_DERIVATIVE_DETAILS_V001")
    # The script is intentionally one-shot; a clean source is always the input.
    mats = (
        material("ART_PR005_WarmWhite", (0.72, 0.74, 0.70), 0.22, 0.34),
        material("ART_PR005_Graphite", (0.045, 0.055, 0.060), 0.72, 0.31),
        material("ART_PR005_CairnwellGreen", (0.025, 0.20, 0.135), 0.24, 0.34),
        material("ART_PR005_SafetyYellow", (0.93, 0.56, 0.055), 0.12, 0.36),
        material("ART_PR005_BrushedSteel", (0.36, 0.40, 0.42), 0.88, 0.23),
        material("ART_PR005_ServiceBlack", (0.008, 0.010, 0.012), 0.28, 0.42),
        material("ART_PR005_InspectionGlass", (0.08, 0.22, 0.24), 0.10, 0.18),
    )
    remake_material("CA_MW_FoundryCharcoal", "ART_PR005_Graphite", (0.045, 0.055, 0.060), 0.72, 0.31)
    remake_material("CA_MW_ServiceGrey", "ART_PR005_WarmWhite", (0.72, 0.74, 0.70), 0.22, 0.34)
    remake_material("CA_MW_CairnwellGreen", "ART_PR005_CairnwellGreen", (0.025, 0.20, 0.135), 0.24, 0.34)
    remake_material("CA_MW_SafetyYellow", "ART_PR005_SafetyYellow", (0.93, 0.56, 0.055), 0.12, 0.36)
    remake_material("CA_MW_WorkedSteel", "ART_PR005_BrushedSteel", (0.36, 0.40, 0.42), 0.88, 0.23)
    remake_material("CA_MW_StripSteel", "ART_PR005_BrushedSteel", (0.36, 0.40, 0.42), 0.88, 0.23)
    remake_material("PR005_EXISTING_SOURCE_CONTEXT", "ART_PR005_Graphite", (0.045, 0.055, 0.060), 0.72, 0.31)
    art_detail(detail_collection, mats)
    stage(scene, mats)
    assert_source_unchanged(before)
    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, copy=False)
    render_review(scene, collection("98_ART_DERIVATIVE_RENDER_STAGE"))
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, copy=False)
    print("DERIVATIVE_SAVED|" + OUT_BLEND)
    print("SOURCE_FINGERPRINT_PRESERVED|" + str(len(before)))


if __name__ == "__main__":
    build()
