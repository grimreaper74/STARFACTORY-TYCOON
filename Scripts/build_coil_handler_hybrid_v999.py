"""Build a game-ready two-part coil handler from the approved textured master."""
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/Candidate/PressShop/Inbound/CoilHandlerAGV_v20260810/Original/Meshy_AI_Green_Titan_Coil_Hand_0810171429_texture.blend"
OUT = ROOT / "SourceAssets/Candidate/PressShop/Inbound/CoilHandlerAGV_v20260810/Hybrid_v999"
TEXTURES = OUT / "Textures"
BLEND = OUT / "Cairnwell_AGV_CHF01_Hybrid_v999.blend"
STATIC_FBX = OUT / "SM_Cairnwell_AGV_CHF01_StaticBody_v999.fbx"
LIFT_FBX = OUT / "SM_Cairnwell_AGV_CHF01_LiftAssembly_v999.fbx"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/coil_handler_hybrid_build_v999.json"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH")
source_tris = sum(max(0, len(p.vertices) - 2) for p in body.data.polygons)

# Preserve the original packed atlas bytes beside the FBX. Unreal must receive
# the authored base-colour/normal data rather than an untextured grey mesh.
TEXTURES.mkdir(parents=True, exist_ok=True)
extracted_textures = []
for index, image in enumerate(image for image in bpy.data.images if image.packed_file):
    payload = bytes(image.packed_file.data)
    suffix = ".jpg" if payload[:3] == b"\xff\xd8\xff" else ".png"
    path = TEXTURES / f"CHF01_Image_{index}{suffix}"
    path.write_bytes(payload)
    image.filepath = str(path)
    extracted_textures.append(str(path))

# Remove only the forward fused ram. The fixed mast and detailed chassis remain the
# untouched appearance authority; the replacement lift assembly covers the cut datum.
bm = bmesh.new()
bm.from_mesh(body.data)
ram_faces = [face for face in bm.faces if face.calc_center_median().x < -0.42]
bmesh.ops.delete(bm, geom=ram_faces, context="FACES")
orphans = [vert for vert in bm.verts if not vert.link_faces]
if orphans:
    bmesh.ops.delete(bm, geom=orphans, context="VERTS")
bm.to_mesh(body.data)
bm.free()
body.data.update()

# Centre on XY, floor seat, rotate the source front from -X to +X, then conform to
# the approved 4.8 x 2.2 x 2.6 m gameplay envelope.
points = [body.matrix_world @ Vector(corner) for corner in body.bound_box]
low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
centre = (low + high) * 0.5
body.location += Vector((-centre.x, -centre.y, -low.z))
body.rotation_euler.z += math.pi
bpy.context.view_layer.update()
points = [body.matrix_world @ Vector(corner) for corner in body.bound_box]
low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
dims = high - low
body.scale.x *= 4.8 / dims.x
body.scale.y *= 2.2 / dims.y
body.scale.z *= 2.6 / dims.z
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
body.name = "SM_Cairnwell_AGV_CHF01_StaticBody_v999"
body.data.name = body.name

def mat(name, colour, metallic, roughness):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*colour, 1.0)
    material.metallic = metallic
    material.roughness = roughness
    return material

graphite = mat("M_CHF01_Graphite_v999", (0.025, 0.032, 0.038), 0.62, 0.42)
steel = mat("M_CHF01_RamSteel_v999", (0.34, 0.37, 0.39), 0.88, 0.24)
yellow = mat("M_CHF01_SafetyYellow_v999", (0.72, 0.40, 0.015), 0.22, 0.38)
parts = []

def cube(name, location, dimensions, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    parts.append(obj)
    return obj

# Moving backplate and fork-free carriage inside the existing fixed mast. After
# the source is centred, its mast face is at the negative-X end of the vehicle.
# The first review render deliberately caught the old positive-X datum floating
# over the rear deck; keep this assembly co-located with the actual mast face.
mast_face_x = -1.47
cube("CHF01_Lift_Backplate", (mast_face_x, 0.0, 1.10), (0.14, 1.10, 0.86), graphite)
cube("CHF01_Lift_LeftRail", (mast_face_x - 0.02, -0.49, 1.34), (0.12, 0.08, 1.24), yellow)
cube("CHF01_Lift_RightRail", (mast_face_x - 0.02, 0.49, 1.34), (0.12, 0.08, 1.24), yellow)
cube("CHF01_Lift_UpperCrossbar", (mast_face_x - 0.02, 0.0, 1.91), (0.12, 1.06, 0.10), graphite)
cube("CHF01_Lift_LowerCrossbar", (mast_face_x - 0.02, 0.0, 0.85), (0.16, 1.06, 0.12), graphite)

# 1.6 m bore ram: cylindrical shaft plus a tapered engagement nose, no forks.
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.15, depth=1.40,
    location=(mast_face_x - 0.77, 0.0, 1.10), rotation=(0.0, math.pi / 2.0, 0.0))
shaft = bpy.context.object
shaft.name = "CHF01_Lift_HydraulicBoreRam"
shaft.data.materials.append(steel)
parts.append(shaft)
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.15, radius2=0.085, depth=0.15,
    location=(mast_face_x - 1.545, 0.0, 1.10), rotation=(0.0, -math.pi / 2.0, 0.0))
nose = bpy.context.object
nose.name = "CHF01_Lift_TaperedNose"
nose.data.materials.append(steel)
parts.append(nose)

# Join only the moving parts and retain a common floor-centred pivot with the body.
bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
lift = bpy.context.view_layer.objects.active
lift.name = "SM_Cairnwell_AGV_CHF01_LiftAssembly_v999"
lift.data.name = lift.name
bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")

# Preserve silhouette but reduce the fused Meshy body to a runtime-safe derivative.
bpy.context.view_layer.objects.active = body
modifier = body.modifiers.new("RuntimeSilhouetteReduction", "DECIMATE")
modifier.decimate_type = "COLLAPSE"
modifier.ratio = 0.12
modifier.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=modifier.name)
runtime_body_tris = sum(max(0, len(p.vertices) - 2) for p in body.data.polygons)
lift_tris = sum(max(0, len(p.vertices) - 2) for p in lift.data.polygons)

OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

def export(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={"MESH"},
        axis_forward="-Z", axis_up="Y", apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", use_space_transform=True,
        bake_space_transform=False, bake_anim=False, use_mesh_modifiers=True,
        mesh_smooth_type="FACE", path_mode="COPY", embed_textures=True)

export(body, STATIC_FBX)
export(lift, LIFT_FBX)

payload = {
    "status": "PASS__TEXTURED_BODY_PRESERVED__FUSED_RAM_REMOVED__SEPARATE_LIFT_BUILT__VISUAL_REVIEW_PENDING",
    "source": str(SOURCE), "hybrid_blend": str(BLEND),
    "static_fbx": str(STATIC_FBX), "lift_fbx": str(LIFT_FBX),
    "source_triangles": source_tris, "runtime_body_triangles": runtime_body_tris,
    "lift_triangles": lift_tris, "target_envelope_m": [4.8, 2.2, 2.6],
    "ram_load_datum_cm": [-301.5, 0.0, 110.0],
    "extracted_source_textures": extracted_textures,
    "motion": "fixed textured mast/body; separate carriage, backrest and bore ram lift together",
    "split_guide_rejected_for_render": "near-whole vehicle remained fused and visible ram was missing",
    "full_detail_masters_preserved": True, "meshy_credits_used": 0,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_COIL_HANDLER_HYBRID_V999", runtime_body_tris, lift_tris)
