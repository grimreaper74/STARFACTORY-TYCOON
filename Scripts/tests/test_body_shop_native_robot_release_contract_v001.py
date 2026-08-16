from __future__ import annotations

import ast
import re
from pathlib import Path
import unittest


PROJECT = Path(__file__).resolve().parents[2]
SCRIPTS = PROJECT / "Scripts"
SOURCE = PROJECT / "Source" / "LineBossCarFactory"
NATIVE_BASELINE_SHA256 = (
    "D967E8CD1596FC620066668138FEE14A47C702D55989FB1DB1C3AAF0ABF0FF31"
)
NATIVE_CLEAN_DISPOSITION_SHA256 = (
    "E9862B44C656586879EF3607C33BD8A536E9CE0D816C144AFF870C31A7B52BC3"
)
NATIVE_LANE_SHA256 = "B1AFEDB019C28B04082497F46B954C29262D0A30B19854D00CF1168537AA2F73"
NATIVE_IMPORT_SHA256 = "B7738C068F344BBA391442F404E38A87BAF0C70B72A19CD2CA5DDDC68A5210BF"
NATIVE_VALIDATION_SHA256 = "9A4097CBB68F46297031A092FF861B20FC4B2F60576150005B483D984E26EBEA"
NATIVE_VALIDATION_STATUS = (
    "PASS__INDEPENDENT_FRESH_PROCESS_LOAD__INCIDENT_ARCHIVE_VERIFIED__"
    "8_ASSETS_3_LODS_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001"
)
RESTORED_PRESS_SHA256 = "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5"


