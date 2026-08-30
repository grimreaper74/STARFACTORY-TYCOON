"""Read-only exact-map PIE diagnosis for the Press Shop V004 route failure.

This lane exists only to explain a failed ``GetConfiguredStationRoute`` call.
It loads the pinned V004 candidate, observes its transient PIE world once, and
captures the five native authority states plus the runtime coordinator's raw
route result.  It calls only pure capture/validation/query functions.  It does
not restore, commission, dispatch, tick, submit, refresh, save, import, build,
cook, package, or change an editor/runtime property.

Unreal Python 5.8 strips a leading native bool when a function also has output
parameters.  Success returns the output value(s); native false returns ``None``
and suppresses ``OutReason``.  Native false is recorded explicitly and is never
accepted as success.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:  # Keeps the module importable by offline tests.
    import unreal  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - offline test seam
    unreal = None  # type: ignore


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
TARGET_MAP = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v004/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004"
)
TARGET_FILE = (
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
    / "PressShop2126_OverheadPresentation_v004" / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004.umap"
)
SOURCE_RECEIPT = (
    PROJECT / "Saved" / "Audits" / "PressShop2126"
    / "OverheadPresentation_v004" / "install_receipt_v001.json"
)
OUTPUT_RECEIPT = (
    PROJECT / "Saved" / "Audits" / "PressShop2126" / "ExactMapPIE_v004"
    / "diagnostics" / "route_preflight_diagnostic_v001.json"
)
GAME_MODE_CLASS = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
GAME_WORLD_TIMEOUT_SECONDS = 75.0
RUN_TIMEOUT_SECONDS = 90.0

TRACKED_FILES: Mapping[Path, str] = {
    PROJECT / "Content" / "LineBoss" / "Factory" / "OneFactory" / "v001"
    / "Maps" / "LB_MoorcrossWorks_OneFactory_v001.umap": (
        "f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c"
    ),
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
    / "PressShop2126_OverheadPlayable_v001" / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001.umap": (
        "43020cb3ea7d18a49319da68a04ae1b96d5af0d535c705e947f81d5c005ba7ce"
    ),
    PROJECT / "Content" / "LineBoss" / "Maps"
    / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": (
        "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8"
    ),
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
    / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": (
        "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0"
    ),
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
    / "PressShop2126_OverheadPresentation_v002" / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002.umap": (
        "58fe57f3af0dfcf4021d6bbcd3a52d7d66de22187b561fb2db41becd83023275"
    ),
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
    / "PressShop2126_OverheadCargo_v003" / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003.umap": (
        "5eae51f2a7d3e1c72deb4fd455d57a6339dee061840b7d062c5ddf680ab6100f"
    ),
    TARGET_FILE: (
        "ab77d9bc327e65fa5bf8b8efd4d6666252247be1420070563f83bb099d98fe9f"
    ),
    SOURCE_RECEIPT: (
        "9c2bca410ebb40a534cdaa65a41c433c6f535df566ae209865f6fe5053a706d4"
    ),
}


LAYOUT_SPECS: Tuple[Mapping[str, Any], ...] = (
    {
        "key": "press",
        "authority_class": "LBOneFactoryPressStarterLayoutAuthority",
        "library_class": "LBOneFactoryPressStarterLayoutLibrary",
        "layout_fields": (
            "version", "layout_id", "revision", "commissioned",
            "stations", "connections",
        ),
        "station_fields": (
            "version", "station_id", "role", "world_transform",
            "footprint_size_cm", "player_reconfigurable", "vehicle_model_id",
            "panel_type_id", "die_id", "active_or_reserved_unit_ids",
        ),
        "connection_fields": (
            "version", "connection_id", "source_station_id",
            "target_station_id", "material_class", "maximum_route_length_cm",
        ),
    },
    {
        "key": "body_weld",
        "authority_class": "LBOneFactoryBodyWeldStarterLayoutAuthority",
        "library_class": "LBOneFactoryBodyWeldStarterLayoutLibrary",
        "layout_fields": (
            "version", "layout_id", "revision", "vehicle_model_id",
            "input_state", "output_state", "commissioned", "stations",
            "connections",
        ),
        "station_fields": (
            "version", "station_id", "line_position", "world_transform",
            "footprint_size_cm", "nominal_cycle_seconds", "subassembly_cell_id",
            "capabilities", "supported_robot_roles", "left_robot_role",
            "right_robot_role", "mirrored_large_six_axis_pair",
            "assigned_programmes", "active_or_reserved_unit_ids",
        ),
        "connection_fields": (
            "version", "connection_id", "source_station_id",
            "target_station_id", "maximum_route_length_cm",
        ),
    },
    {
        "key": "paint",
        "authority_class": "LBOneFactoryPaintStarterLayoutAuthority",
        "library_class": "LBOneFactoryPaintStarterLayoutLibrary",
        "layout_fields": (
            "version", "layout_id", "revision", "vehicle_model_id",
            "input_body_state", "output_body_state", "selected_body_colour",
            "paint_programme_id", "commissioned", "stations", "connections",
        ),
        "station_fields": (
            "version", "station_id", "role", "world_transform",
            "footprint_size_cm", "input_body_state", "output_body_state",
            "paint_programme_id", "target_body_colour", "player_positionable",
            "player_programme_selectable", "active_or_reserved_unit_ids",
        ),
        "connection_fields": (
            "version", "connection_id", "source_station_id",
            "target_station_id", "carried_body_state",
            "maximum_route_length_cm",
        ),
    },
    {
        "key": "assembly",
        "authority_class": "LBOneFactoryAssemblyStarterLayoutAuthority",
        "library_class": "LBOneFactoryAssemblyStarterLayoutLibrary",
        "layout_fields": (
            "version", "layout_id", "revision", "vehicle_model_id",
            "input_state", "output_state", "commissioned", "stations",
            "connections",
        ),
        "station_fields": (
            "version", "station_id", "line_position", "world_transform",
            "footprint_size_cm", "nominal_cycle_seconds", "capabilities",
            "assigned_operations", "active_or_reserved_unit_ids",
        ),
        "connection_fields": (
            "version", "connection_id", "source_station_id",
            "target_station_id", "maximum_route_length_cm",
        ),
    },
)

COMMISSIONING_FIELDS = (
    "press_commissioned", "body_commissioned", "paint_commissioned",
    "assembly_commissioned",
)
LEDGER_FIELDS = (
    "version", "ledger_id", "revision", "maximum_concurrent_wip",
    "next_vehicle_serial", "completed_vehicle_count",
    "dispatched_vehicle_count", "sim_clock_seconds", "line_paused",
    "faulted_departments", "output_blocked_departments", "commissioning",
    "contracts", "units", "fleet_wear01", "maintenance_serial",
    "emergency_contract_serial", "financial_state", "reputation_score",
)
CONTRACT_FIELDS = (
    "contract_id", "vehicle_model_id", "quantity", "dispatched_count",
    "price_per_vehicle_pence", "deadline_sim_seconds", "state", "emergency",
)
UNIT_FIELDS = (
    "version", "unit_id", "build_order_id", "vehicle_model_id",
    "vehicle_recipe_revision_id", "paint_programme_id", "paint_colour_id",
    "source_material_unit_ids", "current_station_id", "department", "stage",
    "stage_revision", "completed", "dispatched", "quality_state",
    "defect_suspected", "fulfilled_contract_id", "evidence_ids",
    "required_panel_type_ids", "pressed_panel_type_ids",
    "route_profile_version", "runtime_station_cursor",
    "runtime_completed_station_count", "runtime_total_station_count",
    "runtime_topology_id", "runtime_current_assignment_id",
    "runtime_cycle_elapsed_seconds", "runtime_cycle_duration_seconds",
    "runtime_started", "created_at_sim_seconds", "dispatched_at_sim_seconds",
)


class DiagnosticError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise DiagnosticError("PRESSSHOP_2126_ROUTE_DIAGNOSTIC_V001_FAIL: " + message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_fingerprint(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        fail("tracked file missing: {}".format(path))
    stat = path.stat()
    return {
        "path": str(path), "sha256": sha256(path),
        "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
    }


def verify_tracked_files() -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for path, expected in TRACKED_FILES.items():
        observed = file_fingerprint(path)
        if observed["sha256"] != expected:
            fail("tracked file SHA-256 mismatch: {}".format(path))
        result[str(path)] = observed
    return result


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False,
                       indent=2, sort_keys=True) + "\n").encode("utf-8")


def _read(value: Any, name: str) -> Any:
    try:
        return value.get_editor_property(name)
    except Exception:
        return getattr(value, name)


def _plain_number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, (list, tuple)):
        return [_value(item) for item in value]
    # Unreal FVector/FQuat/FRotator are deliberately handled structurally.
    coordinates: Dict[str, Any] = {}
    for key in ("x", "y", "z", "w"):
        try:
            coordinates[key] = float(getattr(value, key))
        except Exception:
            pass
    if len(coordinates) >= 2:
        return coordinates
    angles: Dict[str, Any] = {}
    for key in ("roll", "pitch", "yaw"):
        try:
            angles[key] = float(getattr(value, key))
        except Exception:
            pass
    if len(angles) == 3:
        return angles
    # Transform properties are available through get_editor_property in UE 5.8.
    transform: Dict[str, Any] = {}
    for key in ("translation", "rotation", "scale3d"):
        try:
            transform[key] = _value(_read(value, key))
        except Exception:
            pass
    if len(transform) == 3:
        return transform
    try:
        enum_name = value.name
        if isinstance(enum_name, str):
            return enum_name
    except Exception:
        pass
    return str(value)


def _record(value: Any, fields: Iterable[str]) -> Dict[str, Any]:
    output: Dict[str, Any] = {}
    for field in fields:
        output[field] = _value(_read(value, field))
    return output


def _layout_snapshot(state: Any, spec: Mapping[str, Any]) -> Dict[str, Any]:
    output = _record(state, spec["layout_fields"])
    output["stations"] = [
        _record(station, spec["station_fields"])
        for station in list(_read(state, "stations"))
    ]
    output["connections"] = [
        _record(connection, spec["connection_fields"])
        for connection in list(_read(state, "connections"))
    ]
    return output


def _ledger_snapshot(state: Any) -> Dict[str, Any]:
    output = _record(state, LEDGER_FIELDS)
    output["commissioning"] = _record(
        _read(state, "commissioning"), COMMISSIONING_FIELDS)
    output["contracts"] = [
        _record(contract, CONTRACT_FIELDS)
        for contract in list(_read(state, "contracts"))
    ]
    output["units"] = [
        _record(unit, UNIT_FIELDS) for unit in list(_read(state, "units"))
    ]
    return output


def _diff(actual: Any, canonical: Any, path: str = "") -> List[Dict[str, Any]]:
    differences: List[Dict[str, Any]] = []
    if isinstance(actual, dict) and isinstance(canonical, dict):
        for key in sorted(set(actual) | set(canonical)):
            child = "{}.{}".format(path, key) if path else key
            if key not in actual or key not in canonical:
                differences.append({
                    "path": child, "actual": actual.get(key),
                    "canonical": canonical.get(key),
                })
            else:
                differences.extend(_diff(actual[key], canonical[key], child))
        return differences
    if isinstance(actual, list) and isinstance(canonical, list):
        limit = max(len(actual), len(canonical))
        for index in range(limit):
            child = "{}[{}]".format(path, index)
            if index >= len(actual) or index >= len(canonical):
                differences.append({
                    "path": child,
                    "actual": actual[index] if index < len(actual) else None,
                    "canonical": canonical[index] if index < len(canonical) else None,
                })
            else:
                differences.extend(_diff(actual[index], canonical[index], child))
        return differences
    if actual != canonical:
        differences.append({"path": path, "actual": actual,
                            "canonical": canonical})
    return differences


def reflected_bool_out(result: Any) -> Dict[str, Any]:
    """Describe UE's bool+out reflected value without accepting None."""
    if result is None:
        return {
            "native_success": False,
            "raw_shape": "NONE_NATIVE_FALSE_OUT_REASON_SUPPRESSED",
            "out_reason": None,
        }
    if isinstance(result, tuple) and result and isinstance(result[0], bool):
        return {
            "native_success": bool(result[0]),
            "raw_shape": "EXPLICIT_BOOL_TUPLE",
            "out_reason": _value(result[-1]) if len(result) > 1 else None,
        }
    return {
        "native_success": True,
        "raw_shape": "OUTPUT_ONLY_SUCCESS",
        "out_reason": _value(result[-1] if isinstance(result, tuple) else result),
    }


