"""Independently validate the isolated Body Shop prototype map.

This script is intentionally read-only with respect to Content and Config. It
loads only the Body Shop prototype map, inventories it, and emits a receipt in
Saved/Audits. It rejects World Partition, any baked production cell/runtime
authority, legacy/campaign authorities, a missing/multiple bootstrap, and a
WorldSettings GameMode that is not the isolated prototype GameMode. It also
requires BeginPlay-only runtime spawning so the saved map remains an empty
authored shell.
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
AUDIT = ROOT / "Saved/Audits/BodyShop/v001/body_shop_prototype_map_validation_v001.json"
GAME_MODE_PATH = "/Script/LineBossCarFactory.LBBodyShopPrototypeGameMode"
BOOTSTRAP_PATH = "/Script/LineBossCarFactory.LBBodyShopPrototypeWorldBootstrap"
BUILD_AUTHORITY_PATH = "/Script/LineBossCarFactory.LBBodyShopBuildAuthority"
RUNTIME_PATH = "/Script/LineBossCarFactory.LBBodyShopPrototypeRuntime"

MAP_TAG = "LB.BodyShop.Experimental.v001"
GRID_TAG = "LB.BodyShop.Environment.Grid.100cm"
EXPECTED_GRID_COUNT = 272
EXPECTED_SHELL_SIZE_CM = [18_000.0, 9_000.0, 1_650.0]
EXPECTED_BUILD_HALF_EXTENT_CM = [7_600.0, 2_600.0]
EXPECTED_GRID_CM = 100.0
CHECKS = []


def class_path(value):
    return value.get_path_name() if value is not None else None


def property_value(owner, candidates):
    errors = []
    for name in candidates:
        try:
            return name, owner.get_editor_property(name), errors
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    return None, None, errors


def tags_of(actor):
    try:
        return [str(tag) for tag in actor.get_editor_property("tags")]
    except Exception:
        return []


def is_engine_foundation_actor(actor):
    """WorldSettings/DefaultPhysicsVolume may be enumerated by some UE builds."""
    return actor.get_class().get_name() in {
        "WorldSettings",
        "DefaultPhysicsVolume",
    }


def location_of(actor):
    location = actor.get_actor_location()
    return [float(location.x), float(location.y), float(location.z)]


def scale_of(actor):
    scale = actor.get_actor_scale3d()
    return [float(scale.x), float(scale.y), float(scale.z)]


def basic_shape_dimensions(actor):
    """Returns dimensions for cube-based environmental actors, or None."""
    if not isinstance(actor, unreal.StaticMeshActor):
        return None
    component = actor.get_editor_property("static_mesh_component")
    mesh = component.get_editor_property("static_mesh")
    if mesh is None or mesh.get_path_name() != "/Engine/BasicShapes/Cube.Cube":
        return None
    scale = actor.get_actor_scale3d()
    return [round(float(scale.x) * 100.0, 3),
            round(float(scale.y) * 100.0, 3),
            round(float(scale.z) * 100.0, 3)]


def world_partition_status(world):
    getter = getattr(world, "get_world_partition", None)
    if callable(getter):
        partition = getter()
        return {
            "api_available": True,
            "enabled": partition is not None,
            "object": class_path(partition),
        }
    _, partition, errors = property_value(world, ("world_partition",))
    return {
        "api_available": False,
        "enabled": partition is not None,
        "object": class_path(partition),
        "property_errors": errors,
    }


def add_check(name, passed, evidence):
    CHECKS.append({"name": name, "passed": bool(passed), "evidence": evidence})


def main():
    library = unreal.EditorAssetLibrary
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    CHECKS.clear()
    checks = CHECKS

    add_check("map_asset_exists", library.does_asset_exist(MAP), MAP)
    add_check("map_file_exists", MAP_FILE.exists(), str(MAP_FILE))
    if not library.does_asset_exist(MAP) or not MAP_FILE.exists():
        result = {
            "$schema": "cairnwell/body-shop/prototype-map-v001/validate/v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "FAIL",
            "map": MAP,
            "checks": checks,
        }
        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(f"Body Shop prototype map does not exist: {MAP}")

    expected_game_mode = unreal.load_class(None, GAME_MODE_PATH)
    expected_bootstrap = unreal.load_class(None, BOOTSTRAP_PATH)
    expected_build_authority = unreal.load_class(None, BUILD_AUTHORITY_PATH)
    expected_runtime = unreal.load_class(None, RUNTIME_PATH)
    add_check("compiled_game_mode_exists", expected_game_mode is not None, GAME_MODE_PATH)
    add_check("compiled_bootstrap_exists", expected_bootstrap is not None, BOOTSTRAP_PATH)
    add_check(
        "compiled_runtime_authority_classes_exist",
        expected_build_authority is not None and expected_runtime is not None,
        {
            "build_authority": BUILD_AUTHORITY_PATH,
            "runtime": RUNTIME_PATH,
            "build_authority_loaded": expected_build_authority is not None,
            "runtime_loaded": expected_runtime is not None,
        },
    )
    if (expected_game_mode is None or expected_bootstrap is None
            or expected_build_authority is None or expected_runtime is None):
        raise RuntimeError("Current editor module is stale; Body Shop classes are unavailable")

    loaded = levels.load_level(MAP)
    add_check("map_loads", loaded, MAP)
    if not loaded:
        raise RuntimeError(f"Could not load Body Shop prototype map: {MAP}")

    world = unreal.EditorLevelLibrary.get_editor_world()
    map_actors = list(actors_api.get_all_level_actors())
    classes = [actor.get_class().get_name() for actor in map_actors]
    labels = [actor.get_actor_label() for actor in map_actors]

    settings = world.get_world_settings() if world else None
    game_mode = settings.get_editor_property("default_game_mode") if settings else None
    add_check(
        "isolated_game_mode",
        game_mode == expected_game_mode,
        {"actual": class_path(game_mode), "expected": GAME_MODE_PATH},
    )

    partition = world_partition_status(world) if world else {"enabled": None}
    add_check("non_world_partition_map", partition.get("enabled") is False, partition)

    bootstrap_actors = [
        actor for actor in map_actors
        if actor.get_class().get_name() == "LBBodyShopPrototypeWorldBootstrap"
    ]
    add_check(
        "exactly_one_bootstrap",
        len(bootstrap_actors) == 1,
        [actor.get_actor_label() for actor in bootstrap_actors],
    )

    expected_labels = {
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
        "LB_BodyShop_Prototype_ReviewCamera_Flow_v001",
    }
    add_check("required_context_labels", expected_labels.issubset(set(labels)),
              sorted(expected_labels - set(labels)))

    authored_actors = [
        actor for actor in map_actors
        if not is_engine_foundation_actor(actor)
    ]
    tagged_actors = [
        actor for actor in map_actors
        if not is_engine_foundation_actor(actor) and MAP_TAG in tags_of(actor)
    ]
    add_check(
        "all_map_owned_actors_are_tagged",
        len(tagged_actors) == len(authored_actors),
        {"tagged": len(tagged_actors), "authored": len(authored_actors),
         "engine_foundation": len(map_actors) - len(authored_actors)},
    )

    grid_actors = [actor for actor in map_actors if GRID_TAG in tags_of(actor)]
    add_check(
        "one_meter_grid_count",
        len(grid_actors) == EXPECTED_GRID_COUNT,
        {"actual": len(grid_actors), "expected": EXPECTED_GRID_COUNT},
    )
    grid_alignment_failures = [
        {"label": actor.get_actor_label(), "location_cm": location_of(actor)}
        for actor in grid_actors
        if abs(location_of(actor)[0] / EXPECTED_GRID_CM - round(location_of(actor)[0] / EXPECTED_GRID_CM)) > 0.001
        or abs(location_of(actor)[1] / EXPECTED_GRID_CM - round(location_of(actor)[1] / EXPECTED_GRID_CM)) > 0.001
    ]
    add_check("grid_lines_are_100cm_aligned", not grid_alignment_failures, grid_alignment_failures)

    by_label = {actor.get_actor_label(): actor for actor in map_actors}
    shell_expected = {
        "LB_BS_ENV_Floor_180m_x_90m": ([0.0, 0.0, -25.0], [18_000.0, 9_000.0, 50.0]),
        "LB_BS_ENV_Wall_North": ([0.0, 4_500.0, 825.0], [18_000.0, 40.0, 1_650.0]),
        "LB_BS_ENV_Wall_South": ([0.0, -4_500.0, 825.0], [18_000.0, 40.0, 1_650.0]),
        "LB_BS_ENV_Wall_West": ([-9_000.0, 0.0, 825.0], [40.0, 9_000.0, 1_650.0]),
        "LB_BS_ENV_Wall_East": ([9_000.0, 0.0, 825.0], [40.0, 9_000.0, 1_650.0]),
    }
    shell_evidence = {}
    shell_valid = True
    for label, (expected_location, expected_dimensions) in shell_expected.items():
        actor = by_label.get(label)
        actual_location = location_of(actor) if actor else None
        actual_dimensions = basic_shape_dimensions(actor) if actor else None
        valid = (
            actual_location is not None
            and all(abs(a - b) <= 0.01 for a, b in zip(actual_location, expected_location))
            and actual_dimensions is not None
            and all(abs(a - b) <= 0.01 for a, b in zip(actual_dimensions, expected_dimensions))
        )
        shell_valid = shell_valid and valid
        shell_evidence[label] = {
            "valid": valid,
            "location_cm": actual_location,
            "dimensions_cm": actual_dimensions,
            "expected_location_cm": expected_location,
            "expected_dimensions_cm": expected_dimensions,
        }
    add_check("180m_x_90m_shell_contract", shell_valid, shell_evidence)

    build_edges = {
        "LB_BS_ENV_BuildArea_North": ([0.0, 2_600.0, 1.3], [15_200.0, 12.0, 1.2]),
        "LB_BS_ENV_BuildArea_South": ([0.0, -2_600.0, 1.3], [15_200.0, 12.0, 1.2]),
        "LB_BS_ENV_BuildArea_West": ([-7_600.0, 0.0, 1.3], [12.0, 5_200.0, 1.2]),
        "LB_BS_ENV_BuildArea_East": ([7_600.0, 0.0, 1.3], [12.0, 5_200.0, 1.2]),
    }
    edge_evidence = {}
    edge_valid = True
    for label, (expected_location, expected_dimensions) in build_edges.items():
        actor = by_label.get(label)
        actual_location = location_of(actor) if actor else None
        actual_dimensions = basic_shape_dimensions(actor) if actor else None
        valid = (
            actual_location is not None
            and all(abs(a - b) <= 0.01 for a, b in zip(actual_location, expected_location))
            and actual_dimensions is not None
            and all(abs(a - b) <= 0.01 for a, b in zip(actual_dimensions, expected_dimensions))
        )
        edge_valid = edge_valid and valid
        edge_evidence[label] = {
            "valid": valid,
            "location_cm": actual_location,
            "dimensions_cm": actual_dimensions,
        }
    add_check("build_area_152m_x_52m_contract", edge_valid, edge_evidence)

    interface_expected = {
        "LB_BS_INTERFACE_InputDockDatum": [-9_000.0, -3_750.0, 1.4],
        "LB_BS_INTERFACE_EDOutputDatum": [9_000.0, 0.0, 1.4],
    }
    interface_evidence = {
        label: location_of(by_label[label]) if label in by_label else None
        for label in interface_expected
    }
    add_check(
        "fixed_interface_datums",
        all(
            interface_evidence[label] is not None
            and all(abs(a - b) <= 0.01 for a, b in zip(interface_evidence[label], expected))
            for label, expected in interface_expected.items()
        ),
        interface_evidence,
    )

    production_fragments = (
        "LBBodyShopCellActor",
        "LBBodyShopBuildAuthority",
        "LBBodyShopPrototypeRuntime",
    )
    legacy_fragments = (
        "LBBodyWeldLineActor",
        "LBPressShop",
        "LBGameMode",
        "LBECoatLineActor",
        "LBFactoryMachineBuilderSubsystem",
    )
    production_actor_records = [
        {"label": actor.get_actor_label(), "class": actor.get_class().get_name()}
        for actor in map_actors
        if any(fragment in actor.get_class().get_name() for fragment in production_fragments)
    ]
    legacy_actor_records = [
        {"label": actor.get_actor_label(), "class": actor.get_class().get_name()}
        for actor in map_actors
        if any(fragment in actor.get_class().get_name() for fragment in legacy_fragments)
    ]
    add_check("zero_baked_production_cells_or_runtime_authorities",
              not production_actor_records, production_actor_records)
    add_check("zero_legacy_or_campaign_authorities", not legacy_actor_records, legacy_actor_records)

    bootstrap_evidence = {}
    flags_valid = False
    if len(bootstrap_actors) == 1:
        bootstrap = bootstrap_actors[0]
        flag_spec = {
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
            "prototype_build_origin": (
                "prototype_build_origin", "PrototypeBuildOrigin",
            ),
        }
        for semantic, candidates in flag_spec.items():
            name, value, errors = property_value(bootstrap, candidates)
            if isinstance(value, unreal.Vector):
                value = [float(value.x), float(value.y), float(value.z)]
            bootstrap_evidence[semantic] = {
                "property": name, "value": value, "errors": errors,
            }
        flags_valid = (
            all(bootstrap_evidence[name]["value"] is True for name in (
                "prototype_enabled",
                "reject_legacy_authorities",
                "use_experimental_save_only",
                "require_prototype_game_mode",
                "request_initial_underbody_slice",
                "spawn_runtime_on_begin_play",
            ))
            and abs(float(bootstrap_evidence["prototype_grid_size_cm"]["value"]) - EXPECTED_GRID_CM) <= 0.01
            and bootstrap_evidence["prototype_build_origin"]["value"] == [0.0, 0.0, 0.0]
        )
    add_check("bootstrap_isolation_and_save_v1_flags", flags_valid, bootstrap_evidence)

    exact_runtime_authorities_baked = [
        record for record in production_actor_records
        if any(fragment in record["class"] for fragment in (
            "LBBodyShopBuildAuthority",
            "LBBodyShopPrototypeRuntime",
        ))
    ]
    add_check(
        "runtime_authorities_spawn_from_begin_play_only",
        flags_valid and not exact_runtime_authorities_baked,
        {
            "bootstrap_spawn_runtime_on_begin_play": (
                bootstrap_evidence.get("spawn_runtime_on_begin_play", {}).get("value")
            ),
            "baked_runtime_authorities": exact_runtime_authorities_baked,
            "required_sequence": [
                "Runtime.BindBuildAuthority",
                "Bootstrap.BindPrototypeAuthorities",
                "Runtime.BuildAndCommissionApprovedUnderbodySlice",
            ],
        },
    )

    expected_camera = by_label.get("LB_BodyShop_Prototype_ReviewCamera_Overview_v001")
    camera_evidence = None
    if expected_camera is not None:
        camera_component = expected_camera.get_editor_property("camera_component")
        camera_evidence = {
            "location_cm": location_of(expected_camera),
            "fov": float(camera_component.get_editor_property("field_of_view")),
        }
    add_check(
        "overview_review_camera",
        camera_evidence == {"location_cm": [-12500.0, -10500.0, 9400.0], "fov": 50.0},
        camera_evidence,
    )

    all_pass = all(item["passed"] for item in checks)
    result = {
        "$schema": "cairnwell/body-shop/prototype-map-v001/validate/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "PASS__ISOLATED_NON_WP_EMPTY_BODY_SHOP_SHELL__ONE_BOOTSTRAP__"
            "ZERO_PRODUCTION_CELLS__EXPERIMENTAL_SAVE_V1_ONLY"
            "__RUNTIME_SPAWNED_BEGIN_PLAY_ONLY"
            if all_pass else "FAIL"
        ),
        "map": MAP,
        "map_file": str(MAP_FILE),
        "map_sha256": hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper(),
        "actor_count": len(map_actors),
        "class_counts": {
            name: classes.count(name) for name in sorted(set(classes))
        },
        "map_owned_actor_count": len(tagged_actors),
        "shell_contract_cm": {
            "shell": EXPECTED_SHELL_SIZE_CM,
            "build_half_extent": EXPECTED_BUILD_HALF_EXTENT_CM,
            "grid": EXPECTED_GRID_CM,
        },
        "checks": checks,
        "runtime_spawn_sequence": [
            "Runtime.BindBuildAuthority",
            "Bootstrap.BindPrototypeAuthorities",
            "Runtime.BuildAndCommissionApprovedUnderbodySlice",
        ],
        "meshy_credits_used": 0,
        "writes_to_content_or_config": False,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if all_pass:
        unreal.log(
            "LINE_BOSS_BODY_SHOP_PROTOTYPE_MAP_VALIDATE_V001_PASS "
            f"map={MAP} audit={AUDIT}"
        )
    else:
        failed = [item["name"] for item in checks if not item["passed"]]
        unreal.log_error(
            "LINE_BOSS_BODY_SHOP_PROTOTYPE_MAP_VALIDATE_V001_FAIL "
            + " failed=" + ",".join(failed)
        )
        raise RuntimeError("Body Shop map validation failed: " + ", ".join(failed))


main()
