"""Shared Unreal-side gates for the protected OneFactory v002 successor.

There are no top-level authoring actions in this module.  The guarded builder
and the independent fresh-process validator import these functions so both use
one exact shell, lighting, provenance and navigation contract.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Iterable

import unreal

import one_factory_visual_navigation_v002_contract as contract


ROOT = Path(unreal.Paths.project_dir()).resolve()


def path_name(value: Any) -> str | None:
    if value is None:
        return None
    method = getattr(value, "get_path_name", None)
    return str(method()) if callable(method) else str(value)


def tags_of(actor: Any) -> tuple[str, ...]:
    return tuple(sorted(str(tag) for tag in actor.get_editor_property("tags")))


def set_exact_tags(actor: Any, values: Iterable[str]) -> None:
    actor.set_editor_property("tags", [unreal.Name(value) for value in values])


def vector_tuple(value: Any) -> tuple[float, float, float]:
    return float(value.x), float(value.y), float(value.z)


def close_tuple(
    actual: Iterable[float], expected: Iterable[float], tolerance: float = 0.02
) -> bool:
    return all(
        abs(float(left) - float(right)) <= tolerance
        for left, right in zip(actual, expected)
    )


def load_v001_contract() -> Any:
    path = ROOT / contract.V001_VALIDATOR_RELATIVE
    if not path.is_file():
        raise RuntimeError(f"Frozen v001 validator is absent: {path}")
    digest = contract.sha256(path)
    if digest != contract.V001_VALIDATOR_SHA256:
        raise RuntimeError(
            "Frozen v001 validator hash drift: "
            f"{digest} != {contract.V001_VALIDATOR_SHA256}"
        )
    spec = importlib.util.spec_from_file_location(
        "lineboss_frozen_one_factory_shell_v001", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not create frozen v001 validator module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def editor_world() -> Any:
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = subsystem.get_editor_world() if subsystem is not None else None
    if world is None:
        world = unreal.EditorLevelLibrary.get_editor_world()
    if world is None:
        raise RuntimeError("OneFactory editor world is unavailable")
    return world


def actor_index(actors_api: Any) -> tuple[list[Any], dict[str, list[Any]]]:
    actors = list(actors_api.get_all_level_actors())
    nonfoundation = [
        actor
        for actor in actors
        if path_name(actor.get_class())
        not in {"/Script/Engine.WorldSettings", "/Script/Engine.DefaultPhysicsVolume"}
    ]
    by_label: dict[str, list[Any]] = {}
    for actor in nonfoundation:
        by_label.setdefault(actor.get_actor_label(), []).append(actor)
    return nonfoundation, by_label


def require_one(by_label: dict[str, list[Any]], label: str) -> Any:
    rows = by_label.get(label, [])
    if len(rows) != 1:
        raise RuntimeError(f"Expected exactly one {label}, found {len(rows)}")
    return rows[0]


def _raise_state_failures(state: dict[str, Any], context: str) -> None:
    failures = state.get("failures", [])
    if failures:
        names = [str(row.get("name", "unknown")) for row in failures]
        raise RuntimeError(f"{context}: " + ", ".join(names))


def audit_hism_structure(
    base: Any, by_label: dict[str, list[Any]]
) -> dict[str, Any]:
    expected_instances = base.expected_hism_instances()
    evidence: dict[str, Any] = {}
    total = 0
    for label, spec in base.HISM_ACTORS.items():
        actor = require_one(by_label, label)
        components = actor.get_components_by_class(
            unreal.HierarchicalInstancedStaticMeshComponent
        )
        if len(components) != 1:
            raise RuntimeError(f"{label} must retain exactly one HISM component")
        component = components[0]
        expected_navigation = label == contract.FLOOR_HISM_LABEL
        actual = {
            "class": path_name(component.get_class()),
            "component_tags": sorted(
                str(tag)
                for tag in component.get_editor_property("component_tags")
            ),
            "mesh": path_name(component.get_editor_property("static_mesh")),
            "material": path_name(component.get_material(0)),
            "collision_profile": str(component.get_collision_profile_name()),
            "can_ever_affect_navigation": bool(
                component.get_editor_property("can_ever_affect_navigation")
            ),
            "cast_shadow": bool(component.get_editor_property("cast_shadow")),
            "mobility": str(component.get_editor_property("mobility")),
            "instance_count": int(component.get_instance_count()),
        }
        expected = {
            "class": "/Script/Engine.HierarchicalInstancedStaticMeshComponent",
            "component_tags": [spec["component_tag"]],
            "mesh": base.CUBE_PATH,
            "material": base.MATERIALS[spec["material"]],
            "collision_profile": spec["collision_profile"],
            "can_ever_affect_navigation": expected_navigation,
            "cast_shadow": bool(spec["cast_shadow"]),
            "mobility": str(unreal.ComponentMobility.STATIC),
            "instance_count": len(expected_instances[label]),
        }
        if actual != expected:
            raise RuntimeError(
                f"Preserved HISM component drift for {label}: "
                f"expected={expected!r} actual={actual!r}"
            )
        transform_failures = []
        for index, expected_instance in enumerate(expected_instances[label]):
            transform = base.unpack_instance_transform(
                component.get_instance_transform(index, False)
            )
            row = base.transform_evidence(transform)
            expected_transform = {
                "location": list(expected_instance["location"]),
                "scale": [
                    float(value) / 100.0
                    for value in expected_instance["dimensions"]
                ],
                "quaternion": [0.0, 0.0, 0.0, 1.0],
            }
            valid = (
                row is not None
                and close_tuple(row["location"], expected_transform["location"])
                and close_tuple(
                    row["scale"], expected_transform["scale"], 0.0002
                )
                and close_tuple(
                    row["quaternion"], expected_transform["quaternion"], 0.0002
                )
            )
            if not valid:
                transform_failures.append(
                    {"index": index, "expected": expected_transform, "actual": row}
                )
        if transform_failures:
            raise RuntimeError(
                f"Ordered HISM transforms drifted for {label}: "
                f"{transform_failures[:8]!r}"
            )
        total += actual["instance_count"]
        evidence[label] = actual
    if len(evidence) != 10 or total != 1_194:
        raise RuntimeError(
            f"HISM structure cardinality drift: actors={len(evidence)} instances={total}"
        )
    return {
        "actor_count": len(evidence),
        "total_instance_count": total,
        "floor_navigation_enabled_only": contract.FLOOR_HISM_LABEL,
        "actors": evidence,
    }


def audit_preserved_shell(
    world: Any,
    actors_api: Any,
    *,
    run_bootstrap_validation: bool,
) -> dict[str, Any]:
    base = load_v001_contract()
    if world.get_path_name() != contract.TARGET_MAP_OBJECT:
        raise RuntimeError(
            f"Wrong v002 world: {world.get_path_name()} != {contract.TARGET_MAP_OBJECT}"
        )
    if base.world_partition_evidence(world).get("enabled") is not False:
        raise RuntimeError("OneFactory v002 must remain non-World-Partition")

    nonfoundation, by_label = actor_index(actors_api)
    preserved_specs = {
        label: spec
        for label, spec in base.EXPECTED_ACTORS.items()
        if label
        not in {
            contract.OLD_LIGHT_LABEL,
            contract.OLD_EXPOSURE_LABEL,
            contract.RECAST_LABEL,
        }
    }
    expected_labels = (
        set(preserved_specs)
        | {row["label"] for row in contract.high_bay_specs()}
        | {
            contract.EXPOSURE_LABEL,
            contract.SUN_LABEL,
            contract.SKY_LABEL,
            contract.RECAST_LABEL,
        }
    )
    actual_labels = set(by_label)
    duplicates = sorted(label for label, rows in by_label.items() if len(rows) != 1)
    if actual_labels != expected_labels or duplicates:
        raise RuntimeError(
            "OneFactory v002 actor identity drift: "
            f"missing={sorted(expected_labels - actual_labels)} "
            f"unexpected={sorted(actual_labels - expected_labels)} "
            f"duplicates={duplicates}"
        )
    if len(nonfoundation) != 59:
        raise RuntimeError(
            f"OneFactory v002 requires exactly 59 nonfoundation actors, "
            f"found {len(nonfoundation)}"
        )

    state: dict[str, Any] = {"checks": [], "failures": []}
    preserved_rows = {}
    for label, spec in preserved_specs.items():
        preserved_rows[label] = base.validate_actor_contract(
            state, label, by_label[label][0], spec
        )
    _raise_state_failures(state, "Preserved v001 actor contract failed")

    game_mode = world.get_world_settings().get_editor_property("default_game_mode")
    if path_name(game_mode) != base.GAME_MODE_CLASS_PATH:
        raise RuntimeError("Map-local OneFactory GameMode drifted")

    bootstrap_class = unreal.load_class(None, base.BOOTSTRAP_CLASS_PATH)
    authority_class = unreal.load_class(None, base.PRESS_AUTHORITY_CLASS_PATH)
    if bootstrap_class is None or authority_class is None:
        raise RuntimeError("Required OneFactory native classes are unavailable")
    bootstraps = [actor for actor in nonfoundation if actor.get_class() == bootstrap_class]
    authorities = [actor for actor in nonfoundation if actor.get_class() == authority_class]
    if len(bootstraps) != 1 or len(authorities) != 1:
        raise RuntimeError(
            f"Bootstrap/authority singleton drift: {len(bootstraps)}/{len(authorities)}"
        )
    if (
        bootstraps[0].get_owner() is not None
        or authorities[0].get_owner() is not None
        or bootstraps[0].get_attach_parent_actor() is not None
        or authorities[0].get_attach_parent_actor() is not None
        or bootstraps[0].get_outer() != authorities[0].get_outer()
    ):
        raise RuntimeError("Bootstrap/authority map-authored relationship drift")
    authority_state: dict[str, Any] = {"checks": [], "failures": []}
    authority_facts: dict[str, Any] = {}
    base.validate_press_authority(authority_state, authorities[0], authority_facts)
    _raise_state_failures(authority_state, "Press authority layout contract failed")

    bootstrap_evidence = {"executed": False, "passed": None, "reason": None}
    if run_bootstrap_validation:
        result = bootstraps[0].validate_and_lock_shell()
        if isinstance(result, tuple):
            passed = bool(result[0])
            reason = str(result[1]) if len(result) > 1 else ""
        else:
            passed = bool(result)
            reason = ""
        valid = passed and bool(bootstraps[0].has_valid_shell())
        bootstrap_evidence = {
            "executed": True,
            "passed": valid,
            "reason": reason,
        }
        if not valid:
            raise RuntimeError(f"OneFactory bootstrap rejected v002: {reason}")

    unapproved_project = [
        {
            "label": actor.get_actor_label(),
            "class": path_name(actor.get_class()),
        }
        for actor in nonfoundation
        if path_name(actor.get_class()).startswith("/Script/LineBossCarFactory.")
        and actor.get_class() not in {bootstrap_class, authority_class}
    ]
    if unapproved_project:
        raise RuntimeError(
            f"Saved shell contains production/project actors: {unapproved_project!r}"
        )
    forbidden_prefixes = ("lb.wip", "lb.inventory", "lb.material.unit")
    forbidden_identity = []
    for actor in nonfoundation:
        identity = (
            actor.get_actor_label(),
            path_name(actor.get_class()) or "",
            *tags_of(actor),
        )
        lowered = [item.lower() for item in identity]
        if (
            any(item == "processwip" for item in lowered)
            or any(item.startswith(forbidden_prefixes) for item in lowered)
            or any("meshy" in item or "externalgenerated" in item for item in lowered)
        ):
            forbidden_identity.append(identity)
    if forbidden_identity:
        raise RuntimeError(
            "Saved shell contains WIP/forbidden provenance identity: "
            f"{forbidden_identity!r}"
        )

    hism = audit_hism_structure(base, by_label)
    return {
        "nonfoundation_actor_count": len(nonfoundation),
        "preserved_actor_count": len(preserved_rows),
        "preserved_actor_labels": sorted(preserved_rows),
        "bootstrap_count": 1,
        "press_build_authority_count": 1,
        "bootstrap_validation": bootstrap_evidence,
        "press_authority": authority_facts.get("press_authority_contract"),
        "hism": hism,
        "saved_production_actor_count": 0,
        "saved_wip_identity_count": 0,
        "forbidden_provenance_identity_count": 0,
    }


def _component_mobility(component: Any) -> str:
    return str(component.get_editor_property("mobility"))


def audit_lighting(by_label: dict[str, list[Any]]) -> dict[str, Any]:
    expected_tags = tuple(sorted((
        contract.MAP_TAG,
        contract.NATIVE_TAG,
        contract.ENVIRONMENT_TAG,
        contract.HIGH_BAY_GRID_TAG,
        contract.LIGHT_AUTHORITY_TAG,
        contract.PERFORMANCE_TAG,
    )))
    fixtures = []
    for spec in contract.high_bay_specs():
        actor = require_one(by_label, spec["label"])
        component = actor.get_component_by_class(unreal.RectLightComponent)
        if component is None:
            raise RuntimeError(f"{spec['label']} has no RectLightComponent")
        row = {
            "label": spec["label"],
            "location_cm": list(vector_tuple(actor.get_actor_location())),
            "rotation": [
                float(actor.get_actor_rotation().pitch),
                float(actor.get_actor_rotation().yaw),
                float(actor.get_actor_rotation().roll),
            ],
            "tags": list(tags_of(actor)),
            "intensity": float(component.get_editor_property("intensity")),
            "units": str(component.get_editor_property("intensity_units")),
            "attenuation_radius": float(
                component.get_editor_property("attenuation_radius")
            ),
            "source_width": float(component.get_editor_property("source_width")),
            "source_height": float(component.get_editor_property("source_height")),
            "use_temperature": bool(component.get_editor_property("use_temperature")),
            "temperature": float(component.get_editor_property("temperature")),
            "cast_shadows": bool(component.get_editor_property("cast_shadows")),
            "affect_translucent_lighting": bool(
                component.get_editor_property("affect_translucent_lighting")
            ),
            "volumetric_scattering_intensity": float(
                component.get_editor_property("volumetric_scattering_intensity")
            ),
            "mobility": _component_mobility(component),
        }
        valid = (
            close_tuple(row["location_cm"], spec["location_cm"])
            and actor.get_actor_rotation().is_near_equal(
                unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), 0.02
            )
            and tuple(row["tags"]) == expected_tags
            and abs(row["intensity"] - contract.HIGH_BAY_INTENSITY_LM) <= 0.01
            and row["units"] == str(unreal.LightUnits.LUMENS)
            and abs(
                row["attenuation_radius"] - contract.HIGH_BAY_ATTENUATION_CM
            ) <= 0.01
            and abs(row["source_width"] - contract.HIGH_BAY_SOURCE_WIDTH_CM) <= 0.01
            and abs(row["source_height"] - contract.HIGH_BAY_SOURCE_HEIGHT_CM) <= 0.01
            and row["use_temperature"]
            and abs(row["temperature"] - contract.HIGH_BAY_TEMPERATURE_K) <= 0.01
            and not row["cast_shadows"]
            and not row["affect_translucent_lighting"]
            and abs(row["volumetric_scattering_intensity"]) <= 0.0001
            and row["mobility"] == str(unreal.ComponentMobility.MOVABLE)
        )
        if not valid:
            raise RuntimeError(f"High-bay contract drift: {row!r}")
        fixtures.append(row)
    if len(fixtures) != contract.HIGH_BAY_COUNT:
        raise RuntimeError(
            f"High-bay count {len(fixtures)} != {contract.HIGH_BAY_COUNT}"
        )

    old_lights = by_label.get(contract.OLD_LIGHT_LABEL, [])
    old_exposure = by_label.get(contract.OLD_EXPOSURE_LABEL, [])
    if old_lights or old_exposure:
        raise RuntimeError("Legacy giant light/exposure identity survived v002 replacement")

    exposure = require_one(by_label, contract.EXPOSURE_LABEL)
    settings = exposure.get_editor_property("settings")
    exposure_row = {
        "class": path_name(exposure.get_class()),
        "location_cm": list(vector_tuple(exposure.get_actor_location())),
        "scale": list(vector_tuple(exposure.get_actor_scale3d())),
        "unbound": bool(exposure.get_editor_property("unbound")),
        "blend_weight": float(exposure.get_editor_property("blend_weight")),
        "tags": list(tags_of(exposure)),
        "method": str(settings.get_editor_property("auto_exposure_method")),
        "override_method": bool(
            settings.get_editor_property("override_auto_exposure_method")
        ),
        "override_min": bool(
            settings.get_editor_property("override_auto_exposure_min_brightness")
        ),
        "override_max": bool(
            settings.get_editor_property("override_auto_exposure_max_brightness")
        ),
        "minimum": float(settings.get_editor_property("auto_exposure_min_brightness")),
        "maximum": float(settings.get_editor_property("auto_exposure_max_brightness")),
        "override_bias": bool(
            settings.get_editor_property("override_auto_exposure_bias")
        ),
        "bias": float(settings.get_editor_property("auto_exposure_bias")),
    }
    expected_exposure_tags = sorted((
        contract.MAP_TAG,
        contract.NATIVE_TAG,
        contract.ENVIRONMENT_TAG,
        contract.FIXED_EXPOSURE_TAG,
    ))
    if not (
        exposure_row["class"] == "/Script/Engine.PostProcessVolume"
        and close_tuple(exposure_row["location_cm"], (0.0, 0.0, 0.0))
        and close_tuple(exposure_row["scale"], (1.0, 1.0, 1.0), 0.0002)
        and exposure.get_actor_rotation().is_near_equal(unreal.Rotator(), 0.02)
        and exposure_row["unbound"]
        and abs(exposure_row["blend_weight"] - 1.0) <= 0.01
        and exposure_row["tags"] == expected_exposure_tags
        and exposure_row["override_method"]
        and settings.get_editor_property("auto_exposure_method")
        == unreal.AutoExposureMethod.AEM_BASIC
        and exposure_row["override_min"]
        and exposure_row["override_max"]
        and abs(exposure_row["minimum"] - contract.FIXED_EXPOSURE_MIN) <= 0.01
        and abs(exposure_row["maximum"] - contract.FIXED_EXPOSURE_MAX) <= 0.01
        and exposure_row["override_bias"]
        and abs(exposure_row["bias"] - contract.FIXED_EXPOSURE_BIAS) <= 0.01
    ):
        raise RuntimeError(f"Fixed exposure contract drift: {exposure_row!r}")

    sun = require_one(by_label, contract.SUN_LABEL)
    sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sky = require_one(by_label, contract.SKY_LABEL)
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    if sun_component is None or sky_component is None:
        raise RuntimeError("Common sun/sky component is unavailable")
    sun_row = {
        "class": path_name(sun.get_class()),
        "location_cm": list(vector_tuple(sun.get_actor_location())),
        "scale": list(vector_tuple(sun.get_actor_scale3d())),
        "intensity": float(sun_component.get_editor_property("intensity")),
        "tags": list(tags_of(sun)),
        "mobility": _component_mobility(sun_component),
    }
    sky_row = {
        "class": path_name(sky.get_class()),
        "location_cm": list(vector_tuple(sky.get_actor_location())),
        "scale": list(vector_tuple(sky.get_actor_scale3d())),
        "intensity": float(sky_component.get_editor_property("intensity")),
        "tags": list(tags_of(sky)),
        "mobility": _component_mobility(sky_component),
    }
    if (
        sun_row["class"] != "/Script/Engine.DirectionalLight"
        or not close_tuple(sun_row["location_cm"], (0.0, 0.0, 8_000.0))
        or not close_tuple(sun_row["scale"], (1.0, 1.0, 1.0), 0.0002)
        or not sun.get_actor_rotation().is_near_equal(
            unreal.Rotator(roll=0.0, pitch=-52.0, yaw=-28.0), 0.02
        )
        or abs(sun_row["intensity"] - contract.SUN_INTENSITY) > 0.01
        or sun_row["tags"] != sorted((
            contract.MAP_TAG,
            contract.NATIVE_TAG,
            contract.ENVIRONMENT_TAG,
            contract.COMMON_SUN_TAG,
        ))
        or sun_row["mobility"] != str(unreal.ComponentMobility.MOVABLE)
        or sky_row["class"] != "/Script/Engine.SkyLight"
        or not close_tuple(sky_row["location_cm"], (0.0, 0.0, 8_000.0))
        or not close_tuple(sky_row["scale"], (1.0, 1.0, 1.0), 0.0002)
        or not sky.get_actor_rotation().is_near_equal(unreal.Rotator(), 0.02)
        or abs(sky_row["intensity"] - contract.SKY_INTENSITY) > 0.01
        or sky_row["tags"] != sorted((
            contract.MAP_TAG,
            contract.NATIVE_TAG,
            contract.ENVIRONMENT_TAG,
            contract.COMMON_SKY_TAG,
        ))
        or sky_row["mobility"] != str(unreal.ComponentMobility.MOVABLE)
    ):
        raise RuntimeError(f"Common sun/sky contract drift: {sun_row!r} {sky_row!r}")
    return {
        "high_bay_count": len(fixtures),
        "high_bay_grid": fixtures,
        "fixed_exposure": exposure_row,
        "common_sun": sun_row,
        "common_sky": sky_row,
        "legacy_giant_rect_light_count": 0,
    }


def navigation_route(world: Any, name: str, start: tuple[float, float, float],
                     end: tuple[float, float, float]) -> dict[str, Any]:
    requested_start = unreal.Vector(*start)
    requested_end = unreal.Vector(*end)
    extent = unreal.Vector(*contract.NAVIGATION_PROJECT_EXTENT_CM)
    projected_start = unreal.NavigationSystemV1.project_point_to_navigation(
        world, requested_start, None, None, extent
    )
    projected_end = unreal.NavigationSystemV1.project_point_to_navigation(
        world, requested_end, None, None, extent
    )
    path = (
        unreal.NavigationSystemV1.find_path_to_location_synchronously(
            world, projected_start, projected_end
        )
        if projected_start is not None and projected_end is not None
        else None
    )
    return {
        "name": name,
        "requested_start_cm": list(start),
        "requested_end_cm": list(end),
        "projected_start_cm": (
            list(vector_tuple(projected_start)) if projected_start is not None else None
        ),
        "projected_end_cm": (
            list(vector_tuple(projected_end)) if projected_end is not None else None
        ),
        "path_present": path is not None,
        "path_valid": bool(path is not None and path.is_valid()),
        "path_partial": bool(path.is_partial()) if path is not None else None,
        "path_length_cm": (
            float(path.get_path_length()) if path is not None else None
        ),
        "path_point_count": len(path.path_points) if path is not None else 0,
    }


def audit_navigation(
    world: Any,
    by_label: dict[str, list[Any]],
    *,
    require_quiescent: bool,
    require_routes: bool = True,
) -> dict[str, Any]:
    nav_system = unreal.NavigationSystemV1.get_navigation_system(world)
    if nav_system is None:
        raise RuntimeError("NavigationSystemV1 is unavailable")
    building = bool(unreal.NavigationSystemV1.is_navigation_being_built_or_locked(world))
    if require_quiescent and building:
        raise RuntimeError("Navigation is still being built or locked")
    recast = require_one(by_label, contract.RECAST_LABEL)
    if not isinstance(recast, unreal.RecastNavMesh):
        raise RuntimeError("RecastNavMesh-Default is not a RecastNavMesh")
    recast_row = {
        "class": path_name(recast.get_class()),
        "owner": path_name(recast.get_owner()),
        "attach_parent": path_name(recast.get_attach_parent_actor()),
        "runtime_generation": str(recast.get_editor_property("runtime_generation")),
        "can_be_main_nav_data": bool(
            recast.get_editor_property("can_be_main_nav_data")
        ),
        "tags": list(tags_of(recast)),
    }
    if (
        recast_row["class"] != "/Script/NavigationSystem.RecastNavMesh"
        or recast_row["owner"] is not None
        or recast_row["attach_parent"] is not None
        or recast.get_editor_property("runtime_generation")
        != unreal.RuntimeGenerationType.DYNAMIC
        or not recast_row["can_be_main_nav_data"]
        or recast_row["tags"] != [contract.NAVIGATION_TAG]
    ):
        raise RuntimeError(f"Recast contract drift: {recast_row!r}")
    routes = (
        [navigation_route(world, *row) for row in contract.NAVIGATION_PROBES]
        if require_routes else []
    )
    if require_routes:
        failed = [
            row
            for row in routes
            if not row["path_valid"]
            or row["path_partial"]
            or row["path_point_count"] < 2
        ]
        if failed:
            raise RuntimeError(f"OneFactory navigation route gate failed: {failed!r}")
    settings = world.get_world_settings()
    config = settings.get_editor_property("navigation_system_config")
    config_row = {
        "class": path_name(config.get_class()) if config is not None else None,
        "strictly_static": (
            bool(config.get_editor_property("bStrictlyStatic"))
            if config is not None else None
        ),
        "auto_spawn_missing_nav_data": (
            bool(config.get_editor_property("bAutoSpawnMissingNavData"))
            if config is not None else None
        ),
        "spawn_nav_data_in_nav_bounds_level": (
            bool(config.get_editor_property("bSpawnNavDataInNavBoundsLevel"))
            if config is not None else None
        ),
        "navigation_system_class": (
            str(config.get_editor_property("navigation_system_class"))
            if config is not None else None
        ),
    }
    if not (
        config is not None
        and config_row["class"]
        == "/Script/NavigationSystem.NavigationSystemModuleConfig"
        and not config_row["strictly_static"]
        and config_row["auto_spawn_missing_nav_data"]
        and config_row["spawn_nav_data_in_nav_bounds_level"]
        and "NavigationSystemV1" in config_row["navigation_system_class"]
    ):
        raise RuntimeError(f"NavigationSystemConfig contract drift: {config_row!r}")
    return {
        "navigation_system_present": True,
        "building_or_locked": building,
        "recast": recast_row,
        "config": config_row,
        "routes_required": require_routes,
        "routes": routes,
    }


def audit_complete_map(
    world: Any,
    actors_api: Any,
    *,
    run_bootstrap_validation: bool,
    require_navigation_quiescent: bool,
    require_navigation_routes: bool = True,
) -> dict[str, Any]:
    shell = audit_preserved_shell(
        world,
        actors_api,
        run_bootstrap_validation=run_bootstrap_validation,
    )
    _actors, by_label = actor_index(actors_api)
    lighting = audit_lighting(by_label)
    navigation = audit_navigation(
        world,
        by_label,
        require_quiescent=require_navigation_quiescent,
        require_routes=require_navigation_routes,
    )
    return {"shell": shell, "lighting": lighting, "navigation": navigation}
