"""Build a less slab-like fabricated Train A fixed presentation shell.

This is a source-only successor to the v014 visual direction.  It is rebuilt
against immutable AssemblyStudy_v013 and contains no movers, collision or
runtime authority.  All dimensions remain presentation decisions inside the
proven v292 S02-S06 envelope.
"""
import bpy, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PresentationShell_v015"
FBX_DIR, RENDERS = OUT / "FBX", OUT / "Renders"
BLEND_OUT = OUT / "CA_MW_PressTrainA_PresentationShell_v015.blend"
FBX_OUT = FBX_DIR / "SM_CA_MW_PTA_PresentationShell_v015.fbx"
MANIFEST = OUT / "PRESS_TRAIN_A_PRESENTATION_SHELL_MANIFEST_v015.json"
VALIDATION = OUT / "PRESS_TRAIN_A_PRESENTATION_SHELL_VALIDATION_v015.json"
PARENT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v013/CA_MW_PressTrainA_AssemblyStudy_v013.blend"
for path in (OUT, FBX_DIR, RENDERS): path.mkdir(parents=True, exist_ok=True)
if any(path.exists() for path in (BLEND_OUT, FBX_OUT, MANIFEST, VALIDATION)):
    raise RuntimeError("Refusing to overwrite immutable PresentationShell_v015")

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest().upper()

bpy.ops.wm.open_mainfile(filepath=str(PARENT))
scene = bpy.context.scene
collection = bpy.data.collections.new("PTA_PRESENTATION_SHELL_V015")
scene.collection.children.link(collection)

def material(name, colour, metallic, roughness):
    result = bpy.data.materials.new(name); result.diffuse_color = (*colour, 1); result.metallic = metallic; result.roughness = roughness; result.use_nodes = True
    node = result.node_tree.nodes.get("Principled BSDF"); node.inputs["Base Color"].default_value = (*colour, 1); node.inputs["Metallic"].default_value = metallic; node.inputs["Roughness"].default_value = roughness
    return result

M = {
    "green": material("CA_MW_PTA_Shell_CairnwellGreen_v015", (0.035, 0.15, 0.105), 0.34, 0.38),
    "graphite": material("CA_MW_PTA_Shell_FabricatedGraphite_v015", (0.09, 0.105, 0.115), 0.48, 0.47),
    "steel": material("CA_MW_PTA_Shell_MachinedSteel_v015", (0.24, 0.27, 0.29), 0.76, 0.31),
    "dark": material("CA_MW_PTA_Shell_DarkMachined_v015", (0.13, 0.145, 0.155), 0.66, 0.34),
    "yellow": material("CA_MW_PTA_Shell_SafetyYellow_v015", (0.78, 0.40, 0.018), 0.22, 0.43),
}
parts = []
def relink(obj):
    for owner in list(obj.users_collection): owner.objects.unlink(obj)
    collection.objects.link(obj)
def box(name, location, dimensions, mat, bevel=.05, segments=5):
    bpy.ops.mesh.primitive_cube_add(location=location); obj = bpy.context.object; obj.name = name; obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); relink(obj); obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("RolledFabricationEdge", "BEVEL"); mod.width = min(bevel, min(dimensions) * .23); mod.segments = segments
    parts.append(obj); return obj
def cylinder(name, location, radius, depth, mat, rotation=(0, math.pi/2, 0), vertices=64, bevel=.025):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object; obj.name = name; relink(obj); obj.data.materials.append(mat)
    mod = obj.modifiers.new("MachinedEdge", "BEVEL"); mod.width = bevel; mod.segments = 4
    parts.append(obj); return obj
def pipe(name, points, radius, mat):
    curve = bpy.data.curves.new(name, "CURVE"); curve.dimensions = "3D"; curve.bevel_depth = radius; curve.bevel_resolution = 4; curve.resolution_u = 2
    spline = curve.splines.new("POLY"); spline.points.add(len(points)-1)
    for point, coordinate in zip(spline.points, points): point.co = (*coordinate, 1)
    obj = bpy.data.objects.new(name, curve); collection.objects.link(obj); obj.data.materials.append(mat); parts.append(obj); return obj
