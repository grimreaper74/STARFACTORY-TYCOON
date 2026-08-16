"""Offline guards for the exact pre-Meshy v449 owned promotion lane."""

from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path
import sys
import unittest


PROJECT = Path(__file__).resolve().parents[2]
SCRIPTS = PROJECT / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

BASE = importlib.import_module("one_factory_detailed_press_v001_contract")
CONTRACT = importlib.import_module(
    "one_factory_detailed_press_v449_promotion_contract"
)
IMPORTER = SCRIPTS / "promote_one_factory_detailed_press_v449_owned_v001.py"
VALIDATOR = (
    SCRIPTS
    / "validate_one_factory_detailed_press_v449_owned_fresh_load_v001.py"
)


class FrozenPromotionContractTests(unittest.TestCase):
    def test_exact_source_and_protected_hashes_are_pinned(self):
        result = CONTRACT.validate_source(PROJECT)
        self.assertEqual(result["immutable_source_asset_count"], 14)
        self.assertEqual(result["source_material_count"], 13)
        self.assertEqual(result["material_slot_count"], 306)
        self.assertEqual(result["destination_asset_count"], 14)
        self.assertEqual(len(result["material_slot_histogram"]), 13)
        self.assertEqual(
            result["status"],
            "PASS__EXACT_PRE_MESHY_V449_PROMOTION_SOURCE_PINNED",
        )

    def test_destination_is_one_mesh_plus_thirteen_exact_owned_materials(self):
        self.assertEqual(len(CONTRACT.DEST_ASSET_PACKAGES), 14)
        self.assertEqual(len(CONTRACT.DEST_MATERIAL_PACKAGES), 13)
        self.assertEqual(CONTRACT.DEST_ASSET_PACKAGES[0], CONTRACT.DEST_MESH)
        self.assertEqual(
            set(CONTRACT.SOURCE_TO_DEST_MATERIAL), set(BASE.MATERIAL_HASHES)
        )
        self.assertEqual(
            set(CONTRACT.SOURCE_TO_DEST_MATERIAL.values()),
            set(CONTRACT.DEST_MATERIAL_PACKAGES),
        )
        for package in CONTRACT.DEST_ASSET_PACKAGES:
            self.assertTrue(package.startswith(CONTRACT.DEST_ROOT + "/"))
            self.assertIsNone(BASE.forbidden_reference_reason(package))

    def test_exact_306_slot_order_maps_only_to_owned_materials(self):
        source_slots = CONTRACT.source_slot_packages(PROJECT)
        destination_slots = CONTRACT.expected_destination_slot_objects(PROJECT)
        self.assertEqual(len(source_slots), 306)
        self.assertEqual(len(destination_slots), 306)
        self.assertEqual(set(source_slots), set(BASE.MATERIAL_HASHES))
        self.assertEqual(
            {value.split(".", 1)[0] for value in destination_slots},
            set(CONTRACT.DEST_MATERIAL_PACKAGES),
        )

    def test_state_is_either_pristine_or_a_valid_completed_build(self):
        receipt = PROJECT / CONTRACT.BUILD_RECEIPT_RELATIVE
        existing = [
            package
            for package in CONTRACT.DEST_ASSET_PACKAGES
            if CONTRACT.package_file(PROJECT, package).exists()
        ]
        if not receipt.exists():
            self.assertEqual(existing, [])
        else:
            self.assertEqual(set(existing), set(CONTRACT.DEST_ASSET_PACKAGES))
            CONTRACT.validate_build_receipt(
                PROJECT, json.loads(receipt.read_text(encoding="utf-8"))
            )


class PromotionToolStaticSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.importer = IMPORTER.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")

    def test_unreal_scripts_parse_without_importing_unreal(self):
        self.assertIsInstance(ast.parse(self.importer, str(IMPORTER)), ast.Module)
        self.assertIsInstance(ast.parse(self.validator, str(VALIDATOR)), ast.Module)

    def test_neither_unreal_script_can_load_or_save_a_map(self):
        combined = (self.importer + self.validator).lower()
        for forbidden_call in (
            "load_map(",
            "new_level(",
            "save_current_level(",
            "save_map(",
            "save_all_dirty_levels(",
            "editor_save_all(",
            "spawn_actor",
            "destroy_actor",
        ):
            self.assertNotIn(forbidden_call, combined)
        self.assertIn('"map_loaded": false', combined)
        self.assertIn('"map_saved": false', combined)

    def test_mutation_is_scoped_to_exact_new_owned_packages(self):
        self.assertIn("validate_destination_absent(ROOT)", self.importer)
        self.assertIn("TOOLS.duplicate_asset", self.importer)
        self.assertIn("for package in DEST_ASSET_PACKAGES", self.importer)
        self.assertIn("rollback_candidates", self.importer)
        self.assertIn("package_file(ROOT, package).exists()", self.importer)
        self.assertIn("dependencies = registry.get_dependencies(package, options) or []", self.importer)
        self.assertIn("source_dependencies != set(MATERIAL_HASHES)", self.importer)
        self.assertIn("live_binding_material_packages", self.importer)
        self.assertIn("EXACT_LIVE_306_STATIC_MESH_MATERIAL_BINDINGS", self.importer)
        self.assertIn(
            "persisted_asset_registry_dependency_closure_deferred_to_fresh_process",
            self.importer,
        )
        self.assertIn("source_asset_hashes(ROOT)", self.importer)
        self.assertNotIn("rename_asset(", self.importer.lower())
        self.assertNotIn("consolidate_assets(", self.importer.lower())

    def test_fresh_validator_rechecks_material_classes_and_dependency_closure(self):
        self.assertIn("DEST_MATERIAL_PACKAGES", self.validator)
        self.assertIn("unreal.MaterialInterface", self.validator)
        self.assertIn("unexpected_dependencies", self.validator)
        self.assertIn("dependencies = registry.get_dependencies(package, options) or []", self.validator)
        self.assertIn("set(dependency_rows[DEST_MESH])", self.validator)
        self.assertIn("source_asset_hashes(ROOT)", self.validator)

    def test_both_unreal_processes_require_engine_entry_not_a_project_map(self):
        for source in (self.importer, self.validator):
            self.assertIn("require_engine_entry_bootstrap_world", source)
            self.assertIn('path.startswith("/Engine/Maps/Entry.")', source)


if __name__ == "__main__":
    unittest.main()
