"""Create the isolated Body Shop prototype shell exactly once.

This is intentionally a map-only authoring script. It creates
/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001
only when that package does not already exist, verifies the currently compiled
isolated Body Shop classes before making a map, and never loads or modifies the
campaign, Press Shop v913, legacy Body Weld actor, project defaults, or assets.

The map deliberately contains zero Body Shop production cells or runtime
authorities. Its one map-owned gameplay actor is the experimental bootstrap.
The isolated GameMode creates one BuildAuthority and one PrototypeRuntime only
from BeginPlay, then the runtime constructs the first underbody slice.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = ROOT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
AUDIT = ROOT / "Saved/Audits/BodyShop/v001/body_shop_prototype_map_create_v001.json"

GAME_MODE_CLASS_PATH = "/Script/LineBossCarFactory.LBBodyShopPrototypeGameMode"
PAWN_CLASS_PATH = "/Script/LineBossCarFactory.LBBodyShopManagementPawn"
HUD_CLASS_PATH = "/Script/LineBossCarFactory.LBBodyShopPrototypeHUD"
BOOTSTRAP_CLASS_PATH = "/Script/LineBossCarFactory.LBBodyShopPrototypeWorldBootstrap"
BUILD_AUTHORITY_CLASS_PATH = "/Script/LineBossCarFactory.LBBodyShopBuildAuthority"
RUNTIME_CLASS_PATH = "/Script/LineBossCarFactory.LBBodyShopPrototypeRuntime"

MAP_TAG = "LB.BodyShop.Experimental.v001"
ENV_TAG = "LB.BodyShop.Environment"
SHELL_TAG = "LB.BodyShop.Environment.Shell"
STRUCTURE_TAG = "LB.BodyShop.Environment.Structure"
GRID_TAG = "LB.BodyShop.Environment.Grid.100cm"
INTERFACE_TAG = "LB.BodyShop.Interface"
CUTAWAY_TAG = "LB.BodyShop.Environment.ManagementCutaway"

WIDTH_CM = 18_000.0
DEPTH_CM = 9_000.0
CLEAR_HEIGHT_CM = 1_650.0
BUILD_HALF_X_CM = 7_600.0
BUILD_HALF_Y_CM = 2_600.0
GRID_CM = 100.0


def require_class(path: str):
    loaded = unreal.load_class(None, path)
    if loaded is None:
        raise RuntimeError(
            "Required Body Shop class is not in the currently compiled editor "
            f"module: {path}. Build/reload the isolated Body Shop code before "
            "creating this map."
        )
    return loaded


def require_asset(path: str, expected_type=None):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        asset = unreal.load_asset(path)
    if asset is None or (expected_type is not None and not isinstance(asset, expected_type)):
        raise RuntimeError(f"Required existing environment asset is unavailable: {path}")
    return asset


def set_property(owner, candidates, value):
    """Set a reflected property while tolerating UE's Python b-prefix mapping."""
    errors = []
    for name in candidates:
        try:
            owner.set_editor_property(name, value)
            return name
        except Exception as exc:  # UE varies the Python spelling for bFoo fields.
            errors.append(f"{name}: {exc}")
    raise RuntimeError(
        f"Could not set {candidates} on {owner.get_name()}: " + " | ".join(errors)
    )


def get_property(owner, candidates):
    for name in candidates:
        try:
            return name, owner.get_editor_property(name)
        except Exception:
            pass
    return None, None


def set_tags(actor, tags):
    actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])


def box(actors, cube, label, location, dimensions, material, tags,
        rotation=(0.0, 0.0, 0.0), collision=False, cast_shadow=False):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation)
    )
    if actor is None:
        raise RuntimeError(f"Could not create map shell actor {label}")
    actor.set_actor_label(label)
    set_tags(actor, [MAP_TAG, ENV_TAG] + list(tags))
    actor.set_actor_scale3d(unreal.Vector(
        dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0
    ))
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(cube)
    component.set_material(0, material)
    component.set_collision_enabled(
        unreal.CollisionEnabled.QUERY_AND_PHYSICS
        if collision else unreal.CollisionEnabled.NO_COLLISION
    )
    component.set_editor_property("can_ever_affect_navigation", False)
    component.set_cast_shadow(cast_shadow)
    return actor


