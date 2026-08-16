"""Configure dynamic NavigationSystemV1 for clean v019 support-fleet bounds."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();SOURCE='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetNav_v20260809_v019';MAP='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetNav_v20260809_v020';OUT=ROOT/r'Saved\Audits\SupportRobots\clean_support_fleet_nav_config_v20260809_v020.json';P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError('fresh/protected invariant')
if not levels.new_level_from_template(MAP,SOURCE):raise RuntimeError('map child')
vol=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.NavMeshBoundsVolume)]
if len(vol)!=1:raise RuntimeError(f'nav bounds {len(vol)}')
world=unreal.EditorLevelLibrary.get_editor_world();settings=world.get_world_settings();config=unreal.new_object(unreal.NavigationSystemModuleConfig,outer=settings,name='LB_CleanSupportNavigationSystemConfig_v020');config.set_editor_property('strictly_static',False);config.set_editor_property('auto_spawn_missing_nav_data',True);config.set_editor_property('spawn_nav_data_in_nav_bounds_level',True);config.set_editor_property('navigation_system_class',unreal.SoftClassPath('/Script/NavigationSystem.NavigationSystemV1'));settings.set_editor_property('navigation_system_config',config)
unreal.SystemLibrary.execute_console_command(world,'RebuildNavigation');recasts=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.RecastNavMesh)]
for a in recasts:a.set_editor_property('runtime_generation',unreal.RuntimeGenerationType.DYNAMIC);a.set_editor_property('can_be_main_nav_data',True)
if not levels.save_current_level():raise RuntimeError('save')
after=sha(P)
if after!=before:raise RuntimeError('protected changed')
mf=ROOT/r'Content\LineBoss\Maps\LB_PressShop_CleanApprovedTrainsFleetNav_v20260809_v020.umap';OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_BUILD__NON_NULL_DYNAMIC_NAV_CONFIG__PIE_REPEAT_REQUIRED__NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'source':SOURCE,'map':MAP,'map_sha256':sha(mf),'config_class':config.get_class().get_name(),'auto_spawn_missing_nav_data':True,'recast_count_at_build':len(recasts),'v019_pie_status':'FAIL_EXPECTED__NO_NAV_SYSTEM_CONFIG','meshy_credits_used':0,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_CLEAN_SUPPORT_FLEET_NAV_CONFIG_V020_PASS')
