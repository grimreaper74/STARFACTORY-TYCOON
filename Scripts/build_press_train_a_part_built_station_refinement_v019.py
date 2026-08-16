"""Refine retained component-built press source v018 without overwriting it."""
import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v018/CA_MW_PressModulePrototype_v018.blend"
PARENT_SHA = "BCBC3EB0C24C73F511E7472F0344CD61526CC0BA549E12756EB611D632D74A3B"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v019"
FBX_DIR = OUT / "FBX"
RENDERS = OUT / "Renders"
BLEND_OUT = OUT / "CA_MW_PressModulePrototype_v019.blend"
FBX_OUT = FBX_DIR / "SM_CA_MW_PressModulePrototype_v019.fbx"
MANIFEST = OUT / "PRESS_MODULE_PROTOTYPE_MANIFEST_v019.json"
VALIDATION = OUT / "PRESS_MODULE_PROTOTYPE_VALIDATION_v019.json"
for directory in (OUT, FBX_DIR, RENDERS): directory.mkdir(parents=True, exist_ok=True)
if any(path.exists() for path in (BLEND_OUT, FBX_OUT, MANIFEST, VALIDATION)):
    raise RuntimeError("Refusing to overwrite immutable PressModulePrototype_v019")

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest().upper()
if sha(PARENT) != PARENT_SHA: raise RuntimeError("v018 source hash drift")
bpy.ops.wm.open_mainfile(filepath=str(PARENT))
scene = bpy.context.scene
collection = bpy.data.collections.get("CA_MW_PressModulePrototype_v018")
if collection is None: raise RuntimeError("v018 source collection missing")
collection.name = "CA_MW_PressModulePrototype_v019"

# Remove only the joined v018 export duplicate. Individual authored parts remain.
old_export = bpy.data.objects.get("SM_CA_MW_PressModulePrototype_v018")
if old_export is None: raise RuntimeError("v018 joined export missing")
bpy.data.objects.remove(old_export, do_unlink=True)
for obj in collection.objects:
    obj.name = obj.name.replace("v018", "v019")
for mat in bpy.data.materials:
    if "v018" in mat.name: mat.name = mat.name.replace("v018", "v019")

def by_token(token):
    mat = next((m for m in bpy.data.materials if token.lower() in m.name.lower()), None)
    if mat is None: raise RuntimeError(f"material missing {token}")
    return mat
GREEN, GRAPHITE, STEEL, DARK, YELLOW, COPPER = [by_token(t) for t in ("CairnwellGreen", "FabricatedGraphite", "MachinedSteel", "DarkMachined", "SafetyYellow", "CopperService")]

# Darker, rougher production finish than the clean v018 studio prototype.
for mat, colour, metallic, roughness in (
    (GREEN, (0.025, 0.13, 0.085, 1), 0.38, 0.58),
    (GRAPHITE, (0.075, 0.085, 0.09, 1), 0.58, 0.53),
    (STEEL, (0.28, 0.31, 0.33, 1), 0.82, 0.38),
    (DARK, (0.025, 0.030, 0.034, 1), 0.66, 0.46),
    (YELLOW, (0.68, 0.29, 0.008, 1), 0.22, 0.55),
    (COPPER, (0.24, 0.07, 0.025, 1), 0.70, 0.39),
):
    mat.diffuse_color = colour
    mat.metallic = metallic
    mat.roughness = roughness
    node = mat.node_tree.nodes.get("Principled BSDF") if mat.use_nodes else None
    if node:
        node.inputs["Base Color"].default_value = colour
        node.inputs["Metallic"].default_value = metallic
        node.inputs["Roughness"].default_value = roughness

added = []
def relink(obj):
    for owner in list(obj.users_collection): owner.objects.unlink(obj)
    collection.objects.link(obj)
