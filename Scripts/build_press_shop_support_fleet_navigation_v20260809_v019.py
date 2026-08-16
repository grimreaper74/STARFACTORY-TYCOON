"""Add clean south service-corridor nav coverage and stable unit identities to v017."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();SOURCE='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetLit_v20260809_v017';MAP='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetNav_v20260809_v019';OUT=ROOT/r'Saved\Audits\SupportRobots\clean_support_fleet_navigation_build_v20260809_v019.json';P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError('fresh/protected invariant')
if not levels.new_level_from_template(MAP,SOURCE):raise RuntimeError('map child')
identity={'LB_CLEAN_Robot_CR01_01':'LB-CR01-01','LB_CLEAN_Robot_CR01_02':'LB-CR01-02','LB_CLEAN_Robot_MR01_01':'LB-MR01-01','LB_CLEAN_Robot_MR01_02':'LB-MR01-02'}
found={}
for a in actors.get_all_level_actors():
 if a.get_actor_label() in identity:
  uid=identity[a.get_actor_label()];a.tags=list(a.tags)+[unreal.Name('LB.SupportRobot.UnitId.'+uid),unreal.Name('LB.SupportRobot.CleanMap.v019')];found[uid]=a.get_actor_location()
if set(found)!=set(identity.values()):raise RuntimeError(found)
nav=actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume,unreal.Vector(0,-4100,350),unreal.Rotator());nav.set_actor_label('LB_CLEAN_SUPPORT_NavBounds_SouthService_v019');nav.set_actor_scale3d(unreal.Vector(95,7,3.5));nav.tags=[unreal.Name('LB.CleanRebuild.v20260809.v019'),unreal.Name('LB.Navigation.SupportFleet'),unreal.Name('LB.Asset.NewAuthored')]
world=unreal.EditorLevelLibrary.get_editor_world();unreal.SystemLibrary.execute_console_command(world,'RebuildNavigation');recast=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.RecastNavMesh)]
for a in recast:a.set_editor_property('runtime_generation',unreal.RuntimeGenerationType.DYNAMIC);a.set_editor_property('can_be_main_nav_data',True)
if not levels.save_current_level():raise RuntimeError('save')
after=sha(P)
if after!=before:raise RuntimeError('protected changed')
o,e=nav.get_actor_bounds(False);mf=ROOT/r'Content\LineBoss\Maps\LB_PressShop_CleanApprovedTrainsFleetNav_v20260809_v019.umap';OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_BUILD__CLEAN_SUPPORT_FLEET_LOCAL_NAV_AND_STABLE_IDENTITIES__PIE_ROUTE_AUDIT_REQUIRED__NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'source':SOURCE,'map':MAP,'map_sha256':sha(mf),'unit_locations_cm':{k:[v.x,v.y,v.z] for k,v in found.items()},'nav_bounds':{'origin':[o.x,o.y,o.z],'size':[e.x*2,e.y*2,e.z*2]},'recast_count':len(recast),'meshy_credits_used':0,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_CLEAN_SUPPORT_FLEET_NAV_V019_PASS')