def reflected_route(result: Any) -> Dict[str, Any]:
    if result is None:
        return {
            "native_success": False,
            "raw_shape": "NONE_NATIVE_FALSE_OUT_PARAMETERS_SUPPRESSED",
            "route_count": None, "topology_id": None, "out_reason": None,
        }
    values = list(result) if isinstance(result, tuple) else [result]
    if values and isinstance(values[0], bool):
        success = bool(values.pop(0))
        if not success:
            return {
                "native_success": False,
                "raw_shape": "EXPLICIT_BOOL_TUPLE_FALSE",
                "route_count": None, "topology_id": None,
                "out_reason": _value(values[-1]) if values else None,
            }
    if len(values) < 2:
        return {
            "native_success": False,
            "raw_shape": "UNSUPPORTED_REFLECTION_SHAPE",
            "route_count": None, "topology_id": None,
            "out_reason": _value(values),
        }
    route = list(values[0])
    return {
        "native_success": True,
        "raw_shape": "OUTPUT_ONLY_SUCCESS",
        "route_count": len(route),
        "topology_id": str(values[1]),
        "out_reason": _value(values[2]) if len(values) > 2 else None,
        "station_ids": [str(_read(step, "station_id")) for step in route],
    }


def _dirty_packages() -> Dict[str, List[str]]:
    if unreal is None:
        return {"content": [], "maps": []}
    utility = unreal.EditorLoadingAndSavingUtils
    return {
        "content": sorted(str(v) for v in utility.get_dirty_content_packages()),
        "maps": sorted(str(v) for v in utility.get_dirty_map_packages()),
    }