def box(name, location, dimensions, mat, bevel=0.04, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj=bpy.context.object; obj.name=name; obj.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    relink(obj); obj.data.materials.append(mat)
    if bevel:
        mod=obj.modifiers.new("FabricatedEdge","BEVEL"); mod.width=min(bevel,min(dimensions)*0.18); mod.segments=3
    obj["engineering_status"]="VISUAL_PROTOTYPE_TBC"; obj["runtime_authority"]="NONE_SOURCE_ONLY"; obj["collision_intent"]="NoCollision"
    added.append(obj); return obj
def cylinder(name, location, radius, depth, mat, rotation=(math.pi/2,0,0), vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=location,rotation=rotation)
    obj=bpy.context.object; obj.name=name; relink(obj); obj.data.materials.append(mat)
    mod=obj.modifiers.new("MachinedEdge","BEVEL"); mod.width=min(0.018,radius*.10); mod.segments=3
    obj["engineering_status"]="VISUAL_PROTOTYPE_TBC"; obj["runtime_authority"]="NONE_SOURCE_ONLY"; obj["collision_intent"]="NoCollision"
    added.append(obj); return obj

# Fully guarded upper drive: fabricated shell, access doors, vents and lifting details.
box("S03_DriveGuard_Main_v019", (0,0,8.56), (3.70,1.86,1.18), GREEN, .10)
box("S03_DriveGuard_FrontPanel_v019", (0,-.951,8.56), (3.18,.045,.84), GRAPHITE, .025)
for side in (-1,1):
    box(f"S03_DriveGuard_End_{side}_v019", (side*1.68,0,8.56), (.28,1.58,.88), DARK,.06)
    cylinder(f"S03_DriveInspectionCover_{side}_v019", (side*1.70,-.976,8.56), .27,.05,STEEL,vertices=48)
for x in (-1.10,-.73,-.36,0,.36,.73,1.10):
    box(f"S03_DriveVent_{x:+.2f}_v019", (x,-.982,8.48), (.055,.025,.42), STEEL,.008)
for x in (-1.32,1.32):
    cylinder(f"S03_CrownLiftingEye_{x:+.2f}_v019", (x,0,9.20), .12,.10,YELLOW,rotation=(math.pi/2,0,0),vertices=32)

# Heavier crown fabrication: diagonal knee gussets, side ribs and tie-plate seams.
for side in (-1,1):
    for depth_side in (-1,1):
        box(f"S03_CrownKnee_{side}_{depth_side}_v019", (side*1.72,depth_side*.68,6.72), (.58,.48,.68), GRAPHITE,.09,rotation=(0,side*.15,0))
    for z in (6.82,7.28,7.72):
        box(f"S03_CrownSideRib_{side}_{z:.2f}_v019", (side*2.18,0,z), (.055,1.62,.10), STEEL,.012)
box("S03_CrownTiePlate_v019", (0,-1.085,6.96), (3.52,.05,.28), DARK,.024)

# Die/tooling context closes the empty throat without claiming mover authority.
box("S03_LowerDieShoe_v019", (0,0,1.66), (2.82,1.28,.20), DARK,.035)
box("S03_LowerDie_v019", (0,0,1.92), (2.48,1.08,.32), STEEL,.055)
box("S03_UpperDieShoe_v019", (0,0,4.86), (2.82,1.28,.18), DARK,.035)
box("S03_UpperDie_v019", (0,0,4.63), (2.40,1.04,.28), STEEL,.055)
for x in (-1.10,1.10):
    cylinder(f"S03_DieGuidePost_{x:+.2f}_v019", (x,0,3.30), .075,2.50,STEEL,rotation=(0,0,0),vertices=32)
for y in (-.72,.72):
    box(f"S03_TransferRail_{y:+.2f}_v019", (0,y,2.34), (3.10,.10,.11), YELLOW,.022)
for x in (-1.15,-.58,0,.58,1.15):
    cylinder(f"S03_TransferRoller_{x:+.2f}_v019", (x,-.72,2.43), .055,.18,STEEL,rotation=(math.pi/2,0,0),vertices=24)

# Guarded operator-side throat treatment and service identification.
for side in (-1,1):
    box(f"S03_ThroatGuardPost_{side}_v019", (side*1.48,-1.23,3.16), (.08,.08,2.42), YELLOW,.022)
box("S03_ThroatGuardHeader_v019", (0,-1.23,4.38), (3.04,.08,.09), YELLOW,.022)
box("S03_StationIdentity_v019", (0,-1.108,7.46), (1.28,.035,.25), STEEL,.018)

# Join a new export copy while retaining modular source objects in the Blend.
source_parts=[obj for obj in collection.objects if obj.type in {"MESH","CURVE"}]
bpy.ops.object.select_all(action="DESELECT")
for obj in source_parts: obj.select_set(True)
bpy.context.view_layer.objects.active=source_parts[0]
bpy.ops.object.duplicate()
dupes=list(bpy.context.selected_objects)
for obj in dupes:
    if obj.type=="CURVE":
        bpy.context.view_layer.objects.active=obj; bpy.ops.object.convert(target="MESH")
bpy.ops.object.join()
export_obj=bpy.context.object; export_obj.name="SM_CA_MW_PressModulePrototype_v019"; export_obj.hide_render=True
export_obj["engineering_status"]="VISUAL_PROTOTYPE_TBC"; export_obj["collision_intent"]="NoCollision"; export_obj["runtime_authority"]="RETAINED_PRESS_STATION_ONLY"
bpy.ops.object.select_all(action="DESELECT"); export_obj.select_set(True); bpy.context.view_layer.objects.active=export_obj
bpy.ops.export_scene.fbx(filepath=str(FBX_OUT),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"})

scene.render.resolution_x=1500; scene.render.resolution_y=1500; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"
camera=bpy.data.objects.get("PressModule_v018_Camera")
if camera is None: raise RuntimeError("camera missing")
camera.name="PressModule_v019_Camera"
def look(obj,target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
ground_mat=bpy.data.materials.get("StudioGround") or GRAPHITE
bpy.ops.mesh.primitive_plane_add(size=26,location=(0,0,-.02)); floor=bpy.context.object; floor.name="ReviewOnlyFloor_v019"; floor.data.materials.append(ground_mat)
views=[
    ("01_full_operator_v019.png",(10.8,-13.8,7.2),(0,0,4.55),62),
    ("02_full_service_v019.png",(-10.8,-13.2,7.5),(0,0,4.55),62),
    ("03_tooling_front_v019.png",(0,-15.5,3.75),(0,0,3.75),68),
]
for filename,location,target,lens in views:
    camera.location=location; camera.data.lens=lens; look(camera,target); scene.render.filepath=str(RENDERS/filename); bpy.ops.render.render(write_still=True)
bpy.data.objects.remove(floor,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT),check_existing=False)

corners=[export_obj.matrix_world@Vector(c) for c in export_obj.bound_box]
bounds={"min":[min(p[i] for p in corners) for i in range(3)],"max":[max(p[i] for p in corners) for i in range(3)]}
dims=[bounds["max"][i]-bounds["min"][i] for i in range(3)]
failures=[]
if len(source_parts)<115: failures.append(f"part count too low {len(source_parts)}")
if dims[0]>4.95 or dims[1]>2.70 or dims[2]>9.40: failures.append(f"visual envelope escaped {dims}")
if FBX_OUT.stat().st_size<150000: failures.append("FBX implausibly small")
manifest={"$schema":"cairnwell/source/press-module-prototype-v019/v1","created_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_GUARDED_PART_BUILT_PRESS_MODULE__UNREAL_INTAKE_REQUIRED__NOT_PROMOTED","parent_blend":str(PARENT.relative_to(ROOT)).replace("\\","/"),"parent_sha256":PARENT_SHA,"asset_name":export_obj.name,"authored_part_count":len(source_parts),"added_refinement_parts":len(added),"vertices":len(export_obj.data.vertices),"polygons":len(export_obj.data.polygons),"bounds_m":bounds,"dimensions_m":dims,"dimensions_authority":"TBC_VISUAL_ENVELOPE_ONLY","collision_intent":"NoCollision","runtime_authority_added":False,"retained_assets_edited":False,"fbx":{"file":"FBX/"+FBX_OUT.name,"bytes":FBX_OUT.stat().st_size,"sha256":sha(FBX_OUT)},"renders":["Renders/"+v[0] for v in views]}
MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
validation={"status":"PASS__GUARDED_PART_BUILT_SOURCE_REFINEMENT__FRESH_VISUAL_AND_ISOLATED_UNREAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V019_SOURCE_NOT_RETAINED","authored_part_count":len(source_parts),"added_refinement_parts":len(added),"vertices":len(export_obj.data.vertices),"polygons":len(export_obj.data.polygons),"dimensions_m":dims,"retained_assets_edited":False,"promotion_authorized":False,"failures":failures}
VALIDATION.write_text(json.dumps(validation,indent=2),encoding="utf-8")
if failures: raise RuntimeError("; ".join(failures))
print(json.dumps(validation,indent=2))
