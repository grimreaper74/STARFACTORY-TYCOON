"""Offline regression for the preserved OneFactory Slate-size incidents.

This suite never imports Unreal, starts UE, or invokes the one-use recovery.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re
import struct
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "Scripts/validate_one_factory_actual_player_pie_v001.py"
RUNNER = ROOT / "Scripts/run_one_factory_actual_player_pie_v001.ps1"
RECOVERY = ROOT / (
    "Scripts/recover_one_factory_actual_player_pie_ui_resolution_incident_"
    "20260815T031021499Z_v005.ps1"
)
REJECTED_V003 = ROOT / (
    "Scripts/recover_one_factory_actual_player_pie_ui_resolution_incident_"
    "20260815T024250499Z_v003.ps1"
)
FAILED_V004 = ROOT / (
    "Scripts/recover_one_factory_actual_player_pie_ui_resolution_incident_"
    "20260815T024250499Z_v004.ps1"
)
PS51_PNG_REGRESSION = ROOT / (
    "Scripts/tests/test_one_factory_png_ihdr_parser_ps51_v004.ps1"
)
BRIDGE_H = ROOT / "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.h"
BRIDGE_CPP = ROOT / "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.cpp"
FIRST_RUN = ROOT / (
    "Saved/Audits/OneFactory/v001/ActualPlayerPIE/Runs/20260815T023449580Z"
)
SECOND_RUN = ROOT / (
    "Saved/Audits/OneFactory/v001/ActualPlayerPIE/Runs/20260815T024250499Z"
)
THIRD_RUN = ROOT / (
    "Saved/Audits/OneFactory/v001/ActualPlayerPIE/Runs/20260815T031021499Z"
)
FIRST_CAPTURES = ROOT / (
    "Saved/ValidationScreenshots/OneFactory/v001/ActualPlayerPIE/"
    "20260815T023449580Z"
)
SECOND_CAPTURES = ROOT / (
    "Saved/ValidationScreenshots/OneFactory/v001/ActualPlayerPIE/"
    "20260815T024250499Z"
)
THIRD_CAPTURES = ROOT / (
    "Saved/ValidationScreenshots/OneFactory/v001/ActualPlayerPIE/"
    "20260815T031021499Z"
)
FAILED_V004_EVIDENCE = ROOT / (
    "Saved/Audits/OneFactory/v001/ActualPlayerPIE/IncidentRecovery/"
    "Incident_20260815T024250499Z_v004"
)
ENGINE = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Source")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError(f"Not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


class OneFactoryUIResolutionIncidentV005(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8-sig")
        cls.recovery = RECOVERY.read_text(encoding="utf-8-sig")
        cls.rejected_v003 = REJECTED_V003.read_text(encoding="utf-8-sig")
        cls.failed_v004 = FAILED_V004.read_text(encoding="utf-8-sig")
        cls.ps51_png_regression = PS51_PNG_REGRESSION.read_text(
            encoding="utf-8-sig"
        )
        cls.bridge_h = BRIDGE_H.read_text(encoding="utf-8")
        cls.bridge_cpp = BRIDGE_CPP.read_text(encoding="utf-8")
        ast.parse(cls.validator, filename=str(VALIDATOR))

    def test_engine_source_proves_restricted_ui_uses_game_widget_geometry(self):
        viewport = (
            ENGINE / "Runtime/Engine/Private/GameViewportClient.cpp"
        ).read_text(encoding="utf-8")
        slate = (
            ENGINE / "Runtime/Slate/Private/Framework/Application/SlateApplication.cpp"
        ).read_text(encoding="utf-8")
        for token in (
            "FScreenshotRequest::ShouldShowUI()",
            "FScreenshotRequest::ShouldRestrictToGameViewport()",
            "GetGameViewportWidget()",
            "WindowRef = GameViewportWidgetPtr.ToSharedRef()",
            "FSlateApplication::Get().TakeScreenshot(WindowRef, Bitmap, Size)",
            "Using the full window size.",
        ):
            self.assertIn(token, viewport)
        for token in (
            "ArrangedWidget.Geometry.GetDrawSize()",
            "PrepareToTakeScreenshot(ScreenshotRect",
        ):
            self.assertIn(token, slate)
    def test_bridge_is_narrow_arranged_widget_resize_and_restricted_request(self):
        for token in (
            "ResizePIEWindowForGameWidgetSize",
            "GetPIEGameWidgetDrawSize",
            "RequestPIERestrictedUIScreenshot",
            "World->GetGameViewport()",
            "ViewportClient->GetGameViewportWidget()",
            "FindWidgetWindow(",
            "GetCachedGeometry().GetDrawSize()",
            "Window->ReshapeWindow(",
            "FScreenshotRequest::RequestScreenshot(",
            "FIntRect(),",
        ):
            self.assertIn(token, self.bridge_h + self.bridge_cpp)
        for forbidden in (
            "FImageUtils",
            "GetViewportScreenShot",
            "ResizeImage(",
            "CropImage(",
            "CompositeImage(",
            "SaveImage(",
            "SetViewportSize(",
        ):
            self.assertNotIn(forbidden, self.bridge_cpp)
        self.assertEqual(
            sha256(BRIDGE_H),
            "2C5442B15B94504CEA085A3F46F4740BCC4FD0A83CDE70DB37E3C7D0FC04673B",
        )
        self.assertEqual(
            sha256(BRIDGE_CPP),
            "849C7E1ACD6A02B27126831202E774E8C922E422050904EC3DF5349C6D01CA30",
        )
        self.assertRegex(
            self.bridge_cpp,
            r"FScreenshotRequest::RequestScreenshot\(\s*Filename,\s*true,\s*"
            r"false,\s*false,\s*FIntRect\(\),\s*true\s*\)",
        )
        self.assertIn(
            "CurrentWindowSize.X + static_cast<double>(Width - CurrentDrawSize.X)",
            self.bridge_cpp,
        )
        self.assertIn(
            "CurrentWindowSize.Y + static_cast<double>(Height - CurrentDrawSize.Y)",
            self.bridge_cpp,
        )

    def test_validator_waits_for_stable_arranged_size_then_requests_native_ui(self):
        for token in (
            "unreal.LBOneFactoryCaptureBridge.resize_pie_window_for_game_widget_size(",
            "unreal.LBOneFactoryCaptureBridge.get_pie_game_widget_draw_size(",
            "unreal.LBOneFactoryCaptureBridge.request_pie_restricted_ui_screenshot(",
            '"native_ui_capture_viewport_1920x1080"',
            '"resize_api": "SWindow.ReshapeWindow"',
            '"query_api": "SViewport.GetCachedGeometry().GetDrawSize"',
            '"arranged_game_widget": confirmed_size',
            '"native_umg_visible_after_resize": True',
            '"post_processing": False',
            "ui_resize_exact_since",
            "Native UMG was not visible after exact arranged-widget resize",
        ):
            self.assertIn(token, self.validator)
        self.assertGreaterEqual(
            self.validator.count(
                "unreal.LBOneFactoryCaptureBridge.get_pie_game_widget_draw_size("
            ),
            2,
        )
        self.assertNotIn("SHOT SHOWUI", self.validator)
        self.assertNotIn("source.replace(capture_path)", self.validator)

    def test_all_three_failed_runs_are_exact(self):
        first = {
            "Logs/actual_player_pie.stderr.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
            "Logs/actual_player_pie.stdout.log": (330166, "2837BEBA0056057B6339A8956604FA5191DA983B26E9C3D2D6F2AB84E2AF53E4"),
            "Logs/editor_build.stderr.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
            "Logs/editor_build.stdout.log": (1052, "5022D2EEC8BE9C89006E757795E19315E5A2F4D2A2421597452F676E90AA8C0B"),
            "one_factory_actual_player_pie_run_summary_v001.json": (31856, "51AE20C988345075EA7DAAD67E12C44D55CF3568C6A3988DD8188F9B1B62C169"),
            "one_factory_actual_player_pie_v001.json": (16518, "FBE5FA4EF00E365BB6101EF29D7C9510FDC4A6EC77418F5B9906CBDC13C518A5"),
        }
        second = {
            "Logs/actual_player_pie.stderr.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
            "Logs/actual_player_pie.stdout.log": (335102, "5A6A3C9B76D63E51DD4967039EB62A7AC77C0C352C6D0D7F6F0A234B7D6BC1B4"),
            "Logs/editor_build.stderr.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
            "Logs/editor_build.stdout.log": (1052, "752C3C7D5F9663B5CCDB0CB45A442A3435F337C44A114EC27EBD13186D761E58"),
            "one_factory_actual_player_pie_run_summary_v001.json": (31856, "4F1383241C962B664A8C7EFC8CD6A367FC785D1DB90DC20566D6AC7630FC0D5E"),
            "one_factory_actual_player_pie_v001.json": (35026, "FE9C50B9408ED279C50D762A1DF71BB78B9630B8EF11D911A80E0DF6B2001F19"),
        }
        third = {
            "Logs/actual_player_pie.stderr.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
            "Logs/actual_player_pie.stdout.log": (331660, "22C4BCA1F56577975E4452506A0C1E95324302AA3D0595B5C700F6BC5C7DA606"),
            "Logs/editor_build.stderr.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
            "Logs/editor_build.stdout.log": (7833, "01F7B6FEE6172B42BE889FCDD5326372BDA525A506411DCA4BD5BD4F7E569492"),
            "one_factory_actual_player_pie_run_summary_v001.json": (33397, "1F091680D688933ECEAD17AC7FC8E1F6B0BCCC3BE676085E1B402AA1E2B87CC9"),
            "one_factory_actual_player_pie_v001.json": (36495, "E981B74B9D740EAEBA52CF6EC234FB48F9755DCD5D50B8D2E9604ECC6252505D"),
        }
        for root, expected in (
            (FIRST_RUN, first),
            (SECOND_RUN, second),
            (THIRD_RUN, third),
        ):
            names = sorted(str(path.relative_to(root)).replace("\\", "/") for path in root.rglob("*") if path.is_file())
            self.assertEqual(names, sorted(expected))
            for name, (size, digest) in expected.items():
                path = root / name
                self.assertEqual(path.stat().st_size, size)
                self.assertEqual(sha256(path), digest)
        self.assertEqual(list(FIRST_CAPTURES.rglob("*")), [])

    def test_second_and_third_screenshots_pin_the_same_slate_geometry_fault(self):
        second_expected = {
            "01_empty_factory_management_overview.png": (1662302, "C9EB1B2AB86375C7CDF1EECF0A876872834D0C1B374B57ACB4798D8AFB8FE600", (1920, 1080)),
            "02_populated_press_starter_wide_overview.png": (1665220, "CDEF996D2A7A5933B3F0C8EB2FCA58A66624CE2E244F534CA764D7B92C104A3B", (1920, 1080)),
            "03_press_train_dispatch_agv_close.png": (2277618, "ED7D476C42FAE9AF1F757CA0238D691B5A33F0F49E6EF3A3801C499030C9BCFF", (1920, 1080)),
            "04_populated_press_starter_with_umg.png": (431899, "6120A5ECCDB3FA24D00251E92961FE623CBFE4B0E3B4C88AF362BAF8CCC8E11B", (1300, 740)),
        }
        third_expected = {
            "01_empty_factory_management_overview.png": (1663756, "1FDD542C869F4A3BACBA1D61FFDBCC9B3C37147AE5048508D18BED3F00C22DC5", (1920, 1080)),
            "02_populated_press_starter_wide_overview.png": (1669381, "FF81AE126A087AC9952422235A615EC79933E669640C1FCC18BCEF5436B25F08", (1920, 1080)),
            "03_press_train_dispatch_agv_close.png": (2357071, "B3E1BC0FE5959441EB0A0CB230BCCB46CE6AF57C9DD6A2DED47C6D9A403D3AD5", (1920, 1080)),
            "04_populated_press_starter_with_umg.png": (630835, "7DBD3120806F76763A78B92E6AA93F215C3E3F3137011F7909EF0ED017AE5DE8", (1300, 740)),
        }
        for root, expected in (
            (SECOND_CAPTURES, second_expected),
            (THIRD_CAPTURES, third_expected),
        ):
            self.assertEqual(sorted(path.name for path in root.iterdir()), sorted(expected))
            for name, (size, digest, dimensions) in expected.items():
                path = root / name
                self.assertEqual(path.stat().st_size, size)
                self.assertEqual(sha256(path), digest)
                self.assertEqual(png_size(path), dimensions)
        for run in (SECOND_RUN, THIRD_RUN):
            receipt = (run / "one_factory_actual_player_pie_v001.json").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                "OneFactory screenshot is not 1920x1080: 04_populated_press_starter_with_umg.png=[1300, 740]",
                receipt,
            )
            self.assertIn('"map_hash_unchanged": true', receipt)
            self.assertIn('"changes": []', receipt)
        third_receipt = (THIRD_RUN / "one_factory_actual_player_pie_v001.json").read_text(
            encoding="utf-8"
        )
        self.assertIn('"api": "FSceneViewport.SetViewportSize"', third_receipt)
        self.assertIn('"reflected_viewport": [\n          1920,\n          1080', third_receipt)

    def test_failed_v004_recovery_evidence_is_exact(self):
        expected = {
            "fresh_retry_console_v004.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
            "pre_retry_evidence_v004.json": (12615, "A12AEE0D655F689126803F272EAC543C933BD470CCE045AB13E0BF93CA9481F5"),
            "retry_summary_v004.json": (9411, "F689F33B4C411EB06553AAC6D14765042626C7F8426CC9DDD75B7A5BC925AD82"),
        }
        self.assertEqual(
            sorted(path.name for path in FAILED_V004_EVIDENCE.iterdir()),
            sorted(expected),
        )
        for name, (size, digest) in expected.items():
            path = FAILED_V004_EVIDENCE / name
            self.assertEqual(path.stat().st_size, size)
            self.assertEqual(sha256(path), digest)

    def test_one_use_recovery_is_hash_bound_and_nondestructive(self):
        self.assertEqual(self.recovery.count("& $PowerShellExe"), 1)
        for token in ("Remove-Item", "Move-Item", "Delete"):
            self.assertNotIn(token, self.recovery)
        for token in (
            "retry_invocation_limit = 1",
            "20260815T023449580Z",
            "20260815T024250499Z",
            "20260815T031021499Z",
            "FE9C50B9408ED279C50D762A1DF71BB78B9630B8EF11D911A80E0DF6B2001F19",
            "6120A5ECCDB3FA24D00251E92961FE623CBFE4B0E3B4C88AF362BAF8CCC8E11B",
            "E981B74B9D740EAEBA52CF6EC234FB48F9755DCD5D50B8D2E9604ECC6252505D",
            "7DBD3120806F76763A78B92E6AA93F215C3E3F3137011F7909EF0ED017AE5DE8",
            "SWindow.ReshapeWindow",
            "SViewport.GetCachedGeometry().GetDrawSize",
            "FScreenshotRequest.RequestScreenshot(bShowUI=true,bRestrictToGameViewport=true)",
            "rescale_crop_or_composite = $false",
            "ExpectedRejectedV003Sha256",
            "ExpectedFailedV004Sha256",
            "ExpectedParserRegressionSha256",
            "Assert-PreservedIncidents",
        ):
            self.assertIn(token, self.recovery)
        pins = {
            "ExpectedRunnerSha256": sha256(RUNNER),
            "ExpectedValidatorSha256": sha256(VALIDATOR),
            "ExpectedBridgeHeaderSha256": sha256(BRIDGE_H),
            "ExpectedBridgeSourceSha256": sha256(BRIDGE_CPP),
            "ExpectedRejectedV003Sha256": sha256(REJECTED_V003),
            "ExpectedFailedV004Sha256": sha256(FAILED_V004),
            "ExpectedParserRegressionSha256": sha256(PS51_PNG_REGRESSION),
        }
        for variable, digest in pins.items():
            match = re.search(rf"\${variable}\s*=\s*'([A-F0-9]{{64}})'", self.recovery)
            self.assertIsNotNone(match, variable)
            self.assertEqual(match.group(1), digest)

    def test_powershell_files_parse_without_execution(self):
        for path in (
            RUNNER,
            REJECTED_V003,
            FAILED_V004,
            RECOVERY,
            PS51_PNG_REGRESSION,
        ):
            command = (
                "$errors=$null;"
                "[void][System.Management.Automation.Language.Parser]::ParseFile("
                f"'{str(path).replace(chr(39), chr(39) * 2)}',"
                "[ref]$null,[ref]$errors);"
                "if($errors.Count){$errors|ForEach-Object ToString;exit 1}"
            )
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_png_headers_pass_under_windows_powershell_5_1(self):
        version = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "$PSVersionTable.PSVersion.Major",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(version.returncode, 0, version.stdout + version.stderr)
        self.assertEqual(version.stdout.strip(), "5")
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(PS51_PNG_REGRESSION),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "PASS__WINDOWS_POWERSHELL_5_1_PNG_IHDR_1920X1080_AND_1300X740_V004",
        )
        for token in (
            "(([uint32]$Header[16]) -shl 24)",
            "(([uint32]$Header[18]) -shl 8)",
            "(([uint32]$Header[22]) -shl 8)",
        ):
            self.assertIn(token, self.ps51_png_regression)


if __name__ == "__main__":
    unittest.main()
