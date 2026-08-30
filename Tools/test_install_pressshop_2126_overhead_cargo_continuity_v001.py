"""Offline contract tests for the guarded v003 Press Shop cargo integrator."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from collections import Counter
from pathlib import Path


TOOL = Path(__file__).with_name(
    "install_pressshop_2126_overhead_cargo_continuity_v001.py"
)
SPEC = importlib.util.spec_from_file_location("pressshop_cargo_map_v001", TOOL)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("could not load cargo-map integration tool")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class PressShopCargoMapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_receipt = MOD.validate_source_receipt()
        cls.registry, cls.manifest = MOD.validate_registry_and_manifest()
        cls.protected = MOD.protected_snapshot(cls.registry)
        cls.specs, cls.deferred = MOD.build_layer_specs(
            cls.registry, cls.manifest
        )

    def test_01_pinned_source_and_candidate_are_separate(self) -> None:
        self.assertEqual(MOD.digest(MOD.SOURCE_FILE), MOD.SOURCE_FILE_SHA256)
        self.assertEqual(
            MOD.digest(MOD.SOURCE_RECEIPT), MOD.SOURCE_RECEIPT_SHA256
        )
        self.assertEqual(
            MOD.SOURCE_MAP,
            "/Game/LineBoss/Candidates/PressShop/"
            "PressShop2126_OverheadPresentation_v002/Maps/"
            "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002",
        )
        self.assertEqual(
            MOD.TARGET_MAP,
            "/Game/LineBoss/Candidates/PressShop/"
            "PressShop2126_OverheadCargo_v003/Maps/"
            "LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003",
        )
        self.assertNotEqual(MOD.SOURCE_MAP, MOD.TARGET_MAP)
        self.assertFalse(MOD.TARGET_FILE.is_relative_to(MOD.SOURCE_FILE.parent))

    def test_02_locked_cargo_inputs_match_reviewed_hashes(self) -> None:
        self.assertEqual(MOD.digest(MOD.CARGO_REGISTRY), MOD.CARGO_REGISTRY_SHA256)
        self.assertEqual(MOD.digest(MOD.CARGO_MANIFEST), MOD.CARGO_MANIFEST_SHA256)
        self.assertEqual(MOD.digest(MOD.CARGO_IMPORTER), MOD.CARGO_IMPORTER_SHA256)
        self.assertEqual(
            MOD.digest(MOD.CARGO_IMPORT_RECEIPT),
            MOD.CARGO_IMPORT_RECEIPT_SHA256,
        )
        import_receipt = MOD.validate_import_receipt(self.registry)
        self.assertEqual(
            import_receipt["status"],
            "PASS__ASSETS_IMPORTED__NOT_MAP_INTEGRATED",
        )
        self.assertFalse(import_receipt["map_loaded_by_tool"])
        self.assertFalse(import_receipt["map_saved_by_tool"])
        self.assertEqual(len(import_receipt["created_assets"]), 30)
        self.assertEqual(len(self.registry["assets"]), 17)
        self.assertTrue(
            self.registry["map_builder_must_revalidate_all_hashes"]
        )
        self.assertTrue(
            self.registry["map_builder_must_not_spawn_reference_only_rows"]
        )

    def test_03_all_protected_hashes_pass_including_v002_source(self) -> None:
        self.assertEqual(
            self.protected["overhead_presentation_v002_source"],
            MOD.SOURCE_FILE_SHA256,
        )
        self.assertEqual(len(self.protected), 5)
        self.assertEqual(
            self.protected["onefactory_authority"],
            "f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c",
        )

    def test_04_layer_plan_is_exactly_26_native_layers(self) -> None:
        validation = MOD.validate_layer_specs(
            self.specs, self.registry, self.manifest, self.deferred
        )
        self.assertEqual(validation["layer_count"], 26)
        self.assertEqual(validation["motion_range_count"], 14)
        self.assertEqual(
            Counter(row["metadata"]["LayerRole"] for row in self.specs),
            Counter({"MovingOverlay": 14, "Workpiece": 7, "CyanTransfer": 5}),
        )
        self.assertTrue(
            {row["metadata"]["LayerRole"] for row in self.specs}
            <= MOD.SUPPORTED_ROLES
        )

    def test_05_every_panel_segment_keeps_exact_manifest_endpoints(self) -> None:
        source_segments = {
            row["segment_id"]: row
            for row in self.manifest["route_contract"]["panel_process"]["segments"]
        }
        transfers = [
            row for row in self.specs
            if row["metadata"]["LayerRole"] == "CyanTransfer"
        ]
        self.assertEqual(len(transfers), 5)
        for row in transfers:
            segment_id = row["spec_id"].removeprefix("TRANSFER_")
            source = source_segments[segment_id]
            self.assertEqual(
                row["metadata"]["MotionStart"]["translation_cm"],
                source["start_world_anchor_cm"],
            )
            self.assertEqual(
                row["metadata"]["MotionEnd"]["translation_cm"],
                source["end_world_anchor_cm"],
            )

    def test_06_s01_uses_exact_cart_and_decoiler_manifest_route(self) -> None:
        row = next(
            item for item in self.specs
            if item["spec_id"] == "BARE_S01_CART_TO_DECOILER"
        )
        self.assertEqual(row["metadata"]["MachineId"], "S01_DESTACK_LOAD")
        self.assertEqual(row["metadata"]["LayerRole"], "MovingOverlay")
        self.assertEqual(row["metadata"]["StateId"], "LOAD")
        self.assertEqual(
            row["metadata"]["MotionChannel"], "CoilTransferToDecoiler"
        )
        self.assertEqual(
            row["metadata"]["MotionStart"]["translation_cm"],
            [-9265.74999, 5944.187235, 4.2],
        )
        self.assertEqual(
            row["metadata"]["MotionEnd"]["translation_cm"],
            [-8908.74999, 6262.687255, 4.2],
        )

    def test_07_s07_panel_layers_use_only_current_pose_states(self) -> None:
        rows = [
            row for row in self.specs
            if row["spec_id"].startswith("S07_PANEL_")
        ]
        self.assertEqual(len(rows), 4)
        self.assertEqual(
            {row["metadata"]["StateId"] for row in rows},
            {"PARKED", "PICK", "INSPECT", "PLACE"},
        )
        self.assertTrue(all(
            row["metadata"]["MachineId"] == "S07_INSPECTION"
            and row["metadata"]["LayerRole"] == "MovingOverlay"
            for row in rows
        ))

    def test_08_s07_unrepresentable_states_are_explicit_and_not_fabricated(self) -> None:
        deferred = {row["source_state_id"]: row for row in self.deferred}
        self.assertEqual(
            set(deferred),
            {
                "PALLET_EMPTY",
                "PALLET_LOADED_01",
                "PALLET_LOADED_04",
                "PALLET_LOADED_08_DISPATCH_READY",
            },
        )
        self.assertEqual(
            deferred["PALLET_LOADED_01"]["current_visual_mapping"],
            "DEFERRED_NOT_SPAWNED",
        )
        self.assertEqual(
            deferred["PALLET_LOADED_04"]["current_visual_mapping"],
            "DEFERRED_NOT_SPAWNED",
        )
        spawned_assets = {row["asset_id"] for row in self.specs}
        self.assertNotIn("S07_PALLET_STACK_01", spawned_assets)
        self.assertNotIn("S07_PALLET_STACK_04", spawned_assets)
        self.assertIn("S07_PALLET_STACK_08", spawned_assets)

    def test_09_reference_only_zero_alpha_row_is_never_spawned(self) -> None:
        self.assertNotIn(
            "S07_PALLET_STACK_00", {row["asset_id"] for row in self.specs}
        )
        reference_rows = [
            row for row in self.registry["assets"]
            if row["import_action"]
            == "REFERENCE_ONLY_ZERO_ALPHA__EMPTY_STATE_USES_NO_OVERLAY"
        ]
        self.assertEqual(len(reference_rows), 1)
        self.assertEqual(reference_rows[0]["asset_id"], "S07_PALLET_STACK_00")

    def test_10_tampered_transfer_endpoint_fails_closed(self) -> None:
        damaged = copy.deepcopy(self.specs)
        row = next(
            item for item in damaged
            if item["metadata"]["LayerRole"] == "CyanTransfer"
        )
        row["metadata"]["MotionEnd"]["translation_cm"][1] += 1.0
        with self.assertRaisesRegex(
            MOD.CargoMapGuardError, "endpoints differ from manifest"
        ):
            MOD.validate_layer_specs(
                damaged, self.registry, self.manifest, self.deferred
            )

    def test_11_unsupported_role_and_intermediate_stack_fail_closed(self) -> None:
        bad_role = copy.deepcopy(self.specs)
        bad_role[0]["metadata"]["LayerRole"] = "PalletCount"
        with self.assertRaisesRegex(MOD.CargoMapGuardError, "unsupported"):
            MOD.validate_layer_specs(
                bad_role, self.registry, self.manifest, self.deferred
            )
        bad_asset = copy.deepcopy(self.specs)
        bad_asset[0]["asset_id"] = "S07_PALLET_STACK_01"
        with self.assertRaisesRegex(
            MOD.CargoMapGuardError, "intermediate pallet counts"
        ):
            MOD.validate_layer_specs(
                bad_asset, self.registry, self.manifest, self.deferred
            )

    def test_12_integrator_contains_no_map_deletion_or_source_save_lane(self) -> None:
        text = TOOL.read_text(encoding="utf-8")
        self.assertNotIn("destroy_actor(", text)
        self.assertNotIn("delete_directory(", text)
        self.assertNotIn("rename_asset(", text)
        self.assertNotIn("save_loaded_asset(", text)
        self.assertIn("new_level_from_template(TARGET_MAP, SOURCE_MAP)", text)
        self.assertIn("save_current_level()", text)
        self.assertIn("source_actor_mutated_count\": 0", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