class BodyShopNativeRobotReleaseContractV001Tests(unittest.TestCase):
    def test_release_runner_matches_exact_current_body_shop_test_inventory(self) -> None:
        test_pattern = re.compile(
            r"IMPLEMENT_(?:SIMPLE|CUSTOM_SIMPLE)_AUTOMATION_TEST\s*\(\s*[^,]+,\s*"
            r'"([^"]+)"',
            re.DOTALL,
        )
        source_tests = {
            name
            for path in SOURCE.glob("LBBodyShop*Tests.cpp")
            for name in test_pattern.findall(path.read_text(encoding="utf-8-sig"))
        }
        runner = (SCRIPTS / "run_body_shop_release_validation_v001.ps1").read_text(
            encoding="utf-8-sig"
        )
        block = re.search(
            r"\$ExpectedTests\s*=\s*@\((.*?)\n\s*\)", runner, re.DOTALL
        )
        self.assertIsNotNone(block)
        runner_tests = set(re.findall(r"'([^']+)'", block.group(1)))
        self.assertEqual(len(source_tests), 43)
        self.assertEqual(runner_tests, source_tests)
        self.assertIn(
            "$CompletedSuccesses = [int]$Report.succeeded + "
            "[int]$Report.succeededWithWarnings",
            runner,
        )
        self.assertIn("@('Success','SuccessWithWarnings')", runner)

    def test_current_python_release_contracts_parse(self) -> None:
        for name in (
            "analyze_body_shop_packaged_performance_lod_v002.py",
            "validate_body_shop_performance_lod_pie_v001.py",
            "validate_body_shop_presentation_materials_v002.py",
            "validate_body_shop_functional_hism_usage_v001.py",
            "validate_body_shop_release_candidate_manifest_v001.py",
            "validate_body_shop_release_candidate_pie_v002.py",
            "body_shop_support_kit_native_v002_contract.py",
        ):
            with self.subTest(name=name):
                ast.parse((SCRIPTS / name).read_text(encoding="utf-8-sig"))

    def test_current_release_contracts_bind_native_j6_and_open_cgun(self) -> None:
        analyzer = (SCRIPTS / "analyze_body_shop_packaged_performance_lod_v002.py").read_text(
            encoding="utf-8-sig"
        )
        manifest = (SCRIPTS / "validate_body_shop_release_candidate_manifest_v001.py").read_text(
            encoding="utf-8-sig"
        )
        pie = (SCRIPTS / "validate_body_shop_release_candidate_pie_v002.py").read_text(
            encoding="utf-8-sig"
        )
        current = analyzer + manifest
        self.assertIn("EXPECTED_COMPONENTS = 25", analyzer)
        self.assertIn("components=25 meshes=10", analyzer)
        perf_runner = (SCRIPTS / "run_body_shop_packaged_performance_lod_validation_v002.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("component_count -ne 25", perf_runner)
        self.assertIn("unique_mesh_count -ne 10", perf_runner)
        self.assertIn("target_components).Count -ne 25", perf_runner)
        self.assertIn("SM_LB_BodyShopRobotNative_J6_v001", current + pie)
        self.assertIn("SM_LB_BodyShopToolNative_OpenCGun_v001", current + pie)
        self.assertIn("SM_LB_BodyShopTool_PanelPick8Cup_v001", current + pie)
        self.assertNotIn("BodyShopUnderbodySlice_v001/Robot", current)
        self.assertNotIn("WeldRobotRuntime_v001", current)
        self.assertNotIn("SM_LB_WeldTool_SpotGun_v001", current)

    def test_current_release_chain_pins_final_clean_import_authority(self) -> None:
        current_files = (
            "validate_body_shop_presentation_materials_v002.py",
            "validate_body_shop_functional_hism_usage_v001.py",
            "run_validate_body_shop_functional_hism_usage_v001.ps1",
            "run_body_shop_release_validation_v001.ps1",
            "package_body_shop_experimental_development_v001.ps1",
            "validate_body_shop_release_candidate_manifest_v001.py",
            "validate_body_shop_release_candidate_pie_v002.py",
            "analyze_body_shop_packaged_performance_lod_v002.py",
            "run_body_shop_packaged_performance_lod_validation_v002.ps1",
        )
        for name in current_files:
            text = (SCRIPTS / name).read_text(encoding="utf-8-sig")
            with self.subTest(name=name):
                self.assertIn(NATIVE_VALIDATION_SHA256, text)
                self.assertIn(NATIVE_IMPORT_SHA256, text)
                self.assertIn(NATIVE_LANE_SHA256, text)
                self.assertIn(RESTORED_PRESS_SHA256, text)
                self.assertNotIn(
                    "3F9EAA19BDF88AF4D3E70AC807A0E5C83D64E09CF15F724B2166D39A017A5304",
                    text,
                )
                self.assertNotIn(
                    "F41EC783FBDE2208E02FB841ECA1D93F80BC221FD412ED7DD558B10E4F86B75B",
                    text,
                )
                self.assertNotIn("recovery_contract_sha256", text)
                self.assertNotIn(
                    "PASS__INDEPENDENT_FRESH_PROCESS_LOAD_8_ASSETS_3_LODS_"
                    "HIGH_ELBOW_BODYSHOP_ROBOT_NATIVE_V001",
                    text,
                )
        for name in (
            "validate_body_shop_presentation_materials_v002.py",
            "validate_body_shop_functional_hism_usage_v001.py",
            "run_body_shop_release_validation_v001.ps1",
            "package_body_shop_experimental_development_v001.ps1",
            "validate_body_shop_release_candidate_manifest_v001.py",
            "validate_body_shop_release_candidate_pie_v002.py",
            "analyze_body_shop_packaged_performance_lod_v002.py",
        ):
            text = (SCRIPTS / name).read_text(encoding="utf-8-sig")
            with self.subTest(final_contract=name):
                self.assertIn(NATIVE_BASELINE_SHA256, text)
                self.assertIn(NATIVE_CLEAN_DISPOSITION_SHA256, text)
                self.assertIn(
                    "PASS__INDEPENDENT_FRESH_PROCESS_LOAD__INCIDENT_ARCHIVE_VERIFIED__",
                    text,
                )
                self.assertIn(
                    "8_ASSETS_3_LODS_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001",
                    text,
                )
                self.assertIn("2628", text)
                self.assertIn("1964", text)
                self.assertIn("1356", text)
        material = (SCRIPTS / "validate_body_shop_presentation_materials_v002.py").read_text(
            encoding="utf-8-sig"
        )
        hism = (SCRIPTS / "validate_body_shop_functional_hism_usage_v001.py").read_text(
            encoding="utf-8-sig"
        )
        runner = (SCRIPTS / "run_body_shop_release_validation_v001.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn(
            "presentation_materials_v002_native_robot_support_kit_validation_v004.json",
            material,
        )
        self.assertIn(
            "presentation-materials-v002-native-robot-support-kit-validation-v004/v1",
            material,
        )
        self.assertIn("functional_hism_usage_validation_v004.json", hism)
        self.assertIn("functional_hism_usage_validation_summary_v004.json", runner)
        self.assertIn(
            "maps_materials_meshes_native_robot_support_kit_press_changed",
            runner,
        )

    def test_native_support_kit_v002_is_bound_across_the_release_chain(self) -> None:
        helper = (SCRIPTS / "body_shop_support_kit_native_v002_contract.py").read_text(
            encoding="utf-8-sig"
        )
        for token in (
            "20260814T223952Z-fa3434b0",
            "BBE9F02910027B111B07CBABE163CDE3A139DE065FF8E24FE99BB497470090F6",
            "F5E1735BE76AD9F2086AE1B533CA92DD240D740129A9BBC147A872D818B2F286",
            "CDFA05DF4425695F8B6ABC8A06B17F377F6840739E207978E2595FA5A7B3DE82",
            "6797C6C7E295C00D1921DFB378100C26C9905848E8EF63DB0501BBA0FC583C22",
            "A124CE80D77717C062CFFE5AFDD5058905957D29B8A8BB01979A4567149653A6",
            "20408",
            "7580",
            "1780",
        ):
            self.assertIn(token, helper)
        self.assertEqual(helper.count('"Logistics/SM_LB_BodyShopSupport_'), 6)
        downstream = (
            "validate_body_shop_presentation_materials_v002.py",
            "validate_body_shop_functional_hism_usage_v001.py",
            "run_validate_body_shop_functional_hism_usage_v001.ps1",
            "run_body_shop_release_validation_v001.ps1",
            "package_body_shop_experimental_development_v001.ps1",
            "validate_body_shop_release_candidate_manifest_v001.py",
            "validate_body_shop_release_candidate_pie_v002.py",
            "analyze_body_shop_packaged_performance_lod_v002.py",
            "run_body_shop_packaged_performance_lod_validation_v002.ps1",
        )
        for name in downstream:
            text = (SCRIPTS / name).read_text(encoding="utf-8-sig")
            with self.subTest(name=name):
                self.assertIn("support", text.lower())
                self.assertTrue(
                    "BodyShopSupportKitNative_v002" in text
                    or "body_shop_support_kit_native_v002_contract" in text
                    or "SupportKitNative_v002" in text
                )
        pie = (SCRIPTS / "validate_body_shop_release_candidate_pie_v002.py").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("LB_BodyShop_ServiceDressing_v002", pie)
        self.assertIn("EmptyReturnCartNativeV002Instances", pie)
        self.assertIn("ComponentServicePalletNativeV002Instances", pie)
        self.assertIn("EmptySmallPartsCrateNativeV002Instances", pie)
        self.assertIn("get_pilot_stillage_presentation_mesh_path", pie)
        release_runner = (
            SCRIPTS / "run_body_shop_release_validation_v001.ps1"
        ).read_text(encoding="utf-8-sig")
        hism_runner = (
            SCRIPTS / "run_validate_body_shop_functional_hism_usage_v001.ps1"
        ).read_text(encoding="utf-8-sig")
        for token in (
            "LB_BodyShop_ServiceDressing_v002",
            "EmptyReturnCartNativeV002Instances",
            "ComponentServicePalletNativeV002Instances",
            "EmptySmallPartsCrateNativeV002Instances",
            "SM_LB_BodyShopSupport_EmptyReturnCart_v002",
            "SM_LB_BodyShopSupport_ComponentServicePallet_v002",
            "SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002",
        ):
            self.assertIn(token, release_runner)
            self.assertIn(token, hism_runner)
        self.assertIn(
            "ALBBodyShopPrototypeRuntime::GetPilotStillagePresentationMeshPath",
            release_runner,
        )


if __name__ == "__main__":
    unittest.main()
