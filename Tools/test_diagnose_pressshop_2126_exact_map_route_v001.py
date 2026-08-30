"""Offline contract tests for the read-only V004 route diagnostic."""

from __future__ import annotations

import ast
import importlib.util
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "diagnose_pressshop_2126_exact_map_route_v001.py"


def load_module():
    spec = importlib.util.spec_from_file_location("route_diag_v001", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RouteDiagnosticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SCRIPT.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        cls.module = load_module()

    def test_exact_v004_map_and_append_only_output_are_pinned(self) -> None:
        self.assertIn("PressShop2126_OverheadPresentation_v004", self.module.TARGET_MAP)
        self.assertEqual(
            self.module.OUTPUT_RECEIPT.name,
            "route_preflight_diagnostic_v001.json",
        )
        self.assertIn("if OUTPUT_RECEIPT.exists()", self.source)
        self.assertIn("refusing to overwrite route diagnostic", self.source)

    def test_all_five_authority_types_are_covered(self) -> None:
        layout_classes = {
            spec["authority_class"] for spec in self.module.LAYOUT_SPECS
        }
        self.assertEqual(layout_classes, {
            "LBOneFactoryPressStarterLayoutAuthority",
            "LBOneFactoryBodyWeldStarterLayoutAuthority",
            "LBOneFactoryPaintStarterLayoutAuthority",
            "LBOneFactoryAssemblyStarterLayoutAuthority",
        })
        self.assertIn("LBOneFactoryProductionFlowAuthority", self.source)

    def test_four_layouts_and_ledger_are_captured_and_validated(self) -> None:
        self.assertIn("actor.capture_layout()", self.source)
        self.assertIn("library.validate_starter_layout(state)", self.source)
        self.assertIn("production_actors[0].capture_ledger()", self.source)
        self.assertIn("LBOneFactoryProductionFlowLibrary.validate_ledger", self.source)
        self.assertIn("differences_from_canonical", self.source)

    def test_none_is_fail_closed_for_all_bool_out_queries(self) -> None:
        validation = self.module.reflected_bool_out(None)
        route = self.module.reflected_route(None)
        self.assertFalse(validation["native_success"])
        self.assertFalse(route["native_success"])
        self.assertIn("NATIVE_FALSE", validation["raw_shape"])
        self.assertIn("NATIVE_FALSE", route["raw_shape"])

    def test_read_only_ast_has_no_runtime_or_content_mutation_calls(self) -> None:
        forbidden = {
            "set_editor_property", "setattr", "restore_layout", "restore_ledger",
            "commission", "dispatch_next_open_contract", "create_runtime_vehicle_order",
            "start_vehicle", "tick_vehicle", "tick_automatic_flow",
            "submit_runtime_quality_result", "submit_quality_result",
            "reset_quality_after_rework", "refresh_from_runtime",
            "save_map", "save_asset", "save_loaded_asset", "import_asset_tasks",
            "build", "cook", "package_project", "delete_asset", "rename_asset",
        }
        called = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                function = node.func
                if isinstance(function, ast.Attribute):
                    called.add(function.attr)
                elif isinstance(function, ast.Name):
                    called.add(function.id)
        self.assertFalse(forbidden & called, sorted(forbidden & called))

    def test_only_query_side_native_methods_are_named(self) -> None:
        required = {
            "capture_layout", "validate_starter_layout",
            "make_canonical_starter_layout", "capture_ledger",
            "validate_ledger", "get_configured_station_route",
        }
        called = {
            node.func.attr
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(required.issubset(called), sorted(required - called))

    def test_callback_is_registered_before_pie_starts(self) -> None:
        registered = self.source.index("register_slate_post_tick_callback")
        started = self.source.index("editor_play_simulate()")
        self.assertLess(registered, started)

    def test_exact_map_and_install_receipt_hashes_are_frozen(self) -> None:
        tracked = {str(path): digest for path, digest in self.module.TRACKED_FILES.items()}
        map_rows = [value for key, value in tracked.items()
                    if key.endswith("OverheadPresentation_v004.umap")]
        receipt_rows = [value for key, value in tracked.items()
                        if key.endswith("install_receipt_v001.json")]
        self.assertEqual(map_rows, [
            "ab77d9bc327e65fa5bf8b8efd4d6666252247be1420070563f83bb099d98fe9f"
        ])
        self.assertEqual(receipt_rows, [
            "9c2bca410ebb40a534cdaa65a41c433c6f535df566ae209865f6fe5053a706d4"
        ])

    def test_recursive_diff_reports_exact_field_paths(self) -> None:
        actual = {"stations": [{"station_id": "A", "version": 2}]}
        canonical = {"stations": [{"station_id": "A", "version": 1}]}
        self.assertEqual(self.module._diff(actual, canonical), [{
            "path": "stations[0].version", "actual": 2, "canonical": 1,
        }])

    def test_receipt_declares_no_mutation_or_save_lane(self) -> None:
        self.assertIn('"read_only_query_contract": True', self.source)
        self.assertIn('"runtime_mutation_api_called": False', self.source)
        self.assertIn(
            '"save_import_build_cook_or_package_api_called": False',
            self.source,
        )
        self.assertIn("fingerprints_unchanged", self.source)
        self.assertIn("dirty_package_set_unchanged_during_pie", self.source)


if __name__ == "__main__":
    unittest.main()
