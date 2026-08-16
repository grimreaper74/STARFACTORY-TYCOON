"""Add retained 2x CR01, 2x MR01, four docks and balanced hall lighting to clean v015."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();SOURCE='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsPaint_v20260809_v015';MAP='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetLit_v20260809_v017'
OUT=ROOT/r'Saved\Audits\PressShopIntegration\clean_approved_trains_fleet_lit_v20260809_v017.json';P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError('fresh/protected invariant')
paths={'cr01':'/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v065/Blueprints/BP_LB_CR01_CleaningAMR_v065','mr01':'/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v022/Blueprints/BP_LB_MR01_MaintenanceAMR_v022','crdock':'/Game/LineBoss/SupportRobots/ServiceDocks/Runtime_v026/CR01/SM_LB_CR01_ServiceDock_Static_v026','mrdock':'/Game/LineBoss/SupportRobots/ServiceDocks/Runtime_v026/MR01/SM_LB_MR01_ServiceDock_Static_v026'}
assets={k:lib.load_asset(v) for k,v in paths.items()}
if not all(assets.values()):raise RuntimeError(f'asset load {assets}')
if not levels.new_level_from_template(MAP,SOURCE):raise RuntimeError('map child')

placements=[('CR01_01','cr01','crdock',-750),('CR01_02','cr01','crdock',-250),('MR01_01','mr01','mrdock',250),('MR01_02','mr01','mrdock',750)]
installed=[]
for unit,robot_key,dock_key,x in placements:
 d=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,-4380,0),unreal.Rotator(yaw=90));d.set_actor_label(f'LB_CLEAN_Dock_{unit}');d.static_mesh_component.set_static_mesh(assets[dock_key]);d.tags=[unreal.Name(t) for t in ('LB.CleanRebuild.v20260809.v017','LB.SupportFleet.Dock','LB.Asset.RetainedStandalone','LB.PlayerBuild.Reference',f'LB.SupportFleet.{unit}')]
 r=actors.spawn_actor_from_class(assets[robot_key].generated_class(),unreal.Vector(x,-4050,0),unreal.Rotator(yaw=90));r.set_actor_label(f'LB_CLEAN_Robot_{unit}');r.tags=[unreal.Name(t) for t in ('LB.CleanRebuild.v20260809.v017','LB.SupportFleet.Robot','LB.Asset.RetainedStandalone','LB.PlayerBuild.Reference',f'LB.SupportFleet.{unit}')]
 ro,re=r.get_actor_bounds(False);bottom=ro.z-re.z;r.set_actor_location(unreal.Vector(x,-4050,-bottom),False,False)
 installed.extend((d,r))

# Four independently marked reverse-docking berths, clear of the AGV trunk at Y=-4650.
cube=lib.load_asset('/Engine/BasicShapes/Cube.Cube');M='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v001/Materials/';yellow=lib.load_asset(M+'M_LB_CleanShell_SafetyYellow_v001');white=lib.load_asset(M+'M_LB_CleanShell_MarkingWhite_v001');green=lib.load_asset(M+'M_LB_CleanShell_WalkwayGreen_v001')
def paint(label,loc,dims,mat,tags):
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(label);c=a.static_mesh_component;c.set_static_mesh(cube);c.set_world_scale3d(unreal.Vector(dims[0]/100,dims[1]/100,dims[2]/100));c.set_material(0,mat);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_editor_property('can_ever_affect_navigation',False);c.set_cast_shadow(False);a.tags=[unreal.Name(x) for x in ('LB.CleanRebuild.v20260809.v017','LB.FloorPaint.PlacementLinked',*tags)];return a
for unit,_,_,x in placements:
 paint(f'LB_PAINT_DockBay_{unit}',(x,-4215,4),(360,560,2),green,('LB.FloorPaint.SupportDockBay',f'LB.SupportFleet.{unit}'))
 for sx in (-180,180):paint(f'LB_PAINT_DockEdge_{unit}_{sx}',(x+sx,-4215,5),(10,560,2),yellow,('LB.FloorPaint.SupportDockEdge',))
 paint(f'LB_PAINT_DockStop_{unit}',(x,-4490,5),(370,10,2),white,('LB.FloorPaint.SupportDockStop',))

# Balance the hall rather than relying on capture-only exposure commands.
for a in actors.get_all_level_actors():
 if isinstance(a,unreal.RectLight) and a.get_actor_label().startswith('LB_CLEAN_Light_'):
  c=a.get_component_by_class(unreal.RectLightComponent);c.set_editor_property('intensity',26000.0);c.set_editor_property('source_width',1100.0);c.set_editor_property('source_height',320.0)
 if isinstance(a,unreal.SkyLight) and a.get_actor_label()=='LB_CLEAN_Light_Sky':a.get_component_by_class(unreal.SkyLightComponent).set_editor_property('intensity',1.8)
for x in (1000,5000,9000):
 for y in (-3300,-1100,1100,3300):
  l=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(x,y-250,1050),unreal.Rotator(-90,0,0));l.set_actor_label(f'LB_CLEAN_TrainFill_{x}_{y}');c=l.get_component_by_class(unreal.RectLightComponent);c.set_editor_properties({'intensity':16000.0,'source_width':650.0,'source_height':180.0,'light_color':unreal.Color(220,235,255,255)});l.tags=[unreal.Name('LB.CleanRebuild.v20260809.v017'),unreal.Name('LB.Lighting.TrainFill')]

# Bounds/route clearance audit: keep every installed unit north of AGV Y=-4650 and south of Train A safety Y=-3470.
bounds=[]
for a in installed:
 o,e=a.get_actor_bounds(False);rec={'label':a.get_actor_label(),'origin':[o.x,o.y,o.z],'extent':[e.x,e.y,e.z],'min_y':o.y-e.y,'max_y':o.y+e.y};bounds.append(rec)
if any(b['min_y']<=-4590 or b['max_y']>=-3500 for b in bounds):raise RuntimeError(f'fleet clearance {bounds}')
if any(abs((b['origin'][2]-b['extent'][2]))>0.25 for b in bounds if '_Robot_' in b['label']):raise RuntimeError(f'robot floor contact {bounds}')
if not levels.save_current_level():raise RuntimeError('save')
after=sha(P)
if after!=before:raise RuntimeError('protected changed')
mf=ROOT/r'Content\LineBoss\Maps\LB_PressShop_CleanApprovedTrainsFleetLit_v20260809_v017.umap';OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_BUILD__TWO_CR01_TWO_MR01_FOUR_DOCKS__EXACT_FLOOR_CONTACT__ROUTE_CLEARANCE_PASS__BALANCED_LIGHTING__VISUAL_AND_RUNTIME_SWEEP_REVIEW_REQUIRED__NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'source':SOURCE,'map':MAP,'map_sha256':sha(mf),'assets':paths,'placements':placements,'installed_bounds':bounds,'clearance_contract_cm':{'agv_trunk_y':-4650,'fleet_min_y_gt':-4590,'train_a_safety_y':-3470,'fleet_max_y_lt':-3500,'robot_bottom_z_tolerance':0.25},'counts':{'cr01':2,'mr01':2,'docks':4,'train_fill_lights':12},'v016_status':'REJECTED_DIAGNOSTIC_ONLY__ROBOT_BLUEPRINT_ORIGINS_LEFT_UNDERCARRIAGE_BELOW_FLOOR','meshy_credits_used':0,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_CLEAN_SUPPORT_FLEET_LIGHTING_V017_PASS')
