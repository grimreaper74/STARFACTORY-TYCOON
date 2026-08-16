"""Static/offline contract tests for the OneFactory actual-player PIE lane.

These tests deliberately do not import ``unreal`` and never launch Unreal.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "Scripts/validate_one_factory_actual_player_pie_v001.py"
RUNNER = ROOT / "Scripts/run_one_factory_actual_player_pie_v001.ps1"
RECOVERY = ROOT / (
    "Scripts/recover_one_factory_actual_player_pie_widget_lookup_incident_"
    "20260815T023449580Z_v002.ps1"
)
UI_RESOLUTION_RECOVERY = ROOT / (
    "Scripts/recover_one_factory_actual_player_pie_ui_resolution_incident_"
    "20260815T031021499Z_v005.ps1"
)
DOC = ROOT / "Docs/OneFactory/ONE_FACTORY_ACTUAL_PLAYER_PIE_V001.md"
FAILED_RUN = (
    ROOT
    / "Saved/Audits/OneFactory/v001/ActualPlayerPIE/Runs/20260815T023449580Z"
)

EXPECTED_MAP = (
    "/Game/LineBoss/Factory/OneFactory/v001/Maps/"
    "LB_MoorcrossWorks_OneFactory_v001"
)
EXPECTED_MAP_SHA256 = (
    "750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682"
)
EXPECTED_SHOTS = (
    "01_empty_factory_management_overview.png",
    "02_populated_press_starter_wide_overview.png",
    "03_press_train_dispatch_agv_close.png",
    "04_populated_press_starter_with_umg.png",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def assignment(tree: ast.Module, name: str):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                try:
                    return ast.literal_eval(node.value)
                except ValueError:
                    return eval(
                        compile(ast.Expression(node.value), str(VALIDATOR), "eval"),
                        {"__builtins__": {}},
                        {},
                    )
    raise AssertionError(f"Missing literal assignment {name}")


def call_name(node: ast.Call) -> str:
    parts = []
    value = node.func
    while isinstance(value, ast.Attribute):
        parts.append(value.attr)
        value = value.value
    if isinstance(value, ast.Name):
        parts.append(value.id)
    return ".".join(reversed(parts))


class OneFactoryActualPlayerPIEStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator_text = VALIDATOR.read_text(encoding="utf-8")
        cls.runner_text = RUNNER.read_text(encoding="utf-8-sig")
        cls.recovery_text = RECOVERY.read_text(encoding="utf-8-sig")
        cls.ui_resolution_recovery_text = UI_RESOLUTION_RECOVERY.read_text(
            encoding="utf-8-sig"
        )
        cls.doc_text = DOC.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.validator_text, filename=str(VALIDATOR))
        cls.calls = [
            call_name(node)
            for node in ast.walk(cls.tree)
            if isinstance(node, ast.Call)
        ]

    def test_python_is_parseable_and_frozen_map_is_exact(self):
        self.assertIsInstance(self.tree, ast.Module)
        self.assertEqual(assignment(self.tree, "MAP"), EXPECTED_MAP)
        self.assertEqual(
            assignment(self.tree, "EXPECTED_MAP_SHA256"), EXPECTED_MAP_SHA256
        )
        self.assertEqual(assignment(self.tree, "SCREENSHOT_NAMES"), EXPECTED_SHOTS)
        self.assertEqual(assignment(self.tree, "SCREENSHOT_SIZE"), (1920, 1080))
        self.assertEqual(assignment(self.tree, "MINIMUM_SCREENSHOT_BYTES"), 32768)
        self.assertIn(
            're.fullmatch(r"\\d{8}T\\d{6}(?:\\d{3})?Z", STAMP)',
            self.validator_text,
        )
        self.assertIn("Unsafe OneFactory actual-player run stamp", self.validator_text)

    def test_exact_roles_batches_and_native_engine_assets_are_static(self):
        stations = assignment(self.tree, "EXPECTED_STATIONS")
        batches = assignment(self.tree, "EXPECTED_BATCHES")
        self.assertEqual(len(stations), 7)
        self.assertEqual([row[2] for row in stations], [18, 37, 31, 34, 89, 19, 40])
        self.assertEqual(sum(row[2] for row in stations), 268)
        self.assertEqual(len(batches), 8)
        self.assertEqual(
            [row[1] for row in batches.values()], [32, 88, 34, 38, 18, 16, 8, 34]
        )
        self.assertEqual(sum(row[1] for row in batches.values()), 268)
        self.assertEqual(
            {row[2] for row in batches.values()},
            {
                "/Engine/BasicShapes/Cube.Cube",
                "/Engine/BasicShapes/Cylinder.Cylinder",
            },
        )
        self.assertIn(
            'EXPECTED_BASE_MATERIAL = "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"',
            self.validator_text,
        )

    def test_actual_possessed_native_umg_route_is_not_bypassed(self):
        required = (
            "controller.get_controlled_pawn() != pawn",
            "controller.get_view_target() != pawn",
            "controller.get_hud() != hud",
            "unreal.LBManagementRootWidget",
            "hud.open_factory_build()",
            "hud.activate_management_action(0)",
            "hud.activate_management_action(2)",
            "builder.commission_press_starter()",
            "safe_commission_rejection_before_creation",
            "programme_change_and_commission_success_via_umg_hud_route",
        )
        for token in required:
            self.assertIn(token, self.validator_text)
        self.assertNotIn("builder.create_new_factory()", self.validator_text)
        self.assertNotIn("builder.execute_umg_action(", self.validator_text)

    def test_widget_lookup_uses_world_filtered_reflection_not_renamed_library(self):
        self.assertNotIn("WidgetBlueprintLibrary", self.validator_text)
        self.assertNotIn("WidgetLibrary", self.validator_text)
        self.assertIn(
            "unreal.ObjectIterator(unreal.LBManagementRootWidget)",
            self.validator_text,
        )
        self.assertIn("if widget.get_world() == world", self.validator_text)

    def test_exact_empty_shell_and_transient_pair_cardinality_are_checked(self):
        for token in (
            '"LB_OneFactoryBootstrap_v001"',
            '"LB_OneFactory_PressBuildAuthority_v001"',
            '"LB_OneFactory_PressStarter_Data_v001"',
            '"LB_OneFactory_PressStarter_Presentation_v001"',
            '"LB.OneFactory.Bootstrap.v001"',
            '"LB.OneFactory.MapAuthored.PressBuildAuthority.v001"',
            '"LB.Provenance.NativeOnly"',
            '"LB.OneFactory.PressStarter.NativeProcedural"',
            '"LB.NotProcessWIP"',
            '"pie_transient_pair_destroyed_and_editor_shell_retained"',
        ):
            self.assertIn(token, self.validator_text)
        self.assertIn("editor_pair != [0, 0]", self.validator_text)
        self.assertIn("editor_shell != [1, 1]", self.validator_text)

    def test_meshy_vendor_wip_and_reference_gates_are_explicit(self):
        forbidden = assignment(self.tree, "FORBIDDEN_REFERENCE_TOKENS")
        for token in (
            "meshy",
            "runtimeglb",
            "/downloads/",
            "/candidates/",
            "vendor",
        ):
            self.assertIn(token, forbidden)
        self.assertIn('tag == "processwip"', self.validator_text)
        self.assertIn("not bool(item.represents_process_wip)", self.validator_text)
        self.assertIn("any(row[\"active_or_reserved_unit_ids\"] for row in rows)", self.validator_text)

    def test_real_rhi_fixed_exposure_and_all_four_capture_routes_are_required(self):
        for token in (
            "command_line_has_nullrhi",
            "unreal.AutomationLibrary.take_high_res_screenshot(",
            "unreal.LBOneFactoryCaptureBridge.resize_pie_window_for_game_widget_size(",
            "unreal.LBOneFactoryCaptureBridge.get_pie_game_widget_draw_size(",
            "unreal.LBOneFactoryCaptureBridge.request_pie_restricted_ui_screenshot(",
            "native_ui_capture_viewport_1920x1080",
            "SWindow.ReshapeWindow",
            "SViewport.GetCachedGeometry().GetDrawSize",
            "bRestrictToGameViewport=true",
            "5000K",
            "auto_exposure_min_brightness",
            "auto_exposure_max_brightness",
            "SCREENSHOT_SIZE[0]",
            "SCREENSHOT_SIZE[1]",
        ):
            self.assertIn(token, self.validator_text)
        self.assertEqual(self.validator_text.count("start_scene_capture("), 4)
        self.assertEqual(self.validator_text.count("start_ui_capture("), 2)
        self.assertNotIn("SHOT SHOWUI", self.validator_text)

    def test_validator_has_no_unreal_content_save_or_destructive_asset_calls(self):
        forbidden_suffixes = {
            "save_asset",
            "save_loaded_asset",
            "save_directory",
            "save_current_level",
            "save_all_dirty_levels",
            "delete_asset",
            "delete_directory",
            "destroy_actor",
        }
        offending = [name for name in self.calls if name.rsplit(".", 1)[-1] in forbidden_suffixes]
        self.assertEqual(offending, [])
        writes = [
            ast.unparse(node.func.value)
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "write_text"
        ]
        self.assertEqual(writes, ["AUDIT", "AUDIT"])
        self.assertIn("LEVELS.editor_request_end_play()", self.validator_text)
        self.assertIn("unreal.SystemLibrary.quit_editor()", self.validator_text)

    def test_runner_pins_validator_self_hash_processes_and_protected_files(self):
        match = re.search(
            r"\$ExpectedValidatorSha256\s*=\s*'([A-F0-9]{64})'",
            self.runner_text,
        )
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), sha256(VALIDATOR))
        self.assertIn("[Parameter(Mandatory = $true)]", self.runner_text)
        self.assertIn("[string]$ExpectedRunnerSha256", self.runner_text)
        self.assertIn("Runner self-hash mismatch", self.runner_text)
        for process in (
            "UnrealEditor",
            "UnrealEditor-Cmd",
            "UnrealBuildTool",
            "AutomationTool",
            "RunUAT",
            "ShaderCompileWorker",
        ):
            self.assertIn(f"'{process}'", self.runner_text)
        for token in (
            "Saved\\SaveGames",
            "Get-ProtectedSnapshot",
            "Assert-ProtectedCheckpoint",
            "ExpectedCreateReceiptSha256",
            "ExpectedShellValidationReceiptSha256",
        ):
            self.assertIn(token, self.runner_text)

    def test_runner_real_rhi_arguments_have_no_nullrhi_switch(self):
        self.assertIn("'-RenderOffscreen'", self.runner_text)
        self.assertIn("'-ResX=1920'", self.runner_text)
        self.assertIn("'-ResY=1080'", self.runner_text)
        self.assertIn("'-NoAutoSave'", self.runner_text)
        self.assertIn("'-NoSaveOnExit'", self.runner_text)
        self.assertNotRegex(self.runner_text, r"(?im)^\s*'-NullRHI',?\s*$")
        self.assertIn("Internal guard rejected NullRHI", self.runner_text)
        self.assertIn("Assert-LiveReceipt $LiveReceipt $CaptureRoot", self.runner_text)

    def test_powershell_parser_accepts_runner_without_executing_it(self):
        command = (
            "$errors=$null;"
            "[void][System.Management.Automation.Language.Parser]::ParseFile("
            f"'{str(RUNNER).replace(chr(39), chr(39) * 2)}',"
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

    def test_preserved_widget_lookup_incident_and_one_use_recovery_are_exact(self):
        failed = {
            "one_factory_actual_player_pie_v001.json": (
                16518,
                "FBE5FA4EF00E365BB6101EF29D7C9510FDC4A6EC77418F5B9906CBDC13C518A5",
            ),
            "one_factory_actual_player_pie_run_summary_v001.json": (
                31856,
                "51AE20C988345075EA7DAAD67E12C44D55CF3568C6A3988DD8188F9B1B62C169",
            ),
            "Logs/actual_player_pie.stdout.log": (
                330166,
                "2837BEBA0056057B6339A8956604FA5191DA983B26E9C3D2D6F2AB84E2AF53E4",
            ),
        }
        for relative, (size, expected_hash) in failed.items():
            path = FAILED_RUN / relative
            self.assertEqual(path.stat().st_size, size)
            self.assertEqual(sha256(path), expected_hash)
        receipt = (FAILED_RUN / "one_factory_actual_player_pie_v001.json").read_text(
            encoding="utf-8"
        )
        self.assertIn("WidgetBlueprintLibrary", receipt)
        self.assertIn('"map_hash_unchanged": true', receipt)
        self.assertIn('"changes": []', receipt)
        self.assertEqual(
            list(
                (
                    ROOT
                    / "Saved/ValidationScreenshots/OneFactory/v001/ActualPlayerPIE/"
                    "20260815T023449580Z"
                ).iterdir()
            ),
            [],
        )

        self.assertEqual(self.recovery_text.count("& $PowerShellExe"), 1)
        self.assertIn("[string]$ExpectedRecoverySha256", self.recovery_text)
        self.assertIn("FBE5FA4EF00E365", self.recovery_text)
        self.assertIn("WidgetBlueprintLibrary", self.recovery_text)
        self.assertIn("retry_invocation_limit = 1", self.recovery_text)
        for token in ("Remove-Item", "Delete", "Move-Item"):
            self.assertNotIn(token, self.recovery_text)

        command = (
            "$errors=$null;"
            "[void][System.Management.Automation.Language.Parser]::ParseFile("
            f"'{str(RECOVERY).replace(chr(39), chr(39) * 2)}',"
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

    def test_documentation_is_not_a_pass_claim_and_binds_exact_command(self):
        runner_hash = sha256(RUNNER)
        recovery_hash = sha256(UI_RESOLUTION_RECOVERY)
        self.assertIn("CORRECTED V002 RETRY FROZEN, NOT", self.doc_text)
        self.assertIn(sha256(VALIDATOR), self.doc_text)
        self.assertIn(runner_hash, self.doc_text)
        self.assertIn(sha256(RECOVERY), self.doc_text)
        self.assertIn(recovery_hash, self.doc_text)
        expected_command = (
            'powershell.exe -NoProfile -ExecutionPolicy Bypass -File '
            '"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8\\Scripts\\'
            'recover_one_factory_actual_player_pie_ui_resolution_incident_'
            '20260815T031021499Z_v005.ps1" '
            f"-ExpectedRecoverySha256 {recovery_hash}"
        )
        self.assertIn(expected_command, self.doc_text)


if __name__ == "__main__":
    unittest.main()
