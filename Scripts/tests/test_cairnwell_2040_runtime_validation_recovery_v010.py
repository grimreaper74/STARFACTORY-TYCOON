from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import unittest


PROJECT = pathlib.Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = PROJECT / "Scripts"
DOC = PROJECT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010.md"
PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v010.py"
VALIDATOR = SCRIPTS / "validate_cairnwell_2040_runtime_recovery_v010.py"
RUNNER = SCRIPTS / "run_cairnwell_2040_runtime_validation_recovery_v010.ps1"
CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v010_contract.json"
SIDECAR = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v010_contract.sha256"
V009_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v009_contract.json"
V009_SIDECAR = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v009_contract.sha256"
V009_RUN = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v009/20260815T141819Z-435fcd56")
V010_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001/Recovery_v010")
DEST = PROJECT / (
    "Content/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001")
Q6 = PROJECT / (
    "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T124823Z-67c989ee_v006")
WINDOWS_POWERSHELL = pathlib.Path(
    r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
V009_FILES = {
    "import_receipt_recovery_v009.json":
        "F11952FD07E9B573E0882059C49DF474E166CAE9B25F2F677023260ACAA413A6",
    "lane_summary_recovery_v009.json":
        "10025897FA49CDFFB94B37C78B082E0D43391E2062BC15BC426BF52C0E6E9265",
    "quarantine_receipt_v009.json":
        "AB17DB911591102E0EB01D0F3DEC56DE03DB51FCE05157739A642E4E796FD587",
    "unreal_import_recovery_v009.log":
        "976AEC6978AC412C81124B17980907DB77C6025481F2BCC96C45424E7F08F58E",
    "unreal_import_recovery_v009.stderr.log":
        "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    "unreal_import_recovery_v009.stdout.log":
        "FDEE3F83B570D7D42C0E79B7F341415C2E51EA35C9270EBDD2075AE1E4F0EA2C",
}


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def empty_paths(value, path=""):
    result = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f'{path}[""]' if key == "" else (f"{path}.{key}" if path else key)
            if key == "":
                result.append(child_path)
            result.extend(empty_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(empty_paths(child, f"{path}[{index}]"))
    return result


sys.path.insert(0, str(SCRIPTS))
import prepare_cairnwell_2040_runtime_v001_recovery_v010 as recovery_v010


class CairnwellValidationRecoveryV010Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preparer = PREPARER.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_v009_run_import_and_current_packages_are_exact(self) -> None:
        self.assertEqual(
            {path.name for path in V009_RUN.iterdir() if path.is_file()}, set(V009_FILES))
        for name, expected in V009_FILES.items():
            self.assertEqual(sha(V009_RUN / name), expected, name)
        imported = json.loads(
            (V009_RUN / "import_receipt_recovery_v009.json").read_text(encoding="utf-8"))
        summary = json.loads(
            (V009_RUN / "lane_summary_recovery_v009.json").read_text(encoding="utf-8"))
        self.assertEqual(
            empty_paths(imported),
            ['assets.materials.body.graph.detail_clamp.inputs[""]'])
        self.assertEqual(
            list(imported["assets"]["materials"]["body"]["graph"][
                "detail_clamp"]["inputs"]), ["", "Max", "Min"])
        self.assertEqual(imported["process_id"], 36612)
        self.assertEqual(imported["package_count"], 11)
        self.assertEqual(summary["import_process"]["exit_code"], 0)
        self.assertIsNone(summary["validation_process"])
        self.assertIn("-AsHashTable switch", summary["error"])
        actual = {
            rel: sha(PROJECT / rel)
            for rel in imported["namespace_disk_files"]
        }
        self.assertEqual(len(actual), 11)
        self.assertEqual(
            actual,
            {rel: row["sha256"]
             for rel, row in imported["namespace_disk_files"].items()})
        self.assertTrue(Q6.is_dir())

    def test_v009_ubt_contradiction_and_v010_source_guard_are_explicit(self) -> None:
        combined = (
            (V009_RUN / "unreal_import_recovery_v009.log").read_text(
                encoding="utf-8", errors="replace")
            + (V009_RUN / "unreal_import_recovery_v009.stdout.log").read_text(
                encoding="utf-8", errors="replace"))
        self.assertIn("Launching UnrealBuildTool...", combined)
        self.assertIn("Build.bat -Mode=ValidatePlatforms", combined)
        self.assertIn("UBT AutoSDK ReturnCode: 0", combined)
        source = pathlib.Path(
            r"C:\Program Files\Epic Games\UE_5.8\Engine\Source\Developer\TargetPlatform\Private\TargetPlatformManagerModule.cpp")
        self.assertEqual(source.stat().st_size, 61188)
        self.assertEqual(
            sha(source), "E86827925AECB8ED2250F5D7AB655269ED7FE6A83D6691B244FA36FAAD5A4E17")
        text = source.read_text(encoding="utf-8", errors="replace")
        self.assertIn('SkipUBTSDKSetupEnvVar = TEXT("UE_SKIP_UBT_SDK_SETUP")', text)
        self.assertIn("SkipUBTSDKSetupEnvVarValue == 1", text)

    def test_preparer_is_no_write_before_one_pair_cut_and_pins_empty_key(self) -> None:
        compile(self.preparer, str(PREPARER), "exec")
        for token in (
            "V009_RUN_FILES =", "V009_IMPORT_RECEIPT_SHA256",
            'V009_EMPTY_KEY_PATH = \'assets.materials.body.graph.detail_clamp.inputs[""]\'',
            "empty_key_paths(imported) != [V009_EMPTY_KEY_PATH]",
            "object_pairs_hook=strict_pairs", "duplicate JSON property is forbidden",
            'list(clamp_inputs) != ["", "Max", "Min"]',
            "verify_v009_quarantine", "verify_destination", "verify_v009_logs",
            "UE_SKIP_UBT_SDK_SETUP", "--dry-build", "--verify-pre-validation",
            "--verify-post-validation", "validate_candidate_payload(payload, state)",
            "--verify-final", "v010 final exact five-file closure drift",
            'newline="\\n"', "v010 prepared validation-only lane",
        ):
            self.assertIn(token, self.preparer)
        self.assertNotIn("shutil.rmtree", self.preparer)
        self.assertNotIn("unlink(", self.preparer)
        self.assertNotIn("replace(", self.preparer)
        self.assertNotIn("os.remove", self.preparer)

    def test_strict_json_parser_rejects_duplicate_normal_and_empty_keys(self) -> None:
        with self.assertRaises(recovery_v010.RecoveryError):
            recovery_v010.strict_json_text('{"a":1,"a":2}')
        with self.assertRaises(recovery_v010.RecoveryError):
            recovery_v010.strict_json_text('{"":1,"":2}')
        parsed = recovery_v010.strict_json_text(
            '{"inputs":{"":{},"Max":{},"Min":{}}}')
        self.assertEqual(list(parsed["inputs"]), ["", "Max", "Min"])

    def test_validator_is_read_only_and_loads_exact_v009_authority(self) -> None:
        compile(self.validator, str(VALIDATOR), "exec")
        for token in (
            "recovery.load_frozen()", "recovery.validate_v009_receipts",
            "core.validate_all_assets", "core.package_hashes",
            "core.namespace_inventory", "require_persisted_dependencies=True",
            "v009_import_receipt_sha256", "package_sha256_before_loads",
            "package_sha256_after_loads", "asset_mutation_count",
            "UE_SKIP_UBT_SDK_SETUP",
            "LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_VALIDATION_PASS",
        ):
            self.assertIn(token, self.validator)
        for forbidden in (
            "AssetImportTask", "import_asset_tasks", "import_lod", "save_asset",
            "save_loaded_asset", "delete_asset", "rename_asset", "quit_editor",
        ):
            self.assertNotIn(forbidden, self.validator)
        self.assertEqual(self.validator.count("core.write_json("), 2)

    def test_runner_is_ps51_compatible_one_validator_no_import_move_or_receipt_parse(self) -> None:
        for token in (
            "VALIDATE_CAIRNWELL_2040_RUNTIME_V001_V009_IMPORT_V010_ONCE",
            "Invoke-GuardedValidator", "--verify-pre-validation",
            "--verify-post-validation", "UE_SKIP_UBT_SDK_SETUP",
            "SetEnvironmentVariable($SkipUbtEnvironment, '1', 'Process')",
            "Name = $RunEnvironment; Value = $OldRunEnvironment",
            "Name = $AckEnvironment; Value = $OldAckEnvironment",
            "Name = $SkipUbtEnvironment; Value = $OldSkipUbtEnvironment",
            "foreach ($Row in $RestoreRows)",
            "SetEnvironmentVariable($Row.Name, $Row.Value, 'Process')",
            "$RestoreErrors +=",
            "Get-CimInstance Win32_Process", "UnrealBuildTool.dll",
            "Launching UnrealBuildTool", "-Mode=ValidatePlatforms", "AutoSDKInfo.txt",
            "UBT AutoSDK ReturnCode", "Assert-NoProcesses", "-NoCompile",
            "--verify-final", "environment_restoration_verified",
            "-NoCompileEditor", "-NoAutoSave", "-NoSaveOnExit", "/Engine/Maps/Entry",
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

    def test_runner_never_leaves_a_pass_summary_after_a_late_gate_failure(self) -> None:
        restore = self.runner.index("$RestoreRows = @(")
        restoration_gate = self.runner.index(
            "$Summary.environment_restoration_verified =")
        early_failure = self.runner.index("if ($null -ne $CaughtError)")
        pass_status = self.runner.index("$Summary.status = $SummaryPass")
        final_verify = self.runner.index(
            "$FinalVerify = Invoke-RecoveryVerify '--verify-final'")
        final_failure = self.runner.index("catch {", final_verify)
        pass_output = self.runner.index(
            "Write-Output 'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_"
            "VALIDATION_ONLY_LANE'")
        self.assertLess(restore, restoration_gate)
        self.assertLess(restoration_gate, early_failure)
        self.assertLess(early_failure, pass_status)
        self.assertLess(pass_status, final_verify)
        self.assertLess(final_verify, final_failure)
        self.assertLess(final_failure, pass_output)
        early_branch = self.runner[early_failure:pass_status]
        final_branch = self.runner[final_failure:pass_output]
        for branch in (early_branch, final_branch):
            self.assertIn("FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_", branch)
            self.assertIn("Write-Utf8Json $SummaryPath $Summary", branch)
            self.assertIn("throw", branch)
        self.assertEqual(self.runner.count("$Summary.status = $SummaryPass"), 1)
        self.assertEqual(
            self.runner.count("Write-Utf8Json $SummaryPath $Summary"), 3)

    def test_windows_powershell_51_parses_runner_and_has_no_as_hashtable(self) -> None:
        self.assertTrue(WINDOWS_POWERSHELL.is_file())
        command = (
            "$e=$null; [System.Management.Automation.Language.Parser]::ParseFile(" 
            f"'{RUNNER}',[ref]$null,[ref]$e)|Out-Null; "
            "if($e.Count){$e|ForEach-Object{$_.Message};exit 1}; "
            "$has=[bool]((Get-Command ConvertFrom-Json).Parameters.ContainsKey('AsHashtable')); "
            "if($has){exit 2}; Write-Output 'PS51_PARSE_NO_AS_HASHTABLE_PASS'")
        result = subprocess.run(
            [str(WINDOWS_POWERSHELL), "-NoProfile", "-Command", command],
            cwd=PROJECT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PS51_PARSE_NO_AS_HASHTABLE_PASS", result.stdout)

    def test_offline_no_write_preflight_or_frozen_prevalidation_passes(self) -> None:
        self.assertEqual(CONTRACT.exists(), SIDECAR.exists())
        if not CONTRACT.exists():
            mode = "--dry-build"
            marker = (
                "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_"
                "NO_WRITE_FULL_PAYLOAD_PREFLIGHT")
        else:
            mode = "--verify-pre-validation"
            marker = (
                "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_"
                "PRE_VALIDATION_REVERIFIED")
        result = subprocess.run(
            [sys.executable, "-B", str(PREPARER), mode], cwd=PROJECT,
            text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(marker, result.stdout)
        self.assertFalse(V010_ROOT.exists())
        if CONTRACT.exists():
            digest = sha(CONTRACT)
            self.assertEqual(
                SIDECAR.read_text(encoding="ascii"),
                f"{digest}  {CONTRACT.name}\n")
            payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
            self.assertEqual(payload["lane"]["file_count"], 48)
            self.assertEqual(payload["result_topology"]["unreal_process_count"], 1)
            self.assertEqual(payload["result_topology"]["import_process_count"], 0)

    def test_document_states_validation_only_and_no_launch_at_freeze(self) -> None:
        for token in (
            "does not import, reimport, save, move, copy, delete",
            'assets.materials.body.graph.detail_clamp.inputs[""]',
            "Windows PowerShell 5.1 does not provide that switch",
            "UE_SKIP_UBT_SDK_SETUP", "exactly one full `UnrealEditor.exe` process",
            "never invokes the v009 importer", "Contract freeze authorizes no Unreal or UBT launch",
        ):
            self.assertIn(token, self.doc)


if __name__ == "__main__":
    unittest.main()
