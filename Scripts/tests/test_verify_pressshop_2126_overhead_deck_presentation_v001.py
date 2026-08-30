"""Offline evidence and mutation-surface tests for the saved-map verifier."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
VERIFIER_PATH = (
    PROJECT / "Tools" / "verify_pressshop_2126_overhead_deck_presentation_v001.py"
)


def load_subjects():
    previous = sys.modules.get("unreal")
    fake_unreal = types.ModuleType("unreal")
    sys.modules["unreal"] = fake_unreal
    try:
        spec = importlib.util.spec_from_file_location(
            "pressshop_overhead_deck_verifier_v001_test_subject", VERIFIER_PATH
        )
        verifier = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(verifier)
        contract = verifier.load_installer_contract()
        return verifier, contract
    finally:
        if previous is None:
            sys.modules.pop("unreal", None)
        else:
            sys.modules["unreal"] = previous


VERIFIER, CONTRACT = load_subjects()
INSTALL = VERIFIER.load_json(
    VERIFIER.INSTALL_RECEIPT, VERIFIER.INSTALL_RECEIPT_SHA256
)


class SavedEvidenceTests(unittest.TestCase):
    def test_installer_receipt_target_and_protected_hashes_match_disk(self):
        self.assertEqual(VERIFIER.digest(VERIFIER.INSTALLER), VERIFIER.INSTALLER_SHA256)
        self.assertEqual(INSTALL["target_map"], CONTRACT.TARGET_MAP)
        self.assertEqual(
            VERIFIER.digest(CONTRACT.TARGET_FILE), INSTALL["target_map_sha256"]
        )
        self.assertEqual(CONTRACT.TARGET_FILE.stat().st_size, INSTALL["target_map_bytes"])
        self.assertEqual(len(CONTRACT.protected_snapshot()), 6)
        self.assertEqual(
            INSTALL["protected_hashes_before"], INSTALL["protected_hashes_after"]
        )

    def test_all_three_exact_recovery_receipts_are_hash_locked(self):
        for path, expected in VERIFIER.RECOVERY_RECEIPT_HASHES.items():
            value = VERIFIER.load_json(path, expected)
            self.assertTrue(value["performed"])
            self.assertEqual(
                value["status"],
                "PASS_EXACT_FAILED_RUN_ARTIFACTS_REMOVED__TARGET_READY_FOR_REBUILD",
            )
            self.assertEqual(len(value["deleted_artifacts"]), 5)

    def test_install_receipt_has_deterministic_actor_counts_and_honest_flags(self):
        self.assertEqual(INSTALL["source_actor_count"], 13825)
        self.assertEqual(INSTALL["legacy_presentation_removed_count"], 13689)
        self.assertEqual(INSTALL["created_box_actor_count"], 64)
        self.assertEqual(INSTALL["created_text_actor_count"], 15)
        self.assertEqual(INSTALL["created_camera_actor_count"], 3)
        self.assertEqual(INSTALL["created_actor_count"], 82)
        self.assertEqual(INSTALL["roof_actor_count_after"], 0)
        self.assertFalse(INSTALL["collision_enabled_on_created_presentation"])
        for key in (
            "runtime_validated", "runtime_ready", "packaged_build_validated",
            "visual_capture_validated", "steam_capture_validated",
        ):
            self.assertFalse(INSTALL[key], key)

    def test_every_saved_collision_readback_is_no_collision_ignore_all(self):
        rows = INSTALL["created_boxes"] + INSTALL["created_texts"]
        self.assertEqual(len(rows), 79)
        expected_channels = set(CONTRACT.COLLISION_CHANNEL_NAMES)
        for row in rows:
            collision = row["collision_readback"]
            self.assertFalse(collision["actor_collision_enabled"])
            self.assertIn(
                "NO_COLLISION", collision["component_collision_enabled"].upper()
            )
            self.assertEqual(
                collision["profile_acceptance"],
                "CustomWithNoCollisionAndIgnoreAll",
            )
            self.assertEqual(set(collision["ignored_channels"]), expected_channels)

    def test_overview_spine_and_steam_hero_camera_contract_is_receipted(self):
        cameras = {row["id"]: row for row in INSTALL["cameras"]}
        self.assertEqual(set(cameras), {"overview", "press_spine", "steam_hero"})
        self.assertEqual(
            [cameras[key]["ortho_width_cm"] for key in cameras],
            [16500.0, 8900.0, 6900.0],
        )
        steam = cameras["steam_hero"]
        self.assertEqual(steam["location_cm"], [-8990.75, 11200.0, 21712.544])
        self.assertEqual(steam["rotation_deg_pitch_yaw_roll"], [-90.0, 0.0, 0.0])
        self.assertEqual(steam["projection"], "ORTHOGRAPHIC")
        steam_spec = next(
            row for row in CONTRACT.CAMERA_SPECS if row["id"] == "steam_hero"
        )
        self.assertEqual(
            set(steam_spec["additional_tags"]),
            {"LB.SteamReviewCamera", "LB.PressShop.SteamHero.v002"},
        )

    def test_material_packages_match_receipted_hashes_and_palette(self):
        expected_hex = {
            "deck": "#171D21", "zone": "#91AA9C",
            "cream": "#E8DEC2", "yellow": "#E1B94F",
        }
        by_id = {row["id"]: row for row in INSTALL["created_materials"]}
        self.assertEqual(set(by_id), set(expected_hex))
        for material_id, wanted_hex in expected_hex.items():
            row = by_id[material_id]
            path = CONTRACT.asset_disk_path(row["asset"])
            self.assertEqual(row["srgb_hex"], wanted_hex)
            self.assertEqual(VERIFIER.digest(path), row["sha256"])
            self.assertEqual(path.stat().st_size, row["bytes"])


class ReadOnlyVerifierSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = VERIFIER_PATH.read_text(encoding="utf-8")
        cls.main_body = cls.source[cls.source.index("def main() -> None:") :]

    def test_verifier_loads_only_target_and_has_no_asset_mutation_api(self):
        self.assertEqual(self.main_body.count("load_level(contract.TARGET_MAP)"), 1)
        for token in (
            "load_level(contract.SOURCE_MAP)",
            "save_current_level(", "save_asset(", "save_loaded_asset(",
            "save_directory(", "save_dirty_packages(", "delete_asset(",
            "delete_directory(", "create_asset(", "new_level_from_template(",
            "spawn_actor_from_class(", "spawn_actor_from_object(",
        ):
            self.assertNotIn(token, self.source, token)

    def test_validation_receipt_is_exclusive_and_keeps_runtime_claims_false(self):
        self.assertIn('path.open("xb")', self.source)
        for token in (
            '"read_only": True',
            '"source_map_mutated": False',
            '"protected_authority_map_mutated": False',
            '"runtime_validated": False',
            '"runtime_ready": False',
            '"packaged_build_validated": False',
            '"visual_capture_validated": False',
            '"steam_capture_validated": False',
        ):
            self.assertIn(token, self.main_body)


if __name__ == "__main__":
    unittest.main()
