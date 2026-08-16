"""Offline contract tests for the deferred OneFactory v002 guarded lane."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import one_factory_visual_navigation_v002_contract as contract


CONTRACT_FILE = SCRIPTS / "one_factory_visual_navigation_v002_contract.py"
UNREAL_CONTRACT_FILE = SCRIPTS / "one_factory_visual_navigation_v002_unreal.py"
BUILDER_FILE = SCRIPTS / "build_one_factory_visual_navigation_v002.py"
VALIDATOR_FILE = SCRIPTS / "validate_one_factory_visual_navigation_v002.py"
RUNNER_FILE = SCRIPTS / "run_one_factory_visual_navigation_v002.ps1"
TEST_FILE = Path(__file__).resolve()
DOC_FILE = ROOT / "Docs/OneFactory/ONE_FACTORY_VISUAL_NAVIGATION_V002.md"
FREEZE_FILE = SCRIPTS / "one_factory_visual_navigation_v002_static_freeze.json"
FREEZE_SIDECAR = Path(str(FREEZE_FILE) + ".sha256")


class OneFactoryVisualNavigationV002Tests(unittest.TestCase):
    maxDiff = None

    def text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8-sig")

    def test_source_map_is_exact_and_destination_is_guarded(self):
        source = ROOT / contract.SOURCE_MAP_RELATIVE
        target = ROOT / contract.TARGET_MAP_RELATIVE
        self.assertTrue(source.is_file())
        self.assertEqual(contract.sha256(source), contract.SOURCE_MAP_SHA256)
        if target.exists():
            build = ROOT / contract.BUILD_RECEIPT_RELATIVE
            validation = ROOT / contract.VALIDATION_RECEIPT_RELATIVE
            self.assertTrue(build.is_file(), "A v002 map may exist only with its receipt")
            self.assertTrue(validation.is_file(), "A v002 map may exist only after validation")
            build_json = json.loads(self.text(build))
            validation_json = json.loads(self.text(validation))
            self.assertEqual(build_json["status"], contract.BUILD_STATUS)
            self.assertEqual(validation_json["status"], contract.VALIDATION_STATUS)
            self.assertEqual(build_json["target_map_sha256"], contract.sha256(target))
        else:
            self.assertFalse((ROOT / contract.BUILD_RECEIPT_RELATIVE).exists())
            self.assertFalse((ROOT / contract.VALIDATION_RECEIPT_RELATIVE).exists())

    def test_common_cairnwell_visual_and_navigation_contract_is_exact(self):
        specs = contract.high_bay_specs()
        self.assertEqual(len(specs), 32)
        self.assertEqual(len({row["label"] for row in specs}), 32)
        self.assertEqual(
            [min(contract.HIGH_BAY_X_CM), max(contract.HIGH_BAY_X_CM)],
            [-26_250.0, 26_250.0],
        )
        self.assertEqual(
            [min(contract.HIGH_BAY_Y_CM), max(contract.HIGH_BAY_Y_CM)],
            [-10_500.0, 10_500.0],
        )
        self.assertEqual(contract.HIGH_BAY_TEMPERATURE_K, 5_000.0)
        self.assertEqual(contract.HIGH_BAY_INTENSITY_LM, 48_000.0)
        self.assertEqual(contract.SUN_INTENSITY, 0.30)
        self.assertEqual(contract.SKY_INTENSITY, 0.20)
        self.assertEqual(contract.FIXED_EXPOSURE_BIAS, -0.50)
        self.assertEqual(len(contract.NAVIGATION_PROBES), 5)
        self.assertEqual(contract.SCREENSHOT_SIZE, (1_920, 1_080))
        self.assertEqual(
            contract.sha256(ROOT / contract.VISUAL_STANDARD_RELATIVE),
            contract.VISUAL_STANDARD_SHA256,
        )

    def test_genuine_v001_player_evidence_proves_both_failures(self):
        root = ROOT / contract.V001_ACTUAL_PLAYER_SCREENSHOT_RELATIVE_ROOT
        rows = {}
        for expected in contract.V001_ACTUAL_PLAYER_EVIDENCE:
            path = root / expected["name"]
            self.assertTrue(path.is_file())
            self.assertEqual(contract.sha256(path), expected["sha256"])
            rows[path.name] = contract.png_metrics(path)
            self.assertEqual(rows[path.name]["dimensions"], [1_920, 1_080])
        self.assertAlmostEqual(
            rows["01_empty_factory_management_overview.png"]["mean_luma"],
            0.163652,
            places=6,
        )
        self.assertAlmostEqual(
            rows["01_empty_factory_management_overview.png"][
                "black_clip_fraction"
            ],
            0.528524,
            places=6,
        )
        self.assertAlmostEqual(
            rows["02_populated_press_starter_wide_overview.png"]["mean_luma"],
            0.174236,
            places=6,
        )
        self.assertAlmostEqual(
            rows["02_populated_press_starter_wide_overview.png"][
                "black_clip_fraction"
            ],
            0.494309,
            places=6,
        )
        self.assertGreaterEqual(
            rows["04_populated_press_starter_with_umg.png"][
                "top_left_warning_red_pixels"
            ],
            500,
        )
        log = self.text(ROOT / contract.V001_ACTUAL_PLAYER_LOG_RELATIVE)
        self.assertGreaterEqual(
            log.count("Unable to find RecastNavMesh instance"), 2
        )

    def test_python_sources_parse_without_importing_unreal(self):
        for path in (
            CONTRACT_FILE,
            UNREAL_CONTRACT_FILE,
            BUILDER_FILE,
            VALIDATOR_FILE,
            TEST_FILE,
        ):
            ast.parse(self.text(path), filename=str(path))

    def test_builder_is_fresh_only_and_builds_navigation_before_save(self):
        source = self.text(BUILDER_FILE)
        self.assertIn("assets.does_asset_exist(contract.TARGET_MAP)", source)
        self.assertIn("assets.duplicate_asset(contract.SOURCE_MAP, contract.TARGET_MAP)", source)
        self.assertIn("Refusing to overwrite", source)
        self.assertNotIn("delete_asset", source)
        self.assertIn(
            'floor_components[0].set_editor_property("can_ever_affect_navigation", True)',
            source,
        )
        rebuild_positions = [
            match.start() for match in re.finditer('"RebuildNavigation"', source)
        ]
        self.assertGreaterEqual(len(rebuild_positions), 2)
        save_position = source.index("levels.save_current_level()")
        self.assertTrue(all(position < save_position for position in rebuild_positions[:2]))
        self.assertIn("explicit_build_completed_before_save", source)
        self.assertIn("guarded_workspace_snapshot", source)
        self.assertIn("contract.SOURCE_MAP_SHA256", source)
        self.assertIn(
            'unreal.load_class(\n        None, "/Script/NavigationSystem.NavigationSystemModuleConfig"',
            source,
        )
        self.assertIn('"bStrictlyStatic": False', source)
        self.assertIn('"bAutoSpawnMissingNavData": True', source)
        self.assertIn('"bSpawnNavDataInNavBoundsLevel": True', source)

    def test_unreal_contract_preserves_shell_and_replaces_only_visual_nav_seams(self):
        source = self.text(UNREAL_CONTRACT_FILE)
        for token in (
            "len(nonfoundation) != 59",
            "len(evidence) != 10 or total != 1_194",
            "base.validate_press_authority",
            "run_bootstrap_validation",
            "saved_production_actor_count",
            "saved_wip_identity_count",
            "contract.FLOOR_HISM_LABEL",
            "unreal.RuntimeGenerationType.DYNAMIC",
            "find_path_to_location_synchronously",
            "require_quiescent",
            'get_editor_property("bStrictlyStatic")',
            'get_editor_property("bAutoSpawnMissingNavData")',
            'get_editor_property("bSpawnNavDataInNavBoundsLevel")',
            "contract.HIGH_BAY_COUNT",
            "legacy_giant_rect_light_count",
        ):
            self.assertIn(token, source)

    def test_validator_is_real_rhi_fresh_pie_and_read_only(self):
        source = self.text(VALIDATOR_FILE)
        self.assertIn("Real-player visual validator refuses NullRHI", source)
        self.assertIn("LEVELS.editor_request_begin_play()", source)
        self.assertIn("LEVELS.editor_request_end_play()", source)
        self.assertIn("contract.scene_metrics_pass", source)
        self.assertIn("maximum_top_left_warning_red_pixels", source)
        self.assertIn("factory_wide_scene_mean_luma_spread", source)
        self.assertIn("gate.audit_navigation", source)
        self.assertIn("zero_starter_pair_before_player_action", source)
        self.assertIn("saved_starter_pair_count", source)
        self.assertNotIn("save_current_level", source)
        for name in contract.SCREENSHOT_NAMES:
            self.assertIn(name, source)

    def test_runner_parses_pins_tools_and_never_invokes_ubt(self):
        source = self.text(RUNNER_FILE)
        self.assertNotIn("__CONTRACT_SHA256__", source)
        self.assertNotIn("__UNREAL_CONTRACT_SHA256__", source)
        self.assertNotIn("__BUILDER_SHA256__", source)
        self.assertNotIn("__VALIDATOR_SHA256__", source)
        self.assertIn("-NullRHI", source)
        self.assertIn("-RenderOffscreen", source)
        self.assertIn("-ResX=1920", source)
        self.assertIn("-ResY=1080", source)
        self.assertIn("Unable to find RecastNavMesh", source)
        self.assertIn("NAVMESH NEEDS TO BE REBUILT", source)
        self.assertNotIn("Build.bat", source)
        self.assertNotIn("RunUAT.bat", source)
        self.assertNotRegex(source, r"Start-Process[^\n]*(?:UnrealBuildTool|RunUAT)")
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if shell:
            escaped = str(RUNNER_FILE).replace("'", "''")
            command = (
                "$tokens=$null;$errors=$null;"
                f"[System.Management.Automation.Language.Parser]::ParseFile('{escaped}',"
                "[ref]$tokens,[ref]$errors)|Out-Null;"
                "if($errors.Count){$errors|%{$_.ToString()};exit 1}"
            )
            result = subprocess.run(
                [shell, "-NoProfile", "-Command", command],
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_freeze_manifest_matches_every_deliverable(self):
        self.assertTrue(FREEZE_FILE.is_file())
        self.assertTrue(FREEZE_SIDECAR.is_file())
        freeze = json.loads(self.text(FREEZE_FILE))
        self.assertEqual(
            freeze["$schema"],
            "lineboss/static-freeze/one-factory-visual-navigation-v002/v1",
        )
        self.assertEqual(
            freeze["status"],
            "FROZEN__OFFLINE_TOOLING_ONLY__UNREAL_NOT_RUN__TARGET_ABSENT",
        )
        self.assertFalse(freeze["execution"]["unreal_or_ubt_run"])
        self.assertFalse(freeze["execution"]["target_map_created"])
        self.assertEqual(freeze["source_map"]["sha256"], contract.SOURCE_MAP_SHA256)
        self.assertEqual(freeze["target_map"]["package"], contract.TARGET_MAP)
        for name, expected_hash in freeze["files"].items():
            self.assertEqual(contract.sha256(ROOT / name), expected_hash, name)
        sidecar = self.text(FREEZE_SIDECAR).strip().split()
        self.assertEqual(sidecar[0], contract.sha256(FREEZE_FILE))
        self.assertEqual(sidecar[1], FREEZE_FILE.name)
        expected_command = (
            'powershell -NoProfile -ExecutionPolicy Bypass -File '
            '"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8\\Scripts\\'
            'run_one_factory_visual_navigation_v002.ps1"'
        )
        self.assertEqual(freeze["exact_run_command"], expected_command)
        self.assertIn(expected_command, self.text(DOC_FILE))


if __name__ == "__main__":
    unittest.main(verbosity=2)
