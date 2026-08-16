"""Analyze Body Shop CSV/primitive captures against provisional 1080p budgets.

The parser is deliberately fail-closed: a missing timing/memory column, a
missing target component, an invalid renderer LOD, or an ambiguous primitive
dump is a validation failure rather than an omitted metric.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys
from typing import Iterable


EXPECTED_TARGET_COMPONENT_COUNT = 22
EXPECTED_UNIQUE_MESH_COUNT = 9
EXPECTED_LOD_METADATA_SOURCE = "editor_static_mesh_snapshot_pre_pie"


BUDGETS = {
    "basis": "Provisional Windows desktop Development PIE gate at an exact 1920x1080 viewport; not a Shipping-platform commitment.",
    "timing_ms_p95": {
        "frame_time": 33.333,
        "game_thread": 20.0,
        "render_thread": 25.0,
        "gpu": 33.333,
    },
    "frame_time_ms_p99": 50.0,
    "hitch_ratio_over_50ms_max": 0.02,
    "scene_per_view_max": {
        "visible_primitives": 2000,
        "draw_calls": 2500,
        "triangles": 4_000_000,
    },
    "rhi_submitted_p95_max": {
        "draw_calls": 2500,
        "primitives_drawn": 4_000_000,
    },
    "memory": {
        "physical_used_mb_p95_max": 12_288.0,
        "physical_free_mb_p05_min": 512.0,
        "gpu_local_used_to_budget_p95_max": 0.90,
    },
    "texture_streaming": {
        "required_pool_mb_p95_max": 1536.0,
        "desired_data_loaded_percent_p05_min": 95.0,
        "pending_stream_in_mb_p95_max": 32.0,
    },
    "minimum_capture_frames": 240,
    "discard_leading_frames": 30,
    "discard_trailing_frames": 10,
    "minimum_finite_sample_fraction": 0.80,
}


class GateFailure(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normalise_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def as_float(value: str):
    try:
        parsed = float(value.strip())
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def percentile(values: Iterable[float], percent: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise GateFailure("Cannot calculate a percentile from an empty sample")
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * percent
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def summarise(values: list[float]) -> dict:
    return {
        "samples": len(values),
        "mean": round(statistics.fmean(values), 4),
        "p05": round(percentile(values, 0.05), 4),
        "p50": round(percentile(values, 0.50), 4),
        "p95": round(percentile(values, 0.95), 4),
        "p99": round(percentile(values, 0.99), 4),
        "max": round(max(values), 4),
    }


def read_profile(path: Path) -> tuple[list[str], list[list[str]]]:
    if not path.is_file() or path.stat().st_size < 4096:
        raise GateFailure(f"CSV profile is missing or too small: {path}")
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        rows = list(csv.reader(handle))
    # UE 5.8's streaming CSV writer deliberately puts its summary header at the
    # end (metadata HasHeaderRowAtEnd=1), because stat columns can be discovered
    # while the capture is running.  Keep header-first support for synthetic and
    # older captures, but prefer the authoritative trailing EVENTS row.
    header_index = None
    header_at_end = False
    for index in range(len(rows) - 1, -1, -1):
        row = rows[index]
        if (row and row[0].strip().upper() == "EVENTS"
                and any("frametime" in normalise_header(cell) for cell in row)):
            header_index = index
            header_at_end = True
            break
    if header_index is None:
        for index, row in enumerate(rows[:20]):
            if any("frametime" in normalise_header(cell) for cell in row):
                header_index = index
                break
    if header_index is None:
        raise GateFailure(f"CSV profile has no FrameTime header: {path}")
    headers = [cell.strip() for cell in rows[header_index]]
    data = []
    candidates = rows[:header_index] if header_at_end else rows[header_index + 1:]
    for row in candidates:
        if not header_at_end and row and row[0].strip().startswith("["):
            break
        numeric = sum(as_float(cell) is not None for cell in row[:len(headers)])
        if numeric >= 3:
            data.append(row + [""] * max(0, len(headers) - len(row)))
    if len(data) < BUDGETS["minimum_capture_frames"]:
        raise GateFailure(f"CSV profile contains only {len(data)} numeric frames: {path}")
    return headers, data


def choose_column(headers: list[str], metric: str) -> tuple[int, str]:
    normalised = [normalise_header(header) for header in headers]
    exact = {
        "frame_time": {"frametime", "globalframetime"},
        "game_thread": {"gamethread", "gamethreadtime", "gamethreadgamethread"},
        "render_thread": {"renderthread", "renderthreadtime", "renderthreadrenderthread"},
        "gpu": {"gpu", "gputime", "gpuframetime", "gpugpuframetime", "gpugpu"},
        "physical_used_mb": {"physicalusedmb", "globalphysicalusedmb"},
        "physical_free_mb": {"memoryfreemb", "globalmemoryfreemb"},
        "texture_pool_mb": {"texturestreamingstreamingpool", "streamingpool"},
        "desired_loaded_percent": {"texturestreamingdesireddataloadedpercent", "desireddataloadedpercent"},
        "pending_stream_in_mb": {"texturestreamingpendingstreamindata", "pendingstreamindata"},
        "gpu_local_used_mb": {"gpumemlocalusedmb", "localusedmb"},
        "gpu_local_budget_mb": {"gpumemlocalbudgetmb", "localbudgetmb"},
        "rhi_draw_calls": {"rhidrawcalls"},
        "rhi_primitives_drawn": {"rhiprimitivesdrawn"},
    }[metric]
    for index, value in enumerate(normalised):
        if value in exact:
            return index, headers[index]

    def fallback(value: str) -> bool:
        if metric == "frame_time":
            return value.endswith("frametime") and not any(token in value for token in ("gpu", "game", "render", "rhi"))
        if metric == "game_thread":
            return value.endswith("gamethread") or value.endswith("gamethreadtime")
        if metric == "render_thread":
            return value.endswith("renderthread") or value.endswith("renderthreadtime")
        if metric == "gpu":
            return value.endswith("gpuframetime") or value.endswith("gputime")
        tokens = {
            "physical_used_mb": ("physicalusedmb",),
            "physical_free_mb": ("memoryfreemb",),
            "texture_pool_mb": ("texturestreaming", "streamingpool"),
            "desired_loaded_percent": ("desireddataloadedpercent",),
            "pending_stream_in_mb": ("pendingstreamindata",),
            "gpu_local_used_mb": ("gpumem", "localusedmb"),
            "gpu_local_budget_mb": ("gpumem", "localbudgetmb"),
            "rhi_draw_calls": ("rhi", "drawcalls"),
            "rhi_primitives_drawn": ("rhi", "primitivesdrawn"),
        }[metric]
        return all(token in value for token in tokens)

    matches = [(index, headers[index]) for index, value in enumerate(normalised) if fallback(value)]
    if len(matches) != 1:
        raise GateFailure(
            f"Required CSV metric {metric!r} resolved to {len(matches)} columns; "
            f"available headers={headers}"
        )
    return matches[0]


def profile_metrics(path: Path) -> tuple[dict, list[str]]:
    headers, rows = read_profile(path)
    begin = BUDGETS["discard_leading_frames"]
    end = len(rows) - BUDGETS["discard_trailing_frames"]
    usable = rows[begin:end]
    if len(usable) < 180:
        raise GateFailure(f"Only {len(usable)} settled frames remain after trimming: {path}")
    metrics = {}
    resolved = {}
    required = [
        "frame_time", "game_thread", "render_thread", "gpu",
        "physical_used_mb", "physical_free_mb", "texture_pool_mb",
        "desired_loaded_percent", "pending_stream_in_mb",
        "gpu_local_used_mb", "gpu_local_budget_mb",
        "rhi_draw_calls", "rhi_primitives_drawn",
    ]
    for metric in required:
        index, header = choose_column(headers, metric)
        values = [value for row in usable if (value := as_float(row[index])) is not None and value >= 0.0]
        minimum = math.ceil(len(usable) * BUDGETS["minimum_finite_sample_fraction"])
        # GPU-memory counters may update sparsely but must still provide multiple
        # positive hardware samples; zero-only columns are not evidence.
        if metric.startswith("gpu_local_"):
            values = [value for value in values if value > 0.0]
            minimum = 3
        if len(values) < minimum:
            raise GateFailure(
                f"Metric {metric} has {len(values)} usable values; at least {minimum} required in {path}"
            )
        metrics[metric] = summarise(values)
        metrics[metric]["source_header"] = header
        metrics[metric]["values"] = values
        resolved[metric] = header

    frame_values = metrics["frame_time"]["values"]
    metrics["frame_time"]["hitch_frames_over_50ms"] = sum(value > 50.0 for value in frame_values)
    metrics["frame_time"]["hitch_ratio_over_50ms"] = round(
        metrics["frame_time"]["hitch_frames_over_50ms"] / len(frame_values), 6)

    # Pair local-used and local-budget by their own robust percentiles.  This is
    # conservative when samples are not emitted on exactly the same frames.
    used_p95 = metrics["gpu_local_used_mb"]["p95"]
    budget_p05 = metrics["gpu_local_budget_mb"]["p05"]
    if budget_p05 <= 0.0:
        raise GateFailure("GPU local-memory budget is zero")
    metrics["gpu_local_utilisation"] = {
        "used_mb_p95": used_p95,
        "budget_mb_p05": budget_p05,
        "ratio": round(used_p95 / budget_p05, 6),
    }
    for value in metrics.values():
        if isinstance(value, dict):
            value.pop("values", None)
    return {
        "profile_path": str(path),
        "profile_sha256": sha256(path),
        "captured_frames": len(rows),
        "settled_frames": len(usable),
        "resolved_headers": resolved,
        "metrics": metrics,
    }, headers


def read_primitives(path: Path) -> list[dict]:
    if not path.is_file() or path.stat().st_size < 128:
        raise GateFailure(f"Primitive CSV is missing or too small: {path}")
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        required = {"Name", "ActorClass", "Actor", "NumDraws", "LOD", "Triangles"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise GateFailure(f"Primitive CSV schema drifted: {path}; headers={reader.fieldnames}")
        return [{str(key): str(value or "") for key, value in row.items()} for row in reader]


def integer_field(row: dict, field: str) -> int:
    try:
        return int(row[field].strip())
    except (KeyError, TypeError, ValueError) as exc:
        raise GateFailure(f"Primitive row has invalid {field}: {row}") from exc


def primitive_candidate_match(rows: list[dict], targets: list[dict]) -> tuple[bool, str]:
    for target in targets:
        matches = [row for row in rows
                   if row.get("Actor") == target["actor_full_name"]
                   and row.get("Name") == target["component_name"]]
        if len(matches) != 1:
            return False, f"{target['key']} matched {len(matches)} rows"
    return True, f"all {len(targets)} target components matched exactly once"


def validate_editor_lod_snapshot(raw: dict, targets: list[dict]) -> dict:
    """Validate pre-PIE asset metadata and bind it to every runtime target."""
    snapshot = raw.get("editor_lod_metadata_snapshot")
    if not isinstance(snapshot, dict):
        raise GateFailure("Raw capture is missing the pre-PIE editor LOD metadata snapshot")
    if snapshot.get("phase") != "pre_pie" or snapshot.get("source") != "live_editor_assets":
        raise GateFailure("Editor LOD metadata was not captured from live assets before PIE")
    meshes = snapshot.get("meshes")
    if not isinstance(meshes, dict) or len(meshes) != EXPECTED_UNIQUE_MESH_COUNT:
        raise GateFailure(
            f"Pre-PIE editor LOD snapshot does not contain exactly {EXPECTED_UNIQUE_MESH_COUNT} meshes"
        )
    if int(snapshot.get("mesh_count", -1)) != len(meshes):
        raise GateFailure("Pre-PIE editor LOD snapshot mesh count is internally inconsistent")
    target_paths = {target.get("mesh_path") for target in targets}
    if target_paths != set(meshes):
        raise GateFailure("Runtime target mesh family does not match the pre-PIE editor LOD snapshot")

    for mesh_path, metadata in meshes.items():
        if not isinstance(metadata, dict) or metadata.get("object_path") != mesh_path:
            raise GateFailure(f"Pre-PIE editor LOD snapshot identity drifted: {mesh_path}")
        lod_count = int(metadata.get("lod_count", 0))
        screen_sizes = metadata.get("lod_screen_sizes")
        triangles = metadata.get("lod_triangles")
        vertices = metadata.get("lod_vertices")
        if lod_count < 1:
            raise GateFailure(f"Pre-PIE editor snapshot reports no LODs: {mesh_path}")
        if not all(isinstance(values, list) and len(values) == lod_count
                   for values in (screen_sizes, triangles, vertices)):
            raise GateFailure(f"Pre-PIE editor LOD arrays are incomplete: {mesh_path}")
        if any(int(value) <= 0 for value in triangles + vertices):
            raise GateFailure(f"Pre-PIE editor snapshot contains an empty LOD: {mesh_path}")
        asset_file = Path(str(metadata.get("source_asset_file", "")))
        asset_sha = str(metadata.get("source_asset_sha256", ""))
        if not asset_file.is_file() or not re.fullmatch(r"[0-9A-F]{64}", asset_sha):
            raise GateFailure(f"Pinned authored-mesh package evidence is invalid: {mesh_path}")
        if asset_file.stat().st_size != int(metadata.get("source_asset_bytes", -1)):
            raise GateFailure(f"Pinned authored-mesh package length drifted: {asset_file}")
        if sha256(asset_file) != asset_sha:
            raise GateFailure(f"Pinned authored-mesh package hash drifted: {asset_file}")

    for target in targets:
        mesh_path = target["mesh_path"]
        metadata = meshes[mesh_path]
        if target.get("lod_metadata_source") != EXPECTED_LOD_METADATA_SOURCE:
            raise GateFailure(f"Target LOD metadata was not sourced before PIE: {target.get('key')}")
        for key in ("lod_count", "lod_screen_sizes", "lod_triangles", "lod_vertices",
                    "source_asset_sha256"):
            if target.get(key) != metadata.get(key):
                raise GateFailure(f"Target pre-PIE LOD metadata binding drifted: {target.get('key')}::{key}")
    return snapshot


def analyse_primitives(view: dict, targets: list[dict]) -> dict:
    candidates = []
    for candidate in view.get("primitive_csv_candidates", []):
        path = Path(candidate["retained"])
        if sha256(path) != candidate["sha256"]:
            raise GateFailure(f"Retained primitive CSV hash drifted: {path}")
        rows = read_primitives(path)
        matched, detail = primitive_candidate_match(rows, targets)
        candidates.append({"path": path, "rows": rows, "matched": matched, "detail": detail})
    matching = [candidate for candidate in candidates if candidate["matched"]]
    if len(matching) != 1:
        raise GateFailure(
            f"View {view['id']} has {len(matching)} unambiguous renderer primitive dumps; "
            + "; ".join(f"{item['path'].name}: {item['detail']}" for item in candidates)
        )
    selected = matching[0]
    rows = selected["rows"]
    component_rows = []
    by_mesh = {}
    for target in targets:
        row = next(row for row in rows
                   if row.get("Actor") == target["actor_full_name"]
                   and row.get("Name") == target["component_name"])
        lod = integer_field(row, "LOD")
        draws = integer_field(row, "NumDraws")
        triangles = integer_field(row, "Triangles")
        if target["forced_lod_model"] != 0:
            raise GateFailure(f"Target {target['key']} was not in automatic LOD mode")
        if lod < 0 or lod >= int(target["lod_count"]):
            raise GateFailure(
                f"Renderer selected invalid LOD {lod} for {target['key']} with {target['lod_count']} LODs"
            )
        if draws <= 0 or triangles <= 0:
            raise GateFailure(
                f"Renderer target {target['key']} has non-positive draws/triangles ({draws}/{triangles})"
            )
        evidence = {
            "key": target["key"],
            "category": target["category"],
            "actor": target["actor_full_name"],
            "component": target["component_name"],
            "mesh_path": target["mesh_path"],
            "available_lods": target["lod_count"],
            "screen_sizes": target["lod_screen_sizes"],
            "automatic_lod": True,
            "renderer_selected_lod": lod,
            "renderer_draws": draws,
            "renderer_triangles": triangles,
        }
        component_rows.append(evidence)
        by_mesh.setdefault(target["mesh_path"], []).append({
            "target": target["key"], "lod": lod, "draws": draws, "triangles": triangles,
        })

    numeric_rows = []
    for row in rows:
        try:
            numeric_rows.append({
                "draws": max(0, integer_field(row, "NumDraws")),
                "triangles": max(0, integer_field(row, "Triangles")),
            })
        except GateFailure:
            continue
    if not numeric_rows:
        raise GateFailure(f"Primitive dump contains no numeric scene rows: {selected['path']}")
    scene = {
        "visible_primitives": len(numeric_rows),
        "draw_calls": sum(row["draws"] for row in numeric_rows),
        "triangles": sum(row["triangles"] for row in numeric_rows),
    }
    return {
        "selected_dump": str(selected["path"]),
        "selected_dump_sha256": sha256(selected["path"]),
        "candidate_count": len(candidates),
        "scene_totals": scene,
        "target_component_lods": component_rows,
        "selected_lods_by_mesh": [
            {"mesh_path": mesh, "instances": instances}
            for mesh, instances in sorted(by_mesh.items())
        ],
    }


def budget_check(name: str, actual: float, limit: float, comparison: str, failures: list[str]) -> dict:
    passed = actual <= limit if comparison == "max" else actual >= limit
    if not passed:
        operator = "<=" if comparison == "max" else ">="
        failures.append(f"{name} {actual:.4f} does not satisfy {operator} {limit:.4f}")
    return {"passed": passed, "actual": actual, "limit": limit, "comparison": comparison}


def evaluate_budgets(view_id: str, performance: dict, primitives: dict, failures: list[str]) -> dict:
    metrics = performance["metrics"]
    checks = {}
    for metric, limit in BUDGETS["timing_ms_p95"].items():
        checks[f"{metric}_p95"] = budget_check(
            f"{view_id}.{metric}.p95", metrics[metric]["p95"], limit, "max", failures)
    checks["frame_time_p99"] = budget_check(
        f"{view_id}.frame_time.p99", metrics["frame_time"]["p99"],
        BUDGETS["frame_time_ms_p99"], "max", failures)
    checks["hitch_ratio"] = budget_check(
        f"{view_id}.frame_time.hitch_ratio", metrics["frame_time"]["hitch_ratio_over_50ms"],
        BUDGETS["hitch_ratio_over_50ms_max"], "max", failures)
    checks["physical_used_mb_p95"] = budget_check(
        f"{view_id}.physical_used_mb.p95", metrics["physical_used_mb"]["p95"],
        BUDGETS["memory"]["physical_used_mb_p95_max"], "max", failures)
    checks["physical_free_mb_p05"] = budget_check(
        f"{view_id}.physical_free_mb.p05", metrics["physical_free_mb"]["p05"],
        BUDGETS["memory"]["physical_free_mb_p05_min"], "min", failures)
    checks["gpu_local_utilisation"] = budget_check(
        f"{view_id}.gpu_local_utilisation", metrics["gpu_local_utilisation"]["ratio"],
        BUDGETS["memory"]["gpu_local_used_to_budget_p95_max"], "max", failures)
    checks["texture_pool_mb_p95"] = budget_check(
        f"{view_id}.texture_pool_mb.p95", metrics["texture_pool_mb"]["p95"],
        BUDGETS["texture_streaming"]["required_pool_mb_p95_max"], "max", failures)
    checks["desired_loaded_percent_p05"] = budget_check(
        f"{view_id}.desired_loaded_percent.p05", metrics["desired_loaded_percent"]["p05"],
        BUDGETS["texture_streaming"]["desired_data_loaded_percent_p05_min"], "min", failures)
    checks["pending_stream_in_mb_p95"] = budget_check(
        f"{view_id}.pending_stream_in_mb.p95", metrics["pending_stream_in_mb"]["p95"],
        BUDGETS["texture_streaming"]["pending_stream_in_mb_p95_max"], "max", failures)
    for metric, limit in BUDGETS["scene_per_view_max"].items():
        checks[f"scene_{metric}"] = budget_check(
            f"{view_id}.scene.{metric}", primitives["scene_totals"][metric], limit, "max", failures)
    checks["rhi_draw_calls_p95"] = budget_check(
        f"{view_id}.rhi.draw_calls.p95", metrics["rhi_draw_calls"]["p95"],
        BUDGETS["rhi_submitted_p95_max"]["draw_calls"], "max", failures)
    checks["rhi_primitives_drawn_p95"] = budget_check(
        f"{view_id}.rhi.primitives_drawn.p95", metrics["rhi_primitives_drawn"]["p95"],
        BUDGETS["rhi_submitted_p95_max"]["primitives_drawn"], "max", failures)
    return checks


def analyse(raw_capture: Path, output: Path) -> dict:
    payload = {
        "$schema": "cairnwell/body-shop/experimental-v001/performance-lod-release-gate/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "IN_PROGRESS",
        "raw_capture_receipt": str(raw_capture),
        "raw_capture_sha256": None,
        "budgets": BUDGETS,
        "views": {},
        "checks": {},
        "failures": [],
        "engine_api_limitations": [],
    }
    try:
        if not raw_capture.is_file():
            raise GateFailure(f"Raw capture receipt is missing: {raw_capture}")
        payload["raw_capture_sha256"] = sha256(raw_capture)
        raw = json.loads(raw_capture.read_text(encoding="utf-8-sig"))
        if raw.get("status") != "PASS__BODY_SHOP_PERFORMANCE_LOD_RAW_CAPTURE_V001":
            raise GateFailure(f"Raw capture is not PASS: {raw.get('status')}")
        if not raw.get("map_hash_unchanged"):
            raise GateFailure("Raw capture did not preserve the Body Shop map hash")
        if raw.get("target_summary", {}).get("component_count") != EXPECTED_TARGET_COMPONENT_COUNT:
            raise GateFailure(
                f"Raw capture does not bind exactly {EXPECTED_TARGET_COMPONENT_COUNT} target components"
            )
        if raw.get("target_summary", {}).get("unique_mesh_count") != EXPECTED_UNIQUE_MESH_COUNT:
            raise GateFailure(
                f"Raw capture does not bind exactly {EXPECTED_UNIQUE_MESH_COUNT} robot/tool/vision meshes"
            )
        targets = raw["target_components"]
        if len(targets) != EXPECTED_TARGET_COMPONENT_COUNT:
            raise GateFailure("Raw target-component array length drifted")
        if any(int(target.get("forced_lod_model", -1)) != 0 for target in targets):
            raise GateFailure("One or more target components forced an LOD")
        payload["editor_lod_metadata_snapshot"] = validate_editor_lod_snapshot(raw, targets)
        payload["capture_contract"] = raw["capture_contract"]
        payload["target_summary"] = raw["target_summary"]
        payload["engine_api_limitations"] = raw.get("engine_api_notes", [])

        for view_id in ("management", "focus"):
            view = raw.get("views", {}).get(view_id)
            if not view:
                raise GateFailure(f"Missing raw view capture: {view_id}")
            profile = Path(view["raw_csv"]["retained"])
            if sha256(profile) != view["raw_csv"]["sha256"]:
                raise GateFailure(f"Retained performance CSV hash drifted: {profile}")
            performance, _headers = profile_metrics(profile)
            primitives = analyse_primitives(view, targets)
            budget_checks = evaluate_budgets(view_id, performance, primitives, payload["failures"])
            payload["views"][view_id] = {
                "camera": {key: value for key, value in view.items()
                           if key not in ("raw_csv", "primitive_csv_candidates")},
                "performance": performance,
                "renderer_primitives_and_lods": primitives,
                "budget_checks": budget_checks,
            }

        management_camera = payload["views"]["management"]["camera"]
        focus_camera = payload["views"]["focus"]["camera"]
        distinct_cameras = (
            management_camera.get("viewport") == [1920, 1080]
            and focus_camera.get("viewport") == [1920, 1080]
            and float(management_camera.get("zoom_distance_cm", 0.0))
                >= float(focus_camera.get("zoom_distance_cm", 0.0)) + 1500.0
        )
        payload["checks"]["representative_management_and_focus_cameras"] = {
            "passed": distinct_cameras,
            "management_zoom_distance_cm": management_camera.get("zoom_distance_cm"),
            "focus_zoom_distance_cm": focus_camera.get("zoom_distance_cm"),
            "viewport": management_camera.get("viewport"),
        }
        if not distinct_cameras:
            payload["failures"].append(
                "Management/focus cameras are not distinct 1920x1080 representative views"
            )

        for view_id, view in payload["views"].items():
            lod_rows = view["renderer_primitives_and_lods"]["target_component_lods"]
            payload["checks"][f"{view_id}_all_target_lods_proven"] = {
                "passed": len(lod_rows) == EXPECTED_TARGET_COMPONENT_COUNT
                          and all(row["renderer_selected_lod"] >= 0 for row in lod_rows),
                "component_count": len(lod_rows),
                "unique_mesh_count": len({row["mesh_path"] for row in lod_rows}),
            }
        if not all(check["passed"] for check in payload["checks"].values()):
            payload["failures"].append("A representative-camera or renderer-selected LOD proof is incomplete")
        payload["status"] = (
            "PASS__BODY_SHOP_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_GATE_V001"
            if not payload["failures"]
            else "FAIL__BODY_SHOP_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_GATE_V001"
        )
    except Exception as exc:
        payload["failures"].append(str(exc))
        payload["status"] = "FAIL__BODY_SHOP_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_GATE_V001"
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-capture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = analyse(args.raw_capture.resolve(), args.output.resolve())
    print(result["status"])
    for failure in result["failures"]:
        print("FAIL:", failure)
    return 0 if result["status"].startswith("PASS__") else 2


if __name__ == "__main__":
    sys.exit(main())
