"""Fresh clean-shell child containing only Blender-approved inbound/store assets."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();BASE="/Game/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v003";MAP="/Game/LineBoss/Maps/LB_PressShop_CleanInboundStorage_v20260809_v004"
DEST="/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound"
LORRY_FBX=ROOT/r"SourceAssets\Candidate\PressShop\InboundCoilDelivery\LorryLoadedWrappedCoils_v20260809_v006\SM_CA_MW_InboundLorry_Approved_v006.fbx"
STAND_FBX=ROOT/r"SourceAssets\Candidate\PressShop\InboundCoilDelivery\MeshyAdjustableCoilStand_v20260809_v005\SM_CA_MW_AdjustableCoilStand_Approved_v005.fbx"
LORRY=DEST+"/SM_CA_MW_InboundLorry_Approved_v006";STAND=DEST+"/SM_CA_MW_AdjustableCoilStand_Approved_v005";COIL="/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005"
OUT=ROOT/r"Saved\Audits\PressShopIntegration\clean_inbound_storage_build_v20260809_v004.json";P=ROOT/r"Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap";E="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
lib=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError('fresh/protected invariant')
unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")
tasks=[]
for src,name in ((LORRY_FBX,"SM_CA_MW_InboundLorry_Approved_v006"),(STAND_FBX,"SM_CA_MW_AdjustableCoilStand_Approved_v005")):
 if not src.is_file():raise RuntimeError(f'missing {src}')
 t=unreal.AssetImportTask();t.set_editor_properties({'filename':str(src),'destination_path':DEST,'destination_name':name,'automated':True,'replace_existing':True,'replace_existing_settings':True,'save':True})
 o=unreal.FbxImportUI();o.set_editor_properties({'import_mesh':True,'import_as_skeletal':False,'import_materials':True,'import_textures':True,'mesh_type_to_import':unreal.FBXImportType.FBXIT_STATIC_MESH,'automated_import_should_detect_type':False});o.static_mesh_import_data.set_editor_properties({'combine_meshes':True,'generate_lightmap_u_vs':True,'auto_generate_collision':True,'import_uniform_scale':100.0});t.options=o;tasks.append(t)
tools.import_asset_tasks(tasks);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
lm,sm,cm=(lib.load_asset(x) for x in (LORRY,STAND,COIL))
if not all(isinstance(x,unreal.StaticMesh) for x in (lm,sm,cm)):raise RuntimeError('asset import/load')
def dims(m):return m.get_bounds().box_extent*2
ld,sd=dims(lm),dims(sm)
if not (1640<ld.x<1660 and 245<ld.y<265 and 390<ld.z<410):raise RuntimeError(f'lorry bounds {ld}')
if not (188<sd.x<192 and 44<sd.y<49 and 20<sd.z<24):raise RuntimeError(f'stand bounds {sd}')
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError('map child')
def spawn(label,mesh,loc,yaw=0,movable=False,tags=()):
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator(yaw=yaw));a.set_actor_label(label);a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC);a.tags=[unreal.Name(x) for x in ('LB.CleanRebuild.v20260809.v004','LB.Asset.NewApproved','LB.Asset.CandidateNotPromoted',*tags)];return a
# Unloading lorry: long axis north-south, four independent coils and eight independent stands.
lx,ly=-9000.0,-2500.0;spawn('LB_CLEAN_IN_Lorry_v006',lm,(lx,ly,0),90,True,('LB.Inbound.Lorry','LB.PlayerBuild.Reference'))
for i,dy in enumerate((-360,-120,120,360),1):
 cy=ly+dy;spawn(f'LB_CLEAN_IN_TrailerStand_{i:02d}_A',sm,(lx,cy-46,111),0,True,('LB.Inbound.CoilStand',));spawn(f'LB_CLEAN_IN_TrailerStand_{i:02d}_B',sm,(lx,cy+46,111),0,True,('LB.Inbound.CoilStand',));spawn(f'LB_CLEAN_IN_TrailerCoil_{i:02d}',cm,(lx,cy,180),0,True,('LB.Inbound.TrailerCoil','LB.Material.PackagedCoil'))
# Exactly 12 storage positions, 24 independently adjustable approved stands.
store=[]
for row,y in enumerate((2300,0,-2300),1):
 for col,x in enumerate((-6200,-3900,-1600,700),1):
  n=(row-1)*4+col;spawn(f'LB_CLEAN_PR003_Stand_{n:02d}_A',sm,(x,y-46,11),0,False,('LB.Station.PR003','LB.Storage.Stand'));spawn(f'LB_CLEAN_PR003_Stand_{n:02d}_B',sm,(x,y+46,11),0,False,('LB.Station.PR003','LB.Storage.Stand'));spawn(f'LB_CLEAN_PR003_Coil_{n:02d}',cm,(x,y,80),0,True,('LB.Station.PR003','LB.Material.PackagedCoil'));store.append((n,x,y))
if not levels.save_current_level():raise RuntimeError('save')
after=sha(P)
if after!=before:raise RuntimeError('protected changed')
mf=ROOT/r"Content\LineBoss\Maps\LB_PressShop_CleanInboundStorage_v20260809_v004.umap";OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_BUILD__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'map':MAP,'parent':BASE,'map_sha256':sha(mf),'lorry_mesh':LORRY,'stand_mesh':STAND,'coil_mesh':COIL,'lorry_count':1,'trailer_coils':4,'trailer_stands':8,'storage_positions':12,'storage_stands':24,'storage_layout':store,'lorry_bounds_cm':[ld.x,ld.y,ld.z],'stand_bounds_cm':[sd.x,sd.y,sd.z],'meshy_credits_used':0,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_CLEAN_INBOUND_STORAGE_V004_PASS')