def _world_identity(world: Any) -> str:
    values: List[str] = []
    for getter in (
        lambda: world.get_outermost().get_name(),
        lambda: world.get_path_name(),
        lambda: world.get_name(),
    ):
        try:
            values.append(str(getter()))
        except Exception:
            pass
    return " | ".join(values)


def world_is_exact_target(world: Any) -> bool:
    identity = _world_identity(world)
    target_leaf = TARGET_MAP.rsplit("/", 1)[-1]
    return target_leaf in identity


def _actors(world: Any, class_name: str) -> List[Any]:
    actor_class = getattr(unreal, class_name)
    return list(unreal.GameplayStatics.get_all_actors_of_class(world, actor_class))


def _actor_identity(actor: Any) -> Dict[str, Any]:
    try:
        label = str(actor.get_actor_label())
    except Exception:
        label = str(actor.get_name())
    return {
        "label": label,
        "name": str(actor.get_name()),
        "class": str(actor.get_class().get_path_name()),
        "tags": sorted(str(tag) for tag in list(_read(actor, "tags"))),
    }


class RouteDiagnostic:
    def __init__(self, before: Mapping[str, Dict[str, Any]],
                 dirty_before_load: Mapping[str, List[str]]) -> None:
        self.before = dict(before)
        self.dirty_before_load = dict(dirty_before_load)
        self.dirty_before_pie = _dirty_packages()
        self.started_at = time.monotonic()
        self.handle: Any = None
        self.finished = False
        self.capture: Dict[str, Any] = {}
        self.level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        self.editor_worlds = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

    def finish(self, status: str, error: Optional[str] = None) -> None:
        if self.finished:
            return
        self.finished = True
        try:
            self.level_editor.editor_request_end_play()
        except Exception:
            pass
        after = {str(path): file_fingerprint(path) for path in TRACKED_FILES}
        dirty_after = _dirty_packages()
        unchanged = after == self.before
        dirty_unchanged = dirty_after == self.dirty_before_pie
        final_status = status
        if not unchanged:
            final_status = "FAIL_TRACKED_FILE_MUTATED_DURING_DIAGNOSTIC"
        elif not dirty_unchanged:
            final_status = "FAIL_DIRTY_PACKAGE_SET_CHANGED_DURING_DIAGNOSTIC"
        output = {
            "schema": "cairnwell.press_shop.route_preflight_diagnostic.v001",
            "status": final_status,
            "error": error,
            "target_map": TARGET_MAP,
            "source_receipt": str(SOURCE_RECEIPT),
            "read_only_query_contract": True,
            "runtime_mutation_api_called": False,
            "save_import_build_cook_or_package_api_called": False,
            "capture": self.capture,
            "fingerprints_before": self.before,
            "fingerprints_after": after,
            "fingerprints_unchanged": unchanged,
            "dirty_packages_before_load": self.dirty_before_load,
            "dirty_packages_before_pie": self.dirty_before_pie,
            "dirty_packages_after_pie": dirty_after,
            "dirty_package_set_unchanged_during_pie": dirty_unchanged,
            "runtime_seconds": round(time.monotonic() - self.started_at, 3),
        }
        if OUTPUT_RECEIPT.exists():
            # Append-only evidence: never replace a prior diagnostic.
            raise DiagnosticError(
                "refusing to overwrite route diagnostic: {}".format(
                    OUTPUT_RECEIPT))
        OUTPUT_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_RECEIPT.write_bytes(canonical_json_bytes(output))
        if self.handle is not None:
            try:
                unreal.unregister_slate_post_tick_callback(self.handle)
            except Exception:
                pass
            self.handle = None
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)
        unreal.SystemLibrary.quit_editor()

    def capture_once(self, world: Any) -> None:
        if not world_is_exact_target(world):
            fail("PIE started a different world: " + _world_identity(world))
        game_mode = unreal.GameplayStatics.get_game_mode(world)
        if game_mode is None:
            fail("PIE has no authoritative game mode")
        game_mode_class = str(game_mode.get_class().get_path_name())
        if game_mode_class != GAME_MODE_CLASS:
            fail("unexpected game mode: " + game_mode_class)

        authority_capture: Dict[str, Any] = {}
        invalid_layouts: List[str] = []
        authority_count_total = 0
        for spec in LAYOUT_SPECS:
            actors = _actors(world, spec["authority_class"])
            authority_count_total += len(actors)
            entry: Dict[str, Any] = {
                "count": len(actors),
                "actors": [_actor_identity(actor) for actor in actors],
            }
            if len(actors) == 1:
                actor = actors[0]
                state = actor.capture_layout()
                library = getattr(unreal, spec["library_class"])
                validation = reflected_bool_out(
                    library.validate_starter_layout(state))
                actual = _layout_snapshot(state, spec)
                canonical = _layout_snapshot(
                    library.make_canonical_starter_layout(), spec)
                differences = _diff(actual, canonical)
                entry.update({
                    "native_validation": validation,
                    "actual_state": actual,
                    "canonical_state": canonical,
                    "differences_from_canonical": differences,
                    "difference_count": len(differences),
                })
                if not validation["native_success"]:
                    invalid_layouts.append(str(spec["key"]))
            else:
                invalid_layouts.append(str(spec["key"]))
            authority_capture[str(spec["key"])] = entry

        production_actors = _actors(
            world, "LBOneFactoryProductionFlowAuthority")
        authority_count_total += len(production_actors)
        production: Dict[str, Any] = {
            "count": len(production_actors),
            "actors": [_actor_identity(actor) for actor in production_actors],
        }
        ledger_invalid = len(production_actors) != 1
        if len(production_actors) == 1:
            ledger = production_actors[0].capture_ledger()
            ledger_validation = reflected_bool_out(
                unreal.LBOneFactoryProductionFlowLibrary.validate_ledger(ledger))
            production.update({
                "native_validation": ledger_validation,
                "ledger": _ledger_snapshot(ledger),
            })
            ledger_invalid = not ledger_validation["native_success"]

        coordinators = _actors(world, "LBOneFactoryRuntimeCoordinator")
        route = {
            "native_success": False, "raw_shape": "COORDINATOR_COUNT_INVALID",
            "route_count": None, "topology_id": None, "out_reason": None,
        }
        if len(coordinators) == 1:
            route = reflected_route(
                coordinators[0].get_configured_station_route())

        if invalid_layouts:
            diagnosis = "NATIVE_STARTER_LAYOUT_VALIDATION_FAILED"
        elif ledger_invalid:
            diagnosis = "NATIVE_PRODUCTION_LEDGER_VALIDATION_FAILED"
        elif not route["native_success"]:
            diagnosis = (
                "ALL_FIVE_AUTHORITY_PREFLIGHTS_VALID__"
                "ROUTE_BUILD_FAILED_AFTER_PREFLIGHT"
            )
        else:
            diagnosis = "ROUTE_QUERY_SUCCEEDED_DURING_DIAGNOSTIC"

        self.capture = {
            "world_identity": _world_identity(world),
            "game_mode_class": game_mode_class,
            "authority_count_total": authority_count_total,
            "expected_authority_count_total": 5,
            "layout_authorities": authority_capture,
            "invalid_layouts": invalid_layouts,
            "production_authority": production,
            "ledger_invalid": ledger_invalid,
            "runtime_coordinator_count": len(coordinators),
            "runtime_coordinators": [
                _actor_identity(actor) for actor in coordinators],
            "route_query": route,
            "diagnosis": diagnosis,
        }
        self.finish("PASS_READ_ONLY_ROUTE_DIAGNOSTIC_CAPTURED")

    def tick(self, _delta_seconds: float) -> None:
        if self.finished:
            return
        try:
            world = self.editor_worlds.get_game_world()
            if world is None:
                if time.monotonic() - self.started_at > GAME_WORLD_TIMEOUT_SECONDS:
                    self.finish("FAIL_PIE_WORLD_TIMEOUT")
                return
            self.capture_once(world)
        except Exception as exc:
            self.finish("FAIL_ROUTE_DIAGNOSTIC_EXCEPTION", repr(exc))
        if time.monotonic() - self.started_at > RUN_TIMEOUT_SECONDS:
            self.finish("FAIL_ROUTE_DIAGNOSTIC_TIMEOUT")


def main() -> None:
    if unreal is None:
        fail("diagnostic must run inside Unreal Editor Python")
    if OUTPUT_RECEIPT.exists():
        fail("refusing to overwrite route diagnostic: {}".format(OUTPUT_RECEIPT))
    before = verify_tracked_files()
    dirty_before_load = _dirty_packages()
    if not unreal.EditorLoadingAndSavingUtils.load_map(TARGET_MAP):
        fail("could not load exact candidate map")
    editor_world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_editor_world()
    if editor_world is None or not world_is_exact_target(editor_world):
        fail("editor did not load the exact requested candidate map")
    diagnostic = RouteDiagnostic(before, dirty_before_load)
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    diagnostic.handle = unreal.register_slate_post_tick_callback(diagnostic.tick)
    diagnostic.level_editor.editor_play_simulate()


if __name__ == "__main__":
    main()
