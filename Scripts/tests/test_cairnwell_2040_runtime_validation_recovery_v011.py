from __future__ import annotations

import copy
import hashlib
import pathlib
import subprocess
import sys
import unittest


PROJECT = pathlib.Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = PROJECT / "Scripts"
DOC = PROJECT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011.md"
PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v011.py"
VALIDATOR = SCRIPTS / "validate_cairnwell_2040_runtime_recovery_v011.py"
RUNNER = SCRIPTS / "run_cairnwell_2040_runtime_validation_recovery_v011.ps1"
CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v011_contract.json"
SIDECAR = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v011_contract.sha256"
V010_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v010_contract.json"
V010_SIDECAR = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v010_contract.sha256"
V010_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v010")
V011_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v011")
WINDOWS_POWERSHELL = pathlib.Path(
    r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
V010_BOUND = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010.md":
        "1270C114F40DCEF3FD3BD2FD6515393F0C16FD5CCC8ECDDABAA59DB7EDB3313D",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v010.py":
        "96BF56E469FD4E1F03743DAC396DA6A75FFD2D6CA26D8D2FFD9EEA3DFB6E9BAC",
    "Scripts/validate_cairnwell_2040_runtime_recovery_v010.py":
        "7FCDA03BF0C70EEFA0C6594F16420119B1E5C6CCA75377C8F5D50891F5D24969",
    "Scripts/run_cairnwell_2040_runtime_validation_recovery_v010.ps1":
        "2688903AA069F38CE7345BA7DD0B77D34C18147A4CF8AA7E7AE40F7C5C3F23E6",
    "Scripts/tests/test_cairnwell_2040_runtime_validation_recovery_v010.py":
        "1D055C748E1C34E094599CA7468230A01F643E775CD83466BB5824DE159C81D9",
    "Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py":
        "E4DBE0C16B7CAAD006EE901EC57F042661CDCD276F85D22F4CE36393C5991101",
}


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


sys.path.insert(0, str(SCRIPTS))
import prepare_cairnwell_2040_runtime_v001_recovery_v011 as recovery


