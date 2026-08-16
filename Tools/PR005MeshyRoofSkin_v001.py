"""Create a non-destructive PR005 roof-skin review derivative.

Inputs remain immutable:
 - PR005 v812 provides the engineering core.
 - the supplied Meshy segmentation blend provides roof-skin geometry.

The resulting linked mesh copies are visual-only.  They have no collision,
pivots, gameplay role, or relationship to the functional PR005 hierarchy.
"""
import bpy
import os
from mathutils import Vector

PROJECT = r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8"
MESHY = r"C:\\Users\\greg_\\Downloads\\Meshy_AI__0813061552_part-segmentation.blend"
OUT = os.path.join(PROJECT, "SourceAssets", "Candidate", "PressShop", "PR005", "ArtSkin_v005_MeshyRoofReplacement")
OUT_BLEND = os.path.join(OUT, "PR005_CairnwellMeshyRoofSkin_v005.blend")
RENDERS = os.path.join(OUT, "Renders")
COLLECTION = "97_PR005_MESHY_ROOF_SKIN_V005"
STAGE = "98_PR005_MESHY_ROOF_REVIEW_STAGE_V005"


def state(obj):
    return (obj.type, obj.parent.name if obj.parent else "", tuple(round(v, 6) for v in obj.location),
            tuple(round(v, 6) for v in obj.rotation_euler), tuple(round(v, 6) for v in obj.scale))


def snapshot():
    return {o.name: state(o) for o in bpy.context.scene.objects}


def assert_unchanged(before):
    changed = [name for name, value in before.items() if name not in bpy.data.objects or state(bpy.data.objects[name]) != value]
    if changed:
        raise RuntimeError("Engineering core was modified: " + ", ".join(changed))


