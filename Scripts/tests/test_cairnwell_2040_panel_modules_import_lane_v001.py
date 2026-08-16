"""Offline static tests for the frozen Cairnwell panel import lane."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = PROJECT / "Scripts"
CONTRACT_TOOL = SCRIPTS / "prepare_cairnwell_2040_panel_modules_v001_contract.py"
BASELINE_TOOL = SCRIPTS / "prepare_cairnwell_2040_panel_modules_v001_baseline.py"
COMMON = SCRIPTS / "cairnwell_2040_panel_modules_v001.py"
IMPORTER = SCRIPTS / "import_cairnwell_2040_panel_modules_v001.py"
VALIDATOR = SCRIPTS / "validate_cairnwell_2040_panel_modules_fresh_process_v001.py"
RUNNER = SCRIPTS / "run_cairnwell_2040_panel_modules_import_lane_v001.ps1"
DOC = PROJECT / "Docs/OneFactory/CAIRNWELL_2040_PANEL_MODULES_V001_UNREAL_IMPORT_LANE.md"
CONTRACT = SCRIPTS / "cairnwell_2040_panel_modules_v001_import_contract.json"
CONTRACT_SHA = CONTRACT.with_suffix(".sha256")
BASELINE = SCRIPTS / "cairnwell_2040_panel_modules_v001_import_baseline_v002.json"
BASELINE_SHA = BASELINE.with_suffix(".sha256")
FAILED_BASELINE_V001 = SCRIPTS / "cairnwell_2040_panel_modules_v001_import_baseline.json"
FAILED_BASELINE_V001_SHA = FAILED_BASELINE_V001.with_suffix(".sha256")
DEST = PROJECT / (
    "Content/LineBoss/Factory/OneFactory/v001/Vehicles/"
    "Cairnwell2040PanelModules_v001"
)
AUDIT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040PanelModules_v001/"
    "UnrealImportLane_v001"
)
RUNTIME_V013 = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v013_contract.json"
RUNTIME_V013_SHA = RUNTIME_V013.with_suffix(".sha256")
RUNTIME_RUN = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v013/20260815T172802Z-1389784f"
)
SOURCE_ROOT = PROJECT / (
    "SourceAssets/Candidate/Vehicles/Cairnwell2040/"
    "Cairnwell2040PanelModules_v002"
)
MANIFEST = SOURCE_ROOT / "MANIFEST_Cairnwell2040PanelModules_v002.json"
PANEL_IDS = (
    "HOOD_PANEL", "ROOF_PANEL",
    "DOOR_FRONT_LEFT", "DOOR_FRONT_RIGHT",
    "DOOR_REAR_LEFT", "DOOR_REAR_RIGHT",
    "FENDER_FRONT_LEFT", "FENDER_FRONT_RIGHT",
    "QUARTER_PANEL_LEFT", "QUARTER_PANEL_RIGHT",
    "TAILGATE_PANEL",
)
EXPECTED_RUNTIME_FILES = {
    "fresh_process_validation_receipt_recovery_v013.json":
        "54A332C47FE71CE975EE666331882369855770C13B81CE6C195488A957127E44",
    "fresh_process_validation_recovery_v013.log":
        "75D0C27913C1F9F384BAF0E51FC7DDEC048B5F5C6184348D70F93829A5D3E32C",
    "fresh_process_validation_recovery_v013.stderr.log":
        "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    "fresh_process_validation_recovery_v013.stdout.log":
        "238F34F429471415B746C0AB381A497E6F2B2E883E9188A5AFB5329EBB2C5B7E",
    "lane_summary_recovery_v013.json":
        "D24261F1929D3B44EBF6526C148E044A403006DB738F52257A1A16D9CB432488",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PanelLaneStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract_source = CONTRACT_TOOL.read_text(encoding="utf-8")
        cls.baseline_source = BASELINE_TOOL.read_text(encoding="utf-8")
        cls.common_source = COMMON.read_text(encoding="utf-8")
        cls.importer_source = IMPORTER.read_text(encoding="utf-8")
        cls.validator_source = VALIDATOR.read_text(encoding="utf-8")
        cls.runner_source = RUNNER.read_text(encoding="utf-8")
        cls.doc_source = DOC.read_text(encoding="utf-8")
        cls.preparer = load_module("panel_contract_static", CONTRACT_TOOL)
        cls.manifest = cls.preparer.strict_json_file(MANIFEST, "manifest")
        cls.payload = cls.preparer.build_payload(cls.manifest)

    def test_exact_v002_source_authority_and_order(self) -> None:
        provenance = self.payload["provenance"]
        self.assertEqual(
            provenance["manifest"]["sha256"],
            "2FF38357BEC9FB890B2DCCCBC4C5E1728AB35D5BCB772F08811522540F6DF6E8",
        )
        self.assertEqual(
            provenance["production_audit"]["sha256"],
            "F7C9CF062DBC1E5A4B5CBFE8B71A9BD79E1536D0523802F8F118562E9CC24762",
        )
        self.assertEqual(
            provenance["freeze_receipt"]["sha256"],
            "B31900FE90D237952E788361309B747B8C7D831536034CBD23894408E0925B3D",
        )
        self.assertEqual(tuple(self.payload["modules"]), PANEL_IDS)
        self.assertEqual(provenance["source_authority_version"], "v002")
        self.assertEqual(provenance["unreal_destination_version"], "v001")

    def test_every_panel_has_three_clean_authored_lods_and_shared_zero_datum(self) -> None:
        for panel_id in PANEL_IDS:
            panel = self.payload["modules"][panel_id]
            lods = panel["lods"]
            self.assertEqual([row["lod"] for row in lods], [0, 1, 2])
            self.assertGreater(lods[0]["triangles"], lods[1]["triangles"])
            self.assertGreater(lods[1]["triangles"], lods[2]["triangles"])
            self.assertTrue(all(row["uv_channels"] == 1 for row in lods))
            self.assertTrue(all(row["degenerate_triangles"] == 0 for row in lods))
            self.assertTrue(all(row["zero_length_edges"] == 0 for row in lods))
            self.assertTrue(all(row["expected_unreal_bounds"]["pivot_cm"] == [0.0, 0.0, 0.0]
                                for row in lods))
            self.assertEqual(panel["material_slots"], ["VehiclePanelSurface"])
            self.assertFalse(panel["nanite_enabled"])
            self.assertFalse(panel["has_navigation_data"])
            self.assertEqual(panel["collision"]["simple_count"], 0)
            self.assertEqual(panel["collision"]["convex_count"], 0)

    def test_runtime_authority_is_only_exact_v013_five_file_pass(self) -> None:
        runtime = self.payload["runtime_authority"]
        self.assertEqual(
            runtime["recovery_v013_contract_sha256"],
            "5D2B1929086AD33A8354ED0759509BCC6AFFEF8CD4E5BDE77A54546B53E95F12",
        )
        self.assertEqual(runtime["recovery_v013_run_id"], "20260815T172802Z-1389784f")
        self.assertEqual(set(runtime["recovery_v013_result_files"]), set(EXPECTED_RUNTIME_FILES))
        self.assertEqual(len(runtime["package_sha256"]), 11)
        self.assertTrue(runtime["persisted_dependency_closure_verified"])
        self.assertTrue(runtime["cache_and_legacy_surfaces_unchanged"])
        self.assertTrue(runtime["no_build_tool_invoked"])
        self.assertNotRegex(self.contract_source, r"\bmax\s*\(")
        self.assertNotIn("Recovery_v004", self.contract_source)
        self.assertNotIn("recovery_v004", self.contract_source)

    def test_runtime_v013_files_and_sidecar_are_byte_pinned(self) -> None:
        self.assertEqual(
            sha256(RUNTIME_V013),
            "5D2B1929086AD33A8354ED0759509BCC6AFFEF8CD4E5BDE77A54546B53E95F12",
        )
        self.assertEqual(
            RUNTIME_V013_SHA.read_text(encoding="ascii").split()[0].upper(),
            sha256(RUNTIME_V013),
        )
        self.assertEqual({path.name for path in RUNTIME_RUN.iterdir() if path.is_file()},
                         set(EXPECTED_RUNTIME_FILES))
        for name, digest in EXPECTED_RUNTIME_FILES.items():
            self.assertEqual(sha256(RUNTIME_RUN / name), digest)

    def test_runtime_material_reuse_is_solid_colour_and_no_duplication(self) -> None:
        reuse = self.payload["material_reuse"]
        self.assertEqual(set(reuse["materials"]),
                         {"biw_galvanised", "ed_coat", "player_paint"})
        self.assertEqual(reuse["default_role"], "player_paint")
        self.assertEqual(reuse["new_texture_count"], 0)
        self.assertEqual(reuse["new_material_count"], 0)
        self.assertEqual(
            {row["package_sha256"] for row in reuse["materials"].values()},
            {
                self.payload["runtime_authority"]["package_sha256"][row["package_path"]]
                for row in reuse["materials"].values()
            },
        )

    def test_development_model_identity_is_revisionable(self) -> None:
        runtime = self.payload["runtime_authority"]
        self.assertEqual(runtime["vehicle_model_id"], "CAIRNWELL_2040")
        self.assertEqual(
            runtime["production_recipe_id"],
            "CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001",
        )
        self.assertEqual(
            runtime["lifecycle"],
            "DEVELOPMENT__APPROVED_FOR_GAME_BUILD__NOT_FINAL_ART",
        )
        self.assertTrue(runtime["geometry_revisionable"])
        self.assertFalse(runtime["final_release_visual_lock_claimed"])
        self.assertTrue(
            self.payload["policy"][
                "development_geometry_is_revisionable_behind_stable_contract"
            ]
        )

    def test_v013_project_snapshots_are_historical_and_new_baseline_is_authority(self) -> None:
        runtime = self.payload["runtime_authority"]
        boundary = self.payload["project_authority_boundary"]
        self.assertTrue(
            runtime[
                "historical_v013_project_snapshots_are_receipt_evidence_not_live_baseline"
            ]
        )
        self.assertTrue(runtime["current_project_authority_is_the_new_panel_baseline"])
        self.assertEqual(
            boundary["runtime_v013_project_snapshots_role"],
            "HISTORICAL_VALIDATION_EVIDENCE_ONLY",
        )
        self.assertEqual(
            boundary["current_project_authority"],
            "NEW_PANEL_BASELINE_FULL_PROJECT_SNAPSHOT",
        )
        self.assertEqual(
            boundary["authorized_intervening_source_evolution"],
            "PAINT_PRESENTATION_SOURCE_EVOLUTION",
        )
        self.assertTrue(
            boundary[
                "authorized_intervening_source_evolution_is_not_future_drift_permission"
            ]
        )
        self.assertFalse(boundary["unrelated_future_drift_authorized"])
        self.assertFalse(
            self.payload["policy"]["unrelated_post_panel_baseline_drift_authorized"]
        )

    def test_runner_has_v013_lifecycle_cache_and_ubt_guards(self) -> None:
        required = (
            "-NoAssetRegistryCacheWrite", "UE_SKIP_UBT_SDK_SETUP",
            "[System.Management.Automation.Language.NullString]::Value",
            "Get-CimInstance Win32_Process", "-Mode=ValidatePlatforms",
            "Assert-NoProcesses", "--verify-import-result",
            "--verify-validation-result", "--finalize-result",
            "--verify-final-result", "FINAL_NINE_FILE_REVERIFIED",
            "WindowStyle Hidden", "WaitForExit(3600 * 1000)",
            "cairnwell_2040_panel_modules_v001_import_baseline_v002.json",
        )
        for token in required:
            self.assertIn(token, self.runner_source)
        self.assertNotIn("PSObject.Properties", self.runner_source)
        self.assertNotIn("ConvertFrom-Json", self.runner_source)
        self.assertNotIn("Remove-Item", self.runner_source)
        self.assertNotIn("recovery_v004", self.runner_source.casefold())
        self.assertNotIn(
            "-or (Test-Path -LiteralPath $SummaryPath)", self.runner_source
        )
        self.assertIn("catch {\n    Write-FailureSummary $_", self.runner_source)
        self.assertNotIn(
            "$Baseline = Join-Path $Root 'Scripts\\cairnwell_2040_panel_modules_v001_import_baseline.json'",
            self.runner_source,
        )

    def test_failed_v001_baseline_is_exact_unselectable_incident_evidence(self) -> None:
        self.assertEqual(
            sha256(FAILED_BASELINE_V001),
            "6CC7C1F6528A780C486AB8DFEC506066C42298CC516B599BD48B3A94D714FE8F",
        )
        self.assertEqual(
            sha256(FAILED_BASELINE_V001_SHA),
            "BAAF1653721D564149E73363F08335628A3D45C05F8F5A322435BB3BC6D3E0EB",
        )
        baseline_tool = load_module("panel_baseline_v002_static", BASELINE_TOOL)
        evidence = baseline_tool.failed_baseline_v001_evidence()
        self.assertEqual(
            evidence["status"],
            "PRESERVED__UNSELECTABLE__FAILED_IMMEDIATE_REVERIFICATION__"
            "CONCURRENT_AUTHORIZED_PAINT_SOURCE_DRIFT",
        )
        self.assertFalse(evidence["may_authorize_unreal"])
        self.assertFalse(evidence["may_be_selected_as_current_baseline"])
        self.assertEqual(
            evidence["captured_paint_source"]["sha256"],
            "465AAC3D0E81618103E7B6CFD04B83B340EAFE3AAC67D9BD956ECCC91C0FCB4C",
        )
        self.assertEqual(
            evidence["observed_post_cut_paint_source"]["sha256"],
            "A186D6550930B10DFC2D85E7511A5B6D3AC7C5EAFE98CB6026849859D9C4D84A",
        )

    def test_whole_audit_root_blocks_contract_and_baseline_creation(self) -> None:
        baseline_tool = load_module("panel_baseline_audit_root_static", BASELINE_TOOL)
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            original_contract_values = (
                self.preparer.OUTPUT,
                self.preparer.OUTPUT_SHA,
                self.preparer.DEST_DISK,
                self.preparer.AUDIT_ROOT,
            )
            original_baseline_values = (
                baseline_tool.BASELINE,
                baseline_tool.BASELINE_SHA,
                baseline_tool.DEST_DISK,
                baseline_tool.AUDIT_ROOT,
            )
            try:
                self.preparer.OUTPUT = root / "contract.json"
                self.preparer.OUTPUT_SHA = root / "contract.sha256"
                self.preparer.DEST_DISK = root / "absent-destination"
                self.preparer.AUDIT_ROOT = root
                with self.assertRaisesRegex(
                    self.preparer.ContractError, "audit root already exists"
                ):
                    self.preparer.create(MANIFEST, self.preparer.ACK_TOKEN)

                baseline_tool.BASELINE = root / "baseline.json"
                baseline_tool.BASELINE_SHA = root / "baseline.sha256"
                baseline_tool.DEST_DISK = root / "absent-destination"
                baseline_tool.AUDIT_ROOT = root
                with self.assertRaisesRegex(
                    baseline_tool.BaselineError, "audit root already exists"
                ):
                    baseline_tool.create(baseline_tool.ACK_TOKEN)
            finally:
                (
                    self.preparer.OUTPUT,
                    self.preparer.OUTPUT_SHA,
                    self.preparer.DEST_DISK,
                    self.preparer.AUDIT_ROOT,
                ) = original_contract_values
                (
                    baseline_tool.BASELINE,
                    baseline_tool.BASELINE_SHA,
                    baseline_tool.DEST_DISK,
                    baseline_tool.AUDIT_ROOT,
                ) = original_baseline_values

    def test_no_explicit_quit_and_direct_collision_enum_comparison(self) -> None:
        for source in (self.importer_source, self.validator_source, self.common_source):
            self.assertNotRegex(source, r"\bquit_editor\s*\(")
        self.assertIn(
            "trace_enum != unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX",
            self.common_source,
        )
        self.assertNotIn('"SIMPLE_AS_COMPLEX" not in trace.upper()', self.common_source)

    def test_python_result_verifier_owns_package_maps_and_log_gates(self) -> None:
        for token in (
            "strict_pairs", "panel_package_hashes", "process_log_evidence",
            "Fatal error:", "Ensure condition failed", "ModeManager",
            "UnrealBuildTool", "Asset registry cache written as",
            "LogExit: Exiting.", "CleanupOrphanedCacheFiles (PreLoad)",
            "exact nine-file closure",
        ):
            self.assertIn(token, self.baseline_source)

    def test_cache_and_legacy_surfaces_match_v013(self) -> None:
        baseline_tool = load_module("panel_baseline_static", BASELINE_TOOL)
        self.assertEqual(
            baseline_tool.asset_registry_cache_snapshot(),
            self.payload["runtime_authority"]["asset_registry_cache"],
        )
        self.assertEqual(
            baseline_tool.legacy_asset_registry_cache_absence(),
            self.payload["runtime_authority"]["legacy_asset_registry_cache_absence"],
        )

    def test_contract_and_baseline_pairs_are_symmetric_and_fresh(self) -> None:
        self.assertEqual(CONTRACT.exists(), CONTRACT_SHA.exists())
        self.assertEqual(BASELINE.exists(), BASELINE_SHA.exists())
        if CONTRACT.exists():
            self.assertEqual(
                CONTRACT_SHA.read_text(encoding="ascii").split()[0].upper(),
                sha256(CONTRACT),
            )
        if BASELINE.exists():
            self.assertEqual(
                BASELINE_SHA.read_text(encoding="ascii").split()[0].upper(),
                sha256(BASELINE),
            )
            frozen = json.loads(BASELINE.read_text(encoding="utf-8"))
            self.assertEqual(
                frozen["$schema"],
                "lineboss/cairnwell-2040-panel-modules-v001/unreal-import-baseline/v2",
            )
            self.assertFalse(
                frozen["superseded_failed_baseline_v001"]["may_authorize_unreal"]
            )
        self.assertFalse(DEST.exists())
        self.assertFalse(AUDIT.exists())

    def test_lane_file_closure_is_exact_eight(self) -> None:
        expected = {
            "Scripts/prepare_cairnwell_2040_panel_modules_v001_contract.py",
            "Scripts/prepare_cairnwell_2040_panel_modules_v001_baseline.py",
            "Scripts/cairnwell_2040_panel_modules_v001.py",
            "Scripts/import_cairnwell_2040_panel_modules_v001.py",
            "Scripts/validate_cairnwell_2040_panel_modules_fresh_process_v001.py",
            "Scripts/run_cairnwell_2040_panel_modules_import_lane_v001.ps1",
            "Scripts/tests/test_cairnwell_2040_panel_modules_import_lane_v001.py",
            "Docs/OneFactory/CAIRNWELL_2040_PANEL_MODULES_V001_UNREAL_IMPORT_LANE.md",
        }
        self.assertEqual(set(self.payload["lane_files_to_pin_when_baseline_is_cut"]),
                         expected)

    def test_docs_state_exact_authority_and_no_ue_freeze_boundary(self) -> None:
        for token in (
            "Recovery_v013/20260815T172802Z-1389784f",
            "54A332C47FE71CE975EE666331882369855770C13B81CE6C195488A957127E44",
            "11 runtime packages", "33 authored panel LODs",
            "NoAssetRegistryCacheWrite", "UE_SKIP_UBT_SDK_SETUP",
            "DEVELOPMENT", "replaceable", "historical validation evidence",
            "Paint presentation Source evolution", "unrelated later drift",
            "baseline v002", "failed baseline v001",
        ):
            self.assertIn(token.casefold(), self.doc_source.casefold())


if __name__ == "__main__":
    unittest.main()
