from __future__ import annotations

import copy
import hashlib
import pathlib
import subprocess
import sys
import unittest


PROJECT = pathlib.Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = PROJECT / "Scripts"
DOC = PROJECT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013.md"
PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v013.py"
VALIDATOR = SCRIPTS / "validate_cairnwell_2040_runtime_recovery_v013.py"
RUNNER = SCRIPTS / "run_cairnwell_2040_runtime_validation_recovery_v013.ps1"
CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v013_contract.json"
SIDECAR = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v013_contract.sha256"
V012_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v012_contract.json"
V012_SIDECAR = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v012_contract.sha256"
V013_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v013")
WINDOWS_POWERSHELL = pathlib.Path(
    r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
PWSH = pathlib.Path(r"C:\Program Files\PowerShell\7\pwsh.exe")


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


sys.path.insert(0, str(SCRIPTS))
import prepare_cairnwell_2040_runtime_v001_recovery_v013 as recovery


class CairnwellValidationRecoveryV013Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preparer = PREPARER.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.state = recovery.authority_state()
        cls.candidate = recovery.build_candidate_payload(
            cls.state, recovery.candidate_generated_utc(cls.state))
        recovery.validate_candidate_payload(cls.candidate, cls.state)

    def test_v012_pair_run_receipt_and_wrapper_failure_are_exact(self) -> None:
        self.assertEqual(V012_CONTRACT.stat().st_size, 173097)
        self.assertEqual(sha(V012_CONTRACT), recovery.V012_CONTRACT_SHA256)
        self.assertEqual(V012_SIDECAR.stat().st_size, 122)
        self.assertEqual(sha(V012_SIDECAR), recovery.V012_SIDECAR_SHA256)
        self.assertEqual(recovery.exact_v012_run_snapshot()["file_count"], 5)
        incident = self.state["v012_incident"]
        self.assertTrue(incident["fresh_validation_receipt_semantic_pass"])
        self.assertEqual(
            incident["wrapper_failure"]["error"], recovery.V012_SUMMARY_ERROR)
        self.assertFalse(
            incident["wrapper_failure"]["environment_restoration_verified"])

    def test_cleanup_topology_is_exact_and_v012_names_are_truthful(self) -> None:
        cleanup = self.state["v012_incident"]["cache_cleanup"]
        self.assertEqual(set(cleanup["per_primary_log"]), {
            "fresh_process_validation_recovery_v012.log",
            "fresh_process_validation_recovery_v012.stdout.log",
        })
        for row in cleanup["per_primary_log"].values():
            self.assertEqual(row, {
                "preload_informational_occurrences": 1,
                "postwrite_informational_occurrences": 1,
                "adjacent_zero_mutation_summary_occurrences": 2,
                "cache_write_occurrences": 0,
                "orphan_deleted_occurrences": 0,
                "orphan_delete_failed_occurrences": 0,
                "legacy_cleanup_occurrences": 0,
            })
        for token in (
            "PRELOAD_LINE", "POSTWRITE_LINE", "ZERO_MUTATION_SUMMARY_LINE",
            "line.endswith(PRELOAD_LINE)",
            "line.endswith(POSTWRITE_LINE)",
            "line.endswith(ZERO_MUTATION_SUMMARY_LINE)",
            ".EndsWith($PreLoadLine, [StringComparison]::Ordinal)",
            ".EndsWith($PostWriteLine, [StringComparison]::Ordinal)",
            "cleanup_log_evidence({name: actual[name] for name in VALIDATOR_LOGS})",
        ):
            self.assertIn(token, self.preparer + self.runner)

    def test_cache_and_silent_legacy_deletion_surfaces_are_exact(self) -> None:
        cache = recovery.prior.verify_asset_registry_cache_snapshot()
        absence = recovery.verify_legacy_cache_deletion_surface_absent()
        self.assertEqual(
            cache["inventory_sha256"],
            "59DEFE0409EA024EA6FF7B4CF2B7FEF7CD8FC8D652EE356D76ACE7DC2767B3E9")
        self.assertEqual(absence["matching_path_count"], 0)
        self.assertTrue(absence["monolithic_absent"])
        self.assertEqual(absence["legacy_shard_paths"], [])
        self.assertTrue(absence["windows_case_insensitive_name_match"])
        self.assertTrue(recovery.is_legacy_cache_deletion_candidate(
            "cAcHeDaSsEtReGiStRy.BIN"))
        self.assertTrue(recovery.is_legacy_cache_deletion_candidate(
            "CACHEDASSETREGISTRY_7.BIN"))
        self.assertFalse(recovery.is_legacy_cache_deletion_candidate(
            "CachedAssetRegistryDiscovery.bin"))
        self.assertEqual(
            self.candidate["legacy_asset_registry_cache_deletion_surface"]
            ["exact_pre_validation_absence"], absence)
        for token in (
            "-NoAssetRegistryCacheWrite", "silent_tmp_deletion_lines",
            "legacy_shard_deletion_lines", "legacy_monolithic_silent_delete_lines",
            "post_exit_legacy_asset_registry_cache_absence",
            "legacy_asset_registry_cache_absence_before",
            "legacy_asset_registry_cache_absence_after",
        ):
            self.assertIn(token, self.preparer + self.validator + self.runner)

    def test_nullstring_restoration_is_exact_and_ps51_compatible(self) -> None:
        for token in (
            "[System.Management.Automation.Language.NullString]::Value",
            "if ($null -eq $Row.Value)", "$null -eq $ActualRunEnvironment",
            "$null -eq $ActualAckEnvironment", "$null -eq $ActualSkipUbtEnvironment",
            "$Summary.environment_restoration_verified = [bool](",
        ):
            self.assertIn(token, self.runner)
        for shell in (WINDOWS_POWERSHELL, PWSH):
            if not shell.is_file():
                continue
            command = (
                "$n='LINEBOSS_V013_NULLSTRING_TEST_'+[Guid]::NewGuid().ToString('N');"
                "[Environment]::SetEnvironmentVariable($n,'x','Process');"
                "[Environment]::SetEnvironmentVariable($n,"
                "[System.Management.Automation.Language.NullString]::Value,'Process');"
                "if($null -ne [Environment]::GetEnvironmentVariable($n,'Process'))"
                "{exit 1};'NULLSTRING_PASS'")
            result = subprocess.run(
                [str(shell), "-NoProfile", "-Command", command], cwd=PROJECT,
                text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("NULLSTRING_PASS", result.stdout)

    def test_validator_is_one_process_read_only_and_self_validates(self) -> None:
        compile(self.validator, str(VALIDATOR), "exec")
        for token in (
            "prepare_cairnwell_2040_runtime_v001_recovery_v013",
            "core.validate_all_assets", "require_persisted_dependencies=True",
            "recovery.validate_v013_receipt",
            "recovery.verify_legacy_cache_deletion_surface_absent",
            "cache_after != cache_before",
            "legacy_cache_absence_after != legacy_cache_absence_before",
            "LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_VALIDATION_PASS",
        ):
            self.assertIn(token, self.validator)
        for forbidden in (
            "AssetImportTask", "import_asset_tasks", "import_lod", "save_asset",
            "save_loaded_asset", "delete_asset", "rename_asset", "quit_editor",
        ):
            self.assertNotIn(forbidden, self.validator)
        self.assertEqual(self.validator.count("core.write_json("), 2)

    def test_runner_is_one_validator_no_content_mutation_and_fail_closed(self) -> None:
        for token in (
            recovery.RUN_ACK_TOKEN, "Invoke-GuardedValidator",
            "--verify-pre-validation", "--verify-post-validation", "--verify-final",
            "UE_SKIP_UBT_SDK_SETUP", "-NoAssetRegistryCacheWrite",
            "Get-CimInstance Win32_Process", "UnrealBuildTool.dll",
            "/Engine/Maps/Entry", "-NoCompile", "-NoAutoSave", "-NoSaveOnExit",
        ):
            self.assertIn(token, self.runner)
        for forbidden in (
            "ConvertFrom-Json -AsHashtable", "ConvertFrom-Json -AsHashTable",
            ".PSObject.Properties", "Move-Item", "Copy-Item", "Remove-Item",
            "import_cairnwell_2040_runtime_v001.py", "quit_editor",
        ):
            self.assertNotIn(forbidden, self.runner)
        self.assertEqual(self.runner.count("Start-Process -FilePath $Editor"), 1)
        self.assertEqual(self.runner.count("ConvertFrom-Json"), 1)
        restoration = self.runner.index("$Summary.environment_restoration_verified =")
        pass_status = self.runner.index("$Summary.status = $SummaryPass")
        final_verify = self.runner.index(
            "$FinalVerify = Invoke-RecoveryVerify '--verify-final'")
        pass_output = self.runner.index(
            "Write-Output 'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_")
        self.assertLess(restoration, pass_status)
        self.assertLess(pass_status, final_verify)
        self.assertLess(final_verify, pass_output)
        self.assertEqual(self.runner.count(
            "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_"), 2)

    def test_receipt_summary_contract_and_tamper_regressions_are_strict(self) -> None:
        self.assertEqual(self.candidate["lane"]["file_count"], 69)
        self.assertFalse(self.candidate["policy"]["v012_rerun_authorized"])
        self.assertFalse(self.candidate["policy"]["quarantine_move_authorized"])
        self.assertTrue(
            self.candidate["policy"]["legacy_cache_deletion_surface_absence_required"])
        recovery.run_synthetic_regressions(self.candidate, self.state)
        root = recovery.exact_v013_run_root(
            str(recovery.RECOVERY_AUDIT_ROOT / "20260815T170000Z-deadbeef"),
            require_exists=False)
        receipt = recovery.receipt_fixture(self.candidate, self.state, root, 424244)
        bad_legacy = copy.deepcopy(receipt)
        bad_legacy["legacy_asset_registry_cache_mutation_count"] = True
        with self.assertRaises(recovery.RecoveryError):
            recovery.validate_v013_receipt(bad_legacy, self.candidate, self.state, root)
        with self.assertRaises(recovery.RecoveryError):
            recovery.strict_json_text('{"a":1,"a":2}')

    def test_model_identity_is_stable_and_visual_authority_is_revisionable(self) -> None:
        identity = self.candidate["vehicle_model_identity"]
        self.assertEqual(identity["model_id"], "CAIRNWELL_2040")
        self.assertEqual(
            identity["production_recipe_id"],
            "CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001")
        self.assertEqual(
            identity["current_geometry_authority_id"],
            "Cairnwell2040Runtime_v001_V009ImportedGeometry")
        self.assertFalse(identity["final_release_visual_lock_claimed"])
        self.assertNotEqual(identity["model_id"], identity["current_geometry_authority_id"])

    def test_python_and_powershell_sources_parse(self) -> None:
        compile(self.preparer, str(PREPARER), "exec")
        for shell, marker in (
                (WINDOWS_POWERSHELL, "PS51_V013_PARSE_PASS"),
                (PWSH, "PS7_V013_PARSE_PASS")):
            if not shell.is_file():
                continue
            command = (
                "$e=$null; [System.Management.Automation.Language.Parser]::ParseFile("
                f"'{RUNNER}',[ref]$null,[ref]$e)|Out-Null; "
                "if($e.Count){$e|ForEach-Object{$_.Message};exit 1}; "
                f"Write-Output '{marker}'")
            result = subprocess.run(
                [str(shell), "-NoProfile", "-Command", command], cwd=PROJECT,
                text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(marker, result.stdout)

    def test_offline_dry_build_or_frozen_prevalidation_is_no_write(self) -> None:
        self.assertEqual(CONTRACT.exists(), SIDECAR.exists())
        if CONTRACT.exists():
            mode = "--verify-pre-validation"
            marker = recovery.PRE_VALIDATION_PASS
        else:
            mode = "--dry-build"
            marker = (
                "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_"
                "NO_WRITE_FULL_PAYLOAD_PREFLIGHT")
        result = subprocess.run(
            [sys.executable, "-B", str(PREPARER), mode], cwd=PROJECT,
            text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(marker, result.stdout)
        self.assertFalse(V013_ROOT.exists())
        if CONTRACT.exists():
            digest = sha(CONTRACT)
            self.assertEqual(
                SIDECAR.read_text(encoding="ascii"),
                f"{digest}  {CONTRACT.name}\n")

    def test_document_is_truthful_validation_only_development_handoff(self) -> None:
        for token in (
            "V012 is never rerun or rewritten", "does not retroactively call",
            "exactly one PreLoad cleanup line", "exactly one PostWrite cleanup line",
            "zero orphans deleted", "zero orphans locked",
            "`Intermediate/CachedAssetRegistry.bin`",
            "`[System.Management.Automation.Language.NullString]::Value`",
            "stable `CAIRNWELL_2040`", "approved for DEVELOPMENT game builds",
            "remains revisionable, not final-release art", "launches no importer",
            "Contract creation authorizes no Unreal or UBT launch",
        ):
            self.assertIn(token, self.doc)


if __name__ == "__main__":
    unittest.main()
