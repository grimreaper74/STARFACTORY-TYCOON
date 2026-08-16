"""Offline static tests for incident-bound panel Recovery_v002."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = PROJECT / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cairnwell_2040_panel_modules_recovery_v002 as recovery
import prepare_cairnwell_2040_panel_modules_recovery_v002_contract as preparer


def load_source_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verifier_module = load_source_module(
    "panel_recovery_v002_verifier_static",
    SCRIPTS / "verify_cairnwell_2040_panel_modules_recovery_v002.py",
)


class FakeOptions:
    last_kwargs = None

    def __init__(self, **kwargs):
        type(self).last_kwargs = kwargs


class FakeRegistry:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def get_dependencies(self, package, options):
        self.calls.append((package, options))
        return self.result


class RecoveryV002StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = preparer.build_payload(deep_baseline_verify=False)
        cls.runner = (
            SCRIPTS / "run_cairnwell_2040_panel_modules_recovery_v002.ps1"
        ).read_text(encoding="utf-8")
        cls.validator = (
            SCRIPTS / "validate_cairnwell_2040_panel_modules_recovery_v002.py"
        ).read_text(encoding="utf-8")
        cls.verifier = (
            SCRIPTS / "verify_cairnwell_2040_panel_modules_recovery_v002.py"
        ).read_text(encoding="utf-8")
        cls.doc = (
            PROJECT
            / "Docs/OneFactory/CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002.md"
        ).read_text(encoding="utf-8")

    def test_contract_identity_and_exact_one_process_scope(self):
        self.assertEqual(self.payload["$schema"], preparer.CONTRACT_SCHEMA)
        self.assertEqual(self.payload["status"], preparer.CONTRACT_STATUS)
        recovery_row = self.payload["recovery"]
        self.assertEqual(recovery_row["process_count"], 1)
        self.assertEqual(
            recovery_row["process_role"],
            "DISTINCT_FRESH_READ_ONLY_PERSISTED_VALIDATOR",
        )
        self.assertFalse(self.payload["policy"]["reimport_authorized"])
        self.assertFalse(self.payload["policy"]["content_write_authorized"])
        self.assertFalse(
            self.payload["policy"]["recovery_audit_plus_exactly_bounded_engine_ephemera_only"]
        )
        self.assertFalse(
            self.payload["policy"]["zero_untracked_non_authority_ephemera_write_claimed"]
        )

    def test_exact_v001_five_file_incident_is_pinned(self):
        incident = self.payload["incident_v001"]
        self.assertEqual(incident["run_id"], "20260815T182842Z-0205ac3e")
        self.assertEqual(set(incident["files"]), set(preparer.INCIDENT_FILES))
        for name, expected in preparer.INCIDENT_FILES.items():
            self.assertEqual(incident["files"][name]["bytes"], expected["bytes"])
            self.assertEqual(incident["files"][name]["sha256"], expected["sha256"])
        self.assertEqual(
            incident["primary_failure"],
            "OPTIONAL_ASSET_REGISTRY_DEPENDENCY_RESULT_ITERATED_AS_ARRAY",
        )
        self.assertFalse(incident["validator_launched"])
        self.assertFalse(incident["strict_validation_completed"])

    def test_exact_eleven_preserved_package_rows(self):
        destination = self.payload["destination"]
        self.assertEqual(destination["package_count"], 11)
        self.assertEqual(len(destination["package_files"]), 11)
        self.assertEqual(
            sum(item["bytes"] for item in destination["package_files"].values()),
            393909,
        )
        self.assertTrue(all(item["sha256"] for item in destination["package_files"].values()))
        self.assertTrue(all("mtime_ns" in item for item in destination["package_files"].values()))

    def test_any_extra_destination_file_fails_not_only_extra_uasset(self):
        expected = self.payload["destination"]["package_files"]
        extra = dict(expected)
        extra["Content/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040PanelModules_v001/Meshes/escape.uexp"] = {
            "bytes": 1, "mtime_ns": 1, "sha256": "0" * 64
        }
        with mock.patch.object(recovery, "package_files", return_value=extra):
            with self.assertRaisesRegex(recovery.RecoveryError, "11-package"):
                recovery.verify_packages(self.payload)
        with mock.patch.object(
            recovery,
            "destination_directories",
            return_value=self.payload["destination"]["directory_paths"] + [
                "Content/LineBoss/Factory/OneFactory/v001/Vehicles/"
                "Cairnwell2040PanelModules_v001/UnexpectedEmpty"
            ],
        ):
            with self.assertRaisesRegex(recovery.RecoveryError, "11-package"):
                recovery.verify_packages(self.payload)
        common_source = (
            SCRIPTS / "cairnwell_2040_panel_modules_recovery_v002.py"
        ).read_text(encoding="utf-8")
        package_body = common_source.split("def package_files()", 1)[1].split(
            "def verify_packages", 1
        )[0]
        self.assertIn('DEST_ROOT.rglob("*")', package_body)
        self.assertNotIn('rglob("*.uasset")', package_body)

    def test_dependency_option_vector_is_exact_ue58_game_package_query(self):
        self.assertEqual(
            self.payload["recovery"]["persisted_dependency_options"],
            {
                "include_soft_package_references": True,
                "include_hard_package_references": True,
                "include_game_package_references": True,
                "include_editor_only_package_references": False,
                "include_searchable_names": False,
                "include_soft_management_references": False,
                "include_hard_management_references": False,
            },
        )
        registry = FakeRegistry(["/Game/Runtime/Materials/M"])
        fake_unreal = types.SimpleNamespace(
            AssetRegistryDependencyOptions=FakeOptions,
            AssetRegistryHelpers=types.SimpleNamespace(
                get_asset_registry=lambda: registry
            ),
        )
        lane = types.SimpleNamespace(project_dependencies=None)
        observed = recovery.install_persisted_dependency_query(lane, fake_unreal)
        self.assertEqual(FakeOptions.last_kwargs, observed)
        self.assertEqual(lane.project_dependencies("/Game/P"), {"/Game/Runtime/Materials/M"})

    def test_optional_dependency_none_and_empty_fail_closed_for_fresh(self):
        with self.assertRaisesRegex(recovery.RecoveryError, "returned None"):
            recovery.normalize_dependency_values(None, True, "/Game/P")
        self.assertEqual(recovery.normalize_dependency_values(None, False, "/Game/P"), set())
        self.assertEqual(recovery.normalize_dependency_values([], True, "/Game/P"), set())
        for invalid in ("abc", b"abc", {"x": 1}, 7):
            with self.assertRaises(recovery.RecoveryError):
                recovery.normalize_dependency_values(invalid, True, "/Game/P")

    def test_exact_ten_incidental_files_are_content_pinned(self):
        snapshot = self.payload["original_v001_incidental_project_writes"]
        self.assertEqual(snapshot["file_count"], 10)
        self.assertEqual(
            {item["path"] for item in snapshot["files"]},
            set(preparer.INCIDENTAL_PATHS),
        )
        self.assertTrue(snapshot["pre_post_exact_path_byte_hash_invariance_required"])
        self.assertTrue(snapshot["mtime_only_touches_must_be_explicitly_recorded"])
        self.assertEqual(
            recovery.incidental_content_rows(recovery.verify_incidental_content(self.payload)),
            recovery.incidental_content_rows(snapshot),
        )

    def test_crash_config_tree_and_one_new_file_policy_are_bounded(self):
        tree = self.payload["recovery_preflight_crash_reporter_config_tree"]
        self.assertGreater(tree["file_count"], 0)
        self.assertEqual(len(tree["files"]), tree["file_count"])
        self.assertEqual(self.payload["recovery"]["crash_reporter_config_new_file_maximum"], 1)
        self.assertEqual(
            self.payload["recovery"]["crash_reporter_config_new_file_sha256"],
            preparer.CRASH_CONFIG_SHA256,
        )

    def test_validator_is_read_only_and_requires_persisted_validation(self):
        forbidden = (
            "quit_editor(", "AssetImportTask", "import_asset_tasks", "save_loaded_asset",
            "save_asset(", "delete_asset(", "rename_asset(", "os.remove(", "shutil.move(",
        )
        for token in forbidden:
            self.assertNotIn(token, self.validator)
        self.assertIn("require_persisted_dependencies=True", self.validator)
        self.assertIn("include_game_package_references", (
            SCRIPTS / "cairnwell_2040_panel_modules_recovery_v002.py"
        ).read_text(encoding="utf-8"))
        self.assertIn("exact_ten_incidental_files_before", self.validator)

    def test_runner_is_validation_only_one_editor_and_no_content_cleanup(self):
        self.assertEqual(self.runner.count("Start-Process -FilePath $Editor"), 1)
        self.assertNotIn("import_cairnwell_2040_panel_modules", self.runner)
        self.assertNotIn("Remove-Item", self.runner)
        self.assertNotIn("Move-Item", self.runner)
        self.assertNotIn("Copy-Item", self.runner)
        self.assertIn("VALIDATE_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_ONCE", self.runner)
        self.assertIn("-NoAssetRegistryCacheWrite", self.runner)
        self.assertIn("'-nowrite'", self.runner)
        self.assertIn("PYTHONDONTWRITEBYTECODE", self.runner)
        self.assertIn("UE_SKIP_UBT_SDK_SETUP", self.runner)
        self.assertIn("[System.Management.Automation.Language.NullString]::Value", self.runner)

    def test_runner_binds_suppression_and_full_safety_vector(self):
        required = self.payload["recovery"]["required_editor_command_line_tokens"]
        for token in required:
            self.assertIn(token, self.runner)
        self.assertIn(
            self.payload["recovery"]["uncontrolled_changelist_write_suppression_override"],
            self.runner,
        )
        self.assertIn(
            self.payload["recovery"]["python_stub_write_suppression_override"],
            self.runner,
        )

    def test_crc_wait_requires_exact_binding_quiet_streak_and_never_kills_crc(self):
        self.assertIn("-MONITOR=", self.runner)
        self.assertIn("zero_process_stabilization_milliseconds = 1000", self.runner)
        self.assertIn("Foreign/unbound CrashReporter", self.runner)
        self.assertIn("kill_count = 0", self.runner)
        wait_body = self.runner.split("function Wait-ExactNormalCrcMonitor", 1)[1].split(
            "function Invoke-GuardedValidator", 1
        )[0]
        self.assertNotIn("Stop-Process", wait_body)
        self.assertIn("Start-Sleep -Milliseconds 250", wait_body)
        self.assertLess(
            wait_body.index("$Now -ge $Deadline"),
            wait_body.index("TotalMilliseconds -ge 1000) { break }"),
        )
        self.assertIn("wait_elapsed > 15000", self.verifier)
        with self.assertRaises(verifier_module.VerifyError):
            verifier_module.exact_int(999, "synthetic short CRC wait", 1000)
        self.assertEqual(
            verifier_module.exact_int(1000, "synthetic exact quiet streak", 1000),
            1000,
        )

    def test_tooling_and_one_run_topology_are_reverified_after_cut(self):
        self.assertEqual(
            {item["path"] for item in self.payload["tooling"]},
            recovery.EXPECTED_TOOL_PATHS,
        )
        common = (SCRIPTS / "cairnwell_2040_panel_modules_recovery_v002.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("verify_tooling(payload)", common)
        self.assertIn("verify_result_topology(root)", self.validator)
        self.assertIn("recovery.verify_result_topology(root)", self.verifier)

    def test_finalizer_runs_after_environment_restoration_and_can_fail_close(self):
        restoration = self.runner.index("$EnvironmentRestored = $true")
        finalize = self.runner.index("'--finalize'")
        self.assertLess(restoration, finalize)
        self.assertIn("Write-FailureSummary $_ $EnvironmentRestored", self.runner)
        self.assertNotIn("recovery.write_json(summary_path", self.verifier)

    def test_contract_pair_is_either_absent_or_exactly_reproducible(self):
        if preparer.OUTPUT.exists() or preparer.OUTPUT_SHA.exists():
            self.assertTrue(preparer.OUTPUT.is_file() and preparer.OUTPUT_SHA.is_file())
            digest = preparer.sha256(preparer.OUTPUT)
            self.assertEqual(
                preparer.OUTPUT_SHA.read_text(encoding="ascii").strip().split(),
                [digest, preparer.OUTPUT.name],
            )
            self.assertEqual(
                preparer.strict_json(preparer.OUTPUT, "frozen recovery contract"),
                preparer.build_payload(deep_baseline_verify=False),
            )
        else:
            self.assertFalse(preparer.OUTPUT.exists())
            self.assertFalse(preparer.OUTPUT_SHA.exists())

    def test_recovery_root_is_unconsumed_during_static_freeze(self):
        self.assertFalse(recovery.RECOVERY_AUDIT_ROOT.exists())
        recovery.verify_preflight_topology()

    def test_doc_states_both_incidents_and_development_visual_policy(self):
        for token in (
            "None", "CrashReportClientEditor:636", "validation-only",
            "11 panel packages", "33 authored LODs", "DEVELOPMENT model",
            "not claimed as final-release visual art", "do not run",
            "does not exhaustively snapshot every other",
        ):
            self.assertIn(token, self.doc)


if __name__ == "__main__":
    unittest.main()
