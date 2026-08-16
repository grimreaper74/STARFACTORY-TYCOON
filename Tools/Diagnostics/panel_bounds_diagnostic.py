"""Standalone READ-ONLY bounds diagnostic for Cairnwell 2040 panel modules.

Deliberately self-contained: it imports no project lane module, writes nothing
inside the project, and mutates no asset. It answers one question that the
governed lane cannot answer without a full contract regeneration --

    for all 11 panels x 3 LODs, what does Unreal actually measure, and how far
    is that from the expected baseline?

Output goes to a scratch directory outside the project tree.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
BASELINE = PROJECT / "Scripts" / "cairnwell_2040_panel_modules_v001_import_baseline_v002.json"
OUT = Path(os.environ["LB_DIAG_OUT"]).resolve()

FIELDS = ("minimum_cm", "maximum_cm", "dimensions_cm", "pivot_cm")


def vector(value) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def lod_bounds(mesh, lod_index: int) -> dict | None:
    """Same extraction the lane uses: source-model LOD via GeometryScript."""
    dynamic = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    request = unreal.GeometryScriptMeshReadLOD()
    request.set_editor_properties({
        "lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL,
        "lod_index": lod_index,
    })
    dynamic, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic, options, request, False
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        return None
    box = dynamic.get_mesh_bounding_box()
    minimum, maximum = vector(box.min), vector(box.max)
    return {
        "minimum_cm": minimum,
        "maximum_cm": maximum,
        "dimensions_cm": [maximum[i] - minimum[i] for i in range(3)],
        "pivot_cm": [0.0, 0.0, 0.0],
    }


def render_lod_bounds(mesh, lod_index: int) -> dict | None:
    """Cross-check: the *rendered* LOD, which can differ from the source model."""
    dynamic = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    request = unreal.GeometryScriptMeshReadLOD()
    request.set_editor_properties({
        "lod_type": unreal.GeometryScriptLODType.RENDER_DATA,
        "lod_index": lod_index,
    })
    try:
        dynamic, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
            mesh, dynamic, options, request, False
        )
    except Exception:
        return None
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        return None
    box = dynamic.get_mesh_bounding_box()
    minimum, maximum = vector(box.min), vector(box.max)
    return {
        "minimum_cm": minimum,
        "maximum_cm": maximum,
        "dimensions_cm": [maximum[i] - minimum[i] for i in range(3)],
        "pivot_cm": [0.0, 0.0, 0.0],
    }


def compare(actual: dict, expected: dict, tolerance: float) -> dict:
    rows = {}
    worst = 0.0
    for field in FIELDS:
        deltas = [
            float(actual[field][i]) - float(expected[field][i])
            for i in range(3)
        ]
        peak = max(abs(d) for d in deltas)
        worst = max(worst, peak)
        rows[field] = {
            "actual": [round(v, 6) for v in actual[field]],
            "expected": [round(float(v), 6) for v in expected[field]],
            "delta": [round(d, 6) for d in deltas],
            "worst_abs_delta": round(peak, 6),
            "within_tolerance": peak <= tolerance,
        }
    return {
        "fields": rows,
        "worst_abs_delta": round(worst, 6),
        "within_tolerance": worst <= tolerance,
    }


def main() -> None:
    report = {
        "$schema": "lineboss/diagnostic/cairnwell-2040-panel-bounds/v1",
        "read_only": True,
        "writes_inside_project": False,
        "process_id": os.getpid(),
        "engine_version": str(unreal.SystemLibrary.get_engine_version()),
        "panels": {},
        "errors": [],
    }
    try:
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        tolerance = float(baseline["import_contract"]["bounds_tolerance_cm"])
        report["bounds_tolerance_cm"] = tolerance
        report["baseline_file"] = str(BASELINE)

        library = unreal.EditorAssetLibrary
        summary_lines = []

        for panel_id, spec in baseline["modules"].items():
            entry = {"package_path": spec["package_path"], "lods": {}}
            mesh = library.load_asset(spec["package_path"])
            if not isinstance(mesh, unreal.StaticMesh):
                entry["error"] = "not a StaticMesh / failed to load"
                report["panels"][panel_id] = entry
                continue

            entry["num_lods"] = int(mesh.get_num_lods())

            for lod_index, expected_lod in enumerate(spec["lods"]):
                expected = expected_lod["expected_unreal_bounds"]
                actual = lod_bounds(mesh, lod_index)
                row = {
                    "triangles_actual": int(mesh.get_num_triangles(lod_index)),
                    "triangles_expected": int(expected_lod["triangles"]),
                    "vertices_actual": int(mesh.get_num_vertices(lod_index)),
                }
                if actual is None:
                    row["error"] = "source-model bounds extraction failed"
                else:
                    row["source_model"] = compare(actual, expected, tolerance)

                render = render_lod_bounds(mesh, lod_index)
                if render is not None:
                    row["render_data"] = compare(render, expected, tolerance)

                entry["lods"][f"LOD{lod_index}"] = row

                if actual is not None:
                    sm = row["source_model"]
                    flag = "OK  " if sm["within_tolerance"] else "FAIL"
                    summary_lines.append(
                        f"{flag} {panel_id}:LOD{lod_index} "
                        f"worst_delta={sm['worst_abs_delta']:.6f}cm"
                    )

            report["panels"][panel_id] = entry

        report["summary"] = summary_lines
        failing = [line for line in summary_lines if line.startswith("FAIL")]
        report["failing_count"] = len(failing)
        report["total_checked"] = len(summary_lines)
        report["status"] = "CLEAN" if not failing else "DRIFT_DETECTED"

    except Exception as error:  # noqa: BLE001 - diagnostic must always report
        report["status"] = "DIAGNOSTIC_ERROR"
        report["errors"].append({
            "error": str(error),
            "traceback": traceback.format_exc(),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    unreal.log("LB_PANEL_BOUNDS_DIAGNOSTIC_STATUS: " + str(report.get("status")))
    for line in report.get("summary", []):
        unreal.log("LB_PANEL_BOUNDS_DIAGNOSTIC_ROW: " + line)
    for item in report["errors"]:
        unreal.log_error("LB_PANEL_BOUNDS_DIAGNOSTIC_ERROR: " + item["error"])


if __name__ == "__main__":
    main()
