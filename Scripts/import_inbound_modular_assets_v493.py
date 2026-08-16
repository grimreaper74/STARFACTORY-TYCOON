"""Import/bind inbound Modular_v002 to an isolated Unreal candidate folder."""
from pathlib import Path
import hashlib,json,unreal
PROJECT=Path(unreal.Paths.project_dir());SOURCE=PROJECT/"SourceAssets/Candidate/PressShop/InboundCoilDelivery/Modular_v002/FBX";DEST="/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v002";MAT="/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001";OUT=Path(unreal.Paths.project_saved_dir())/"Audits/PressShopIntegration/inbound_modular_import_v493.json"
MODULES={
"SM_CA_MW_MOD_LorryCab_v002":((240,300),(260,340),(270,330)),"SM_CA_MW_MOD_CoilTrailer_v002":((220,300),(1000,1200),(300,450)),"SM_CA_MW_MOD_DockGuidesAndRestraint_v002":((280,380),(650,750),(50,100)),"SM_CA_MW_MOD_DockControlAndSignals_v002":((100,180),(30,100),(240,290)),"SM_CA_MW_MOD_ReceivingSaddle_v002":((240,300),(300,370),(80,130)),"SM_CA_MW_MOD_AGVHandoffGuides_v002":((220,290),(380,450),(20,60)),"SM_CA_MW_MOD_IdentityScanner_v002":((25,60),(20,50),(160,210)),"SM_CA_MW_MOD_EntranceDockEnvelope_v002":((550,650),(80,150),(450,520)),"SM_CA_MW_MOD_CraneBayStructure_v002":((650,720),(620,700),(620,680))}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
library=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0");tasks=[];hashes={}
for name in MODULES:
 p=SOURCE/f"{name}.fbx";hashes[name]=sha(p);task=unreal.AssetImportTask();task.set_editor_properties({"filename":str(p),"destination_path":DEST,"destination_name":name,"automated":True,"replace_existing":False,"save":True});options=unreal.FbxImportUI();options.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":False,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,"automated_import_should_detect_type":False});options.static_mesh_import_data.set_editor_properties({"combine_meshes":True,"convert_scene":True,"convert_scene_unit":True,"generate_lightmap_u_vs":True,"auto_generate_collision":True,"remove_degenerates":True,"import_uniform_scale":1.0});task.options=options;tasks.append(task)
tools.import_asset_tasks(tasks);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();rows=[]
for name,gates in MODULES.items():
 path=f"{DEST}/{name}";mesh=library.load_asset(path)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(f"Missing imported v002 mesh {path}")
 size=mesh.get_bounds().box_extent*2;actual=(float(size.x),float(size.y),float(size.z))
 for axis,value,gate in zip("XYZ",actual,gates):
  if not gate[0]<=value<=gate[1]:raise RuntimeError(f"{name} {axis}={value:.2f} outside {gate}")
 slots=[]
 for index,slot in enumerate(mesh.get_editor_property("static_materials")):
  slotname=str(slot.get_editor_property("material_slot_name"));mat=library.load_asset(f"{MAT}/{slotname}_v001")
  if mat is None:raise RuntimeError(f"Unknown v002 slot {slotname} on {name}")
  mesh.set_material(index,mat);slots.append(slotname)
 library.save_loaded_asset(mesh,only_if_is_dirty=False);rows.append({"asset":path,"bounds_cm":[round(v,3) for v in actual],"slots":slots,"source_sha256":hashes[name],"has_body_setup":mesh.get_editor_property("body_setup") is not None})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"candidate":"InboundCoilDelivery_Candidate_v002","parent":"Modular_v001","status":"PASS_ISOLATED_IMPORT_NOT_PROMOTED","engineering":"TBC","assets":rows},indent=2),encoding="utf-8");unreal.log("LINE_BOSS_INBOUND_IMPORT_V493_PASS "+str(OUT))
