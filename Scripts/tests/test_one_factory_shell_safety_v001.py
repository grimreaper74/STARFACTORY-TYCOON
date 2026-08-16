"""Static fail-closed and immutability tests for One Factory shell tooling."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re
import unittest


PROJECT = Path(__file__).resolve().parents[2]
BUILDER = PROJECT / "Scripts/create_one_factory_shell_v001.py"
VALIDATOR = PROJECT / "Scripts/validate_one_factory_shell_v001.py"
RUNNER = PROJECT / "Scripts/run_one_factory_shell_validation_v001.ps1"
HISTORICAL_RECOVERY = (
    PROJECT / "Scripts/recover_one_factory_shell_failed_run_20260815_v001.ps1"
)
RECOVERY = PROJECT / "Scripts/recover_one_factory_shell_failed_run_20260815_v002.ps1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class OneFactoryShellSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = BUILDER.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.recovery = RECOVERY.read_text(encoding="utf-8")
        cls.historical_recovery = HISTORICAL_RECOVERY.read_text(encoding="utf-8")
        cls.builder_tree = ast.parse(cls.builder, filename=str(BUILDER))
        cls.validator_tree = ast.parse(cls.validator, filename=str(VALIDATOR))

    def test_python_scripts_parse(self):
        self.assertIsInstance(self.builder_tree, ast.Module)
        self.assertIsInstance(self.validator_tree, ast.Module)

    def test_builder_refuses_destination_and_receipt_overwrite(self):
        self.assertIn("Refusing to overwrite protected One Factory destination", self.builder)
        self.assertIn("Refusing to overwrite One Factory creation receipt", self.builder)
        self.assertIn("library.does_asset_exist(MAP) or MAP_FILE.exists()", self.builder)

    def test_validator_is_independent_and_never_saves_content(self):
        self.assertNotIn("import create_one_factory_shell_v001", self.validator)
        self.assertNotIn("save_current_level", self.validator)
        self.assertNotIn("save_asset", self.validator)
        self.assertNotIn("duplicate_asset", self.validator)
        self.assertNotIn("delete_asset", self.validator)
        self.assertIn("levels.load_level(MAP)", self.validator)

    def test_builder_never_serializes_a_prevalidated_bootstrap(self):
        self.assertIn(
            "validate_current_map(classes, actors, run_bootstrap_validation=False)",
            self.builder,
        )
        self.assertIn("if run_bootstrap_validation", self.builder)
        save_index = self.builder.index("levels.save_current_level()")
        fresh_validation_index = self.builder.index(
            "validate_current_map(classes, actors, run_bootstrap_validation=True)"
        )
        self.assertLess(save_index, fresh_validation_index)

    def test_no_destructive_filesystem_or_asset_calls(self):
        combined = self.builder + self.validator
        for forbidden in (
            ".unlink(", "rmtree(", "remove_item", "delete_asset(",
            "delete_directory(", "consolidate_assets(", "rename_asset(",
        ):
            self.assertNotIn(forbidden, combined.lower())

    def test_recast_nav_actor_is_exactly_recognized_not_broadly_ignored(self):
        for source in (self.builder, self.validator):
            self.assertIn('ENGINE_NAVIGATION_ACTOR_LABEL = "RecastNavMesh-Default"', source)
            self.assertIn(
                'ENGINE_NAVIGATION_ACTOR_CLASS_PATH = "/Script/NavigationSystem.RecastNavMesh"',
                source,
            )
        self.assertIn('"tags": ()', self.validator)
        self.assertIn("exact_26_nonfoundation_actors", self.validator)
        self.assertNotIn("NavigationData", self.builder)
        self.assertNotIn('get_editor_property("persistent_level")', self.builder)
        self.assertNotIn('get_editor_property("persistent_level")', self.validator)
        self.assertIn(
            "navigation_rows[0].get_outer() == bootstraps[0].get_outer()",
            self.builder,
        )
        self.assertIn("navigation.get_outer() == bootstrap.get_outer()", self.validator)

    def test_all_required_protected_anchors_are_hash_pinned(self):
        expected = {
            "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
            "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5",
            "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F",
            "2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069",
        }
        for value in expected:
            self.assertIn(value, self.builder)
            self.assertIn(value, self.validator)
            self.assertIn(value, self.runner)
            self.assertIn(value, self.recovery)
        self.assertIn('ROOT / "Config"', self.builder)
        self.assertIn('ROOT / "Saved/SaveGames"', self.builder)
        self.assertIn("Get-ProtectedSnapshot", self.runner)

    def test_runner_hash_pins_current_builder_and_validator(self):
        builder_match = re.search(
            r"\$ExpectedBuilderSha256 = '([0-9A-F]{64})'", self.runner
        )
        validator_match = re.search(
            r"\$ExpectedValidatorSha256 = '([0-9A-F]{64})'", self.runner
        )
        self.assertIsNotNone(builder_match)
        self.assertIsNotNone(validator_match)
        self.assertEqual(builder_match.group(1), digest(BUILDER))
        self.assertEqual(validator_match.group(1), digest(VALIDATOR))
        self.assertIn(digest(BUILDER), self.validator)

    def test_runner_uses_two_separate_unreal_processes(self):
        invocations = re.findall(r"& \$Editor \$Project", self.runner)
        self.assertEqual(len(invocations), 2)
        self.assertIn("$BuilderCommand", self.runner)
        self.assertIn("$ValidatorCommand", self.runner)
        self.assertGreaterEqual(self.runner.count("-NullRHI"), 2)
        self.assertIn("LINE_BOSS_ONE_FACTORY_SHELL_CREATE_V001_PASS", self.runner)
        self.assertIn("LINE_BOSS_ONE_FACTORY_SHELL_VALIDATION_V001_PASS", self.runner)

    def test_default_engine_is_only_protected_not_modified(self):
        self.assertIn("Config/DefaultEngine.ini", self.runner)
        self.assertIn("DefaultEngine.ini changed", self.runner)
        self.assertNotIn("Set-Content -LiteralPath $DefaultEngine", self.runner)
        self.assertNotIn("default_game_map", self.builder.lower())
        self.assertIn('set_editor_property("default_game_mode"', self.builder)

    def test_runner_refuses_all_one_shot_outputs(self):
        for variable in ("$Map", "$CreateReceipt", "$ValidationReceipt"):
            self.assertIn(f"Test-Path -LiteralPath {variable}", self.runner)
        self.assertIn("Close active Unreal/build processes", self.runner)

    def test_incident_v002_recovery_is_exact_hash_guarded_move_then_one_retry(self):
        self.assertIn(
            "44E082B43719CA8B44E453ACBC9BF9BF018572102DABAA26D2EDF93E9B6A5B52",
            self.recovery,
        )
        self.assertIn("$ExpectedFailedMapLength = 272679", self.recovery)
        self.assertIn("20260815T011006Z", self.recovery)
        self.assertIn("$ExpectedFailedRunFiles", self.recovery)
        self.assertEqual(self.recovery.count("Move-Item -LiteralPath $FailedMap"), 1)
        self.assertEqual(self.recovery.count("& $Runner -EngineRoot $EngineRoot"), 1)
        self.assertNotIn("Remove-Item", self.recovery)
        self.assertNotIn("-Force", self.recovery)
        self.assertIn("Second incident archive already exists; recovery is one-use only", self.recovery)
        self.assertIn("Get-ProtectedSnapshot", self.recovery)
        self.assertIn(digest(BUILDER), self.recovery)
        self.assertIn(digest(VALIDATOR), self.recovery)
        self.assertIn(digest(RUNNER), self.recovery)
        self.assertIn(digest(HISTORICAL_RECOVERY), self.recovery)
        self.assertIn("$ExpectedPriorArchiveFiles", self.recovery)
        self.assertIn("Incident_20260815T005506Z", self.recovery)


if __name__ == "__main__":
    unittest.main()
