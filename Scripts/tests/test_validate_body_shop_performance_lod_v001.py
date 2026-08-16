from __future__ import annotations

import csv
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import analyze_body_shop_performance_lod_v001 as gate


PROFILE_HEADERS = [
    "FrameTime", "GameThread", "RenderThread", "GPU",
    "PhysicalUsedMB", "MemoryFreeMB",
    "TextureStreaming/StreamingPool",
    "TextureStreaming/DesiredDataLoadedPercent",
    "TextureStreaming/PendingStreamInData",
    "GPUMem/LocalUsedMB", "GPUMem/LocalBudgetMB",
    "RHI/DrawCalls", "RHI/PrimitivesDrawn",
]


class BodyShopPerformanceLodAnalyzerTests(unittest.TestCase):
    def write_profile(self, path: Path, headers=None):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            for _index in range(260):
                writer.writerow(["", 16.0, 4.0, 6.0, 9.0, 4096.0, 8192.0,
                                 512.0, 100.0, 0.0, 2048.0, 8192.0, 500.0, 750000.0])
            writer.writerow(["EVENTS", *(headers or PROFILE_HEADERS)])
            writer.writerow(["HasHeaderRowAtEnd", "1"])

    def make_targets_and_csv(self, path: Path, invalid_lod=False):
        targets = []
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "Name", "ActorClass", "Actor", "Location", "NumMaterials",
                "Materials", "NumDraws", "LOD", "Triangles",
            ])
            writer.writeheader()
            for index in range(gate.EXPECTED_TARGET_COMPONENT_COUNT):
                actor = f"LBBodyShopRobotActor /Memory/Test_{index}"
                component = f"Presentation_{index}"
                targets.append({
                    "key": f"TARGET_{index}:{component}",
                    "category": "robot_link",
                    "identity": f"TARGET_{index}",
                    "actor_full_name": actor,
                    "actor_name": f"Test_{index}",
                    "component_name": component,
                    "mesh_path": f"/Game/Test/Mesh_{index % gate.EXPECTED_UNIQUE_MESH_COUNT}.Mesh_{index % gate.EXPECTED_UNIQUE_MESH_COUNT}",
                    "lod_count": 3,
                    "lod_screen_sizes": [1.0, 0.55, 0.25],
                    "lod_triangles": [300, 150, 75],
                    "lod_vertices": [600, 300, 150],
                    "lod_metadata_source": gate.EXPECTED_LOD_METADATA_SOURCE,
                    "source_asset_sha256": None,
                    "forced_lod_model": 0,
                })
                writer.writerow({
                    "Name": component,
                    "ActorClass": "LBBodyShopRobotActor",
                    "Actor": actor,
                    "Location": "{X=0 Y=0 Z=0}",
                    "NumMaterials": "1",
                    "Materials": "[M_Test]",
                    "NumDraws": "1",
                    "LOD": "3" if invalid_lod and index == 7 else "1",
                    "Triangles": "100",
                })
        return targets

    def make_editor_lod_snapshot(self, root: Path, targets: list[dict]):
        meshes = {}
        for mesh_path in sorted({target["mesh_path"] for target in targets}):
            asset_file = root / (mesh_path.rsplit("/", 1)[-1].split(".", 1)[0] + ".uasset")
            asset_file.write_bytes((mesh_path + "\n").encode("utf-8"))
            digest = hashlib.sha256(asset_file.read_bytes()).hexdigest().upper()
            meshes[mesh_path] = {
                "object_path": mesh_path,
                "lod_count": 3,
                "lod_screen_sizes": [1.0, 0.55, 0.25],
                "lod_triangles": [300, 150, 75],
                "lod_vertices": [600, 300, 150],
                "source_asset_file": str(asset_file),
                "source_asset_bytes": asset_file.stat().st_size,
                "source_asset_sha256": digest,
            }
        for target in targets:
            target["source_asset_sha256"] = meshes[target["mesh_path"]]["source_asset_sha256"]
        return {
            "phase": "pre_pie",
            "source": "live_editor_assets",
            "api": "test fixture",
            "mesh_count": len(meshes),
            "meshes": meshes,
        }

    def test_profile_parser_requires_and_summarises_numeric_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.csv"
            self.write_profile(path)
            result, _headers = gate.profile_metrics(path)
            self.assertEqual(result["captured_frames"], 260)
            self.assertEqual(result["metrics"]["frame_time"]["p95"], 16.0)
            self.assertEqual(result["metrics"]["gpu_local_utilisation"]["ratio"], 0.25)

    def test_profile_parser_fails_closed_when_gpu_timing_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.csv"
            headers = PROFILE_HEADERS.copy()
            headers[3] = "UnrelatedCounter"
            self.write_profile(path, headers)
            with self.assertRaises(gate.GateFailure):
                gate.profile_metrics(path)

    def test_renderer_lod_evidence_requires_every_target_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "primitives.csv"
            targets = self.make_targets_and_csv(path)
            view = {
                "id": "management",
                "primitive_csv_candidates": [{"retained": str(path), "sha256": gate.sha256(path)}],
            }
            result = gate.analyse_primitives(view, targets)
            self.assertEqual(len(result["target_component_lods"]), gate.EXPECTED_TARGET_COMPONENT_COUNT)
            self.assertTrue(all(row["renderer_selected_lod"] == 1
                                for row in result["target_component_lods"]))

            targets.pop()
            targets.append({**targets[-1], "key": "MISSING:Presentation",
                            "actor_full_name": "Missing Actor", "component_name": "Missing"})
            with self.assertRaises(gate.GateFailure):
                gate.analyse_primitives(view, targets)

    def test_renderer_lod_outside_available_range_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "primitives.csv"
            targets = self.make_targets_and_csv(path, invalid_lod=True)
            view = {
                "id": "focus",
                "primitive_csv_candidates": [{"retained": str(path), "sha256": gate.sha256(path)}],
            }
            with self.assertRaises(gate.GateFailure):
                gate.analyse_primitives(view, targets)

    def test_complete_synthetic_gate_passes_both_distinct_views(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            management_profile = root / "management_performance.csv"
            focus_profile = root / "focus_performance.csv"
            management_primitives = root / "management_primitives.csv"
            focus_primitives = root / "focus_primitives.csv"
            self.write_profile(management_profile)
            self.write_profile(focus_profile)
            targets = self.make_targets_and_csv(management_primitives)
            self.make_targets_and_csv(focus_primitives)
            editor_snapshot = self.make_editor_lod_snapshot(root, targets)

            def view(view_id, zoom, profile, primitives):
                return {
                    "id": view_id,
                    "viewport": [1920, 1080],
                    "zoom_distance_cm": zoom,
                    "raw_csv": {"retained": str(profile), "sha256": gate.sha256(profile)},
                    "primitive_csv_candidates": [{
                        "retained": str(primitives), "sha256": gate.sha256(primitives),
                    }],
                }

            raw = root / "raw.json"
            raw.write_text(json.dumps({
                "status": "PASS__BODY_SHOP_PERFORMANCE_LOD_RAW_CAPTURE_V001",
                "map_hash_unchanged": True,
                "capture_contract": {"resolution": [1920, 1080]},
                "target_summary": {
                    "component_count": gate.EXPECTED_TARGET_COMPONENT_COUNT,
                    "unique_mesh_count": gate.EXPECTED_UNIQUE_MESH_COUNT,
                    "unique_mesh_paths": sorted({target["mesh_path"] for target in targets}),
                },
                "target_components": targets,
                "editor_lod_metadata_snapshot": editor_snapshot,
                "engine_api_notes": [],
                "views": {
                    "management": view("management", 6100.0, management_profile, management_primitives),
                    "focus": view("focus", 4000.0, focus_profile, focus_primitives),
                },
            }), encoding="utf-8")
            result = gate.analyse(raw, root / "gate.json")
            self.assertEqual(
                result["status"],
                "PASS__BODY_SHOP_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_GATE_V001",
            )
            self.assertFalse(result["failures"])

    def test_gate_fails_closed_without_pre_pie_editor_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            targets = self.make_targets_and_csv(root / "targets.csv")
            raw = root / "raw.json"
            raw.write_text(json.dumps({
                "status": "PASS__BODY_SHOP_PERFORMANCE_LOD_RAW_CAPTURE_V001",
                "map_hash_unchanged": True,
                "target_summary": {
                    "component_count": gate.EXPECTED_TARGET_COMPONENT_COUNT,
                    "unique_mesh_count": gate.EXPECTED_UNIQUE_MESH_COUNT,
                },
                "target_components": targets,
            }), encoding="utf-8")
            result = gate.analyse(raw, root / "gate.json")
            self.assertEqual(
                result["status"],
                "FAIL__BODY_SHOP_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_GATE_V001",
            )
            self.assertTrue(any("missing the pre-PIE" in failure for failure in result["failures"]))

    def test_pre_pie_snapshot_fails_closed_when_pinned_package_hash_drifts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            targets = self.make_targets_and_csv(root / "targets.csv")
            snapshot = self.make_editor_lod_snapshot(root, targets)
            first = next(iter(snapshot["meshes"].values()))
            Path(first["source_asset_file"]).write_bytes(b"DRIFT")
            with self.assertRaises(gate.GateFailure):
                gate.validate_editor_lod_snapshot(
                    {"editor_lod_metadata_snapshot": snapshot}, targets
                )

    def test_capture_snapshots_editor_lod_metadata_before_pie(self):
        capture = SCRIPTS / "validate_body_shop_performance_lod_pie_v001.py"
        source = capture.read_text(encoding="utf-8")
        ast.parse(source)
        snapshot_call = source.rindex("EDITOR_LOD_METADATA = snapshot_editor_lod_metadata()")
        begin_play = source.rindex("request_new_window_pie()")
        self.assertLess(snapshot_call, begin_play)
        self.assertNotIn("LEVELS.editor_request_begin_play()", source)
        component_start = source.index("def component_record(")
        component_end = source.index("\ndef build_target_manifest", component_start)
        component_source = source[component_start:component_end]
        self.assertNotIn("STATIC_MESHES.get_lod_count", component_source)
        self.assertIn("EDITOR_LOD_METADATA.get(mesh_path)", component_source)

    def test_capture_and_runner_pin_true_1920x1080_new_window_pie(self):
        capture = (SCRIPTS / "validate_body_shop_performance_lod_pie_v001.py").read_text(
            encoding="utf-8"
        )
        runner = (SCRIPTS / "run_body_shop_performance_lod_validation_v001.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn('inspector.call_method("PressKey", ("Alt+P",))', capture)
        self.assertIn("controller.get_viewport_size()", capture)
        self.assertNotIn("WidgetLayoutLibrary.get_viewport_size", capture)
        self.assertIn("def resize_floating_pie_window(current_viewport):", capture)
        self.assertIn("SetThreadDpiAwarenessContext", capture)
        self.assertIn("DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2", capture)
        self.assertIn("GetWindowDpiAwarenessContext", capture)
        self.assertIn("GetDpiForWindow", capture)
        self.assertIn("AdjustWindowRectExForDpi", capture)
        self.assertIn("user32.SetWindowPos", capture)
        self.assertIn("0x0400", capture)
        self.assertIn('phase == "enforce_viewport"', capture)
        self.assertIn("if actual_viewport == EXPECTED_VIEWPORT:", capture)
        request_start = capture.index("def request_new_window_pie():")
        request_end = capture.index("\ndef tick(", request_start)
        request_source = capture[request_start:request_end]
        self.assertLess(
            request_source.index("enable_physical_pixel_dpi_context()"),
            request_source.index('inspector.call_method("PressKey", ("Alt+P",))'),
        )
        self.assertIn("MAX_VIEWPORT_RESIZE_ATTEMPTS", capture)
        self.assertIn("LastExecutedPlayModeType=PlayMode_InEditorFloating", runner)
        self.assertIn("NewWindowWidth=1920", runner)
        self.assertIn("NewWindowHeight=1080", runner)
        self.assertIn("-ResX=1920 -ResY=1080 -csvGpuStats", runner)
        self.assertIn("EditorPerProjectUserSettings.before-run.ini", runner)

    def test_retired_editor_pie_lane_fails_before_any_launch_or_window_manipulation(self):
        capture = (SCRIPTS / "validate_body_shop_performance_lod_pie_v001.py").read_text(
            encoding="utf-8"
        )
        runner = (SCRIPTS / "run_body_shop_performance_lod_validation_v001.ps1").read_text(
            encoding="utf-8"
        )
        blocker = "BLOCKED__BODY_SHOP_1920X1080_EDITOR_PIE_PERFORMANCE_LOD_V001"
        self.assertIn(blocker, capture)
        self.assertIn(blocker, runner)
        self.assertLess(capture.index("raise RuntimeError("), capture.index("set_keep_python_script_alive"))
        self.assertLess(runner.index("throw $EditorPieBlocker"), runner.index("& $Editor $Project"))

    def test_performance_lane_does_not_collide_with_release_capture_lane(self):
        performance_runner = (
            SCRIPTS / "run_body_shop_performance_lod_validation_v001.ps1"
        ).read_text(encoding="utf-8")
        release_runner = (SCRIPTS / "run_body_shop_release_validation_v001.ps1").read_text(
            encoding="utf-8"
        )
        release_capture = (
            SCRIPTS / "validate_body_shop_release_candidate_pie_v002.py"
        ).read_text(encoding="utf-8")
        self.assertIn("PerformanceLODValidation", performance_runner)
        self.assertIn("LB_BODYSHOP_PERF_LOD_STAMP", performance_runner)
        self.assertNotIn("PerformanceLODValidation", release_runner + release_capture)
        self.assertNotIn("LB_BODYSHOP_PERF_LOD_STAMP", release_runner + release_capture)
        self.assertIn("ReleaseValidation", release_runner)
        self.assertIn("LB_BODYSHOP_VALIDATION_STAMP", release_runner)


if __name__ == "__main__":
    unittest.main()