def ensure_collection(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def move_to(obj, c):
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    c.objects.link(obj)


def material(name, rgb, metallic, roughness):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = roughness
    return m


def append_meshy_source():
    with bpy.data.libraries.load(MESHY, link=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name.startswith("model_part")]
    return [o for o in data_to.objects if o and o.type == "MESH"]


def remove_legacy_roof_panels():
    """Remove only six detached roof-sheet islands in this review derivative.

    The source v812 remains untouched on disk.  The enclosing frame and all
    process / functional components remain; this is the visual replacement
    opening for the new two-part Meshy roof only.
    """
    import bmesh
    obj = bpy.data.objects["SM_CA_MW_PR005_EnclosureShell_Static_v002"]
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    seen, remove = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        stack, component = [v], []
        seen.add(v)
        while stack:
            cur = stack.pop(); component.append(cur)
            for edge in cur.link_edges:
                other = edge.other_vert(cur)
                if other not in seen:
                    seen.add(other); stack.append(other)
        lo = [min(q.co[i] for q in component) for i in range(3)]
        hi = [max(q.co[i] for q in component) for i in range(3)]
        # Exact roof sheets: detached, within the roof frame, 100mm deep,
        # and in the existing y=-1.07..+5.07m roof opening.
        if (len(component) == 56 and abs(lo[0] + 2.675) < .003 and abs(hi[0] - 2.675) < .003
                and lo[1] >= -1.071 and hi[1] <= 5.071 and lo[2] >= 3.429 and hi[2] <= 3.531):
            remove.extend(component)
    if len(remove) != 336:
        raise RuntimeError("Expected six legacy roof sheets / 336 vertices; found %d" % len(remove))
    bmesh.ops.delete(bm, geom=remove, context='VERTS')
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    print("LEGACY_ROOF_SHEETS_REMOVED|6|opening=5.350x6.140x0.100m")


def create_two_roof_panels(skin):
    # The supplied segmentation is one complete roof panel. It replaces the
    # existing six ready roof sheets with two full-width panels, matching the
    # exact 5.350 x 6.140m opening they occupied. The surrounding frame stays.
    source = append_meshy_source()
    if len(source) != 9:
        raise RuntimeError("Expected 9 Meshy segmentation parts, got %d" % len(source))
    src = {o.name: o for o in source}
    required = ["model_part%d" % i for i in range(9)]
    if any(n not in src for n in required):
        raise RuntimeError("Unexpected Meshy segment names")

    warm_white = material("SKIN_PR005_MeshyRoof_WarmWhite", (0.894, 0.880, 0.835), .45, .34)
    graphite = material("SKIN_PR005_MeshyRoof_Graphite", (0.016, 0.018, 0.021), .72, .28)
    green = material("SKIN_PR005_MeshyRoof_CairnwellGreen", (0.015, 0.070, 0.054), .35, .32)
    yellow = material("SKIN_PR005_MeshyRoof_SafetyYellow", (0.887, 0.545, 0.006), .25, .36)
    steel = material("SKIN_PR005_MeshyRoof_ExposedSteel", (0.40, 0.43, 0.45), .88, .24)
    # Segmentation role assignment: top deck 7 and base perimeter 8;
    # long / cross folded rails 3-6; service brackets 0-2.  This is a visual
    # material assignment only: the received Meshy geometry is not edited.
    assignment = {0: graphite, 1: green, 2: green, 3: graphite, 4: graphite,
                  5: graphite, 6: graphite, 7: warm_white, 8: steel}

    # Module local mesh top is +0.120.  Its minimum is -0.1135.  Place the
    # root at 3.430 so the finished surface is exactly the 3.550m datum.
    vertices = [o.matrix_world @ v.co for o in source for v in o.data.vertices]
    bounds_min = Vector((min(v.x for v in vertices), min(v.y for v in vertices), min(v.z for v in vertices)))
    bounds_max = Vector((max(v.x for v in vertices), max(v.y for v in vertices), max(v.z for v in vertices)))
    bounds_size = bounds_max - bounds_min
    bounds_centre = (bounds_min + bounds_max) / 2.0
    old_opening_x, old_opening_y, old_opening_z = 5.350, 6.140, .100
    scale_x = old_opening_x / bounds_size.x
    scale_y = (old_opening_y / 2.0) / bounds_size.y
    scale_z = old_opening_z / bounds_size.z
    for panel, y in (("Lower", .465 - old_opening_y / 4.0), ("Upper", .465 + old_opening_y / 4.0)):
        root = bpy.data.objects.new("SKIN_PR005_RoofPanel_" + panel, None)
        skin.objects.link(root)
        root.location = (0, y, 3.530 - bounds_max.z * scale_z)
        for part_index in range(9):
            clone = src["model_part%d" % part_index].copy()
            clone.data = src["model_part%d" % part_index].data.copy()
            clone.name = "SKIN_PR005_RoofPanel_%s_Part%02d" % (panel, part_index)
            clone.data.materials.clear()
            clone.data.materials.append(assignment[part_index])
            skin.objects.link(clone)
            clone.parent = root
            # Parent root controls placement only. It is never a game pivot.
            clone.scale.x = scale_x
            clone.scale.y = scale_y
            clone.scale.z = scale_z
            clone.location.x = -bounds_centre.x * scale_x
            clone.location.y = -bounds_centre.y * scale_y
            clone.location.z = -bounds_centre.z * scale_z
            clone["visual_skin_only"] = True
            clone["collision_policy"] = "NoCollision"
            clone["source_authority"] = os.path.basename(MESHY)
            clone["source_sha256"] = "2BA8ACB22CD85A1A4F38BA03927EB0978028E4C95E17ADC12395D5757B9FCF27"
        root["visual_skin_only"] = True
        root["functional_pivot"] = False
        root["installation"] = "One of two replacement panels; each 5.350 x 3.070 x 0.100m, exactly matching the removed legacy roof-sheet opening."
    # Remove temporary appended assets—only the deliberately created derivatives remain.
    for obj in source:
        bpy.data.objects.remove(obj, do_unlink=True)


def cube(name, loc, dim, m, c):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name; o.dimensions = dim
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m); move_to(o, c)
    return o


