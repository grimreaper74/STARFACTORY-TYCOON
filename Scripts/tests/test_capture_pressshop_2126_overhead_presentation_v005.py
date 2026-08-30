"""Offline fail-closed tests for the v005 saved-map capture lane."""

from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPT = PROJECT / "Tools/capture_pressshop_2126_overhead_presentation_v005.py"
FINAL_MAP_SHA = "4d3ce8973cc7bede00f0204a1e653117935cfc9f120fac8b6a939510ad01fe4b"
FINAL_RECEIPT_SHA = "cf13095f09fbf1422b7ee4a41c8f45ca36ceb016af096abf73ccf2aae9eb4246"
FINAL_MAP_BYTES = 1_694_902


def load_module():
    spec = importlib.util.spec_from_file_location(
        "capture_pressshop_2126_overhead_presentation_v005_for_tests", SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load v005 capture script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PresentationV005CaptureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.receipt, cls.contract = cls.module.load_guarded_install_receipt(
            FINAL_MAP_SHA, FINAL_RECEIPT_SHA
        )

    def validate(self, receipt):
        return self.module.validate_install_receipt(
            receipt, FINAL_MAP_SHA, FINAL_MAP_BYTES,
            {
                "module": self.contract["plan"] and self.module._installer_contract()["module"],
                "plan": self.contract["plan"],
                "validation": self.contract["validation"],
                "protected": self.contract["protected"],
                "reused_materials": self.module._installer_contract()["reused_materials"],
            },
        )

    def test_exact_final_disk_contract_passes(self) -> None:
        self.assertEqual(self.module.digest(self.module.TARGET_FILE), FINAL_MAP_SHA)
        self.assertEqual(self.module.digest(self.module.INSTALL_RECEIPT), FINAL_RECEIPT_SHA)
        self.assertEqual(self.module.TARGET_FILE.stat().st_size, FINAL_MAP_BYTES)
        self.assertEqual(len(self.contract["mutations"]), 61)
        self.assertEqual(len(self.contract["additions"]), 55)
        self.assertEqual(self.contract["validation"]["final_actor_count"], 302)
        self.assertEqual(self.contract["validation"]["station_port_count"], 12)
        self.assertEqual(self.contract["validation"]["station_connector_max_gap_cm"], 0.0)

    def test_installer_contract_and_camera_sizes_are_frozen(self) -> None:
        self.assertEqual(
            self.module.digest(self.module.INSTALLER), self.module.INSTALLER_SHA256
        )
        self.assertEqual(
            {key: value["ortho_width_cm"] for key, value in self.module.CAMERA_SPECS.items()},
            {"overview": 17200.0, "press_spine": 10800.0, "steam_hero": 6000.0},
        )

    def test_both_independent_hashes_are_mandatory(self) -> None:
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.required_guard_hashes({})
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.required_guard_hashes({self.module.MAP_SHA_ENV: FINAL_MAP_SHA})
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.required_guard_hashes({
                self.module.MAP_SHA_ENV: "0" * 64,
                self.module.RECEIPT_SHA_ENV: FINAL_RECEIPT_SHA,
            })
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.required_guard_hashes({
                self.module.MAP_SHA_ENV: FINAL_MAP_SHA.upper(),
                self.module.RECEIPT_SHA_ENV: FINAL_RECEIPT_SHA,
            })
        self.assertEqual(
            self.module.required_guard_hashes({
                self.module.MAP_SHA_ENV: FINAL_MAP_SHA,
                self.module.RECEIPT_SHA_ENV: FINAL_RECEIPT_SHA,
            }),
            (FINAL_MAP_SHA, FINAL_RECEIPT_SHA),
        )

    def test_wrong_map_or_receipt_hash_fails_before_unreal(self) -> None:
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.load_guarded_install_receipt("1" * 64, FINAL_RECEIPT_SHA)
        with self.assertRaises(self.module.CaptureGuardError):
            self.module.load_guarded_install_receipt(FINAL_MAP_SHA, "2" * 64)

    def test_missing_or_reordered_mutation_fails(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        receipt["presentation_mutations"].pop()
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)
        receipt = copy.deepcopy(self.receipt)
        receipt["presentation_mutations"][0], receipt["presentation_mutations"][1] = (
            receipt["presentation_mutations"][1], receipt["presentation_mutations"][0]
        )
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)

    def test_new_box_transform_and_collision_drift_fail(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        receipt["created_presentation_boxes"][0]["location_cm"][0] += 1.0
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)
        receipt = copy.deepcopy(self.receipt)
        receipt["created_presentation_boxes"][0]["collision_readback"][
            "actor_collision_enabled"
        ] = True
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)

    def test_camera_width_and_complete_route_drift_fail(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        row = next(row for row in receipt["presentation_mutations"] if row["id"] == "overview")
        row["target_ortho_width_cm"] = 17199.0
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)
        receipt = copy.deepcopy(self.receipt)
        receipt["plan_validation"]["station_port_count"] = 11
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)

    def test_material_and_style_drift_fail(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        receipt["created_materials"][1]["srgb_hex"] = "#000000"
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)
        receipt = copy.deepcopy(self.receipt)
        receipt["presentation_style"]["route_bed_srgb_hex"] = "#000000"
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)

    def test_visual_cargo_and_preserved_fingerprint_drift_fail(self) -> None:
        for key, value in (
            ("combined_visual_layer_count", 145),
            ("cargo_layer_count", 25),
            ("preserved_nonpresentation_actor_fingerprints_after_sha256", "3" * 64),
        ):
            receipt = copy.deepcopy(self.receipt)
            receipt[key] = value
            with self.assertRaises(self.module.CaptureGuardError):
                self.validate(receipt)

    def test_evidence_directory_is_never_merged_or_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            existing = Path(temporary) / "evidence"
            existing.mkdir()
            with self.assertRaises(self.module.CaptureGuardError):
                self.module.ensure_output_absent(existing)
            self.module.ensure_output_absent(Path(temporary) / "new_evidence")

    def test_script_has_no_saved_layout_material_or_save_mutator(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            ".set_static_mesh(", ".set_material(", ".set_actor_location(",
            ".set_actor_rotation(", ".set_actor_scale3d(", "save_current_level(",
            "save_loaded_asset(", "save_directory(",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("map_save_calls\": 0", source)
        self.assertIn("content_save_calls\": 0", source)
        self.assertIn("open(\"xb\")", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