class CairnwellValidationRecoveryV011Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preparer = PREPARER.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_stale_v010_pair_and_bound_sources_are_byte_exact_unexecuted(self) -> None:
        self.assertEqual(V010_CONTRACT.stat().st_size, 155045)
        self.assertEqual(
            sha(V010_CONTRACT),
            "CBE1DA417B4009F188E9D35D13402AEA1C7D0CAB9A3EED041ED57F20DA4ADF45")
        self.assertEqual(V010_SIDECAR.stat().st_size, 122)
        self.assertEqual(
            sha(V010_SIDECAR),
            "0FAA9591022AB275E88BE0DFBDD201BC39FA2BDB69200AA4C345DFBED5ED1C5A")
        self.assertFalse(V010_ROOT.exists())
        for relative, expected in V010_BOUND.items():
            self.assertEqual(sha(PROJECT / relative), expected, relative)

    def test_preparer_is_additive_no_write_and_reconstructs_exact_55_file_lane(self) -> None:
        compile(self.preparer, str(PREPARER), "exec")
        for token in (
            "V011_ADDITIONS =", "snapshot[\"file_count\"] != 55",
            "stale_unexecuted_v010", "recovery_v010_result_root_absent",
            "PROVISIONAL_GAME_BUILD__REVISIONABLE_BEFORE_FINAL_RELEASE",
            "runtime_asset_identity_decoupled_from_visual_geometry_revision",
            '"final_release_visual_lock_claimed": False',
            "run_synthetic_binding_regressions(payload, state)",
            "object_hash(payload) != object_hash(build_candidate_payload(state, generated))",
            "refusing to overwrite v011 recovery contract or sidecar",
            "--dry-build", "--verify-pre-validation", "--verify-final",
        ):
            self.assertIn(token, self.preparer)
        for forbidden in (
            "shutil.rmtree", "unlink(", "replace(", "os.remove", "rmdir(",
        ):
            self.assertNotIn(forbidden, self.preparer)

    def test_strict_parser_and_synthetic_tamper_regressions_fail_closed(self) -> None:
        with self.assertRaises(recovery.RecoveryError):
            recovery.strict_json_text('{"a":1,"a":2}')
        with self.assertRaises(recovery.RecoveryError):
            recovery.strict_json_text('{"":1,"":2}')
        state = recovery.authority_state()
        contract = recovery.build_candidate_payload(
            state, recovery.candidate_generated_utc(state))
        recovery.run_synthetic_binding_regressions(contract, state)
        fake_root = recovery.exact_v011_run_root(
            str(recovery.RECOVERY_AUDIT_ROOT / "20260815T150000Z-deadbeef"),
            require_exists=False)
        receipt = recovery.receipt_fixture(contract, state, fake_root, 424242)
        receipt["baseline_sha256"] = "0" * 64
        with self.assertRaises(recovery.RecoveryError):
            recovery.validate_v011_receipt(receipt, contract, state, fake_root)
        boolean_numeric = copy.deepcopy(contract)
        boolean_numeric["result_topology"]["import_process_count"] = False
        with self.assertRaises(recovery.RecoveryError):
            recovery.validate_candidate_payload(boolean_numeric, state)

    def test_receipt_binding_is_complete_and_exact(self) -> None:
        for token in (
            "contract_sha256", "baseline_sha256", "v010_recovery_contract_sha256",
            "v009_quarantine_receipt_sha256", "v009_wrapper_failure_classification",
            "v009_wrapper_incident_binding_sha256", "incident_chain_sha256",
            "quarantine_receipt", "ENGINE_VERSION_PREFIX",
            "object_hash(payload) != object_hash(expected)",
            "exact chronology/content drift", "prior.expected_fresh_assets",
        ):
            self.assertIn(token, self.preparer)

    def test_summary_binding_is_complete_and_tamper_paths_are_explicit(self) -> None:
        for token in (
            '"acknowledgement": RUN_ACK_TOKEN', '"run_root": str(run_root)',
            '"destination": str(prior.DEST)', '"contract_sha256": state["contract_digest"]',
            '"baseline_sha256": state["baseline_digest"]',
            '"v009_run_id": prior.V009_RUN_ID',
            '"path": str(run_root / VALIDATION_RECEIPT)',
            "PRE_VALIDATION_PASS + \"\\n\" + recovery_sha",
            "POST_VALIDATION_PASS + \"\\n\" + receipt_sha256",
            "exact_iso_utc(summary.get(\"generated_utc\")",
            "missing summary acknowledgement", "wrong summary receipt path",
            "object_hash(summary) != object_hash(expected)",
        ):
            self.assertIn(token, self.preparer)

    def test_validator_is_read_only_and_self_validates_complete_receipt(self) -> None:
        compile(self.validator, str(VALIDATOR), "exec")
        for token in (
            "recovery.load_frozen()", "core.validate_all_assets",
            "require_persisted_dependencies=True", "recovery.validate_v011_receipt",
            "v010_recovery_contract_sha256", "v009_quarantine_receipt_sha256",
            "v009_wrapper_failure_classification", "incident_chain_sha256",
            "UE_SKIP_UBT_SDK_SETUP",
            "LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_VALIDATION_PASS",
        ):
            self.assertIn(token, self.validator)
        for forbidden in (
            "AssetImportTask", "import_asset_tasks", "import_lod", "save_asset",
            "save_loaded_asset", "delete_asset", "rename_asset", "quit_editor",
        ):
            self.assertNotIn(forbidden, self.validator)
        self.assertEqual(self.validator.count("core.write_json("), 2)

    def test_runner_is_ps51_one_validator_no_import_move_or_receipt_parse(self) -> None:
        for token in (
            "VALIDATE_CAIRNWELL_2040_RUNTIME_V001_V009_IMPORT_V011_ONCE",
            "Invoke-GuardedValidator", "--verify-pre-validation",
            "--verify-post-validation", "--verify-final", "UE_SKIP_UBT_SDK_SETUP",
            "Get-CimInstance Win32_Process", "UnrealBuildTool.dll",
            "Launching UnrealBuildTool", "-Mode=ValidatePlatforms", "AutoSDKInfo.txt",
            "Name = $RunEnvironment; Value = $OldRunEnvironment",
            "SetEnvironmentVariable($Row.Name, $Row.Value, 'Process')",
            "environment_restoration_verified", "/Engine/Maps/Entry",
            "-NoCompile", "-NoCompileEditor", "-NoAutoSave", "-NoSaveOnExit",
        ):
            self.assertIn(token, self.runner)
        for forbidden in (
            "ConvertFrom-Json -AsHashtable", "ConvertFrom-Json -AsHashTable",
            "Read-Receipt", ".PSObject.Properties", "Move-Item", "Copy-Item",
            "Remove-Item", "import_cairnwell_2040_runtime_v001.py", "quit_editor",
        ):
            self.assertNotIn(forbidden, self.runner)
        self.assertEqual(self.runner.count("Start-Process -FilePath $Editor"), 1)
        self.assertEqual(self.runner.count("ConvertFrom-Json"), 1)

    def test_runner_pass_summary_lifecycle_is_fail_closed(self) -> None:
        restoration = self.runner.index("$Summary.environment_restoration_verified =")
        early_failure = self.runner.index("if ($null -ne $CaughtError)")
        pass_status = self.runner.index("$Summary.status = $SummaryPass")
        final_verify = self.runner.index(
            "$FinalVerify = Invoke-RecoveryVerify '--verify-final'")
        final_catch = self.runner.index("catch {", final_verify)
        pass_output = self.runner.index(
            "Write-Output 'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_"
            "VALIDATION_ONLY_LANE'")
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

    def test_windows_powershell_51_parses_and_has_no_as_hashtable(self) -> None:
        command = (
            "$e=$null; [System.Management.Automation.Language.Parser]::ParseFile("
            f"'{RUNNER}',[ref]$null,[ref]$e)|Out-Null; "
            "if($e.Count){$e|ForEach-Object{$_.Message};exit 1}; "
            "$has=[bool]((Get-Command ConvertFrom-Json).Parameters.ContainsKey('AsHashtable')); "
            "if($has){exit 2}; Write-Output 'PS51_V011_PARSE_PASS'")
        result = subprocess.run(
            [str(WINDOWS_POWERSHELL), "-NoProfile", "-Command", command],
            cwd=PROJECT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PS51_V011_PARSE_PASS", result.stdout)

    def test_offline_no_write_preflight_or_frozen_prevalidation_passes(self) -> None:
        self.assertEqual(CONTRACT.exists(), SIDECAR.exists())
        if CONTRACT.exists():
            mode = "--verify-pre-validation"
            marker = recovery.PRE_VALIDATION_PASS
        else:
            mode = "--dry-build"
            marker = (
                "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V011_"
                "NO_WRITE_FULL_PAYLOAD_PREFLIGHT")
        result = subprocess.run(
            [sys.executable, "-B", str(PREPARER), mode], cwd=PROJECT,
            text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(marker, result.stdout)
        self.assertFalse(V010_ROOT.exists())
        self.assertFalse(V011_ROOT.exists())
        if CONTRACT.exists():
            digest = sha(CONTRACT)
            self.assertEqual(
                SIDECAR.read_text(encoding="ascii"),
                f"{digest}  {CONTRACT.name}\n")
            payload = recovery.strict_json_file(CONTRACT)
            self.assertEqual(payload["lane"]["file_count"], 55)
            self.assertEqual(payload["result_topology"]["unreal_process_count"], 1)
            self.assertEqual(payload["result_topology"]["import_process_count"], 0)

    def test_document_records_stale_v010_and_exact_validation_only_guards(self) -> None:
        for token in (
            "V010 is therefore preserved byte-for-byte as stale, unexecuted chronology",
            "does not edit any V010-bound file", "exactly one full `UnrealEditor.exe`",
            "compared as a complete object", "missing acknowledgement",
            "wrong receipt path", "UE_SKIP_UBT_SDK_SETUP=1",
            "PASS marker is emitted only after the final five-file verifier",
            "Contract cut still authorizes no Unreal or UBT launch",
            "approved for the game build, not visually locked for final",
            "explicitly provisional and revisionable",
        ):
            self.assertIn(token, self.doc)


if __name__ == "__main__":
    unittest.main()
