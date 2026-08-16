from __future__ import annotations

import copy
import hashlib
import pathlib
import subprocess
import sys
import unittest


PROJECT = pathlib.Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = PROJECT / "Scripts"
DOC = PROJECT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012.md"
PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v012.py"
VALIDATOR = SCRIPTS / "validate_cairnwell_2040_runtime_recovery_v012.py"
RUNNER = SCRIPTS / "run_cairnwell_2040_runtime_validation_recovery_v012.ps1"
CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v012_contract.json"
SIDECAR = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v012_contract.sha256"
V011_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v011_contract.json"
V011_SIDECAR = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v011_contract.sha256"
V011_RUN = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v011/20260815T154711Z-18d3ce40")
V012_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v012")
WINDOWS_POWERSHELL = pathlib.Path(
    r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
PWSH = pathlib.Path(r"C:\Program Files\PowerShell\7\pwsh.exe")


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


sys.path.insert(0, str(SCRIPTS))
import prepare_cairnwell_2040_runtime_v001_recovery_v012 as recovery


class CairnwellValidationRecoveryV012Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preparer = PREPARER.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_v011_pair_and_consumed_five_file_failure_are_byte_exact(self) -> None:
        self.assertEqual(V011_CONTRACT.stat().st_size, 159507)
        self.assertEqual(
            sha(V011_CONTRACT),
            "09A223675EC26F93F85EA2BE8B97568014AA9073681094C46EE04BDADC18719F")
        self.assertEqual(V011_SIDECAR.stat().st_size, 122)
        self.assertEqual(
            sha(V011_SIDECAR),
            "B8343772ABCDF81909067CF8B9594B0817B7766AC53177716B2F8AA65385B8B4")
        snapshot = recovery.exact_v011_run_snapshot()
        self.assertEqual(snapshot["file_count"], 5)
        self.assertEqual({path.name for path in V011_RUN.iterdir()}, {
            "fresh_process_validation_failure_recovery_v011.json",
            "fresh_process_validation_recovery_v011.log",
            "fresh_process_validation_recovery_v011.stdout.log",
            "fresh_process_validation_recovery_v011.stderr.log",
            "lane_summary_recovery_v011.json",
        })
        v011, state = recovery.exact_v011_pair()
        incident = recovery.validate_v011_execution(v011, state)
        self.assertEqual(
            incident["asset_registry_cache_side_effect"]["classification"],
            "V011_READ_ONLY_CONTENT_VALIDATION_WROTE_PROJECT_ASSET_REGISTRY_"
            "CACHE_AND_DELETED_ONE_ORPHAN__V012_MUST_SUPPRESS_AND_PROVE_"
            "EXACT_CACHE_INVARIANCE")

    def test_six_persisted_dependency_lists_are_exact(self) -> None:
        _v011, state = recovery.exact_v011_pair()
        assets = recovery.corrected_fresh_assets(state)
        self.assertEqual(
            recovery.object_hash(assets),
            "7E8A56991C48F8AEC017C0B4308E220729388A076ABC17C731F70405243B985B")
        self.assertEqual(
            assets["materials"]["body"]["texture_dependencies"],
            recovery.TEXTURE_DEPENDENCIES)
        self.assertEqual(
            assets["materials"]["rolling_gear"]["texture_dependencies"],
            recovery.TEXTURE_DEPENDENCIES)
        for role, expected in recovery.MODULE_DEPENDENCIES.items():
            self.assertEqual(
                assets["modules"][role]["persisted_runtime_dependencies"], expected)
        self.assertEqual(len(recovery.MODULE_DEPENDENCIES), 4)

    def test_cache_snapshot_source_and_no_write_flag_are_exact(self) -> None:
        snapshot = recovery.verify_asset_registry_cache_snapshot()
        source = recovery.verify_asset_registry_cache_source()
        self.assertEqual(snapshot["file_count"], 2)
        self.assertEqual(
            snapshot["inventory_sha256"],
            "59DEFE0409EA024EA6FF7B4CF2B7FEF7CD8FC8D652EE356D76ACE7DC2767B3E9")
        self.assertEqual(
            source["sha256"],
            "9B62B0B7AFF852029CA82576570B5F9A9F3791E605667B1D20F0B7896511D6CC")
        for token in (
            "-NoAssetRegistryCacheWrite", "Asset registry cache written as",
            "deleted (orphaned", "CleanupOrphanedCacheFiles (PostWrite)",
            "asset_registry_cache_before", "asset_registry_cache_after",
            "asset_registry_cache_mutation_count",
        ):
            self.assertIn(token, self.preparer + self.validator + self.runner)

    def test_stable_model_id_is_separate_from_recipe_geometry_and_lifecycle(self) -> None:
        self.assertEqual(recovery.VEHICLE_MODEL_ID, "CAIRNWELL_2040")
        self.assertEqual(
            recovery.DEVELOPMENT_RECIPE_ID,
            "CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001")
        self.assertEqual(
            recovery.CURRENT_GEOMETRY_AUTHORITY_ID,
            "Cairnwell2040Runtime_v001_V009ImportedGeometry")
        for token in (
            '"model_identity_is_independent_of_current_asset_paths": True',
            '"current_asset_paths_are_revision_specific_bindings": True',
            '"final_release_visual_lock_claimed": False',
            '"lifecycle": "DEVELOPMENT__APPROVED_FOR_GAME_BUILD__NOT_FINAL_ART"',
        ):
            self.assertIn(token, self.preparer)
        self.assertNotEqual(recovery.VEHICLE_MODEL_ID, recovery.CURRENT_GEOMETRY_AUTHORITY_ID)

    def test_validator_is_one_process_read_only_and_self_validates(self) -> None:
        compile(self.validator, str(VALIDATOR), "exec")
        for token in (
            "prepare_cairnwell_2040_runtime_v001_recovery_v012",
            "core.validate_all_assets", "require_persisted_dependencies=True",
            "recovery.validate_v012_receipt", "recovery.verify_asset_registry_cache_snapshot",
            "len(cache_flag_matches) != 1", "cache_after != cache_before",
            "v011_failure_receipt_sha256", "current_geometry_authority_id",
            "LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_VALIDATION_PASS",
        ):
            self.assertIn(token, self.validator)
        for forbidden in (
            "AssetImportTask", "import_asset_tasks", "import_lod", "save_asset",
            "save_loaded_asset", "delete_asset", "rename_asset", "quit_editor",
        ):
            self.assertNotIn(forbidden, self.validator)
        self.assertEqual(self.validator.count("core.write_json("), 2)

    def test_runner_is_ps51_one_validator_no_content_mutation_and_cache_guarded(self) -> None:
        for token in (
            "VALIDATE_CAIRNWELL_2040_RUNTIME_V001_V009_IMPORT_V012_ONCE",
            "recovery-v012/validation-only-lane-summary/v12",
            "Invoke-GuardedValidator", "--verify-pre-validation",
            "--verify-post-validation", "--verify-final",
            "UE_SKIP_UBT_SDK_SETUP", "-NoAssetRegistryCacheWrite",
            "Get-CimInstance Win32_Process", "UnrealBuildTool.dll",
            "Name = $RunEnvironment; Value = $OldRunEnvironment",
            "SetEnvironmentVariable($Row.Name, $Row.Value, 'Process')",
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

    def test_runner_pass_lifecycle_rewrites_late_failure_summary(self) -> None:
        restoration = self.runner.index("$Summary.environment_restoration_verified =")
        early_failure = self.runner.index("if ($null -ne $CaughtError)")
        pass_status = self.runner.index("$Summary.status = $SummaryPass")
        final_verify = self.runner.index(
            "$FinalVerify = Invoke-RecoveryVerify '--verify-final'")
        final_catch = self.runner.index("catch {", final_verify)
        pass_output = self.runner.index(
            "Write-Output 'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_")
        self.assertLess(restoration, early_failure)
        self.assertLess(early_failure, pass_status)
        self.assertLess(pass_status, final_verify)
        self.assertLess(final_verify, final_catch)
        self.assertLess(final_catch, pass_output)
        for branch in (
                self.runner[early_failure:pass_status],
                self.runner[final_catch:pass_output]):
            self.assertIn("FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_", branch)
            self.assertIn("Write-Utf8Json $SummaryPath $Summary", branch)
            self.assertIn("throw", branch)

    def test_strict_receipt_summary_and_tamper_regressions(self) -> None:
        with self.assertRaises(recovery.RecoveryError):
            recovery.strict_json_text('{"a":1,"a":2}')
        state = recovery.authority_state()
        contract = recovery.build_candidate_payload(
            state, recovery.candidate_generated_utc(state))
        recovery.validate_candidate_payload(contract, state)
        fake_root = recovery.exact_v012_run_root(
            str(recovery.RECOVERY_AUDIT_ROOT / "20260815T160000Z-deadbeef"),
            require_exists=False)
        receipt = recovery.receipt_fixture(contract, state, fake_root, 424243)
        bad_cache = copy.deepcopy(receipt)
        bad_cache["asset_registry_cache_mutation_count"] = True
        with self.assertRaises(recovery.RecoveryError):
            recovery.validate_v012_receipt(bad_cache, contract, state, fake_root)
        wrong_model = copy.deepcopy(receipt)
        wrong_model["vehicle_model_id"] = wrong_model["current_geometry_authority_id"]
        with self.assertRaises(recovery.RecoveryError):
            recovery.validate_v012_receipt(wrong_model, contract, state, fake_root)

    def test_python_and_powershell_sources_parse(self) -> None:
        compile(self.preparer, str(PREPARER), "exec")
        for shell, marker in (
                (WINDOWS_POWERSHELL, "PS51_V012_PARSE_PASS"),
                (PWSH, "PS7_V012_PARSE_PASS")):
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
                "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V012_"
                "NO_WRITE_FULL_PAYLOAD_PREFLIGHT")
        result = subprocess.run(
            [sys.executable, "-B", str(PREPARER), mode], cwd=PROJECT,
            text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(marker, result.stdout)
        self.assertFalse(V012_ROOT.exists())
        if CONTRACT.exists():
            digest = sha(CONTRACT)
            self.assertEqual(
                SIDECAR.read_text(encoding="ascii"),
                f"{digest}  {CONTRACT.name}\n")
            payload = recovery.strict_json_file(CONTRACT)
            self.assertEqual(payload["lane"]["file_count"], 62)

    def test_document_is_truthful_validation_only_development_handoff(self) -> None:
        for token in (
            "V011 and its consumed five-file failed run remain byte-for-byte",
            "six lists are the only semantic difference",
            "`-NoAssetRegistryCacheWrite`", "exact two-file cache snapshot",
            "stable `CAIRNWELL_2040`", "not an asset path",
            "approved for DEVELOPMENT game builds", "not final-release art",
            "exactly one full `UnrealEditor.exe`", "launches no importer",
            "Contract creation authorizes no Unreal or UBT launch",
        ):
            self.assertIn(token, self.doc)


if __name__ == "__main__":
    unittest.main()
