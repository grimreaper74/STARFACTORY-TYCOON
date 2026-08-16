"""Add and rebuild the local PR-004 operator/logistics navigation volume."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_navigation_build_v026.json"
LABEL = "LB_PR004_V026_NavBounds"
RECAST_LABEL = "LB_PR004_V026_RecastNavMesh"
BOOTSTRAP_LABEL = "LB_PR004_V026_NavigationBootstrap"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label() in {LABEL, RECAST_LABEL, BOOTSTRAP_LABEL}:
        actors.destroy_actor(actor)

volume = actors.spawn_actor_from_class(
    unreal.NavMeshBoundsVolume,
    unreal.Vector(-5050.0, -1950.0, 350.0),
    unreal.Rotator(),
)
if volume is None:
    raise RuntimeError("Could not spawn PR-004 navigation bounds volume")
volume.set_actor_label(LABEL)
volume.tags = [
    unreal.Name("LB.Asset.Candidate.v026"),
    unreal.Name("LB.PR004.Navigation"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]
# Default volume brush is 200 cm per axis. Cover 22 x 20 x 7 m locally,
# including operator access, both waste bins and the PR-005 transfer approach.
volume.set_actor_scale3d(unreal.Vector(11.0, 10.0, 3.5))
origin, extent = volume.get_actor_bounds(False, False)
size = [extent.x * 2.0, extent.y * 2.0, extent.z * 2.0]
if size[0] < 2000.0 or size[1] < 1800.0 or size[2] < 600.0:
    raise RuntimeError(f"Navigation bounds unexpectedly small: {size}")

bootstrap = actors.spawn_actor_from_class(
    unreal.LBPressShopNavigationBootstrap, unreal.Vector(-5050.0, -1950.0, 20.0), unreal.Rotator())
if bootstrap is None:
    raise RuntimeError("Could not spawn Press Shop navigation bootstrap")
bootstrap.set_actor_label(BOOTSTRAP_LABEL)
bootstrap.tags = [
    unreal.Name("LB.Asset.Candidate.v026"),
    unreal.Name("LB.PR004.Navigation"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]

world = unreal.EditorLevelLibrary.get_editor_world()
world_settings = world.get_world_settings()
nav_config = world_settings.get_editor_property("navigation_system_config")
nav_config_override = None
if nav_config is None:
    nav_config = unreal.new_object(
        unreal.NavigationSystemModuleConfig,
        outer=world_settings,
        name="LB_PR004_NavigationSystemConfig_v026",
    )
    nav_config.set_editor_property("strictly_static", False)
    nav_config.set_editor_property("auto_spawn_missing_nav_data", True)
    nav_config.set_editor_property("spawn_nav_data_in_nav_bounds_level", True)
    world_settings.set_editor_property("navigation_system_config", nav_config)
nav_config.set_editor_property(
    "navigation_system_class",
    unreal.SoftClassPath("/Script/NavigationSystem.NavigationSystemV1"),
)
unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
for actor in actors.get_all_level_actors():
    if isinstance(actor, unreal.RecastNavMesh):
        actor.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
        actor.set_editor_property("can_be_main_nav_data", True)
if not levels.save_current_level():
    raise RuntimeError("Could not save PR-004 navigation volume")

nav_actors = []
for actor in actors.get_all_level_actors():
    class_name = actor.get_class().get_name()
    if "Nav" in class_name or "Recast" in class_name:
        nav_actors.append({"label": actor.get_actor_label(), "class": class_name})

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-navigation-build-v026/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "LOCAL_NAV_BOUNDS_AUTHORED__RUNTIME_PATH_GATE_OPEN__NOT_PROMOTED",
    "map": MAP,
    "bounds_actor": LABEL,
    "bootstrap_actor": BOOTSTRAP_LABEL,
    "recast_actor_policy": "auto-spawned from non-null world NavigationSystemModuleConfig",
    "origin_cm": [origin.x, origin.y, origin.z],
    "size_cm": size,
    "navigation_actors": nav_actors,
    "world_navigation_system_config": nav_config.get_path_name() if nav_config is not None else None,
    "world_navigation_system_config_class": nav_config.get_class().get_name() if nav_config is not None else None,
    "world_navigation_system_class": str(nav_config.get_editor_property("navigation_system_class")) if nav_config is not None else None,
    "world_navigation_system_config_override": nav_config_override.get_path_name() if nav_config_override is not None else None,
    "runtime_path_passed": False,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_NAV_BUILD_PASS output={OUT} size={size}")
