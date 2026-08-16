"""Correct v663 navigation world settings and bake fresh Recast data."""
import json,unreal
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v663";MAP="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v665";OUT=ROOT/r"Saved\Audits\PressTrains\complete_train_a_navigation_build_v665.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);library=unreal.EditorAssetLibrary
if library.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("Refusing to overwrite v665")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("Could not derive v665")
volumes=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.NavMeshBoundsVolume)]
if len(volumes)!=1:raise RuntimeError(f"Expected one nav bounds volume, got {len(volumes)}")
origin,extent=volumes[0].get_actor_bounds(False,False);size=[extent.x*2,extent.y*2,extent.z*2]
if size[0]<2500 or size[1]<6500 or size[2]<900:raise RuntimeError(f"Nav bounds too small {size}")
world=unreal.EditorLevelLibrary.get_editor_world();settings=world.get_world_settings();config=settings.get_editor_property("navigation_system_config")
if config is None:config=unreal.new_object(unreal.NavigationSystemModuleConfig,outer=settings,name="LB_TrainA_NavigationSystemConfig_v665")
config.set_editor_property("strictly_static",False);config.set_editor_property("auto_spawn_missing_nav_data",True);config.set_editor_property("spawn_nav_data_in_nav_bounds_level",True);config.set_editor_property("navigation_system_class",unreal.SoftClassPath("/Script/NavigationSystem.NavigationSystemV1"));settings.set_editor_property("navigation_system_config",config)
unreal.SystemLibrary.execute_console_command(world,"RebuildNavigation")
recasts=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.RecastNavMesh)]
for recast in recasts:recast.set_editor_property("runtime_generation",unreal.RuntimeGenerationType.DYNAMIC);recast.set_editor_property("can_be_main_nav_data",True)
if not levels.save_current_level():raise RuntimeError("Failed saving v665")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v665","status":"PASS__NON_NULL_DYNAMIC_NAV_CONFIGURATION__PIE_PENDING","map":MAP,"source":BASE,"bounds_origin_cm":[origin.x,origin.y,origin.z],"bounds_size_cm":size,"recast_actor_count":len(recasts),"auto_spawn_missing_nav_data":True,"protected_map_modified":False,"promotion_authorized":False},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_TRAIN_A_NAV_BUILD_V665_PASS")