def torus(name, location, major, minor, mat, rotation=(0, math.pi/2, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=48, minor_segments=12, location=location, rotation=rotation)
    obj = bpy.context.object; obj.name = name; relink(obj); obj.data.materials.append(mat); parts.append(obj); return obj

stages = [("S02", 7.5, 10.5, 2.55), ("S03", 15.0, 8.2, 2.30), ("S04", 22.5, 8.2, 2.30), ("S05", 30.0, 8.2, 2.30), ("S06", 37.5, 8.2, 2.30)]
for stage, y, height, half_span in stages:
    face_x = 4.35 if stage == "S02" else 4.22
    crown_z = height - .82
    post_z = height * .43
    post_height = height * .62
    # Two rolled H-frame posts leave the working throat open and remove the old monolithic cheek slabs.
    for side in (-1, 1):
        post_y = y + side * (half_span - .22)
        box(f"{stage}_RolledPost_{side}", (face_x, post_y, post_z), (.42, .38, post_height), M["graphite"], .14, 7)
        box(f"{stage}_PostWearStrip_{side}", (face_x + .225, post_y, post_z), (.055, .20, post_height * .76), M["dark"], .025)
        box(f"{stage}_PostFoot_{side}", (face_x, post_y, .48), (.58, .72, .32), M["steel"], .09)
        # Large eccentric bearing stack, grounded in the real press references.
        cylinder(f"{stage}_BearingOuter_{side}", (face_x + .25, post_y, crown_z + .03), .49, .24, M["dark"])
        cylinder(f"{stage}_BearingRace_{side}", (face_x + .40, post_y, crown_z + .03), .31, .10, M["steel"])
        cylinder(f"{stage}_BearingHub_{side}", (face_x + .47, post_y, crown_z + .03), .14, .06, M["graphite"])
        torus(f"{stage}_LiftingEye_{side}", (face_x, post_y, height - .02), .16, .045, M["yellow"], rotation=(0, math.pi/2, 0))
    # A rounded central crown and separate end gearbox pods replace the uninterrupted full-width slab.
    center_span = half_span * 1.12
    box(f"{stage}_CrownCore", (face_x, y, crown_z), (.56, center_span, 1.36), M["green"], .20, 8)
    box(f"{stage}_CrownLowerTie", (face_x, y, crown_z - .76), (.46, half_span * 1.70, .24), M["graphite"], .08)
    box(f"{stage}_CrownTopTie", (face_x, y, crown_z + .78), (.44, half_span * 1.48, .20), M["steel"], .08)
    for side in (-1, 1):
        pod_y = y + side * (half_span * .70)
        box(f"{stage}_GearboxPod_{side}", (face_x, pod_y, crown_z), (.52, half_span * .42, 1.10), M["graphite"], .17, 7)
    # Recessed crown panels, ribs and fasteners create readable fabrication layers.
    for panel, offset in enumerate((-0.66, 0.0, 0.66)):
        box(f"{stage}_CrownRecess_{panel}", (face_x + .305, y + offset, crown_z), (.035, .48, .72), M["dark"], .045)
        for dz in (-.28, .28): cylinder(f"{stage}_CrownBolt_{panel}_{dz}", (face_x + .345, y + offset, crown_z + dz), .035, .035, M["steel"], vertices=24, bevel=.008)
    # Narrow lower service spine and separate doors avoid another broad facade slab.
    service_z = 2.85 if stage != "S02" else 3.20
    box(f"{stage}_ServiceSpine", (face_x, y, service_z), (.34, .30, 2.75), M["graphite"], .10)
    for door, offset in enumerate((-1.05, 1.05)):
        box(f"{stage}_ServiceDoor_{door}", (face_x + .19, y + offset, service_z), (.065, .82, 1.72), M["green"], .055)
        box(f"{stage}_ServiceDoorInset_{door}", (face_x + .228, y + offset, service_z), (.022, .58, 1.30), M["graphite"], .035)
        box(f"{stage}_DoorHandle_{door}", (face_x + .255, y + offset + .25, service_z), (.035, .055, .34), M["yellow"], .015)
    # Visible hydraulic manifold, vessels and protected pipe runs.
    manifold_y = y - half_span - .48
    box(f"{stage}_Manifold", (face_x - .02, manifold_y, 1.38), (.50, .74, 1.68), M["dark"], .09)
    for line, z in enumerate((.82, 1.16, 1.50, 1.84)):
        pipe(f"{stage}_HydraulicPipe_{line}", [(face_x + .27, manifold_y - .22, z), (face_x + .38, manifold_y + .15, z), (face_x + .38, y - half_span + .15, z + .22)], .026, M["steel"])
        cylinder(f"{stage}_Valve_{line}", (face_x + .38, manifold_y - .28, z), .085, .075, M["yellow"], vertices=32, bevel=.01)
    for vessel, offset in enumerate((-.20, .20)):
        cylinder(f"{stage}_Accumulator_{vessel}", (face_x - .14, manifold_y + offset, 2.58), .17, 1.02, M["steel"], rotation=(0, 0, 0), vertices=48)
    # Stage identity plate, intentionally text-free for Unreal authority.
    box(f"{stage}_IdentityPlate", (face_x + .315, y, crown_z - .52), (.035, .90, .26), M["green"], .035)

bpy.ops.object.select_all(action="DESELECT")
for part in parts: part.select_set(True); bpy.context.view_layer.objects.active = part
bpy.ops.object.convert(target="MESH"); bpy.ops.object.join()
asset = bpy.context.object; asset.name = "SM_CA_MW_PTA_PresentationShell_v015"
asset["role"] = "fixed_visual_presentation_shell"; asset["collision_intent"] = "NoCollision"; asset["runtime_authority"] = "retained_components_only"; asset["engineering_status"] = "GAME_VISUAL_DETAIL_TBC"
bpy.context.scene.cursor.location = (0, 0, 0); bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

bpy.ops.object.select_all(action="DESELECT"); asset.select_set(True); bpy.context.view_layer.objects.active = asset
bpy.ops.export_scene.fbx(filepath=str(FBX_OUT), use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False, use_custom_props=True, object_types={"MESH"})

scene.render.engine = "BLENDER_EEVEE"; scene.render.resolution_x = 1600; scene.render.resolution_y = 900; scene.render.resolution_percentage = 100; scene.render.image_settings.file_format = "PNG"; scene.view_settings.look = "AgX - Medium High Contrast"; scene.world.color = (.012, .016, .02)
def look(obj, target): obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
camera_data = bpy.data.cameras.new("PTA_v015_Camera"); camera = bpy.data.objects.new("PTA_v015_Camera", camera_data); scene.collection.objects.link(camera); scene.camera = camera
for name, location, target, energy, size in (("Key", (13, -1, 12), (2, 23, 4), 1500, 8), ("Rim", (-10, 28, 13), (2, 23, 4), 1200, 8), ("Roof", (6, 23, 16), (2, 23, 3), 1650, 10)):
    light_data = bpy.data.lights.new("PTA_v015_" + name, "AREA"); light_data.energy = energy; light_data.shape = "DISK"; light_data.size = size
    light = bpy.data.objects.new("PTA_v015_" + name, light_data); scene.collection.objects.link(light); light.location = location; look(light, target)
def render(filename, location, target, lens):
    camera.location = location; camera.data.lens = lens; look(camera, target); scene.render.filepath = str(RENDERS / filename); bpy.ops.render.render(write_still=True)
render("01_operator_fabrication_v015.png", (14, -3, 7.0), (3.2, 23, 4.2), 58)
render("02_mid_train_detail_v015.png", (10.5, 17, 5.4), (3.8, 23, 4.0), 62)
render("03_management_fabrication_v015.png", (17, 18, 12.5), (2.5, 23, 4.2), 58)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT), check_existing=False)
local_bounds = {"min": [min(v[i] for v in asset.bound_box) for i in range(3)], "max": [max(v[i] for v in asset.bound_box) for i in range(3)]}
manifest = {"$schema": "cairnwell/source/press-train-presentation-shell-v015/v1", "created_utc": datetime.now(timezone.utc).isoformat(), "status": "SOURCE_ONLY_FABRICATED_SHELL__UNREAL_INTAKE_REQUIRED__NOT_PROMOTED", "parent_v013_sha256": sha(PARENT), "asset_name": asset.name, "source_part_count_before_join": len(parts), "vertices": len(asset.data.vertices), "polygons": len(asset.data.polygons), "local_bounds_m": local_bounds, "material_slots": [m.name for m in asset.data.materials], "stage_coverage": [s[0] for s in stages], "collision_intent": "NoCollision", "retained_authorities_edited": False, "moving_parts_duplicated": False, "unverified_engineering_values_adopted": False, "fbx": {"file": "FBX/" + FBX_OUT.name, "bytes": FBX_OUT.stat().st_size, "sha256": sha(FBX_OUT)}, "renders": ["Renders/01_operator_fabrication_v015.png", "Renders/02_mid_train_detail_v015.png", "Renders/03_management_fabrication_v015.png"]}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
failures = []
if len(parts) < 180: failures.append(f"insufficient part layering {len(parts)}")
if local_bounds["max"][0] > 4.95 or local_bounds["min"][0] < 3.70: failures.append(f"X envelope escaped {local_bounds}")
if local_bounds["max"][1] > 40.2 or local_bounds["min"][1] < 3.7: failures.append(f"Y envelope escaped {local_bounds}")
if local_bounds["max"][2] > 10.75 or local_bounds["min"][2] < .25: failures.append(f"Z envelope escaped {local_bounds}")
validation = {"status": "PASS__V015_FABRICATED_FIXED_SHELL_SOURCE__UNREAL_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V015_SOURCE_NOT_RETAINED", "asset_count": 1, "stage_count": 5, "source_part_count": len(parts), "vertices": len(asset.data.vertices), "polygons": len(asset.data.polygons), "local_bounds_m": local_bounds, "collision_intent": "NoCollision", "retained_authorities_edited": False, "promotion_authorized": False, "failures": failures}
VALIDATION.write_text(json.dumps(validation, indent=2), encoding="utf-8")
print(json.dumps(validation, indent=2))
if failures: raise RuntimeError("; ".join(failures))
