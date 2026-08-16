"""Build clean A-D trains from Blender-approved modular assets and paint operational floor zones."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE="/Game/LineBoss/Maps/LB_PressShop_CleanInboundStorageFit_v20260809_v005"
MAP="/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsPaint_v20260809_v013"
DEST="/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v013/PressTrains"
MODULE_DIR=Path(r"C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\TrainA\NewApprovedAssembly_v20260809_v005\RuntimeModules_v006")
OUT=ROOT/r"Saved\Audits\PressShopIntegration\clean_approved_trains_paint_v20260809_v013.json"
PROTECTED=ROOT/r"Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"

lib=unreal.EditorAssetLibrary; tools=unreal.AssetToolsHelpers.get_asset_tools()
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper(); before=sha(PROTECTED)
if before!=EXPECTED or lib.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError("fresh/protected invariant")

files={
 "station":"SM_CA_MW_PressStation_S02_S06_Approved_v006.fbx",
 "roller":"SM_CA_MW_InterstageRoller_Approved_v006.fbx",
 "s01":"SM_CA_MW_S01_Destack_Approved_v006.fbx",
 "s07":"SM_CA_MW_S07_UnloadRobot_Static_v006.fbx",
}
unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")
tasks=[]
for key,filename in files.items():
 src=MODULE_DIR/filename
 if not src.is_file(): raise RuntimeError(f"missing {src}")
 name=src.stem
 t=unreal.AssetImportTask(); t.set_editor_properties({'filename':str(src),'destination_path':DEST,'destination_name':name,'automated':True,'replace_existing':True,'replace_existing_settings':True,'save':True})
 o=unreal.FbxImportUI(); o.set_editor_properties({'import_mesh':True,'import_as_skeletal':False,'import_materials':True,'import_textures':True,'mesh_type_to_import':unreal.FBXImportType.FBXIT_STATIC_MESH,'automated_import_should_detect_type':False})
 o.static_mesh_import_data.set_editor_properties({'combine_meshes':True,'generate_lightmap_u_vs':True,'auto_generate_collision':True,'import_uniform_scale':1.0})
 t.options=o; tasks.append(t)
tools.import_asset_tasks(tasks); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
paths={k:f"{DEST}/{Path(v).stem}" for k,v in files.items()}
meshes={k:lib.load_asset(p) for k,p in paths.items()}
if not all(isinstance(v,unreal.StaticMesh) for v in meshes.values()): raise RuntimeError(f"module import failed {meshes}")

if not levels.new_level_from_template(MAP,SOURCE): raise RuntimeError("map child failed")
cube=lib.load_asset('/Engine/BasicShapes/Cube.Cube')
M='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v001/Materials/'
mats={
 'green':lib.load_asset(M+'M_LB_CleanShell_WalkwayGreen_v001'),
 'yellow':lib.load_asset(M+'M_LB_CleanShell_SafetyYellow_v001'),
 'red':lib.load_asset(M+'M_LB_CleanShell_SignalRed_v001'),
 'white':lib.load_asset(M+'M_LB_CleanShell_MarkingWhite_v001'),
}
# Blue AGV material is newly authored because it was not part of the fixed shell palette.
blue_path='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v013/Materials/M_LB_AGVRouteBlue_v013'
mat_dir,mat_name=blue_path.rsplit('/',1)
blue=tools.create_asset(mat_name,mat_dir,unreal.Material,unreal.MaterialFactoryNew())
mel=unreal.MaterialEditingLibrary; c=mel.create_material_expression(blue,unreal.MaterialExpressionConstant3Vector,-300,0);c.set_editor_property('constant',unreal.LinearColor(0.02,0.25,0.72,1));r=mel.create_material_expression(blue,unreal.MaterialExpressionConstant,-300,120);r.set_editor_property('r',0.48);mel.connect_material_property(c,'',unreal.MaterialProperty.MP_BASE_COLOR);mel.connect_material_property(r,'',unreal.MaterialProperty.MP_ROUGHNESS);mel.recompile_material(blue);lib.save_loaded_asset(blue);mats['blue']=blue
if not all(mats.values()): raise RuntimeError('paint material load')

created=[]
def spawn_mesh(label,mesh,loc,yaw=0,scale=1.0,tags=()):
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator(yaw=yaw));a.set_actor_label(label);a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_world_scale3d(unreal.Vector(scale,scale,scale));a.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC);a.tags=[unreal.Name(x) for x in ('LB.CleanRebuild.v20260809.v013','LB.Asset.NewApproved','LB.PlayerBuild.Reference',*tags)];created.append(a);return a
def paint(label,loc,dims,mat,tags=()):
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(label);c=a.static_mesh_component;c.set_static_mesh(cube);c.set_world_scale3d(unreal.Vector(dims[0]/100,dims[1]/100,dims[2]/100));c.set_material(0,mat);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_editor_property('can_ever_affect_navigation',False);c.set_cast_shadow(False);a.tags=[unreal.Name(x) for x in ('LB.CleanRebuild.v20260809.v013','LB.FloorPaint.PlacementLinked',*tags)];created.append(a);return a

train_rows={'A':-3300.0,'B':-1100.0,'C':1100.0,'D':3300.0}; centre_x=5000.0
stations=(-2400,-1200,0,1200,2400); rollers=(-3100,-1800,-600,600,1800,3100)
for train,y in train_rows.items():
 spawn_mesh(f'LB_CLEAN_Train{train}_S01_Destack',meshes['s01'],(centre_x-4000,y,0),-90,.72,(f'LB.PressTrain.{train}','LB.Station.S01'))
 for stage,dx in zip(range(2,7),stations):
  spawn_mesh(f'LB_CLEAN_Train{train}_S{stage:02d}_Press',meshes['station'],(centre_x+dx,y,0),0,1.0,(f'LB.PressTrain.{train}',f'LB.Station.S{stage:02d}'))
 for i,dx in enumerate(rollers,1):
  spawn_mesh(f'LB_CLEAN_Train{train}_Roller_{i:02d}',meshes['roller'],(centre_x+dx,y,0),-90,2.2,(f'LB.PressTrain.{train}','LB.Module.RollerBed'))
 spawn_mesh(f'LB_CLEAN_Train{train}_S07_UnloadRobot',meshes['s07'],(centre_x+4000,y+300,0),180,2.3,(f'LB.PressTrain.{train}','LB.Station.S07','LB.StaticVisual.PendingJointRepair'))
 spawn_mesh(f'LB_CLEAN_Train{train}_S07_DischargeRoller',meshes['roller'],(centre_x+3600,y,0),-90,2.2,(f'LB.PressTrain.{train}','LB.Station.S07','LB.Module.RollerBed'))
 # Green operator-side walkway plus safety perimeter and individual machine footprints.
 paint(f'LB_PAINT_Train{train}_OperatorWalkway',(centre_x,y-245,1.2),(8400,150,2),mats['green'],('LB.FloorPaint.Walkway',f'LB.PressTrain.{train}'))
 paint(f'LB_PAINT_Train{train}_SafetyNorth',(centre_x,y+170,1.8),(8400,10,2),mats['yellow'],('LB.FloorPaint.SafetyBoundary',))
 paint(f'LB_PAINT_Train{train}_SafetySouth',(centre_x,y-170,1.8),(8400,10,2),mats['yellow'],('LB.FloorPaint.SafetyBoundary',))
 paint(f'LB_PAINT_Train{train}_SafetyWest',(800,y,1.8),(10,350,2),mats['yellow'],('LB.FloorPaint.SafetyBoundary',))
 paint(f'LB_PAINT_Train{train}_SafetyEast',(9200,y,1.8),(10,350,2),mats['yellow'],('LB.FloorPaint.SafetyBoundary',))
 for stage,dx in zip(range(2,7),stations):
  paint(f'LB_PAINT_Train{train}_S{stage:02d}_Footprint',(centre_x+dx,y,2.4),(850,285,2),mats['white'],('LB.FloorPaint.EquipmentFootprint',f'LB.Station.S{stage:02d}'))

# Main AGV loop and four train handoff spurs, painted as blue route centre-lines.
for label,loc,dims in [
 ('SouthTrunk',(0,-4650,2.6),(18800,12,2)),('NorthTrunk',(0,4650,2.6),(18800,12,2)),
 ('WestReturn',(-9400,0,2.6),(12,9300,2)),('EastReturn',(9400,0,2.6),(12,9300,2)),
 ('InboundLink',(-7000,-3900,2.6),(4800,12,2)),('StorageNorth',(-3000,3900,2.6),(8000,12,2))]:
 paint('LB_PAINT_AGV_'+label,loc,dims,mats['blue'],('LB.FloorPaint.AGVRoute','LB.PlayerBuild.DynamicRouteReference'))
for train,y in train_rows.items():
 paint(f'LB_PAINT_AGV_Train{train}_Handoff',(9500,y,2.6),(600,12,2),mats['blue'],('LB.FloorPaint.AGVHandoff',f'LB.PressTrain.{train}'))

# Protected zebra crossings between support/perimeter walkways and production routes.
crossings=[]
for x in (-9000,0,9000):
 for y in (-4650,4650):
  for n in range(7):
   paint(f'LB_PAINT_Crossing_{x}_{y}_{n}',(x-120+n*40,y,3.2),(22,190,2),mats['white'],('LB.FloorPaint.PedestrianCrossing',));crossings.append((x,y,n))

# Inbound overhead-crane exclusion and wrapped-coil storage boundary.
for label,loc,dims in [('N',(-8200,4100,3.8),(4800,10,2)),('S',(-8200,-4100,3.8),(4800,10,2)),('W',(-10600,0,3.8),(10,8200,2)),('E',(-5800,0,3.8),(10,8200,2))]: paint('LB_PAINT_CraneExclusion_'+label,loc,dims,mats['red'],('LB.FloorPaint.CraneExclusion',))
for label,loc,dims in [('N',(-2750,3500,3.8),(7600,10,2)),('S',(-2750,-3500,3.8),(7600,10,2)),('W',(-6550,0,3.8),(10,7000,2)),('E',(1050,0,3.8),(10,7000,2))]: paint('LB_PAINT_CoilStorage_'+label,loc,dims,mats['yellow'],('LB.FloorPaint.StorageBoundary',))

if not levels.save_current_level(): raise RuntimeError('save failed')
after=sha(PROTECTED)
if after!=before: raise RuntimeError('protected changed')
map_file=ROOT/r'Content\LineBoss\Maps\LB_PressShop_CleanApprovedTrainsPaint_v20260809_v013.umap'
bounds={k:[(m.get_bounds().box_extent*2).x,(m.get_bounds().box_extent*2).y,(m.get_bounds().box_extent*2).z] for k,m in meshes.items()}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_BUILD__NEW_APPROVED_MODULAR_TRAINS_A_D__PLACEMENT_LINKED_FLOOR_PAINT__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'source':SOURCE,'map':MAP,'map_sha256':sha(map_file),'module_assets':paths,'module_bounds_cm':bounds,'train_rows_cm':train_rows,'train_centre_x_cm':centre_x,'train_count':4,'press_station_count':20,'roller_count':28,'s01_count':4,'s07_static_visual_count':4,'paint':{'operator_walkways':4,'train_safety_boundaries':16,'equipment_footprints':20,'agv_route_segments':10,'zebra_bars':len(crossings),'crane_exclusion_edges':4,'storage_boundary_edges':4},'player_build_reference':True,'s07_status':'STATIC_VISUAL_PENDING_JOINT_REPAIR','meshy_credits_used':0,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8')
unreal.log('LINE_BOSS_CLEAN_APPROVED_TRAINS_PAINT_V013_PASS')