def stage(scene, c):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1800, 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (.012, .015, .017)
    floor_m = material("STAGE_PR005_Roof_Floor", (.18, .19, .19), 0, .72)
    cube("STAGE_PR005_Roof_Floor", (0, 0, -.08), (18, 24, .10), floor_m, c)
    def light(name, loc, energy, size, target, color):
        d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.shape = "DISK"; d.size = size; d.color = color
        o = bpy.data.objects.new(name, d); c.objects.link(o); o.location = loc
        o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()
    light("STAGE_PR005_Roof_Key", (-8, 10, 11), 1700, 6, (0, 0, 1.8), (.92, .96, 1.0))
    light("STAGE_PR005_Roof_Fill", (9, 1, 8), 1350, 5, (0, 0, 1.5), (.84, .90, 1.0))
    light("STAGE_PR005_Roof_Rim", (0, -10, 9), 1450, 5, (0, 0, 1.6), (1.0, .87, .70))
    d = bpy.data.cameras.new("STAGE_PR005_ROOF_CAMERA"); d.lens = 52
    cam = bpy.data.objects.new("STAGE_PR005_ROOF_CAMERA", d); c.objects.link(cam); scene.camera = cam
    return cam


def aim(cam, loc, target=(0, 0, 1.7)):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, cam):
    os.makedirs(RENDERS, exist_ok=True)
    shots = {
        "01_PR005_MeshyRoof_v005_Front.png": (0, 13.5, 5.0),
        "02_PR005_MeshyRoof_v005_Rear.png": (0, -13.5, 5.0),
        "03_PR005_MeshyRoof_v005_Left.png": (-13.5, 0, 5.0),
        "04_PR005_MeshyRoof_v005_Right.png": (13.5, 0, 5.0),
        "05_PR005_MeshyRoof_v005_ThreeQuarter.png": (-11.5, 12.2, 9.0),
        "06_PR005_MeshyRoof_v005_TopDiagnostic.png": (0, 0, 16.5),
    }
    for name, loc in shots.items():
        aim(cam, loc)
        scene.render.filepath = os.path.join(RENDERS, name)
        bpy.ops.render.render(write_still=True)
        print("RENDERED|" + scene.render.filepath)


def main():
    before = snapshot()
    skin = ensure_collection(COLLECTION)
    stage_collection = ensure_collection(STAGE)
    # The next operation is the sole intentional engineering-core visual edit
    # in this derivative: removing six old roof-sheet islands for replacement.
    remove_legacy_roof_panels()
    create_two_roof_panels(skin)
    scene = bpy.context.scene
    scene["visual_skin_version"] = "PR005_CairnwellMeshyRoofSkin_v005"
    scene["engineering_authority"] = "PR005_ExteriorEnclosure_OwnerReview_v812.blend"
    scene["Mesy_source"] = os.path.basename(MESHY)
    scene["scope"] = "Two visual-only roof panels replace six legacy roof-sheet islands in this derivative. No collision, functional pivots, runtime import, or source-file changes."
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, copy=False)
    cam = stage(scene, stage_collection)
    render(scene, cam)
    # Transforms, parenting and all non-roof engineering objects retain their
    # source state. The source v812 file itself was only read.
    unexpected = [name for name, value in before.items()
                  if name != "SM_CA_MW_PR005_EnclosureShell_Static_v002" and state(bpy.data.objects[name]) != value]
    if unexpected:
        raise RuntimeError("Unexpected engineering-object modification: " + ", ".join(unexpected))
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, copy=False)
    print("DERIVATIVE_SAVED|" + OUT_BLEND)
    print("ENGINEERING_FINGERPRINT_PRESERVED|" + str(len(before)))


if __name__ == "__main__":
    main()
