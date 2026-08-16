"""Build the protected OneFactory v002 lighting/navigation successor once.

The exact v001 map is duplicated into a new namespace.  Only the duplicate is
changed: its one hall-sized RectLight becomes a bounded no-shadow 5000 K
high-bay grid plus the common Cairnwell sun/sky/fixed-exposure response, and
the preserved floor HISM becomes the sole navigation-generating shell layer.
Navigation is explicitly rebuilt and queried before the first save.

This script refuses an existing target or receipt and never saves the source
map.  It is intended for the frozen guarded runner, not interactive execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import traceback
from typing import Any

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
SCRIPTS = ROOT / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import one_factory_visual_navigation_v002_contract as contract
import one_factory_visual_navigation_v002_unreal as gate


SCRIPT_FILE = ROOT / "Scripts/build_one_factory_visual_navigation_v002.py"
SOURCE_FILE = ROOT / contract.SOURCE_MAP_RELATIVE
TARGET_FILE = ROOT / contract.TARGET_MAP_RELATIVE
RECEIPT = ROOT / contract.BUILD_RECEIPT_RELATIVE
FAILURE_RECEIPT = RECEIPT.with_name(
    "one_factory_visual_navigation_build_v002_failed.json"
)


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def frozen_anchor_snapshot() -> dict[str, str]:
    rows = {}
    for name, expected in contract.STATIC_PROTECTED_HASHES.items():
        path = ROOT / name
        if not path.is_file():
            raise RuntimeError(f"Protected anchor is absent: {name}")
        actual = contract.sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"Protected anchor drift: {name} {actual} != {expected}"
            )
        rows[name] = actual
    return rows


def guarded_workspace_snapshot() -> dict[str, str]:
    """Hash every state-bearing tree, excluding only this new target map."""
    rows: dict[str, str] = {}
    patterns = (
        (ROOT / "Source", "*", True),
        (ROOT / "Config", "*", True),
        (ROOT / "Saved/SaveGames", "*.sav", True),
        (ROOT / "Content", "*", True),
    )
    target = TARGET_FILE.resolve()
    for root, pattern, recursive in patterns:
        if not root.exists():
            continue
        iterator = root.rglob(pattern) if recursive else root.glob(pattern)
        for path in sorted((item for item in iterator if item.is_file()), key=str):
            if path.resolve() == target:
                continue
            rows[relative(path)] = contract.sha256(path)
    return rows


def assert_destination_absent(assets: Any) -> None:
    if assets.does_asset_exist(contract.TARGET_MAP):
        raise RuntimeError(
            f"Refusing to overwrite existing OneFactory v002 asset: {contract.TARGET_MAP}"
        )
    if TARGET_FILE.exists():
        raise RuntimeError(
            f"Refusing to overwrite existing OneFactory v002 file: {TARGET_FILE}"
        )
    if RECEIPT.exists() or FAILURE_RECEIPT.exists():
        raise RuntimeError(
            "Refusing a repeated OneFactory v002 run while prior receipt evidence exists"
        )


def validate_exact_duplicate_before_mutation(world: Any, actors_api: Any) -> dict[str, Any]:
    base = gate.load_v001_contract()
    nonfoundation, by_label = gate.actor_index(actors_api)
    expected_labels = set(base.EXPECTED_ACTORS)
    actual_labels = set(by_label)
    duplicates = sorted(label for label, rows in by_label.items() if len(rows) != 1)
    if (
        len(nonfoundation) != 26
        or actual_labels != expected_labels
        or duplicates
    ):
        raise RuntimeError(
            "Duplicated v001 pre-state is not exact: "
            f"count={len(nonfoundation)} "
            f"missing={sorted(expected_labels - actual_labels)} "
            f"unexpected={sorted(actual_labels - expected_labels)} "
            f"duplicates={duplicates}"
        )
    state: dict[str, Any] = {"checks": [], "failures": []}
    facts: dict[str, Any] = {}
    for label, spec in base.EXPECTED_ACTORS.items():
        base.validate_actor_contract(state, label, by_label[label][0], spec)
    base.validate_hism_contracts(state, by_label, facts)
    authority = by_label["LB_OneFactory_PressBuildAuthority_v001"][0]
    base.validate_press_authority(state, authority, facts)
    base.validate_lighting_and_camera(state, by_label, facts)
    if state["failures"]:
        raise RuntimeError(
            "Exact v001 duplicate contract failed: "
            + ", ".join(str(row.get("name")) for row in state["failures"])
        )
    if world.get_world_settings().get_editor_property("default_game_mode") \
            != unreal.load_class(None, base.GAME_MODE_CLASS_PATH):
        raise RuntimeError("Duplicated v001 map-local GameMode drifted")
    return {
        "nonfoundation_actor_count": len(nonfoundation),
        "hism_actor_count": facts.get("hism_actor_count"),
        "hism_total_instance_count": facts.get("hism_total_instance_count"),
        "press_authority": facts.get("press_authority_contract"),
        "lighting_authority": facts.get("lighting_authority"),
        "fixed_exposure_authority": facts.get("fixed_exposure_authority"),
    }


def configure_high_bay_grid(actors_api: Any) -> list[dict[str, Any]]:
    rows = []
    tags = (
        contract.MAP_TAG,
        contract.NATIVE_TAG,
        contract.ENVIRONMENT_TAG,
        contract.HIGH_BAY_GRID_TAG,
        contract.LIGHT_AUTHORITY_TAG,
        contract.PERFORMANCE_TAG,
    )
    for spec in contract.high_bay_specs():
        actor = actors_api.spawn_actor_from_class(
            unreal.RectLight,
            unreal.Vector(*spec["location_cm"]),
            unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0),
        )
        if actor is None:
            raise RuntimeError(f"Could not spawn {spec['label']}")
        actor.set_actor_label(spec["label"])
        gate.set_exact_tags(actor, tags)
        component = actor.get_component_by_class(unreal.RectLightComponent)
        if component is None:
            raise RuntimeError(f"Could not resolve component for {spec['label']}")
        component.set_editor_properties({
            "intensity": contract.HIGH_BAY_INTENSITY_LM,
            "intensity_units": unreal.LightUnits.LUMENS,
            "attenuation_radius": contract.HIGH_BAY_ATTENUATION_CM,
            "source_width": contract.HIGH_BAY_SOURCE_WIDTH_CM,
            "source_height": contract.HIGH_BAY_SOURCE_HEIGHT_CM,
            "use_temperature": True,
            "temperature": contract.HIGH_BAY_TEMPERATURE_K,
            "cast_shadows": False,
            "affect_translucent_lighting": False,
            "volumetric_scattering_intensity": 0.0,
            "mobility": unreal.ComponentMobility.MOVABLE,
        })
        rows.append({
            "label": spec["label"],
            "location_cm": list(spec["location_cm"]),
        })
    if len(rows) != contract.HIGH_BAY_COUNT:
        raise RuntimeError("High-bay authoring cardinality drift")
    return rows


def configure_common_sun_sky(actors_api: Any) -> dict[str, Any]:
    sun = actors_api.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(0.0, 0.0, 8_000.0),
        unreal.Rotator(roll=0.0, pitch=-52.0, yaw=-28.0),
    )
    if sun is None:
        raise RuntimeError("Could not spawn common OneFactory sun")
    sun.set_actor_label(contract.SUN_LABEL)
    gate.set_exact_tags(sun, (
        contract.MAP_TAG,
        contract.NATIVE_TAG,
        contract.ENVIRONMENT_TAG,
        contract.COMMON_SUN_TAG,
    ))
    sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
    if sun_component is None:
        raise RuntimeError("Could not resolve common sun component")
    sun_component.set_editor_properties({
        "intensity": contract.SUN_INTENSITY,
        "mobility": unreal.ComponentMobility.MOVABLE,
    })

    sky = actors_api.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0.0, 0.0, 8_000.0), unreal.Rotator()
    )
    if sky is None:
        raise RuntimeError("Could not spawn common OneFactory sky")
    sky.set_actor_label(contract.SKY_LABEL)
    gate.set_exact_tags(sky, (
        contract.MAP_TAG,
        contract.NATIVE_TAG,
        contract.ENVIRONMENT_TAG,
        contract.COMMON_SKY_TAG,
    ))
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    if sky_component is None:
        raise RuntimeError("Could not resolve common sky component")
    sky_component.set_editor_properties({
        "intensity": contract.SKY_INTENSITY,
        "mobility": unreal.ComponentMobility.MOVABLE,
    })
    try:
        sky_component.recapture_sky()
    except Exception:
        # Runtime capture is not part of the saved contract.  The independent
        # real-RHI validator is the visual authority.
        pass
    return {"sun": contract.SUN_LABEL, "sky": contract.SKY_LABEL}


def replace_exposure_and_old_light(actors_api: Any) -> dict[str, Any]:
    _actors, by_label = gate.actor_index(actors_api)
    old_light = gate.require_one(by_label, contract.OLD_LIGHT_LABEL)
    exposure = gate.require_one(by_label, contract.OLD_EXPOSURE_LABEL)
    if not actors_api.destroy_actor(old_light):
        raise RuntimeError("Could not remove the inherited giant RectLight")
    exposure.set_actor_label(contract.EXPOSURE_LABEL)
    gate.set_exact_tags(exposure, (
        contract.MAP_TAG,
        contract.NATIVE_TAG,
        contract.ENVIRONMENT_TAG,
        contract.FIXED_EXPOSURE_TAG,
    ))
    exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0})
    settings = exposure.get_editor_property("settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": contract.FIXED_EXPOSURE_MIN,
        "auto_exposure_max_brightness": contract.FIXED_EXPOSURE_MAX,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": contract.FIXED_EXPOSURE_BIAS,
    })
    exposure.set_editor_property("settings", settings)
    return {
        "removed": contract.OLD_LIGHT_LABEL,
        "renamed_exposure": [contract.OLD_EXPOSURE_LABEL, contract.EXPOSURE_LABEL],
    }


def configure_and_build_navigation(world: Any, actors_api: Any) -> dict[str, Any]:
    _actors, by_label = gate.actor_index(actors_api)
    floor_actor = gate.require_one(by_label, contract.FLOOR_HISM_LABEL)
    floor_components = floor_actor.get_components_by_class(
        unreal.HierarchicalInstancedStaticMeshComponent
    )
    if len(floor_components) != 1:
        raise RuntimeError("Navigation floor must retain exactly one HISM component")
    floor_components[0].set_editor_property("can_ever_affect_navigation", True)

    settings = world.get_world_settings()
    module_config_class = unreal.load_class(
        None, "/Script/NavigationSystem.NavigationSystemModuleConfig"
    )
    if module_config_class is None:
        raise RuntimeError(
            "Could not load Unreal 5.8 NavigationSystemModuleConfig class"
        )
    config = unreal.new_object(
        module_config_class,
        outer=settings,
        name="LB_OF_NavigationSystemConfig_v002",
    )
    config.set_editor_properties({
        # UE 5.8 exposes these UPROPERTY names verbatim to Python.  The usual
        # snake_case aliases are absent; retained reflection evidence pins
        # these spellings.
        "bStrictlyStatic": False,
        "bAutoSpawnMissingNavData": True,
        "bSpawnNavDataInNavBoundsLevel": True,
        "navigation_system_class": unreal.SoftClassPath(
            "/Script/NavigationSystem.NavigationSystemV1"
        ),
    })
    settings.set_editor_property("navigation_system_config", config)

    nav_system = unreal.NavigationSystemV1.get_navigation_system(world)
    if nav_system is None:
        raise RuntimeError("NavigationSystemV1 unavailable before explicit build")
    bounds = list(unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.NavMeshBoundsVolume
    ))
    if len(bounds) != 1:
        raise RuntimeError(f"Expected one NavMesh bounds volume, found {len(bounds)}")
    nav_system.on_navigation_bounds_updated(bounds[0])

    # This exact command is intentionally before every save operation.
    unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
    recasts = list(unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.RecastNavMesh
    ))
    if len(recasts) != 1:
        raise RuntimeError(
            f"Explicit RebuildNavigation produced {len(recasts)} Recast actors"
        )
    recasts[0].set_editor_properties({
        "runtime_generation": unreal.RuntimeGenerationType.DYNAMIC,
        "can_be_main_nav_data": True,
    })
    gate.set_exact_tags(recasts[0], (contract.NAVIGATION_TAG,))
    nav_system.on_navigation_bounds_updated(bounds[0])
    unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
    recasts_after = list(unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.RecastNavMesh
    ))
    if len(recasts_after) != 1:
        raise RuntimeError(
            f"Second explicit navigation build produced {len(recasts_after)} Recast actors"
        )
    recasts_after[0].set_editor_properties({
        "runtime_generation": unreal.RuntimeGenerationType.DYNAMIC,
        "can_be_main_nav_data": True,
    })
    gate.set_exact_tags(recasts_after[0], (contract.NAVIGATION_TAG,))
    if unreal.NavigationSystemV1.is_navigation_being_built_or_locked(world):
        raise RuntimeError(
            "Navigation did not become quiescent after explicit pre-save build"
        )
    _actors, by_label = gate.actor_index(actors_api)
    evidence = gate.audit_navigation(world, by_label, require_quiescent=True)
    evidence["explicit_build_command"] = "RebuildNavigation"
    evidence["explicit_build_completed_before_save"] = True
    return evidence


def main() -> None:
    assets = unreal.EditorAssetLibrary
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if levels is None or actors_api is None:
        raise RuntimeError("Required Unreal editor subsystems are unavailable")
    assert_destination_absent(assets)
    anchors_before = frozen_anchor_snapshot()
    workspace_before = guarded_workspace_snapshot()

    if not SOURCE_FILE.is_file():
        raise RuntimeError(f"Source OneFactory v001 map is absent: {SOURCE_FILE}")
    if contract.sha256(SOURCE_FILE) != contract.SOURCE_MAP_SHA256:
        raise RuntimeError("Source OneFactory v001 map hash drifted before duplication")
    if not assets.does_asset_exist(contract.SOURCE_MAP):
        raise RuntimeError(f"Source map is absent from Asset Registry: {contract.SOURCE_MAP}")
    if not assets.duplicate_asset(contract.SOURCE_MAP, contract.TARGET_MAP):
        raise RuntimeError(
            f"Could not duplicate {contract.SOURCE_MAP} -> {contract.TARGET_MAP}"
        )
    if not levels.load_level(contract.TARGET_MAP):
        raise RuntimeError(f"Could not load fresh successor {contract.TARGET_MAP}")
    world = gate.editor_world()
    pre_mutation = validate_exact_duplicate_before_mutation(world, actors_api)

    replacement = replace_exposure_and_old_light(actors_api)
    high_bays = configure_high_bay_grid(actors_api)
    common_lighting = configure_common_sun_sky(actors_api)
    navigation = configure_and_build_navigation(world, actors_api)

    pre_save = gate.audit_complete_map(
        world,
        actors_api,
        run_bootstrap_validation=False,
        require_navigation_quiescent=True,
    )
    if not navigation.get("explicit_build_completed_before_save"):
        raise RuntimeError("Navigation build-before-save ordering evidence is absent")
    if not levels.save_current_level():
        raise RuntimeError(f"Could not save new OneFactory v002 map {contract.TARGET_MAP}")
    if not TARGET_FILE.is_file():
        raise RuntimeError("Saved OneFactory v002 map file is absent")
    target_hash_after_save = contract.sha256(TARGET_FILE)
    if contract.sha256(SOURCE_FILE) != contract.SOURCE_MAP_SHA256:
        raise RuntimeError("Source v001 map changed while saving v002")

    # Force a true level unload/reload before accepting the authored package.
    if not levels.load_level(contract.SOURCE_MAP):
        raise RuntimeError("Could not unload v002 through exact source-map reload")
    if not levels.load_level(contract.TARGET_MAP):
        raise RuntimeError("Could not fresh-reload saved OneFactory v002 map")
    fresh_world = gate.editor_world()
    fresh_reload = gate.audit_complete_map(
        fresh_world,
        actors_api,
        run_bootstrap_validation=True,
        require_navigation_quiescent=False,
        require_navigation_routes=False,
    )
    target_hash_after_reload = contract.sha256(TARGET_FILE)
    if target_hash_after_reload != target_hash_after_save:
        raise RuntimeError("OneFactory v002 map bytes changed during fresh reload")

    anchors_after = frozen_anchor_snapshot()
    workspace_after = guarded_workspace_snapshot()
    if anchors_after != anchors_before:
        raise RuntimeError("Static protected anchors changed during v002 authoring")
    if workspace_after != workspace_before:
        changed = sorted(
            set(workspace_before) ^ set(workspace_after)
            | {
                key for key in set(workspace_before) & set(workspace_after)
                if workspace_before[key] != workspace_after[key]
            }
        )
        raise RuntimeError(
            "Content (except target), Source, Config or SaveGames changed: "
            + ", ".join(changed[:40])
        )

    payload = {
        "$schema": "lineboss/audit/one-factory/visual-navigation-build-v002/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": contract.BUILD_STATUS,
        "builder_script": relative(SCRIPT_FILE),
        "builder_script_sha256": contract.sha256(SCRIPT_FILE),
        "source_map": contract.SOURCE_MAP,
        "source_map_file": contract.SOURCE_MAP_RELATIVE,
        "source_map_sha256_before": contract.SOURCE_MAP_SHA256,
        "source_map_sha256_after": contract.sha256(SOURCE_FILE),
        "target_map": contract.TARGET_MAP,
        "target_map_file": contract.TARGET_MAP_RELATIVE,
        "target_map_sha256": target_hash_after_reload,
        "destination_preexisted": False,
        "overwrite_refused": True,
        "exact_duplicate_pre_mutation": pre_mutation,
        "replacement": replacement,
        "high_bay_authoring": {
            "count": len(high_bays),
            "fixtures": high_bays,
            "intensity_lm_each": contract.HIGH_BAY_INTENSITY_LM,
            "temperature_kelvin": contract.HIGH_BAY_TEMPERATURE_K,
            "shadows": False,
        },
        "common_lighting": common_lighting,
        "navigation_build": navigation,
        "pre_save_audit": pre_save,
        "fresh_reload_audit": fresh_reload,
        "protected_anchors_before": anchors_before,
        "protected_anchors_after": anchors_after,
        "guarded_workspace_file_count": len(workspace_before),
        "guarded_workspace_unchanged": True,
        "source_content_config_save_mutations": [],
        "writes": [contract.TARGET_MAP_RELATIVE, contract.BUILD_RECEIPT_RELATIVE],
        "unreal_or_ubt_launched_by_static_preparation": False,
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(
        "LINE_BOSS_ONE_FACTORY_VISUAL_NAVIGATION_BUILD_V002_PASS "
        f"map={contract.TARGET_MAP} sha256={target_hash_after_reload}"
    )


try:
    main()
except Exception as exc:
    try:
        FAILURE_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        if not FAILURE_RECEIPT.exists():
            FAILURE_RECEIPT.write_text(json.dumps({
                "$schema": "lineboss/audit/one-factory/visual-navigation-build-v002-failure/v1",
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "status": "FAIL__ONE_FACTORY_VISUAL_NAVIGATION_BUILD_V002",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "source_map_sha256": (
                    contract.sha256(SOURCE_FILE) if SOURCE_FILE.is_file() else None
                ),
                "target_file_exists": TARGET_FILE.exists(),
                "target_map": contract.TARGET_MAP,
                "rerun_without_manual_review_forbidden": True,
            }, indent=2) + "\n", encoding="utf-8")
    finally:
        unreal.log_error(
            "LINE_BOSS_ONE_FACTORY_VISUAL_NAVIGATION_BUILD_V002_FAIL "
            f"{type(exc).__name__}: {exc}"
        )
        unreal.SystemLibrary.quit_editor()
    raise
else:
    unreal.SystemLibrary.quit_editor()
