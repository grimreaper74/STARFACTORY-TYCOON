from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
PROJECT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import analyze_body_shop_packaged_performance_lod_v002 as gate
import body_shop_support_kit_native_v002_contract as support_contract


PROFILE_HEADERS = [
    "FrameTime", "GameThread", "RenderThread", "GPU",
    "PhysicalUsedMB", "MemoryFreeMB",
    "TextureStreaming/StreamingPool",
    "TextureStreaming/DesiredDataLoadedPercent",
    "TextureStreaming/PendingStreamInData",
    "GPUMem/LocalUsedMB", "GPUMem/LocalBudgetMB",
    "RHI/DrawCalls", "RHI/PrimitivesDrawn",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class BodyShopPackagedPerformanceLodV002Tests(unittest.TestCase):
    def test_native_six_axis_renderer_contract_is_exact(self):
        self.assertEqual(gate.EXPECTED_COMPONENTS, 25)
        self.assertEqual(len(gate.EXPECTED_MESHES), 10)
        joined = "\n".join(sorted(gate.EXPECTED_MESHES))
        for joint in range(1, 7):
            self.assertIn(f"SM_LB_BodyShopRobotNative_J{joint}_v001", joined)
        self.assertIn("SM_LB_BodyShopToolNative_OpenCGun_v001", joined)
        self.assertIn("SM_LB_BodyShopTool_PanelPick8Cup_v001", joined)
        self.assertNotIn("BodyShopUnderbodySlice_v001/Robot", joined)
        self.assertNotIn("WeldRobotRuntime_v001", joined)
        self.assertNotIn("SM_LB_WeldTool_SpotGun_v001", joined)

    def write_profile(self, path: Path):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            for _index in range(300):
                writer.writerow([
                    "", 16.0, 4.0, 6.0, 9.0, 4096.0, 8192.0,
                    512.0, 100.0, 0.0, 2048.0, 8192.0, 500.0, 750000.0,
                ])
            writer.writerow(["EVENTS", *PROFILE_HEADERS])
            writer.writerow(["HasHeaderRowAtEnd", "1"])

    def targets(self):
        mesh_paths = sorted(gate.EXPECTED_MESHES)
        targets = []
        for index in range(gate.EXPECTED_COMPONENTS):
            actor = f"LBBodyShopRobotActor /Game/Test.PersistentLevel.Target_{index}"
            component = f"Presentation_{index}"
            target = {
                "key": f"TARGET_{index}:{component}",
                "category": (
                    "vision_gate"
                    if index == gate.EXPECTED_COMPONENTS - 1
                    else "robot_link"
                ),
                "identity": f"TARGET_{index}",
                "actor_full_name": actor,
                "actor_name": f"Target_{index}",
                "component_name": component,
                "mesh_path": mesh_paths[index % len(mesh_paths)],
                "lod_count": 3,
                "lod_screen_sizes": [1.0, 0.55, 0.25],
                "lod_sections": [2, 1, 1],
                "lod_triangles": [300, 150, 75],
                "lod_vertices": [600, 300, 150],
                "lod_metadata_source": "packaged_runtime_static_mesh_render_data",
                "forced_lod_model": 0,
                "selected_lod": 1,
                "selected_lod_sections": 1,
                "selected_lod_triangles": 150,
                "selected_lod_vertices": 300,
                "selected_lod_source": "FPrimitiveSceneProxy::GetLOD(FSceneView)",
                "last_render_time_on_screen_seconds": 2.0,
                "last_render_age_seconds": 0.0,
                "snapshot_world_time_seconds": 2.0,
                "rendered_since_view_configured": True,
            }
            targets.append(target)
        return targets

    def make_fixture(self, root: Path):
        archive = root / "archive"
        executable = (
            archive / "Windows" / "LineBossCarFactory" / "Binaries" / "Win64"
            / "LineBossCarFactory.exe"
        )
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"MZ" + b"x" * 5000)
        build_receipt = root / "build.json"
        manifest_receipt = root / "manifest.json"
        listing_receipt = root / "listing.json"
        native_robot_receipt = root / "fresh_load_validation_receipt_v001.json"
        native_support = support_contract.validate(PROJECT)
        native_support_receipt = Path(native_support["validation_receipt"]["path"])
        build_receipt.write_text("{}\n", encoding="utf-8")
        manifest_receipt.write_text(json.dumps({
            "native_support_kit_v002": native_support,
        }), encoding="utf-8")
        listing_receipt.write_text("{}\n", encoding="utf-8")
        native_authority = (
            PROJECT
            / "Saved/Audits/BodyShop/RobotNative_v001/UnrealImportLane/20260814T204134Z-19e41ca7"
        )
        for name in (
            "lane_summary_v001.json",
            "import_receipt_v001.json",
            "fresh_load_validation_receipt_v001.json",
        ):
            shutil.copyfile(native_authority / name, root / name)
        source_root = root / "source"
        source_root.mkdir()
        source_records = []
        for name in (
            "LBBodyShopPrototypeGameMode.cpp",
            "LBBodyShopPrototypeGameMode.h",
            "LBBodyShopPackagedPerformanceBridgeTests.cpp",
        ):
            source = source_root / name
            source.write_text(f"// pinned {name}\n", encoding="utf-8")
            source_records.append({"path": str(source), "sha256": digest(source)})
        package_summary = root / "development_package_summary_v002.json"
        package_summary.write_text(json.dumps({
            "schema": gate.PACKAGE_SCHEMA,
            "status": gate.PACKAGE_STATUS,
            "configuration": "Development",
            "shipping_requested": False,
            "explicit_map": gate.MAP,
            "protected_unchanged": True,
            "archive": str(archive),
            "build_receipt": str(build_receipt),
            "build_receipt_sha256": digest(build_receipt),
            "manifest_receipt": str(manifest_receipt),
            "manifest_receipt_sha256": digest(manifest_receipt),
            "container_listing_receipt": str(listing_receipt),
            "container_listing_receipt_sha256": digest(listing_receipt),
            "native_robot_fresh_load_validation_receipt": str(native_robot_receipt),
            "native_robot_fresh_load_validation_receipt_sha256": digest(native_robot_receipt),
            "native_support_kit_v002_fresh_load_validation_receipt": str(native_support_receipt),
            "native_support_kit_v002_fresh_load_validation_receipt_sha256": digest(native_support_receipt),
            "native_support_kit_v002_authority": native_support,
            "protected_before": {"all_body_shop_source": source_records},
            "protected_after": {
                "all_body_shop_source": [dict(record) for record in source_records]
            },
        }), encoding="utf-8")
        package_json = json.loads(package_summary.read_text(encoding="utf-8"))
        package_json["protected_before"]["press_full_factory_restored_v001"] = (
            "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5"
        )
        package_json["protected_after"]["press_full_factory_restored_v001"] = (
            "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5"
        )
        package_json["protected_before"]["default_game"] = gate.EXPECTED_DEFAULT_GAME_SHA256
        package_json["protected_after"]["default_game"] = gate.EXPECTED_DEFAULT_GAME_SHA256
        package_summary.write_text(json.dumps(package_json), encoding="utf-8")

        run_root = root / "run"
        run_root.mkdir()
        token = "0123456789abcdef0123456789abcdef"
        targets = None
        views = {}
        for view_id, zoom in (("management", 6100.0), ("focus", 4000.0)):
            view_root = run_root / view_id
            view_root.mkdir()
            profile = view_root / f"{view_id}.csv"
            receipt = view_root / f"{view_id}_runtime_capture_v002.json"
            log = view_root / f"{view_id}.engine.log"
            self.write_profile(profile)
            current_targets = self.targets()
            if targets is None:
                targets = current_targets
            runtime = {
                "$schema": gate.RUNTIME_SCHEMA,
                "status": gate.RUNTIME_STATUS,
                "token": token,
                "view": view_id,
                "map": gate.MAP,
                "capture_contract": {
                    "surface": "packaged_development_game",
                    "viewport": [1920, 1080],
                    "warmup_frames": 120,
                    "csv_capture_frames": 300,
                    "force_res": True,
                    "real_rhi_required": True,
                    "null_rhi_forbidden": True,
                    "gpu_csv_stats_required": True,
                    "renderer_lod_snapshot_phase":
                        "game_thread_after_warmup_before_csv",
                    "renderer_lod_selection_source":
                        "FPrimitiveSceneProxy::GetLOD(FSceneView)",
                    "primitive_debug_dump_used": False,
                    "visible_primitives_budget_authority":
                        "registered_scene_proxy_component_upper_bound",
                },
                "rhi": {
                    "graphics_rhi": "D3D12",
                    "can_ever_render": True,
                    "null_rhi_command_line": False,
                    "r.GPUCsvStatsEnabled": 1,
                },
                "camera": {"viewport": [1920, 1080], "zoom_distance_cm": zoom},
                "target_summary": {
                    "robot_count": 3,
                    "component_count": gate.EXPECTED_COMPONENTS,
                    "unique_mesh_count": len(gate.EXPECTED_MESHES),
                    "unique_mesh_paths": sorted(gate.EXPECTED_MESHES),
                    "any_forced_lod": False,
                    "global_forced_lod": -1,
                },
                "target_components": current_targets,
                "renderer_lod_snapshot": {
                    "thread": "game_thread",
                    "phase": "after_120_warmup_frames_before_csv",
                    "selection_source": "FPrimitiveSceneProxy::GetLOD(FSceneView)",
                    "scene_view_unscaled_size": [1920, 1080],
                    "component_count": gate.EXPECTED_COMPONENTS,
                    "unique_mesh_count": len(gate.EXPECTED_MESHES),
                    "global_forced_lod": -1,
                    "registered_scene_proxy_component_count": 64,
                    "view_configured_world_time_seconds": 1.0,
                    "snapshot_world_time_seconds": 2.0,
                    "all_targets_rendered_since_view_configured": True,
                },
                "raw_csv": {
                    "path": str(profile), "bytes": profile.stat().st_size,
                    "requested_frames": 300,
                },
            }
            receipt.write_text(json.dumps(runtime), encoding="utf-8")
            log.write_text(
                "LINE_BOSS_BODY_SHOP_PACKAGED_PERFORMANCE_LOD_V002 "
                f"view={view_id.upper()} token={token} result=PASS viewport=1920x1080 "
                f"frames=300 components={gate.EXPECTED_COMPONENTS} "
                f"meshes={len(gate.EXPECTED_MESHES)} rhi=D3D12 "
                f"receipt={receipt.name}\n",
                encoding="utf-8",
            )
            views[view_id] = {"receipt": receipt, "log": log}
        return package_summary, executable, run_root, views

    def run_fixture(self, root: Path):
        package, executable, run_root, views = self.make_fixture(root)
        return gate.analyse(
            package,
            executable,
            views["management"]["receipt"],
            views["focus"]["receipt"],
            views["management"]["log"],
            views["focus"]["log"],
            run_root,
            run_root / "gate.json",
        )

    def test_complete_hash_bound_packaged_gate_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_fixture(Path(directory))
            self.assertEqual(result["status"], gate.PASS_STATUS)
            self.assertFalse(result["failures"])
            self.assertEqual(result["views"]["focus"]["performance"]["captured_frames"], 300)
            self.assertEqual(
                len(result["views"]["management"]["renderer_lod_selection"]["target_component_lods"]),
                gate.EXPECTED_COMPONENTS,
            )
            self.assertEqual(result["package"]["native_support_kit_v002"]["asset_count"], 12)
            self.assertEqual(
                result["package"]["native_support_kit_v002"]["lod_triangle_totals"],
                [20408, 7580, 1780],
            )
            self.assertEqual(
                result["package"]["core_renderer_lod_manifest"],
                {
                    "component_count": 25,
                    "unique_mesh_count": 10,
                    "service_props_in_scene_totals_only": True,
                },
            )
            self.assertEqual(
                result["views"]["management"]["renderer_lod_selection"]
                    ["target_lod_totals"]["triangles"],
                gate.EXPECTED_COMPONENTS * 150,
            )
            self.assertEqual(
                result["views"]["management"]["scene_budget_measurements"]
                    ["visible_primitives"],
                64,
            )

    def test_null_rhi_runtime_receipt_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package, executable, run_root, views = self.make_fixture(root)
            focus = json.loads(views["focus"]["receipt"].read_text(encoding="utf-8"))
            focus["rhi"]["graphics_rhi"] = "NullRHI"
            views["focus"]["receipt"].write_text(json.dumps(focus), encoding="utf-8")
            result = gate.analyse(
                package, executable,
                views["management"]["receipt"], views["focus"]["receipt"],
                views["management"]["log"], views["focus"]["log"],
                run_root, run_root / "gate.json",
            )
            self.assertEqual(result["status"], gate.FAIL_STATUS)
            self.assertTrue(any("real-RHI" in failure for failure in result["failures"]))

    def test_package_manifest_hash_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package, executable, run_root, views = self.make_fixture(root)
            package_json = json.loads(package.read_text(encoding="utf-8"))
            Path(package_json["manifest_receipt"]).write_text("DRIFT", encoding="utf-8")
            result = gate.analyse(
                package, executable,
                views["management"]["receipt"], views["focus"]["receipt"],
                views["management"]["log"], views["focus"]["log"],
                run_root, run_root / "gate.json",
            )
            self.assertEqual(result["status"], gate.FAIL_STATUS)
            self.assertTrue(any("hash drifted" in failure for failure in result["failures"]))

    def test_native_robot_fresh_load_receipt_hash_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package, executable, run_root, views = self.make_fixture(root)
            package_json = json.loads(package.read_text(encoding="utf-8"))
            Path(package_json["native_robot_fresh_load_validation_receipt"]).write_text(
                "DRIFT", encoding="utf-8"
            )
            result = gate.analyse(
                package, executable,
                views["management"]["receipt"], views["focus"]["receipt"],
                views["management"]["log"], views["focus"]["log"],
                run_root, run_root / "gate.json",
            )
            self.assertEqual(result["status"], gate.FAIL_STATUS)
            self.assertTrue(any("native six-axis robot" in failure
                                for failure in result["failures"]))

    def test_native_support_receipt_hash_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package, executable, run_root, views = self.make_fixture(root)
            package_json = json.loads(package.read_text(encoding="utf-8"))
            package_json[
                "native_support_kit_v002_fresh_load_validation_receipt_sha256"
            ] = "0" * 64
            package.write_text(json.dumps(package_json), encoding="utf-8")
            result = gate.analyse(
                package, executable,
                views["management"]["receipt"], views["focus"]["receipt"],
                views["management"]["log"], views["focus"]["log"],
                run_root, run_root / "gate.json",
            )
            self.assertEqual(result["status"], gate.FAIL_STATUS)
            self.assertTrue(any("native support-kit" in failure
                                for failure in result["failures"]))

    def test_native_robot_final_authority_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package, executable, run_root, views = self.make_fixture(root)
            package_json = json.loads(package.read_text(encoding="utf-8"))
            native_path = Path(package_json["native_robot_fresh_load_validation_receipt"])
            native = json.loads(native_path.read_text(encoding="utf-8"))
            native["baseline_sha256"] = "0" * 64
            native_path.write_text(json.dumps(native), encoding="utf-8")
            package_json["native_robot_fresh_load_validation_receipt_sha256"] = digest(native_path)
            package.write_text(json.dumps(package_json), encoding="utf-8")
            result = gate.analyse(
                package, executable,
                views["management"]["receipt"], views["focus"]["receipt"],
                views["management"]["log"], views["focus"]["log"],
                run_root, run_root / "gate.json",
            )
            self.assertEqual(result["status"], gate.FAIL_STATUS)
            self.assertTrue(any("final validation receipt" in failure
                                for failure in result["failures"]))

    def test_packaged_body_shop_source_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package, executable, run_root, views = self.make_fixture(root)
            package_json = json.loads(package.read_text(encoding="utf-8"))
            source = Path(package_json["protected_after"]["all_body_shop_source"][0]["path"])
            source.write_text("// drifted after package\n", encoding="utf-8")
            result = gate.analyse(
                package, executable,
                views["management"]["receipt"], views["focus"]["receipt"],
                views["management"]["log"], views["focus"]["log"],
                run_root, run_root / "gate.json",
            )
            self.assertEqual(result["status"], gate.FAIL_STATUS)
            self.assertTrue(any("source hash drifted" in failure for failure in result["failures"]))

    def test_selected_lod_triangle_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package, executable, run_root, views = self.make_fixture(root)
            focus = json.loads(views["focus"]["receipt"].read_text(encoding="utf-8"))
            focus["target_components"][0]["selected_lod_triangles"] = 149
            views["focus"]["receipt"].write_text(json.dumps(focus), encoding="utf-8")
            result = gate.analyse(
                package, executable,
                views["management"]["receipt"], views["focus"]["receipt"],
                views["management"]["log"], views["focus"]["log"],
                run_root, run_root / "gate.json",
            )
            self.assertEqual(result["status"], gate.FAIL_STATUS)
            self.assertTrue(any("LOD metadata drifted" in failure for failure in result["failures"]))

    def test_global_forced_lod_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package, executable, run_root, views = self.make_fixture(root)
            focus = json.loads(views["focus"]["receipt"].read_text(encoding="utf-8"))
            focus["target_summary"]["global_forced_lod"] = 0
            focus["renderer_lod_snapshot"]["global_forced_lod"] = 0
            views["focus"]["receipt"].write_text(json.dumps(focus), encoding="utf-8")
            result = gate.analyse(
                package, executable,
                views["management"]["receipt"], views["focus"]["receipt"],
                views["management"]["log"], views["focus"]["log"],
                run_root, run_root / "gate.json",
            )
            self.assertEqual(result["status"], gate.FAIL_STATUS)
            self.assertTrue(any("target summary drifted" in failure for failure in result["failures"]))

    def test_stale_primitive_dump_receipt_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package, executable, run_root, views = self.make_fixture(root)
            focus = json.loads(views["focus"]["receipt"].read_text(encoding="utf-8"))
            focus["primitive_csv_candidates"] = []
            views["focus"]["receipt"].write_text(json.dumps(focus), encoding="utf-8")
            result = gate.analyse(
                package, executable,
                views["management"]["receipt"], views["focus"]["receipt"],
                views["management"]["log"], views["focus"]["log"],
                run_root, run_root / "gate.json",
            )
            self.assertEqual(result["status"], gate.FAIL_STATUS)
            self.assertTrue(any("primitive-dump evidence" in failure for failure in result["failures"]))

    def test_stale_on_screen_render_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package, executable, run_root, views = self.make_fixture(root)
            focus = json.loads(views["focus"]["receipt"].read_text(encoding="utf-8"))
            focus["target_components"][0]["last_render_age_seconds"] = 0.75
            views["focus"]["receipt"].write_text(json.dumps(focus), encoding="utf-8")
            result = gate.analyse(
                package, executable,
                views["management"]["receipt"], views["focus"]["receipt"],
                views["management"]["log"], views["focus"]["log"],
                run_root, run_root / "gate.json",
            )
            self.assertEqual(result["status"], gate.FAIL_STATUS)
            self.assertTrue(any("LOD metadata drifted" in failure for failure in result["failures"]))

    def test_native_bridge_and_separate_runner_pin_the_packaged_contract(self):
        source = (PROJECT / "Source/LineBossCarFactory/LBBodyShopPrototypeGameMode.cpp").read_text(
            encoding="utf-8"
        )
        header = (PROJECT / "Source/LineBossCarFactory/LBBodyShopPrototypeGameMode.h").read_text(
            encoding="utf-8"
        )
        tests = (PROJECT / "Source/LineBossCarFactory/LBBodyShopPackagedPerformanceBridgeTests.cpp").read_text(
            encoding="utf-8"
        )
        runner = (SCRIPTS / "run_body_shop_packaged_performance_lod_validation_v002.ps1").read_text(
            encoding="utf-8"
        )
        analyzer = (SCRIPTS / "analyze_body_shop_packaged_performance_lod_v002.py").read_text(
            encoding="utf-8"
        )
        build_rules = (PROJECT / "Source/LineBossCarFactory/LineBossCarFactory.Build.cs").read_text(
            encoding="utf-8"
        )
        package_runner = (SCRIPTS / "package_body_shop_experimental_development_v001.ps1").read_text(
            encoding="utf-8"
        )
        for token in (
            "LineBossBodyShopPerformanceValidation=",
            "PackagedPerformanceCaptureFrames = 300",
            "CsvProfile FRAMES=%d",
            "GetViewportSize(ViewportX, ViewportY)",
            "packaged_runtime_static_mesh_render_data",
            "SnapshotPackagedPerformanceRendererLODs",
            "CalcSceneView",
            "GetSceneProxy()->GetLOD(SceneView)",
            "GetLastRenderTimeOnScreen",
            'FindConsoleVariable(TEXT("r.ForceLOD"))',
            "BW003_UNDERBODY_FIXTURE_BASIC",
            "UNDERBODY FIXTURE MAIN PRESENTATION MUST REMAIN ABSENT",
        ):
            self.assertIn(token, source + header)
        self.assertIn("-ForceRes", runner)
        self.assertIn("-ResX=1920", runner)
        self.assertIn("-ResY=1080", runner)
        self.assertIn("-csvGpuStats", runner)
        self.assertIn("views=@('management','focus')", runner)
        self.assertIn("all_body_shop_source", runner)
        self.assertIn("$null = $Process.Handle", runner)
        self.assertIn("$null = $AnalyzerProcess.Handle", runner)
        self.assertIn("if ($null -eq $ExitCode)", runner)
        self.assertIn("if ($null -eq $AnalysisExit)", runner)
        self.assertIn("ExactTokenedMarkers", tests)
        self.assertNotIn("DumpDetailedPrimitives", source + header + analyzer + runner)
        self.assertNotIn("WaitPrimitiveDump", source + header)
        self.assertNotIn("DrawPrimitiveDebugger", build_rules)
        self.assertNotIn("LineBossBodyShopPerformanceValidation", package_runner)

    def test_external_package_roots_are_manifest_hash_bound_and_source_stays_protected(self):
        runner = (SCRIPTS / "run_body_shop_packaged_performance_lod_validation_v002.ps1").read_text(
            encoding="utf-8"
        )
        for token in (
            "Resolve-DeclaredAbsoluteRoot",
            "Resolve-ExactChildLeaf",
            "Assert-ExactHashRecord",
            "$ManifestSchema",
            "$ManifestStatus",
            "$PackageSummaryHashAtLoad",
            "$PackageArtifactFiles",
            "$Manifest.archive_root",
            "$Manifest.stage_root",
            "$Manifest.archive_executables",
            "$Manifest.stage_executables",
            "$Manifest.archive_containers",
            "$Manifest.stage_containers",
            "Archived Development executable",
            "Staged Development executable",
            "Archived IoStore UTOC",
            "Archived IoStore UCAS",
            "Staged IoStore UTOC",
            "Staged IoStore UCAS",
            "Stage/archive Development executable hashes differ",
            "Stage/archive IoStore container hashes differ",
            "$CurrentBodyShopSourceFiles + $NativeRobotAssetFiles + $NativeSupportAssetFiles +",
            "native_robot_fresh_load_validation_receipt",
            "native_support_kit_v002_fresh_load_validation_receipt",
            "core_renderer_manifest_components=25",
            "native_service_props_in_scene_totals=$true",
        ):
            self.assertIn(token, runner)
        self.assertIn(
            "$Archive = Resolve-DeclaredAbsoluteRoot ([string]$Package.archive)", runner
        )
        self.assertIn(
            "$Stage = Resolve-DeclaredAbsoluteRoot ([string]$Package.stage)", runner
        )
        self.assertIn(
            "$ManifestReceiptPath = Resolve-ProjectLeaf ([string]$Package.manifest_receipt)",
            runner,
        )
        self.assertIn(
            "$PackageSummaryPath = Resolve-ProjectLeaf $DevelopmentPackageSummary", runner
        )
        self.assertNotIn(
            "$Archive = Resolve-ProjectPath ([string]$Package.archive)", runner
        )
        self.assertNotIn(
            "$Stage = Resolve-ProjectPath ([string]$Package.stage)", runner
        )


if __name__ == "__main__":
    unittest.main()
