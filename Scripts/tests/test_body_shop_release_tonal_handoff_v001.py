"""Regression tests for the release runner's tonal-analysis subprocess handoff."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[2]
RUNNER = PROJECT / "Scripts" / "run_body_shop_release_validation_v001.ps1"
ANALYZER = PROJECT / "Scripts" / "analyze_body_shop_visual_readability_v004.py"
POWERSHELL = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
UE_PYTHON = Path(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe"
)
TONAL_PYTHON = Path(
    r"C:\Users\greg_\AppData\Local\Programs\Python\Python313\python.exe"
)
TONAL_PYTHON_DLL = TONAL_PYTHON.with_name("python313.dll")
EXPECTED_TONAL_PYTHON_SHA256 = (
    "D87063E5597F257004C731B66C59C56C91038861C6877B1A3DCA6B8C4E919125"
)
EXPECTED_TONAL_PYTHON_DLL_SHA256 = (
    "69FD86EA29370697C203F7E12830084F920F490766A8E3045AF52C036A9AD529"
)
RELEASE_RUN = "20260814T232505Z"
CAPTURE_DIR = (
    PROJECT / "Saved" / "ValidationScreenshots" / "BodyShop" / "Experimental_v001"
    / "ReleaseValidation" / RELEASE_RUN
)
LIVE_RECEIPT = (
    PROJECT / "Saved" / "Audits" / "BodyShop" / "Experimental_v001"
    / "ReleaseValidation" / RELEASE_RUN / "live_pie_release_validation_v003.json"
)
EXPECTED_CAPTURE_HASHES = {
    "overview": "8E71E86BA113306CAFFB156C98A32FEAB10D60E485BFA4FFC5EE194ACBAD02A9",
    "fixture": "C3AE4E41EFC0C5CAD30A5BE93FF5C9BF6278509E1D460C78F3291D23379B710F",
}
EXPECTED_GATE_ACTUALS = {
    "overview_p90": 0.509804,
    "fixture_p90": 0.52549,
    "overview_middle_lower_fraction_over_0_75": 0.000792,
    "fixture_middle_lower_fraction_over_0_75": 0.000661,
    "overview_empty_aisle_floor_mean": 0.362914,
}


def ps_literal(value: Path | str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def run_windows_powershell(source: str) -> subprocess.CompletedProcess[str]:
    encoded = base64.b64encode(source.encode("utf-16-le")).decode("ascii")
    return subprocess.run(
        [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        text=True,
        capture_output=True,
        check=False,
    )


@unittest.skipUnless(
    POWERSHELL.is_file() and UE_PYTHON.is_file() and TONAL_PYTHON.is_file(),
    "Windows UE and pinned tonal Python toolchains required",
)
class TonalHandoffTests(unittest.TestCase):
    def test_filter_zero_through_four_rgba_self_test_on_available_python_runtimes(self) -> None:
        runtimes = {str(path.resolve()): path for path in (Path(sys.executable), UE_PYTHON, TONAL_PYTHON)}
        for runtime in runtimes.values():
            with self.subTest(runtime=str(runtime)):
                result = subprocess.run(
                    [str(runtime), str(ANALYZER), "--self-test"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(
                    payload["status"], "PASS__PNG_DECODER_AND_TONAL_METRIC_SELF_TEST"
                )
                self.assertEqual(payload["metrics"]["sample_count"], 15)

    @unittest.skipUnless(
        CAPTURE_DIR.is_dir() and LIVE_RECEIPT.is_file(),
        "preserved 20260814T232505Z release captures required",
    )
    def test_exact_release_captures_pass_with_both_native_streams_redirected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="LineBossTonalExactCapture_") as temporary:
            for iteration in range(3):
                output = Path(temporary) / f"tonal_analysis_{iteration}.json"
                result = subprocess.run(
                    [
                        str(TONAL_PYTHON),
                        str(ANALYZER),
                        "--capture-dir",
                        str(CAPTURE_DIR),
                        "--live-receipt",
                        str(LIVE_RECEIPT),
                        "--output",
                        str(output),
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(output.is_file())
                payload = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(
                    payload["status"], "PASS__BODYSHOP_VISUAL_READABILITY_V004_TONAL_GATES"
                )
                self.assertEqual(payload["failures"], [])
                self.assertEqual(payload["runtime"]["python_version"], "3.13.3")
                self.assertEqual(
                    payload["runtime"]["executable_sha256"], EXPECTED_TONAL_PYTHON_SHA256
                )
                self.assertEqual(
                    payload["runtime"]["runtime_library_sha256"],
                    EXPECTED_TONAL_PYTHON_DLL_SHA256,
                )
                self.assertEqual(
                    {
                        name: payload["captures"][name]["sha256"]
                        for name in EXPECTED_CAPTURE_HASHES
                    },
                    EXPECTED_CAPTURE_HASHES,
                )
                self.assertEqual(
                    {gate["name"]: gate["actual"] for gate in payload["gates"]},
                    EXPECTED_GATE_ACTUALS,
                )
                self.assertTrue(all(gate["passed"] for gate in payload["gates"]))

    def test_full_gate_rejects_unsafe_ue_python_before_decoding(self) -> None:
        with tempfile.TemporaryDirectory(prefix="LineBossTonalUnsafeRuntime_") as temporary:
            output = Path(temporary) / "must_not_exist.json"
            result = subprocess.run(
                [
                    str(UE_PYTHON), str(ANALYZER),
                    "--capture-dir", str(CAPTURE_DIR),
                    "--live-receipt", str(LIVE_RECEIPT),
                    "--output", str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("full tonal analysis requires CPython 3.13+", result.stderr)
            self.assertFalse(output.exists())

    def test_runner_parses_and_has_fail_closed_stable_logged_handoff(self) -> None:
        text = RUNNER.read_text(encoding="utf-8-sig")
        self.assertIn("function Wait-StableLeaf", text)
        self.assertIn("Assert-TonalInputsStable $Live $StableLiveReceiptSha256", text)
        self.assertIn("Start-Process -FilePath $TonalPython", text)
        self.assertIn(EXPECTED_TONAL_PYTHON_SHA256, text)
        self.assertIn(EXPECTED_TONAL_PYTHON_DLL_SHA256, text)
        self.assertIn("-RedirectStandardOutput $StdoutLog", text)
        self.assertIn("-RedirectStandardError $StderrLog", text)
        self.assertNotIn("& $Python $TonalAnalyzer", text)

        parse = run_windows_powershell(
            "$tokens=$null;$errors=$null;"
            f"[void][System.Management.Automation.Language.Parser]::ParseFile({ps_literal(RUNNER)},[ref]$tokens,[ref]$errors);"
            "if($errors.Count){$errors|%{$_.Message};exit 1};'PASS__POWERSHELL_AST_PARSE'"
        )
        self.assertEqual(parse.returncode, 0, parse.stdout + parse.stderr)
        self.assertIn("PASS__POWERSHELL_AST_PARSE", parse.stdout)

    def test_native_stderr_is_retained_instead_of_becoming_native_command_error(self) -> None:
        with tempfile.TemporaryDirectory(prefix="LineBossTonalHandoff_") as temporary:
            temporary_path = Path(temporary)
            logs = temporary_path / "logs"
            output = temporary_path / "must_not_exist.json"
            script = f"""
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile({ps_literal(RUNNER)},[ref]$tokens,[ref]$errors)
if($errors.Count){{throw ($errors|Out-String)}}
$node=@($ast.FindAll({{param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Invoke-TonalAnalyzer'}},$true))
if($node.Count -ne 1){{throw 'Invoke-TonalAnalyzer function inventory mismatch'}}
Invoke-Expression $node[0].Extent.Text
$Root={ps_literal(PROJECT)}
$TonalPython={ps_literal(TONAL_PYTHON)}
$Logs={ps_literal(logs)}
$CaptureDir={ps_literal(temporary_path / 'missing captures')}
$LiveReceipt={ps_literal(temporary_path / 'missing receipt.json')}
New-Item -ItemType Directory -Force -Path $Logs|Out-Null
$caught=$false
try {{ Invoke-TonalAnalyzer {ps_literal(ANALYZER)} {ps_literal(output)} }} catch {{
    $caught=$true
    if($_.Exception.Message -notmatch '\\(2\\).*full stdout/stderr'){{throw "wrong failure surface: $($_.Exception.Message)"}}
}}
if(-not $caught){{throw 'expected analyzer failure was not surfaced'}}
$stderr=Get-Content -Raw -LiteralPath (Join-Path $Logs 'visual_readability_v004_tonal_analysis.stderr.log')
$combined=Get-Content -Raw -LiteralPath (Join-Path $Logs 'visual_readability_v004_tonal_analysis.log')
if($stderr -notmatch 'BODYSHOP_VISUAL_READABILITY_V004_TONAL_ANALYSIS_ERROR'){{throw 'stderr diagnostic missing'}}
if($combined -notmatch '=== stderr ==='){{throw 'combined diagnostic missing stderr section'}}
if(Test-Path -LiteralPath {ps_literal(output)}){{throw 'failure unexpectedly produced a receipt'}}
'PASS__NATIVE_STDERR_RETAINED_AND_EXIT_CODE_SURFACED'
"""
            result = run_windows_powershell(script)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(
                "PASS__NATIVE_STDERR_RETAINED_AND_EXIT_CODE_SURFACED", result.stdout
            )


if __name__ == "__main__":
    unittest.main()
