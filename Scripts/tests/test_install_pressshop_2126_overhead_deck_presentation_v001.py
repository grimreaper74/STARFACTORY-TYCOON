"""Offline guards for the Press Shop 2126 overhead deck presentation lane.

The tests import the installer with an empty ``unreal`` stub.  They exercise
only source receipts, disk hashes, pure layout arithmetic, deletion selectors,
and the script's mutation surface.  They do not launch Unreal, create assets,
clone a map, delete actors, save packages, or write the install receipt.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import types
import unittest
from collections import Counter
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
INSTALLER = (
    PROJECT
    / "Tools"
    / "install_pressshop_2126_overhead_deck_presentation_v001.py"
)
SOURCE_BUILDER = PROJECT / "Tools" / "build_pressshop_2126_overhead_playable_v002.py"


def load_installer_module():
    previous = sys.modules.get("unreal")
    sys.modules["unreal"] = types.ModuleType("unreal")
    try:
        spec = importlib.util.spec_from_file_location(
            "pressshop_overhead_deck_presentation_v001_test_subject",
            INSTALLER,
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        if previous is None:
            sys.modules.pop("unreal", None)
        else:
            sys.modules["unreal"] = previous


MODULE = load_installer_module()


def source_receipt():
    return json.loads(MODULE.SOURCE_RECEIPT.read_text(encoding="utf-8"))


class ExactSourceAndTargetContractTests(unittest.TestCase):
    def test_installer_is_separate_from_source_builder_and_native_files(self):
        self.assertTrue(INSTALLER.is_file())
        self.assertTrue(SOURCE_BUILDER.is_file())
        self.assertNotEqual(INSTALLER.resolve(), SOURCE_BUILDER.resolve())
        source = INSTALLER.read_text(encoding="utf-8")
        self.assertNotIn("LBPressShopOverheadVisualLayerActor.cpp", source)
        self.assertNotIn("LBPressShopOverheadVisualLayerActor.h", source)
        self.assertNotIn("LBPressShopOverheadPresentationActor.cpp", source)
        self.assertNotIn("LBPressShopOverheadPresentationActor.h", source)

    def test_source_and_new_superseding_target_are_exact_and_disjoint(self):
        self.assertEqual(
            MODULE.SOURCE_MAP,
            "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPlayable_v001/"
            "Maps/LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001",
        )
        self.assertEqual(
            MODULE.TARGET_MAP,
            "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPresentation_v002/"
            "Maps/LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002",
        )
        self.assertNotEqual(MODULE.SOURCE_MAP, MODULE.TARGET_MAP)
        self.assertNotIn(MODULE.TARGET_FILE, MODULE.PROTECTED_MAPS)
        self.assertIn(MODULE.SOURCE_FILE, MODULE.PROTECTED_MAPS)
        self.assertEqual(
            MODULE.digest(MODULE.SOURCE_FILE), MODULE.SOURCE_FILE_SHA256
        )

    def test_hash_locked_source_receipt_passes_honestly(self):
        receipt = MODULE.load_and_validate_source_receipt()
        self.assertEqual(receipt["schema"], MODULE.SOURCE_RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], MODULE.SOURCE_RECEIPT_STATUS)
        self.assertTrue(receipt["map_integrated"])
        self.assertFalse(receipt["runtime_ready"])
        self.assertFalse(receipt["runtime_validated"])
        self.assertFalse(receipt["packaged_build_validated"])
        self.assertEqual(
            MODULE.digest(MODULE.SOURCE_RECEIPT),
            MODULE.SOURCE_RECEIPT_SHA256,
        )

    def test_all_protected_map_hashes_are_current(self):
        snapshot = MODULE.protected_snapshot()
        self.assertEqual(len(snapshot), 6)
        self.assertEqual(
            snapshot[MODULE.SOURCE_FILE.as_posix()], MODULE.SOURCE_FILE_SHA256
        )
        authority = next(
            path for path in MODULE.PROTECTED_MAPS
            if path.name == "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
        )
        self.assertEqual(
            snapshot[authority.as_posix()],
            "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
        )


class NativeDeckDesignContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = MODULE.validate_design_contract()
        cls.boxes = list(cls.design["box_specs"])
        cls.texts = list(cls.design["text_specs"])

    def test_palette_is_coherent_unlit_candidate_material_set(self):
        by_id = {row["id"]: row for row in MODULE.MATERIAL_SPECS}
        self.assertEqual(set(by_id), {"deck", "zone", "cream", "yellow"})
        self.assertEqual(by_id["deck"]["srgb_hex"], "#171D21")
        self.assertEqual(by_id["zone"]["srgb_hex"], "#91AA9C")
        self.assertEqual(by_id["cream"]["srgb_hex"], "#E8DEC2")
        self.assertEqual(by_id["yellow"]["srgb_hex"], "#E1B94F")
        for row in MODULE.MATERIAL_SPECS:
            linear = MODULE.srgb_hex_to_linear(row["srgb_hex"])
            self.assertEqual(len(linear), 3)
            self.assertTrue(all(0.0 <= value <= 1.0 for value in linear))
            self.assertTrue(row["name"].endswith("_Unlit_v001"))

    def test_exact_native_geometry_and_label_counts(self):
        self.assertEqual(len(self.boxes), 64)
        self.assertEqual(len(self.texts), 15)
        self.assertEqual(len(MODULE.CAMERA_SPECS), 3)
        self.assertEqual(
            self.design["box_role_counts"],
            {
                "Deck": 1,
                "DeckBorder": 4,
                "StationPad": 12,
                "StationKey": 12,
                "FlowLane": 1,
                "FlowEdge": 4,
                "FlowConnector": 6,
                "FlowArrow": 24,
            },
        )
        self.assertEqual(
            self.design["text_role_counts"],
            {"StationLabel": 12, "DeckTitle": 1, "FlowLabel": 2},
        )

    def test_station_pads_are_ordered_nonoverlapping_and_labelled(self):
        pads = list(MODULE.STATION_PADS)
        self.assertEqual(
            [row["id"] for row in pads],
            [
                "IN01", "IN02", "IN03", "IN04_05", "S01", "S02",
                "S03", "S04", "S05", "S06", "S07_INSPECT", "S07_PALLET",
            ],
        )
        previous_end = None
        for row in pads:
            start = row["center_y"] - row["length_y"] / 2.0
            end = row["center_y"] + row["length_y"] / 2.0
            if previous_end is not None:
                self.assertGreaterEqual(start - previous_end, 40.0)
            previous_end = end
            self.assertIn("\n", row["text"])
        station_texts = [row for row in self.texts if row["role"] == "StationLabel"]
        self.assertEqual(len(station_texts), len(pads))

    def test_material_flow_is_a_cream_lane_with_yellow_edges_and_arrows(self):
        lane = [row for row in self.boxes if row["role"] == "FlowLane"]
        edges = [row for row in self.boxes if row["role"] == "FlowEdge"]
        arrows = [row for row in self.boxes if row["role"] == "FlowArrow"]
        connectors = [row for row in self.boxes if row["role"] == "FlowConnector"]
        self.assertEqual(len(lane), 1)
        self.assertEqual(lane[0]["material_id"], "cream")
        self.assertEqual({row["material_id"] for row in edges}, {"yellow"})
        self.assertEqual({row["material_id"] for row in arrows}, {"yellow"})
        self.assertEqual({row["material_id"] for row in connectors}, {"cream"})
        self.assertEqual(len(arrows), len(MODULE.FLOW_ARROW_Y) * 3)
        self.assertEqual(tuple(sorted(MODULE.FLOW_ARROW_Y)), MODULE.FLOW_ARROW_Y)

    def test_all_presentation_surfaces_stay_below_sprite_zero_plane(self):
        for row in self.boxes:
            top_z = row["location_cm"][2] + row["dimensions_cm"][2] / 2.0
            self.assertLessEqual(top_z, MODULE.PRESENTATION_TOP_Z + 0.001)
        deck = next(row for row in self.boxes if row["id"] == "DECK_BASE")
        self.assertEqual(deck["material_id"], "deck")
        self.assertEqual(deck["dimensions_cm"][:2], MODULE.DECK_SIZE_XY)

    def test_no_generated_geometry_or_text_implies_a_roof(self):
        generated = self.boxes + self.texts
        for row in generated:
            self.assertFalse(MODULE.is_roof_record({
                "label": row["label"],
                "tags": [MODULE.PASS_TAG, MODULE.ROOFLESS_TAG],
            }))
        self.assertFalse(MODULE.is_roof_record({
            "label": "roofless deck overview",
            "tags": [MODULE.ROOFLESS_TAG],
        }))
        self.assertTrue(MODULE.is_roof_record({
            "label": "PT_LB_WHOLE_RoofLiner_01",
            "tags": [],
        }))

    def test_cameras_are_true_overhead_and_tighter_than_source(self):
        source_widths = [17600.0, 10800.0]
        target_widths = [row["ortho_width_cm"] for row in MODULE.CAMERA_SPECS]
        self.assertEqual(MODULE.CAMERA_ROTATION, (-90.0, 0.0, 0.0))
        self.assertLess(target_widths[0], source_widths[0])
        self.assertLess(target_widths[1], source_widths[1])
        steam = next(row for row in MODULE.CAMERA_SPECS if row["id"] == "steam_hero")
        self.assertEqual(steam["center_xy_cm"], (-8990.75, 11200.0))
        self.assertEqual(steam["ortho_width_cm"], 6900.0)
        self.assertEqual(
            set(steam["additional_tags"]),
            {"LB.SteamReviewCamera", "LB.PressShop.SteamHero.v002"},
        )
        for row in MODULE.CAMERA_SPECS:
            margins = MODULE.camera_margins(row)
            self.assertGreaterEqual(
                margins["screen_horizontal_world_y_cm"],
                MODULE.CAMERA_MIN_MARGIN_CM,
            )
            self.assertGreaterEqual(
                margins["screen_vertical_world_x_cm"],
                MODULE.CAMERA_MIN_MARGIN_CM,
            )


class ExactLegacyPresentationSelectorTests(unittest.TestCase):
    def test_receipted_source_has_the_exact_legacy_removal_set(self):
        receipt = source_receipt()
        rows = list(receipt["pre_existing_actor_fingerprints_after"].values())
        removals = [row for row in rows if MODULE.legacy_removal_reason(row)]
        self.assertEqual(len(rows), MODULE.EXPECTED_SOURCE_PRE_EXISTING_ACTORS)
        self.assertEqual(len(removals), 13687)
        self.assertEqual(
            Counter(MODULE.legacy_removal_reason(row) for row in removals),
            Counter({
                "legacy_visual_only_not_wip": 13671,
                "onefactory_hism_shell": 8,
                "legacy_management_camera": 1,
                "legacy_unbound_presentation_class": 7,
            }),
        )
        self.assertEqual(
            len(removals) + MODULE.EXPECTED_SOURCE_CAMERAS,
            MODULE.EXPECTED_SOURCE_LEGACY_REMOVALS,
        )
        self.assertFalse(any(
            token in row["class_path"]
            for row in removals
            for token in MODULE.PROTECTED_NATIVE_CLASS_TOKENS
        ))

    def test_visual_layer_and_native_adapter_tags_always_win_preservation(self):
        common = {
            "class_path": "/Script/Engine.StaticMeshActor",
            "tags": [MODULE.VISUAL_ONLY_TAG, MODULE.NOT_WIP_TAG],
        }
        layer = copy.deepcopy(common)
        layer["tags"].append(MODULE.VISUAL_LAYER_TAG)
        adapter = copy.deepcopy(common)
        adapter["tags"].append(MODULE.PRESENTATION_TAG)
        self.assertIsNone(MODULE.legacy_removal_reason(layer))
        self.assertIsNone(MODULE.legacy_removal_reason(adapter))

    def test_visual_only_requires_explicit_not_wip_contract(self):
        record = {
            "class_path": "/Script/Engine.StaticMeshActor",
            "tags": [MODULE.VISUAL_ONLY_TAG],
        }
        self.assertIsNone(MODULE.legacy_removal_reason(record))
        record["tags"].append(MODULE.NOT_WIP_TAG)
        self.assertEqual(
            MODULE.legacy_removal_reason(record),
            "legacy_visual_only_not_wip",
        )

    def test_no_fuzzy_roof_label_drives_deletion(self):
        record = {
            "label": "Unclassified roof-like machine component",
            "class_path": "/Script/Engine.StaticMeshActor",
            "tags": [],
        }
        self.assertTrue(MODULE.is_roof_record(record))
        self.assertIsNone(MODULE.legacy_removal_reason(record))

    def test_authority_classes_are_never_selected(self):
        for class_path in (
            "/Script/LineBossCarFactory.LBOneFactoryBootstrap",
            "/Script/LineBossCarFactory.LBPressShopBuildAuthority",
        ):
            record = {
                "class_path": class_path,
                "tags": [MODULE.VISUAL_ONLY_TAG, MODULE.NOT_WIP_TAG],
            }
            self.assertIsNone(MODULE.legacy_removal_reason(record))


class FailedRunRecoveryGuardTests(unittest.TestCase):
    def test_exact_failed_run_fingerprint_is_complete_and_log_locked(self):
        rows = list(MODULE.FAILED_RUN_ARTIFACTS)
        self.assertEqual(len(rows), 5)
        self.assertEqual({row["asset"] for row in rows}, {
            MODULE.TARGET_MAP,
            MODULE.MATERIAL_ROOT + "/M_CA_MW_PS2126_DeckCharcoal_Unlit_v001",
            MODULE.MATERIAL_ROOT + "/M_CA_MW_PS2126_FlowCream_Unlit_v001",
            MODULE.MATERIAL_ROOT + "/M_CA_MW_PS2126_SafetyYellow_Unlit_v001",
            MODULE.MATERIAL_ROOT + "/M_CA_MW_PS2126_ZonePaleGreen_Unlit_v001",
        })
        self.assertEqual(sum(row["bytes"] for row in rows), 33989767)
        self.assertTrue(all(len(row["sha256"]) == 64 for row in rows))
        self.assertTrue(MODULE.FAILED_RUN_LOG.is_file())
        self.assertEqual(
            MODULE.digest(MODULE.FAILED_RUN_LOG), MODULE.FAILED_RUN_LOG_SHA256
        )
        log_text = MODULE.FAILED_RUN_LOG.read_text(encoding="utf-8")
        self.assertIn(MODULE.FAILED_RUN_ERROR, log_text)
        self.assertNotIn(
            "PRESSSHOP_2126_OVERHEAD_DECK_PRESENTATION_V001_PASS", log_text
        )

    def test_pure_recovery_validator_accepts_only_exact_disk_and_registry_sets(self):
        exact_disk = MODULE.expected_failed_run_disk_fingerprints()
        exact_registry = [row["asset"] + "." + row["asset"].rsplit("/", 1)[-1]
                          for row in MODULE.FAILED_RUN_ARTIFACTS]
        MODULE.validate_failed_run_artifact_fingerprints(
            exact_disk, exact_registry
        )

        altered = copy.deepcopy(exact_disk)
        first = next(iter(altered))
        altered[first]["sha256"] = "0" * 64
        with self.assertRaises(MODULE.PresentationGuardError):
            MODULE.validate_failed_run_artifact_fingerprints(
                altered, exact_registry
            )

        extra = copy.deepcopy(exact_disk)
        extra[(MODULE.TARGET_ROOT_DISK / "unexpected.uasset").as_posix()] = {
            "sha256": "1" * 64,
            "bytes": 1,
        }
        with self.assertRaises(MODULE.PresentationGuardError):
            MODULE.validate_failed_run_artifact_fingerprints(extra, exact_registry)
        with self.assertRaises(MODULE.PresentationGuardError):
            MODULE.validate_failed_run_artifact_fingerprints(
                exact_disk, exact_registry[:-1]
            )

    def test_second_recovery_lane_preserves_and_locks_first_recovery_evidence(self):
        self.assertTrue(MODULE.RECOVERY_RECEIPT.is_file())
        self.assertEqual(
            MODULE.digest(MODULE.RECOVERY_RECEIPT),
            MODULE.RECOVERY_RECEIPT_SHA256_AFTER_FIRST_RECOVERY,
        )
        self.assertTrue(MODULE.SECOND_FAILED_RUN_LOG.is_file())
        self.assertEqual(
            MODULE.digest(MODULE.SECOND_FAILED_RUN_LOG),
            MODULE.SECOND_FAILED_RUN_LOG_SHA256,
        )
        second_log = MODULE.SECOND_FAILED_RUN_LOG.read_text(encoding="utf-8")
        self.assertIn(MODULE.SECOND_FAILED_RUN_ERROR, second_log)
        self.assertNotIn(
            "PRESSSHOP_2126_OVERHEAD_DECK_PRESENTATION_V001_PASS", second_log
        )
        rows = list(MODULE.SECOND_FAILED_RUN_ARTIFACTS)
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(len(row["sha256"]) == 64 for row in rows))
        exact_disk = MODULE.expected_failed_run_disk_fingerprints(rows)
        exact_registry = [row["asset"] for row in rows]
        MODULE.validate_failed_run_artifact_fingerprints(
            exact_disk, exact_registry, rows
        )

    def test_third_recovery_lane_locks_profile_last_failure_and_prior_receipt(self):
        self.assertTrue(MODULE.RECOVERY_RECEIPT_V002.is_file())
        self.assertEqual(
            MODULE.digest(MODULE.RECOVERY_RECEIPT_V002),
            MODULE.RECOVERY_RECEIPT_SHA256_AFTER_SECOND_RECOVERY,
        )
        self.assertTrue(MODULE.THIRD_FAILED_RUN_LOG.is_file())
        self.assertEqual(
            MODULE.digest(MODULE.THIRD_FAILED_RUN_LOG),
            MODULE.THIRD_FAILED_RUN_LOG_SHA256,
        )
        third_log = MODULE.THIRD_FAILED_RUN_LOG.read_text(encoding="utf-8")
        self.assertIn(MODULE.THIRD_FAILED_RUN_ERROR, third_log)
        self.assertNotIn(
            "PRESSSHOP_2126_OVERHEAD_DECK_PRESENTATION_V001_PASS", third_log
        )
        rows = list(MODULE.THIRD_FAILED_RUN_ARTIFACTS)
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(len(row["sha256"]) == 64 for row in rows))
        MODULE.validate_failed_run_artifact_fingerprints(
            MODULE.expected_failed_run_disk_fingerprints(rows),
            [row["asset"] for row in rows],
            rows,
        )

    def test_collision_contract_sets_profile_actor_gate_and_ignore_all_channels(self):
        class FakeActor:
            def __init__(self):
                self.enabled = True

            def set_actor_enable_collision(self, value):
                self.enabled = bool(value)

            def get_actor_enable_collision(self):
                return self.enabled

        class FakeComponent:
            def __init__(self):
                self.profile = ""
                self.enabled = "CollisionEnabled.QUERY_AND_PHYSICS"
                self.response = "CollisionResponseType.ECR_BLOCK"

            def set_collision_profile_name(self, value, update_overlaps=True):
                self.profile = str(value)

            def set_collision_response_to_all_channels(self, value):
                self.response = str(value)
                self.profile = "Custom"

            def set_collision_enabled(self, value):
                self.enabled = str(value)

            def set_editor_property(self, _name, _value):
                pass

            def get_collision_enabled(self):
                return self.enabled

            def get_collision_profile_name(self):
                return self.profile

            def get_collision_response_to_channel(self, _channel):
                return self.response

        MODULE.unreal.Name = lambda value: value
        MODULE.unreal.CollisionEnabled = types.SimpleNamespace(
            NO_COLLISION="CollisionEnabled.NO_COLLISION"
        )
        MODULE.unreal.CollisionResponseType = types.SimpleNamespace(
            ECR_IGNORE="CollisionResponseType.ECR_IGNORE"
        )
        MODULE.unreal.CollisionChannel = types.SimpleNamespace(**{
            name: name for name in MODULE.COLLISION_CHANNEL_NAMES
        })
        record = MODULE.disable_and_verify_collision(
            FakeActor(), FakeComponent(), "OFFLINE_TEST"
        )
        self.assertFalse(record["actor_collision_enabled"])
        self.assertEqual(record["collision_profile"], "Custom")
        self.assertEqual(
            record["profile_acceptance"], "CustomWithNoCollisionAndIgnoreAll"
        )
        self.assertIn("NO_COLLISION", record["component_collision_enabled"])
        self.assertEqual(
            tuple(record["ignored_channels"]), MODULE.COLLISION_CHANNEL_NAMES
        )


class MutationSurfaceAndReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = INSTALLER.read_text(encoding="utf-8")
        cls.main_body = cls.source[cls.source.index("def main() -> None:") :]

    def test_all_fail_closed_preflights_precede_target_creation(self):
        create_index = self.main_body.index(
            "new_level_from_template(TARGET_MAP, SOURCE_MAP)"
        )
        for token in (
            "validate_design_contract()",
            "load_and_validate_source_receipt()",
            "protected_snapshot()",
            "recover_exact_failed_run_assets(protected_before)",
            "TARGET_FILE.exists() or remaining_disk_files",
            "does_asset_exist(TARGET_MAP)",
            "remaining_registry_assets",
            "dirty_package_paths()",
            "world_before_name in {SOURCE_MAP, TARGET_MAP}",
            "unreal.load_asset(CUBE_ASSET)",
        ):
            self.assertLess(self.main_body.index(token), create_index, token)

    def test_actor_deletion_is_bounded_to_verified_new_target_world(self):
        create_index = self.main_body.index(
            "new_level_from_template(TARGET_MAP, SOURCE_MAP)"
        )
        active_world_index = self.main_body.index(
            "_world_package_name(world) != TARGET_MAP"
        )
        inventory_index = self.main_body.index(
            "validate_source_world_inventory(records, source_receipt)"
        )
        prefix_index = self.main_body.index(
            "actor_path.startswith(target_actor_prefix)"
        )
        destroy_index = self.main_body.index("actor_subsystem.destroy_actor(actor)")
        self.assertLess(create_index, active_world_index)
        self.assertLess(active_world_index, inventory_index)
        self.assertLess(inventory_index, prefix_index)
        self.assertLess(prefix_index, destroy_index)

    def test_no_source_load_overwrite_or_broad_asset_mutation_surface(self):
        forbidden = (
            "load_map(SOURCE_MAP)",
            "save_asset(SOURCE_MAP)",
            "duplicate_asset(",
            "rename_asset(",
            "delete_asset(",
            "save_directory(",
            "save_dirty_packages(",
            "AssetImportTask",
            "import_asset_tasks",
            "DefaultEngine.ini",
        )
        for token in forbidden:
            self.assertNotIn(token, self.source, token)
        self.assertEqual(
            self.source.count("new_level_from_template(TARGET_MAP, SOURCE_MAP)"),
            1,
        )
        self.assertEqual(self.source.count("save_current_level()"), 1)
        self.assertEqual(self.source.count("delete_directory(TARGET_ROOT)"), 1)
        recovery_body = self.source[
            self.source.index("def recover_exact_failed_run_assets("):
            self.source.index("def _vector(")
        ]
        self.assertLess(
            recovery_body.index("validate_failed_run_artifact_fingerprints"),
            recovery_body.index("delete_directory(TARGET_ROOT)"),
        )
        self.assertLess(
            recovery_body.index("TARGET_ROOT_DISK.resolve() != exact_root"),
            recovery_body.index("delete_directory(TARGET_ROOT)"),
        )

    def test_collision_is_explicitly_disabled_and_read_back_for_boxes_and_text(self):
        helper_body = self.source[
            self.source.index("def disable_and_verify_collision("):
            self.source.index("def spawn_box_actor(")
        ]
        for token in (
            'set_actor_enable_collision(False)',
            'unreal.Name("NoCollision")',
            'set_collision_response_to_all_channels(',
            'unreal.CollisionResponseType.ECR_IGNORE',
            'set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)',
            'get_actor_enable_collision()',
            'get_collision_enabled()',
            'get_collision_profile_name()',
            'get_collision_response_to_channel(channel)',
        ):
            self.assertIn(token, helper_body)
        profile_index = helper_body.index("set_collision_profile_name(")
        self.assertLess(
            profile_index,
            helper_body.index("set_collision_response_to_all_channels("),
        )
        self.assertLess(
            profile_index, helper_body.index("set_collision_enabled(")
        )
        self.assertIn(
            'normalised_profile not in {"nocollision", "custom"}', helper_body
        )
        self.assertEqual(
            self.source.count("disable_and_verify_collision(actor, component"), 2
        )

    def test_creation_scope_uses_only_native_cube_text_camera_and_material(self):
        for token in (
            MODULE.CUBE_ASSET,
            "unreal.StaticMeshActor",
            "unreal.TextRenderActor",
            "unreal.CameraActor",
            "unreal.MaterialFactoryNew()",
            "unreal.MaterialShadingModel.MSM_UNLIT",
            "unreal.MaterialProperty.MP_EMISSIVE_COLOR",
        ):
            self.assertIn(token, self.source)
        self.assertNotIn("spawn_actor_from_object", self.source)
        self.assertNotIn("StaticMeshFactory", self.source)

    def test_receipt_is_exclusive_create_and_keeps_claims_honest(self):
        self.assertIn('path.open("xb")', self.source)
        for token in (
            '"candidate_only": True',
            '"protected_authority_map_mutated": False',
            '"roof_created": False',
            '"roof_actor_count_after": 0',
            '"runtime_validated": False',
            '"runtime_ready": False',
            '"packaged_build_validated": False',
            '"visual_capture_validated": False',
            '"steam_capture_validated": False',
        ):
            self.assertIn(token, self.main_body)

    def test_canonical_json_rejects_nan(self):
        with self.assertRaises(ValueError):
            MODULE.canonical_json_bytes({"invalid": float("nan")})


if __name__ == "__main__":
    unittest.main()
