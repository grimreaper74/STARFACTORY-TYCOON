"""Export v022's sixteen organised groups as a reusable Train A-D module kit."""
import bpy, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v022/CA_MW_PressModulePrototype_v022.blend"
SOURCE_SHA="9B3A72FB41B5C52C928B77E165898B15FD3370A357CCCF1CD791593989DE9A51"
REF_SHA="4638AAD84029DFAD74941CCD0586B182E4F39D4EE6230E3D87B388BF87E95DFD"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/Shared/PressBodyModuleLibrary_v024"
FBX_DIR=OUT/"FBX"; MANIFEST=OUT/"PRESS_BODY_MODULE_LIBRARY_MANIFEST_v024.json"; VALIDATION=OUT/"PRESS_BODY_MODULE_LIBRARY_VALIDATION_v024.json"
for d in (OUT,FBX_DIR): d.mkdir(parents=True,exist_ok=True)
if MANIFEST.exists() or VALIDATION.exists() or any(FBX_DIR.glob("*.fbx")): raise RuntimeError("refusing to overwrite v024")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""): h.update(c)
    return h.hexdigest().upper()
if sha(SOURCE)!=SOURCE_SHA: raise RuntimeError("v022 source hash drift")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
root=bpy.data.collections.get("CA_MW_PressModulePrototype_v022")
if not root: raise RuntimeError("v022 root missing")
keys=("01_DriveMotorEnclosure","02_CrownCrosshead","03_MainHydraulicCylinders","04_UpperUprights","05_RamSlide","06_GuidesWearPlates","07_BolsterTooling","08_BedPlateFixed","09_TransferClearance","10_LowerUprights","11_HydraulicManifold","12_ElectricalCabinet","13_OperatorHMI","14_SafetyGuarding","15_ServicePlatformAccess","16_FoundationAnchors")
common={"01_DriveMotorEnclosure","02_CrownCrosshead","03_MainHydraulicCylinders","04_UpperUprights","05_RamSlide","06_GuidesWearPlates","08_BedPlateFixed","10_LowerUprights","11_HydraulicManifold","12_ElectricalCabinet","13_OperatorHMI","14_SafetyGuarding","15_ServicePlatformAccess","16_FoundationAnchors"}
variant={"07_BolsterTooling":"S03_RESTRIKE_FORM_VARIANT","09_TransferClearance":"SHARED_INTERFACE_WITH_STATION_SPECIFIC_TOOLING"}
groups={}
for k in keys:
    c=next((x for x in root.children if x.name.startswith(k)),None)
    if not c: raise RuntimeError("missing group "+k)
    groups[k]=c
records=[]; failures=[]
for k in keys:
    objects=[o for o in groups[k].objects if o.type in {"MESH","CURVE","FONT"}]
    if not objects: failures.append(k+" empty"); continue
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects: o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]; bpy.ops.object.duplicate(); dupes=list(bpy.context.selected_objects)
    for o in dupes:
        if o.type in {"CURVE","FONT"}: bpy.context.view_layer.objects.active=o; bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join(); export=bpy.context.object; export.name="SM_CA_MW_PressBody_"+k+"_v024"
    export["module_scope"]="SHARED_TRAIN_A_D" if k in common else variant[k]
    export["engineering_status"]="VISUAL_TBC"; export["collision_intent"]="NoCollision_SOURCE_ONLY"; export["runtime_authority"]="NONE_SOURCE_ONLY"
    corners=[export.matrix_world@Vector(c) for c in export.bound_box]; dims=[max(p[i] for p in corners)-min(p[i] for p in corners) for i in range(3)]
    fbx=FBX_DIR/(export.name+".fbx")
    bpy.ops.object.select_all(action="DESELECT"); export.select_set(True); bpy.context.view_layer.objects.active=export
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"})
    records.append({"group":k,"scope":"SHARED_S02_S06_AND_TRAINS_A_D" if k in common else variant[k],"source_part_count":len(objects),"vertices":len(export.data.vertices),"polygons":len(export.data.polygons),"dimensions_m_tbc":dims,"fbx":"FBX/"+fbx.name,"bytes":fbx.stat().st_size,"sha256":sha(fbx),"origin_policy":"PRESERVE_V022_COMMON_STATION_DATUM"})
    bpy.data.objects.remove(export,do_unlink=True)
if len(records)!=16: failures.append(f"exported module count {len(records)} != 16")
if sum(x["source_part_count"] for x in records)!=537: failures.append(f"part conservation {sum(x['source_part_count'] for x in records)} != 537")
if any(x["bytes"]<1000 for x in records): failures.append("implausibly small module FBX")
manifest={"$schema":"cairnwell/source/press-body-module-library-v024/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_REUSABLE_PRESS_BODY_MODULE_LIBRARY__UNREAL_INTAKE_AND_WHOLE_TRAIN_ASSEMBLY_REQUIRED__NOT_PROMOTED","source":{"path":str(SOURCE.relative_to(ROOT)).replace('\\','/'),"sha256":SOURCE_SHA},"complete_train_reference_sha256":REF_SHA,"reuse_contract":{"trains":["A","B","C","D"],"shared_press_stations":["S02","S03","S04","S05","S06"],"dedicated_cells":["S01","S07"],"identity_variation":["train signs","accent materials","HMI identity","tooling","EOAT","workpieces","bins and stillages","runtime recipes and counts"]},"modules":records,"total_source_parts":sum(x["source_part_count"] for x in records),"retained_assets_edited":False,"runtime_authority_added":False,"promotion_authorized":False}
MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
validation={"status":"PASS__SIXTEEN_REUSABLE_MODULE_EXPORTS__EXACT_PART_CONSERVATION__NOT_PROMOTED" if not failures else "FAIL__V024_MODULE_LIBRARY_NOT_RETAINED","module_count":len(records),"common_module_count":sum(1 for x in records if x["group"] in common),"variant_or_interface_module_count":sum(1 for x in records if x["group"] not in common),"total_source_parts":sum(x["source_part_count"] for x in records),"retained_assets_edited":False,"promotion_authorized":False,"failures":failures}
VALIDATION.write_text(json.dumps(validation,indent=2),encoding="utf-8")
if failures: raise RuntimeError('; '.join(failures))
print(json.dumps(validation,indent=2))
