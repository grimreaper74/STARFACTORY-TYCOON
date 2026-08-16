"""Independent clean-scene FBX round-trip and fixed-view audit for v035."""

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SRC = ROOT / "SourceAssets/IndustrialKit/BridgeCrane/PoweredCHook/Candidate_v035"
FBX = SRC / "SM_LB_Crane_PoweredCHook_Candidate_v035.fbx"
OUT = ROOT / "Saved/ValidationScreenshots/SourceAssets/BridgeCrane/PoweredCHook/Candidate_v035"
AUDIT = ROOT / "Saved/Audits/press_shop_crane_powered_chook_candidate_v035_source.json"
OUT.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX), use_custom_normals=True)
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if len(meshes) != 1:
    raise RuntimeError(f"Expected one merged mesh, got {len(meshes)}")
hook = meshes[0]
dims = [round(float(v), 6) for v in hook.dimensions]
pivot = [round(float(v), 6) for v in hook.location]
slots = [slot.material.name for slot in hook.material_slots]
required_tokens = ["SafetyYellow", "YellowEdgeWear", "FabricatedDarkSteel", "WorkedSteel", "WeldMetal", "ReplaceableContactRed", "LoadContactRubber", "CairnwellPlate", "SensorGreen", "StatusAmber"]
missing = [token for token in required_tokens if not any(token in slot for slot in slots)]
vertices = len(hook.data.vertices)
polygons = len(hook.data.polygons)
finite = all(mathutils_value == mathutils_value for vertex in hook.data.vertices for mathutils_value in vertex.co)

# Neutral stage.
bpy.ops.mesh.primitive_plane_add(size=9.0, location=(0,0,-0.86))
floor = bpy.context.object
floor_mat = bpy.data.materials.new("AuditFloor")
floor_mat.diffuse_color, floor_mat.roughness = (0.045,0.052,0.060,1), 0.70
floor.data.materials.append(floor_mat)
world = bpy.data.worlds.new("AuditWorld")
bpy.context.scene.world = world
world.color = (0.010,0.014,0.020)
for name,location,energy,size in (("Key",(3.5,-4.0,4.4),1500,3.2),("Fill",(-3.0,-2.0,2.5),900,2.5),("Rim",(-2.0,3.2,4.2),1200,2.2)):
    data=bpy.data.lights.new(name,"AREA"); data.energy, data.shape, data.size=energy,"DISK",size
    obj=bpy.data.objects.new(name,data); obj.location=location; bpy.context.collection.objects.link(obj)
    obj.rotation_euler=(Vector((0.35,0,0.35))-obj.location).to_track_quat("-Z","Y").to_euler()
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage=1400,1100,100
scene.render.image_settings.file_format="PNG"
scene.view_settings.look="AgX - Medium High Contrast"

def render(name, location, target, lens=58):
    data=bpy.data.cameras.new(name); camera=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(camera)
    camera.location=location; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler(); camera.data.lens=lens
    scene.camera=camera; path=OUT/f"lb_crane_powered_chook_v035_{name.lower()}.png"; scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True); bpy.data.objects.remove(camera,do_unlink=True); return str(path)

images=[render("Side",(4.2,-4.7,2.25),(0.48,0,0.35)),render("BoreAxis",(5.0,-0.18,0.75),(0.75,0,-0.22),62)]
sha=hashlib.sha256(FBX.read_bytes()).hexdigest()
pass_gate=(3.82<=dims[0]<=3.90 and 1.18<=dims[1]<=1.28 and 2.70<=dims[2]<=2.90 and pivot==[0.0,0.0,0.0] and not missing and vertices>3000 and polygons>3000 and finite)
payload={"$schema":"line-boss/audit/bridge-crane-powered-chook-candidate-v035-source/v1","status":"SOURCE_DIMENSION_PIVOT_MATERIAL_FBX_ROUND_TRIP_PASS__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED" if pass_gate else "SOURCE_FBX_GATE_FAIL__NOT_PROMOTED","method":"Independent Blender 5.2 clean-scene FBX import and fixed neutral-stage renders","fbx":str(FBX),"fbx_sha256":sha,"mesh_count":len(meshes),"dimensions_m":dims,"pivot_m":pivot,"vertices":vertices,"polygons":polygons,"finite_geometry":finite,"material_slots":slots,"missing_required_material_tokens":missing,"project_interfaces":{"bore_load_datum_below_hook_m":0.59,"hook_body_to_load_centre_m":1.50,"nominal_coil_m":[1.90,1.50],"coil_interface_od_m":[1.80,2.10],"coil_width_max_m":1.55},"engineering_values":"TBC_NOT_INVENTED","fixed_renders":images,"promotion_authorized":False}
AUDIT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
if not pass_gate: raise RuntimeError(json.dumps(payload,indent=2))
print(json.dumps(payload,indent=2))