def light(actors, label, location, rotation, intensity, source_width, source_height):
    actor = actors.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(*location), unreal.Rotator(*rotation)
    )
    if actor is None:
        raise RuntimeError(f"Could not create light {label}")
    actor.set_actor_label(label)
    set_tags(actor, [MAP_TAG, ENV_TAG, "LB.BodyShop.Environment.Lighting"])
    component = actor.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_properties({
        "intensity": float(intensity),
        "attenuation_radius": 4_200.0,
        "source_width": float(source_width),
        "source_height": float(source_height),
    })
    return actor


def camera(actors, label, location, target, fov):
    actor = actors.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(*location), unreal.Rotator()
    )
    if actor is None:
        raise RuntimeError(f"Could not create review camera {label}")
    actor.set_actor_label(label)
    set_tags(actor, [MAP_TAG, ENV_TAG, "LB.BodyShop.Environment.ReviewCamera"])
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(
            actor.get_actor_location(), unreal.Vector(*target)
        ),
        False,
    )
    actor.get_editor_property("camera_component").set_editor_properties({
        "field_of_view": float(fov),
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    return actor


def class_path(value):
    return value.get_path_name() if value is not None else None


def world_partition_status(world):
    """Report the supported API result; an empty basic level must not be WP."""
    getter = getattr(world, "get_world_partition", None)
    if callable(getter):
        partition = getter()
        return {
            "api_available": True,
            "enabled": partition is not None,
            "object": partition.get_path_name() if partition is not None else None,
        }
    _, partition = get_property(world, ("world_partition",))
    return {
        "api_available": partition is not None,
        "enabled": partition is not None,
        "object": class_path(partition),
    }


def validate_current_map(classes, actors):
    """Creation-time checks duplicated independently in the validator script."""
    failures = []
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world is None:
        failures.append("editor world is unavailable")
        return failures, {}

    settings = world.get_world_settings()
    game_mode = settings.get_editor_property("default_game_mode")
    if game_mode != classes["game_mode"]:
        failures.append(
            "WorldSettings.default_game_mode is not "
            "ALBBodyShopPrototypeGameMode"
        )

    partition = world_partition_status(world)
    if partition["enabled"]:
        failures.append("prototype map unexpectedly uses World Partition")

    map_actors = list(actors.get_all_level_actors())
    bootstrap_actors = [
        actor for actor in map_actors
        if actor.get_class().get_name() == "LBBodyShopPrototypeWorldBootstrap"
    ]
    if len(bootstrap_actors) != 1:
        failures.append(f"expected one bootstrap actor, found {len(bootstrap_actors)}")

    production_fragments = (
        "LBBodyShopCellActor",
        "LBBodyShopBuildAuthority",
        "LBBodyShopPrototypeRuntime",
        "LBBodyWeldLineActor",
        "LBPressShop",
        "LBGameMode",
        "LBECoatLineActor",
        "LBFactoryMachineBuilderSubsystem",
    )
    production_actors = [
        f"{actor.get_actor_label()} ({actor.get_class().get_name()})"
        for actor in map_actors
        if any(fragment in actor.get_class().get_name() for fragment in production_fragments)
        and actor.get_class().get_name() != "LBBodyShopPrototypeWorldBootstrap"
    ]
    if production_actors:
        failures.append("forbidden production/legacy actors: " + "; ".join(production_actors))

    required_labels = {
        "LB_BS_ENV_Floor_180m_x_90m",
        "LB_BS_ENV_Wall_North",
        "LB_BS_ENV_Wall_South",
        "LB_BS_ENV_Wall_West",
        "LB_BS_ENV_Wall_East",
        "LB_BS_INTERFACE_InputDockDatum",
        "LB_BS_INTERFACE_EDOutputDatum",
        "LB_BodyShop_PrototypeBootstrap_v001",
        "LB_BodyShop_Prototype_PlayerStart_v001",
        "LB_BodyShop_Prototype_ReviewCamera_Overview_v001",
    }
    labels = {actor.get_actor_label() for actor in map_actors}
    missing_labels = sorted(required_labels - labels)
    if missing_labels:
        failures.append("missing required shell/interface actors: " + ", ".join(missing_labels))

    grid_count = sum(
        GRID_TAG in {str(tag) for tag in actor.get_editor_property("tags")}
        for actor in map_actors
    )
    expected_grid_count = 272  # 181 x-lines + 91 y-lines, one per 100 cm.
    if grid_count != expected_grid_count:
        failures.append(
            f"visible 100 cm grid actor count {grid_count}, expected {expected_grid_count}"
        )

    # Reproducibility contract for the management-camera cutaway: only the
    # nine cross-shop trusses and the nine camera-side south columns carry the
    # durable cutaway tag and persist HiddenInGame. North columns stay visible.
    by_label = {actor.get_actor_label(): actor for actor in map_actors}
    cutaway_labels = set()
    cutaway_rows = {}
    for x in range(-8_000, 8_001, 2_000):
        specs = {
            f"LB_BS_ENV_Truss_{x:+05d}": (
                (float(x), 0.0, 1_600.0), (0.45, 80.5, 0.45)
            ),
            f"LB_BS_ENV_Column_South_{x:+05d}": (
                (float(x), -4_050.0, CLEAR_HEIGHT_CM / 2.0), (0.55, 0.55, 16.5)
            ),
        }
        for label, (expected_location, expected_scale) in specs.items():
            cutaway_labels.add(label)
            actor = by_label.get(label)
            if actor is None:
                failures.append(f"missing management-cutaway actor {label}")
                continue
            location = actor.get_actor_location()
            scale = actor.get_actor_scale3d()
            actual_location = (float(location.x), float(location.y), float(location.z))
            actual_scale = (float(scale.x), float(scale.y), float(scale.z))
            tags = {str(tag) for tag in actor.get_editor_property("tags")}
            hidden = bool(actor.get_editor_property("hidden"))
            expected_tags = {MAP_TAG, ENV_TAG, SHELL_TAG, STRUCTURE_TAG, CUTAWAY_TAG}
            if (any(abs(a - b) > 0.02 for a, b in zip(actual_location, expected_location))
                    or any(abs(a - b) > 0.0002 for a, b in zip(actual_scale, expected_scale))
                    or tags != expected_tags or not hidden):
                failures.append(f"management-cutaway transform/tag/HiddenInGame drift: {label}")
            cutaway_rows[label] = {
                "location_cm": list(actual_location),
                "scale": list(actual_scale),
                "tags": sorted(tags),
                "hidden_in_game": hidden,
            }
    tagged_cutaways = {
        actor.get_actor_label() for actor in map_actors
        if CUTAWAY_TAG in {str(tag) for tag in actor.get_editor_property("tags")}
    }
    if tagged_cutaways != cutaway_labels:
        failures.append("management-cutaway tag is not scoped to the exact 18 actors")
    north_labels = {
        f"LB_BS_ENV_Column_North_{x:+05d}" for x in range(-8_000, 8_001, 2_000)
    }
    if any(label not in by_label or bool(by_label[label].get_editor_property("hidden"))
           or CUTAWAY_TAG in {str(tag) for tag in by_label[label].get_editor_property("tags")}
           for label in north_labels):
        failures.append("north structural columns are not all visible and outside the cutaway scope")

    bootstrap_flags = {}
    if len(bootstrap_actors) == 1:
        bootstrap = bootstrap_actors[0]
        properties = {
            "prototype_enabled": ("prototype_enabled", "b_prototype_enabled", "bPrototypeEnabled"),
            "reject_legacy_authorities": (
                "reject_legacy_authorities", "b_reject_legacy_authorities",
                "bRejectLegacyAuthorities",
            ),
            "use_experimental_save_only": (
                "use_experimental_save_only", "b_use_experimental_save_only",
                "bUseExperimentalSaveOnly",
            ),
            "require_prototype_game_mode": (
                "require_prototype_game_mode", "b_require_prototype_game_mode",
                "bRequirePrototypeGameMode",
            ),
            "request_initial_underbody_slice": (
                "request_initial_underbody_slice", "b_request_initial_underbody_slice",
                "bRequestInitialUnderbodySlice",
            ),
            "spawn_runtime_on_begin_play": (
                "spawn_runtime_on_begin_play", "b_spawn_runtime_on_begin_play",
                "bSpawnRuntimeOnBeginPlay",
            ),
            "prototype_grid_size_cm": (
                "prototype_grid_size_cm", "PrototypeGridSizeCm",
            ),
        }
        for key, candidates in properties.items():
            property_name, value = get_property(bootstrap, candidates)
            bootstrap_flags[key] = {"property": property_name, "value": value}
        for key in (
            "prototype_enabled",
            "reject_legacy_authorities",
            "use_experimental_save_only",
            "require_prototype_game_mode",
            "request_initial_underbody_slice",
            "spawn_runtime_on_begin_play",
        ):
            if bootstrap_flags[key]["value"] is not True:
                failures.append(f"bootstrap flag {key} is not true")
        grid_value = bootstrap_flags["prototype_grid_size_cm"]["value"]
        if grid_value is None or abs(float(grid_value) - GRID_CM) > 0.01:
            failures.append(f"bootstrap grid is not {GRID_CM} cm")

    facts = {
        "game_mode": class_path(game_mode),
        "world_partition": partition,
        "actor_count": len(map_actors),
        "bootstrap_count": len(bootstrap_actors),
        "grid_actor_count": grid_count,
        "management_cutaway_actor_count": len(cutaway_rows),
        "management_cutaway_actors": cutaway_rows,
        "north_columns_visible_count": len(north_labels),
        "production_or_legacy_actor_count": len(production_actors),
        "bootstrap_flags": bootstrap_flags,
        "runtime_spawn_sequence": [
            "ALBBodyShopPrototypeRuntime.BindBuildAuthority",
            "ALBBodyShopPrototypeWorldBootstrap.BindPrototypeAuthorities",
            "ALBBodyShopPrototypeRuntime.BuildAndCommissionApprovedUnderbodySlice",
        ],
    }
    return failures, facts


def main():
    # This check happens before new_level(), so a stale DLL cannot create an
    # incompatible content package.
    classes = {
        "game_mode": require_class(GAME_MODE_CLASS_PATH),
        "pawn": require_class(PAWN_CLASS_PATH),
        "hud": require_class(HUD_CLASS_PATH),
        "bootstrap": require_class(BOOTSTRAP_CLASS_PATH),
        "build_authority": require_class(BUILD_AUTHORITY_CLASS_PATH),
        "runtime": require_class(RUNTIME_CLASS_PATH),
    }
    library = unreal.EditorAssetLibrary
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    if library.does_asset_exist(MAP) or MAP_FILE.exists():
        raise RuntimeError(
            f"Refusing to overwrite the isolated Body Shop map: {MAP}. "
            "Use the independent validator; do not rebuild an existing map."
        )

    cube = require_asset("/Engine/BasicShapes/Cube.Cube", unreal.StaticMesh)
    materials = {
        "floor": require_asset(
            "/Game/LineBoss/Materials/Environment/MI_LB_SealedFactoryConcrete_Neutral_v001",
            unreal.MaterialInterface,
        ),
        "charcoal": require_asset(
            "/Game/LineBoss/Materials/M_LB_ShellCharcoal", unreal.MaterialInterface
        ),
        "marking": require_asset(
            "/Game/LineBoss/Materials/M_LB_SafetyYellow", unreal.MaterialInterface
        ),
    }

    if not levels.new_level(MAP):
        raise RuntimeError(f"Could not create non-World-Partition empty level {MAP}")

    world = unreal.EditorLevelLibrary.get_editor_world()
    if world is None:
        raise RuntimeError("New level did not create an editor world")
    settings = world.get_world_settings()
    set_property(settings, ("default_game_mode",), classes["game_mode"])

    # Exact shell authority: 180 m x 90 m, top of floor at Z = 0, clear walls
    # at 16.5 m. No roof liner: open trusses retain the factory scale while
    # keeping the early slice easy to inspect.
    box(
        actors, cube, "LB_BS_ENV_Floor_180m_x_90m", (0.0, 0.0, -25.0),
        (WIDTH_CM, DEPTH_CM, 50.0), materials["floor"], [SHELL_TAG], collision=True,
        cast_shadow=True,
    )
    wall_specs = (
        ("North", (0.0, DEPTH_CM / 2.0, CLEAR_HEIGHT_CM / 2.0), (WIDTH_CM, 40.0, CLEAR_HEIGHT_CM)),
        ("South", (0.0, -DEPTH_CM / 2.0, CLEAR_HEIGHT_CM / 2.0), (WIDTH_CM, 40.0, CLEAR_HEIGHT_CM)),
        ("West", (-WIDTH_CM / 2.0, 0.0, CLEAR_HEIGHT_CM / 2.0), (40.0, DEPTH_CM, CLEAR_HEIGHT_CM)),
        ("East", (WIDTH_CM / 2.0, 0.0, CLEAR_HEIGHT_CM / 2.0), (40.0, DEPTH_CM, CLEAR_HEIGHT_CM)),
    )
    for direction, location, dimensions in wall_specs:
        box(
            actors, cube, f"LB_BS_ENV_Wall_{direction}", location, dimensions,
            materials["charcoal"], [SHELL_TAG, "LB.BodyShop.Environment.Wall"],
            collision=True, cast_shadow=True,
        )

    # Visible 1 m squares make the 100 cm placement rule legible without
    # placing any player-owned equipment into the map.
    for x in range(-9_000, 9_001, 100):
        box(
            actors, cube, f"LB_BS_ENV_GridX_{x:+05d}", (x, 0.0, 0.55),
            (0.8, DEPTH_CM - 80.0, 0.7), materials["charcoal"],
            [GRID_TAG], collision=False,
        )
    for y in range(-4_500, 4_501, 100):
        box(
            actors, cube, f"LB_BS_ENV_GridY_{y:+05d}", (0.0, y, 0.60),
            (WIDTH_CM - 80.0, 0.8, 0.7), materials["charcoal"],
            [GRID_TAG], collision=False,
        )

    # The inner yellow rectangle is the exact buildable area (+/- 7600 cm x
    # +/- 2600 cm). It is context only; placement validation remains owned by
    # ALBBodyShopBuildAuthority at runtime.
    build_edges = (
        ("North", (0.0, BUILD_HALF_Y_CM, 1.3), (BUILD_HALF_X_CM * 2.0, 12.0, 1.2)),
        ("South", (0.0, -BUILD_HALF_Y_CM, 1.3), (BUILD_HALF_X_CM * 2.0, 12.0, 1.2)),
        ("West", (-BUILD_HALF_X_CM, 0.0, 1.3), (12.0, BUILD_HALF_Y_CM * 2.0, 1.2)),
        ("East", (BUILD_HALF_X_CM, 0.0, 1.3), (12.0, BUILD_HALF_Y_CM * 2.0, 1.2)),
    )
    for direction, location, dimensions in build_edges:
        box(
            actors, cube, f"LB_BS_ENV_BuildArea_{direction}", location, dimensions,
            materials["marking"], ["LB.BodyShop.Environment.BuildAreaBoundary"],
            collision=False,
        )

    # Fixed movement/service context: pedestrians +Y, FLT -Y, and clear
    # services either side of the player-owned buildable rectangle.
    box(
        actors, cube, "LB_BS_ENV_PedestrianProtectedLane", (0.0, 4_000.0, 1.0),
        (17_000.0, 350.0, 1.0), materials["charcoal"],
        ["LB.BodyShop.Environment.PedestrianProtected"], collision=False,
    )
    box(
        actors, cube, "LB_BS_ENV_FLTProtectedRoute", (0.0, -3_750.0, 1.0),
        (17_000.0, 300.0, 1.0), materials["charcoal"],
        ["LB.BodyShop.Environment.FLTProtected"], collision=False,
    )
    for label, y in (("NorthService", 3_000.0), ("SouthService", -3_000.0)):
        box(
            actors, cube, f"LB_BS_ENV_{label}Boundary", (0.0, y, 1.15),
            (17_000.0, 10.0, 1.0), materials["marking"],
            ["LB.BodyShop.Environment.ServiceBoundary"], collision=False,
        )

    # Perimeter-only structural rhythm; no interior production fixtures are
    # baked into the map. Each span is 20 m, leaving broad visibility around
    # the experimental build zone.
    for x in range(-8_000, 8_001, 2_000):
        for side, y in (("North", 4_050.0), ("South", -4_050.0)):
            column_tags = [SHELL_TAG, STRUCTURE_TAG]
            if side == "South":
                column_tags.append(CUTAWAY_TAG)
            column = box(
                actors, cube, f"LB_BS_ENV_Column_{side}_{x:+05d}",
                (x, y, CLEAR_HEIGHT_CM / 2.0), (55.0, 55.0, CLEAR_HEIGHT_CM),
                materials["charcoal"], column_tags,
                collision=True, cast_shadow=True,
            )
            if side == "South":
                column.set_actor_hidden_in_game(True)
        truss = box(
            actors, cube, f"LB_BS_ENV_Truss_{x:+05d}", (x, 0.0, 1_600.0),
            (45.0, 8_050.0, 45.0), materials["charcoal"],
            [SHELL_TAG, STRUCTURE_TAG, CUTAWAY_TAG],
            collision=True, cast_shadow=True,
        )
        truss.set_actor_hidden_in_game(True)

    # Input/output datum pads match the early prototype contract but have no
    # production logic or spawned vehicle/fixture content on the map.
    box(
        actors, cube, "LB_BS_INTERFACE_InputDockDatum", (-9_000.0, -3_750.0, 1.4),
        (600.0, 650.0, 1.6), materials["marking"], [INTERFACE_TAG], collision=False,
    )
    box(
        actors, cube, "LB_BS_INTERFACE_EDOutputDatum", (9_000.0, 0.0, 1.4),
        (600.0, 650.0, 1.6), materials["marking"], [INTERFACE_TAG], collision=False,
    )

    for x in (-6_000.0, -3_000.0, 0.0, 3_000.0, 6_000.0):
        for y in (-1_800.0, 0.0, 1_800.0):
            light(
                actors, f"LB_BS_ENV_Light_{int(x):+05d}_{int(y):+05d}",
                (x, y, 1_475.0), (-90.0, 0.0, 0.0), 12_000.0, 800.0, 170.0
            )
    sun = actors.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 1_600.0),
        unreal.Rotator(-52.0, -28.0, 0.0)
    )
    sun.set_actor_label("LB_BS_ENV_DirectionalLight")
    set_tags(sun, [MAP_TAG, ENV_TAG, "LB.BodyShop.Environment.Lighting"])
    sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property(
        "intensity", 2.0
    )
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 1_500.0), unreal.Rotator())
    sky.set_actor_label("LB_BS_ENV_SkyLight")
    set_tags(sky, [MAP_TAG, ENV_TAG, "LB.BodyShop.Environment.Lighting"])
    sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 0.55)

    exposure = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
    exposure.set_actor_label("LB_BS_ENV_NeutralExposure")
    set_tags(exposure, [MAP_TAG, ENV_TAG, "LB.BodyShop.Environment.Lighting"])
    exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0})
    settings_pp = exposure.get_editor_property("settings")
    settings_pp.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -1.0,
    })
    exposure.set_editor_property("settings", settings_pp)

    player_start = actors.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(0.0, 0.0, 180.0), unreal.Rotator()
    )
    player_start.set_actor_label("LB_BodyShop_Prototype_PlayerStart_v001")
    set_tags(player_start, [MAP_TAG, "LB.BodyShop.Prototype.PlayerStart"])

    camera(
        actors, "LB_BodyShop_Prototype_ReviewCamera_Overview_v001",
        (-12_500.0, -10_500.0, 9_400.0), (0.0, 0.0, 0.0), 50.0,
    )
    camera(
        actors, "LB_BodyShop_Prototype_ReviewCamera_Flow_v001",
        (-10_600.0, -8_600.0, 5_900.0), (-4_500.0, -1_800.0, 250.0), 48.0,
    )

    bootstrap = actors.spawn_actor_from_class(
        classes["bootstrap"], unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator()
    )
    if bootstrap is None:
        raise RuntimeError("Could not place ALBBodyShopPrototypeWorldBootstrap")
    bootstrap.set_actor_label("LB_BodyShop_PrototypeBootstrap_v001")
    set_tags(bootstrap, [MAP_TAG, "LB.BodyShop.Prototype.Bootstrap"])
    set_property(bootstrap, ("prototype_enabled", "b_prototype_enabled", "bPrototypeEnabled"), True)
    set_property(
        bootstrap,
        ("reject_legacy_authorities", "b_reject_legacy_authorities", "bRejectLegacyAuthorities"),
        True,
    )
    set_property(
        bootstrap,
        (
            "spawn_runtime_on_begin_play", "b_spawn_runtime_on_begin_play",
            "bSpawnRuntimeOnBeginPlay",
        ),
        True,
    )
    set_property(
        bootstrap,
        ("use_experimental_save_only", "b_use_experimental_save_only", "bUseExperimentalSaveOnly"),
        True,
    )
    set_property(
        bootstrap,
        ("require_prototype_game_mode", "b_require_prototype_game_mode", "bRequirePrototypeGameMode"),
        True,
    )
    set_property(
        bootstrap,
        (
            "request_initial_underbody_slice", "b_request_initial_underbody_slice",
            "bRequestInitialUnderbodySlice",
        ),
        True,
    )
    set_property(
        bootstrap, ("show_prototype_hud", "b_show_prototype_hud", "bShowPrototypeHUD"), True
    )
    set_property(bootstrap, ("prototype_build_origin", "PrototypeBuildOrigin"), unreal.Vector())
    set_property(bootstrap, ("prototype_grid_size_cm", "PrototypeGridSizeCm"), GRID_CM)

    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    failures, facts = validate_current_map(classes, actors)
    if failures:
        raise RuntimeError("Pre-save Body Shop map contract failed: " + " | ".join(failures))
    if not levels.save_current_level():
        raise RuntimeError(f"Could not save isolated Body Shop map: {MAP}")
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not reload isolated Body Shop map: {MAP}")
    failures, facts = validate_current_map(classes, actors)
    if failures:
        raise RuntimeError("Post-save Body Shop map contract failed: " + " | ".join(failures))

    payload = {
        "$schema": "cairnwell/body-shop/prototype-map-v001/create/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "PASS__ISOLATED_NON_WP_EMPTY_BODY_SHOP_SHELL__ONE_BOOTSTRAP__"
            "ZERO_PRODUCTION_CELLS__EXPERIMENTAL_SAVE_V1_ONLY"
            "__RUNTIME_SPAWNED_BEGIN_PLAY_ONLY"
        ),
        "map": MAP,
        "map_file": str(MAP_FILE),
        "map_sha256": hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper(),
        "classes": {
            "game_mode": GAME_MODE_CLASS_PATH,
            "pawn": PAWN_CLASS_PATH,
            "hud": HUD_CLASS_PATH,
            "bootstrap": BOOTSTRAP_CLASS_PATH,
            "build_authority": BUILD_AUTHORITY_CLASS_PATH,
            "runtime": RUNTIME_CLASS_PATH,
        },
        "dimensions_cm": {
            "shell": [WIDTH_CM, DEPTH_CM, CLEAR_HEIGHT_CM],
            "build_half_extent": [BUILD_HALF_X_CM, BUILD_HALF_Y_CM],
            "placement_grid_cm": GRID_CM,
        },
        "fixed_interfaces_cm": {
            "input_dock": [-9_000.0, -3_750.0, 0.0],
            "ed_output": [9_000.0, 0.0, 0.0],
            "pedestrian_protected_y": 4_000.0,
            "flt_protected_y": -3_750.0,
        },
        "facts": facts,
        "meshy_credits_used": 0,
        "production_cells_baked_into_map": 0,
        "runtime_authorities_baked_into_map": 0,
        "runtime_spawn_sequence": [
            "Runtime.BindBuildAuthority",
            "Bootstrap.BindPrototypeAuthorities",
            "Runtime.BuildAndCommissionApprovedUnderbodySlice",
        ],
        "legacy_authorities_baked_into_map": 0,
        "global_default_map_or_config_changed": False,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(
        "LINE_BOSS_BODY_SHOP_PROTOTYPE_MAP_CREATE_V001_PASS "
        f"map={MAP} audit={AUDIT}"
    )


main()
