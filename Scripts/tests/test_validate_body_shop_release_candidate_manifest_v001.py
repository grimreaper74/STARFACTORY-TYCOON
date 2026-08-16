from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "validate_body_shop_release_candidate_manifest_v001.py"
)
SPEC = importlib.util.spec_from_file_location("body_shop_manifest_validator", SCRIPT)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


class BuildCookRunLogParsingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.command = (
            "Parsing command line: BuildCookRun -build -cook "
            f"-map={VALIDATOR.MAP_PACKAGE} -stage -pak -iostore -archive\n"
        )

    def decode(self, payload: bytes) -> str:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "buildcookrun.log"
            path.write_bytes(payload)
            return VALIDATOR.read_buildcookrun_log(path)

    def test_accepts_windows_powershell_utf16_log(self) -> None:
        decoded = self.decode(self.command.encode("utf-16"))
        self.assertTrue(VALIDATOR.has_exact_buildcookrun_map_invocation(decoded))

    def test_accepts_utf8_log_and_quoted_exact_map(self) -> None:
        command = (
            "Parsing command line: BuildCookRun -build -cook "
            f"-map=\"{VALIDATOR.MAP_PACKAGE}\" -stage\n"
        )
        decoded = self.decode(command.encode("utf-8"))
        self.assertTrue(VALIDATOR.has_exact_buildcookrun_map_invocation(decoded))

    def test_rejects_map_prefix_or_suffix(self) -> None:
        for altered in (
            f"{VALIDATOR.MAP_PACKAGE}_Other",
            VALIDATOR.MAP_PACKAGE.rsplit("/", 1)[0],
        ):
            with self.subTest(altered=altered):
                command = f"BuildCookRun -map={altered} -stage\n"
                self.assertFalse(
                    VALIDATOR.has_exact_buildcookrun_map_invocation(command)
                )

    def test_rejects_unrelated_map_mention(self) -> None:
        command = f"BuildCookRun -cook\nCooked package {VALIDATOR.MAP_PACKAGE}\n"
        self.assertFalse(VALIDATOR.has_exact_buildcookrun_map_invocation(command))

    def test_required_inventory_uses_exact_native_six_axis_robot_family(self) -> None:
        inventory = VALIDATOR.REQUIRED_SOURCE_ASSETS
        expected_parts = {"base", "j1", "j2", "j3", "j4", "j5", "j6"}
        self.assertEqual(
            {key.removeprefix("robot_") for key in inventory if key.startswith("robot_")},
            expected_parts,
        )
        for part in expected_parts:
            self.assertIn(
                "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/",
                inventory[f"robot_{part}"],
            )
        self.assertEqual(
            inventory["native_open_cgun"],
            "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/"
            "SM_LB_BodyShopToolNative_OpenCGun_v001.uasset",
        )
        joined = "\n".join(inventory.values())
        self.assertNotIn("WeldRobotRuntime_v001", joined)
        self.assertNotIn("SM_LB_WeldTool_SpotGun_v001", joined)

    def test_manifest_binds_exact_final_native_robot_authority(self) -> None:
        project = SCRIPT.parents[1]
        receipt = (
            project
            / VALIDATOR.FINAL_NATIVE_ROBOT_RUN_RELATIVE
            / "fresh_load_validation_receipt_v001.json"
        )
        failures: list[str] = []
        authority = VALIDATOR.validate_final_native_robot_authority(
            project, receipt, failures
        )
        self.assertEqual(failures, [])
        self.assertEqual(authority["asset_count"], 8)
        self.assertEqual(authority["lod_count_per_asset"], 3)
        self.assertEqual(authority["lod_triangle_totals"], [2628, 1964, 1356])
        self.assertEqual(
            authority["validation_receipt"]["sha256"],
            "9A4097CBB68F46297031A092FF861B20FC4B2F60576150005B483D984E26EBEA",
        )
        self.assertEqual(
            authority["import_receipt"]["sha256"],
            "B7738C068F344BBA391442F404E38A87BAF0C70B72A19CD2CA5DDDC68A5210BF",
        )

    def test_required_inventory_contains_all_native_support_assets_and_v002_stillage(self) -> None:
        inventory = VALIDATOR.REQUIRED_SOURCE_ASSETS
        support_rows = {
            key: value for key, value in inventory.items()
            if "BodyShopSupportKitNative_v002" in value
        }
        self.assertEqual(len(support_rows), 12)
        self.assertEqual(
            inventory["active_body_stillage_native_v002"],
            "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/"
            "Logistics/SM_LB_BodyShopSupport_PanelStillage_Full_v002.uasset",
        )
        self.assertNotIn("panel_stillage", inventory)
        self.assertNotIn("panel_stillage_material", inventory)

    def test_native_support_authority_is_byte_exact(self) -> None:
        project = SCRIPT.parents[1]
        receipt = (
            project
            / "Saved/Audits/BodyShop/SupportKitNative_v002/UnrealImportLane_v003/"
            "20260814T223952Z-fa3434b0/fresh_load_validation_receipt_v003.json"
        )
        authority = VALIDATOR.validate_support_kit(project, receipt)
        self.assertEqual(authority["asset_count"], 12)
        self.assertEqual(authority["lod_count_per_asset"], 3)
        self.assertEqual(authority["lod_triangle_totals"], [20408, 7580, 1780])
        self.assertEqual(len(authority["packages"]), 12)
        self.assertEqual(
            authority["validation_receipt"]["sha256"],
            "CDFA05DF4425695F8B6ABC8A06B17F377F6840739E207978E2595FA5A7B3DE82",
        )


if __name__ == "__main__":
    unittest.main()
