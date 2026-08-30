"""Offline fail-closed tests for the v004 saved-map capture lane."""

from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPT = PROJECT / "Tools/capture_pressshop_2126_overhead_presentation_v004.py"
FINAL_MAP_SHA = "ab77d9bc327e65fa5bf8b8efd4d6666252247be1420070563f83bb099d98fe9f"
FINAL_RECEIPT_SHA = "9c2bca410ebb40a534cdaa65a41c433c6f535df566ae209865f6fe5053a706d4"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "capture_pressshop_2126_overhead_presentation_v004_for_tests", SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load v004 capture script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PresentationV004CaptureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.receipt, cls.contract = cls.module.load_guarded_install_receipt(
            FINAL_MAP_SHA, FINAL_RECEIPT_SHA
        )

    def test_exact_completed_v004_disk_contract_passes(self) -> None:
        self.assertEqual(self.module.digest(self.module.TARGET_FILE), FINAL_MAP_SHA)
        self.assertEqual(
            self.module.digest(self.module.INSTALL_RECEIPT), FINAL_RECEIPT_SHA
        )
        self.assertEqual(self.receipt["target_map_bytes"], 1_211_122)
        self.assertEqual(len(self.contract["mutations"]), 38)
        self.assertEqual(len(self.contract["connectors"]), 3)
        self.assertEqual(
            self.contract["material"]["sha256"],
            "961086fa48097c6a6a11a69a09efb4685d9dbd6dc2f973a80afbf7f76b545ebf",
        )

    def test_both_independent_hashes_are_required(self) -> None:
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.required_guard_hashes({})
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.required_guard_hashes(
                {self.module.MAP_SHA_ENV: FINAL_MAP_SHA}
            )
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.required_guard_hashes({
                self.module.MAP_SHA_ENV: "0" * 64,
                self.module.RECEIPT_SHA_ENV: FINAL_RECEIPT_SHA,
            })
        self.assertEqual(
            self.module.required_guard_hashes({
                self.module.MAP_SHA_ENV: FINAL_MAP_SHA,
                self.module.RECEIPT_SHA_ENV: FINAL_RECEIPT_SHA,
            }),
            (FINAL_MAP_SHA, FINAL_RECEIPT_SHA),
        )

    def test_native_class_and_content_asset_paths_normalise_differently(self) -> None:
        self.assertEqual(
            self.module._asset_path(
                "/Script/LineBossCarFactory.LBOneFactoryGameMode"
            ),
            "/Script/LineBossCarFactory.LBOneFactoryGameMode",
        )
        self.assertEqual(
            self.module._asset_path(
                "/Game/Test/M_Test.M_Test"
            ),
            "/Game/Test/M_Test",
        )

    def test_wrong_map_or_receipt_hash_fails_before_unreal(self) -> None:
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.load_guarded_install_receipt("1" * 64, FINAL_RECEIPT_SHA)
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.load_guarded_install_receipt(FINAL_MAP_SHA, "2" * 64)

    def test_connector_omission_is_rejected(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        receipt["created_press_connectors"].pop()
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.validate_install_receipt(
                receipt, FINAL_MAP_SHA, receipt["target_map_bytes"]
            )

    def test_slate_deck_or_camera_drift_is_rejected(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        receipt["deck_style"]["full_deck_srgb_hex"] = "#000000"
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.validate_install_receipt(
                receipt, FINAL_MAP_SHA, receipt["target_map_bytes"]
            )

        receipt = copy.deepcopy(self.receipt)
        camera = next(
            row
            for row in receipt["presentation_mutations"]
            if row["id"] == "steam_hero"
        )
        camera["target_ortho_width_cm"] = 9999.0
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.validate_install_receipt(
                receipt, FINAL_MAP_SHA, receipt["target_map_bytes"]
            )

    def test_readable_text_rotation_drift_is_rejected(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        label = next(
            row
            for row in receipt["presentation_mutations"]
            if row["id"] == "LABEL_S03"
        )
        label["target_rotation_deg_pitch_yaw_roll"] = [90.0, 0.0, 0.0]
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.validate_install_receipt(
                receipt, FINAL_MAP_SHA, receipt["target_map_bytes"]
            )

    def test_evidence_directory_is_never_merged_or_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "existing_evidence"
            path.mkdir()
            with self.assertRaises(self.module.CaptureGuardError):
                self.module.ensure_output_absent(path)
            self.module.ensure_output_absent(Path(temporary) / "new_evidence")

    def test_script_contains_no_saved_layout_material_or_save_mutator(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "apply_presentation_state(",
            ".set_static_mesh(",
            ".set_material(",
            ".set_actor_location(",
            ".set_actor_rotation(",
            ".set_actor_scale3d(",
            "save_current_level(",
            "save_loaded_asset(",
            "save_directory(",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("transient=True", source)
        self.assertIn("map_save_calls\": 0", source)
        self.assertIn("content_save_calls\": 0", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
