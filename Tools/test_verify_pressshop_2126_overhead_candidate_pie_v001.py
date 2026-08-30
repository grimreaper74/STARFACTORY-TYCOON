"""Offline tests for the guarded exact-map Press Shop 2126 PIE verifier."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock


TOOLS = Path(__file__).resolve().parent
SUBJECT = TOOLS / "verify_pressshop_2126_overhead_candidate_pie_v001.py"
SPEC = importlib.util.spec_from_file_location("exact_map_pie_v001", SUBJECT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class ExactMapPieOfflineTests(unittest.TestCase):
    def test_v003_profile_is_frozen(self) -> None:
        profile = module.resolve_profile({})
        self.assertEqual(profile.key, "v003")
        self.assertEqual(
            profile.expected_map_sha256,
            "5eae51f2a7d3e1c72deb4fd455d57a6339dee061840b7d062c5ddf680ab6100f",
        )
        self.assertEqual(
            profile.expected_receipt_sha256,
            "0d58168d05869693aef7aaac8ddd4d5bac3e7e71785b4b4db6d6f32cd6569619",
        )
        self.assertTrue(profile.target_map.endswith("OverheadCargo_v003"))
        self.assertFalse(profile.expects_press_inspection_quality_gate)
        self.assertEqual(profile.expected_topology_prefix,
                         "OF_RUNTIME_TOPOLOGY_V001_")
        self.assertEqual(profile.output_schema,
                         "cairnwell.press_shop.exact_map_pie_receipt.v001")
        self.assertEqual(profile.output_receipt.name,
                         "exact_map_pie_receipt_v001.json")

    def test_v003_rejects_hash_override(self) -> None:
        with self.assertRaises(module.GuardError):
            module.resolve_profile({
                module.PROFILE_ENV: "v003",
                module.MAP_SHA_ENV: "0" * 64,
            })

    def test_v004_fails_closed_until_both_hashes_are_pinned(self) -> None:
        with self.assertRaises(module.GuardError):
            module.resolve_profile({module.PROFILE_ENV: "v004"})
        with self.assertRaises(module.GuardError):
            module.resolve_profile({
                module.PROFILE_ENV: "v004",
                module.RECEIPT_SHA_ENV: "a" * 64,
            })
        profile = module.resolve_profile({
            module.PROFILE_ENV: "v004",
            module.RECEIPT_SHA_ENV: "a" * 64,
            module.MAP_SHA_ENV: "b" * 64,
        })
        self.assertEqual(profile.expected_receipt_sha256, "a" * 64)
        self.assertEqual(profile.expected_map_sha256, "b" * 64)
        self.assertTrue(profile.target_map.endswith("OverheadPresentation_v004"))
        self.assertTrue(profile.expects_press_inspection_quality_gate)
        self.assertEqual(profile.expected_topology_prefix,
                         "OF_RUNTIME_TOPOLOGY_V002_")
        self.assertEqual(profile.expected_inspection_semantic_stage,
                         "PRESS_PANEL_INSPECTION")
        self.assertEqual(profile.output_schema,
                         "cairnwell.press_shop.exact_map_pie_receipt.v002")
        self.assertEqual(profile.output_receipt.name,
                         "exact_map_pie_receipt_v002.json")

    def test_v006_fails_closed_until_both_hashes_are_pinned(self) -> None:
        with self.assertRaises(module.GuardError):
            module.resolve_profile({module.PROFILE_ENV: "v006"})
        with self.assertRaises(module.GuardError):
            module.resolve_profile({
                module.PROFILE_ENV: "v006",
                module.RECEIPT_SHA_ENV: "a" * 64,
            })
        profile = module.resolve_profile({
            module.PROFILE_ENV: "v006",
            module.RECEIPT_SHA_ENV: "a" * 64,
            module.MAP_SHA_ENV: "b" * 64,
        })
        self.assertEqual(profile.expected_receipt_sha256, "a" * 64)
        self.assertEqual(profile.expected_map_sha256, "b" * 64)
        self.assertTrue(profile.target_map.endswith("OverheadPresentation_v006"))
        self.assertEqual(profile.output_schema,
                         "cairnwell.press_shop.exact_map_pie_receipt.v003")
        self.assertEqual(profile.output_receipt.name,
                         "exact_map_pie_receipt_v003.json")
        self.assertTrue(profile.expects_press_inspection_quality_gate)

    def _actual_v006_receipt(self) -> dict:
        return json.loads(
            module.PROFILES["v006"].source_receipt.read_text(encoding="utf-8"))

    def test_actual_v006_receipt_and_map_match_semantic_contract(self) -> None:
        profile = module.resolve_profile({
            module.PROFILE_ENV: "v006",
            module.RECEIPT_SHA_ENV: (
                "c0b76461edabd0a455e2a4b2bb47774e797d1817d2c38f3ca4d17054934d380c"
            ),
            module.MAP_SHA_ENV: (
                "34840087dad80312c8d7d1e010489fcb277bebfee3597f831aa53d89349ef9ec"
            ),
        })
        receipt = module.load_and_validate_source_receipt(profile)
        module.validate_v006_semantic_fingerprint_contract(receipt)
        self.assertEqual(
            receipt["clone_semantic_fingerprint_normalization"],
            module.V006_SEMANTIC_FINGERPRINT_NORMALIZATION,
        )

    def test_v006_semantic_gate_rejects_missing_or_renamed_fields(self) -> None:
        baseline = self._actual_v006_receipt()
        semantic_key = (
            "visual_layer_actor_semantic_fingerprints_before_sha256"
        )
        missing = dict(baseline)
        missing.pop(semantic_key)
        with self.assertRaises(module.GuardError):
            module.validate_v006_semantic_fingerprint_contract(missing)

        renamed = dict(baseline)
        renamed["visual_layer_actor_fingerprints_before_sha256"] = (
            renamed.pop(semantic_key))
        with self.assertRaises(module.GuardError):
            module.validate_v006_semantic_fingerprint_contract(renamed)

    def test_v006_semantic_gate_rejects_unequal_before_after(self) -> None:
        receipt = self._actual_v006_receipt()
        receipt["cargo_actor_semantic_fingerprints_after_sha256"] = "f" * 64
        self.assertNotEqual(
            receipt["cargo_actor_semantic_fingerprints_before_sha256"],
            receipt["cargo_actor_semantic_fingerprints_after_sha256"],
        )
        with self.assertRaises(module.GuardError):
            module.validate_v006_semantic_fingerprint_contract(receipt)

    def test_v006_semantic_gate_rejects_normalization_drift(self) -> None:
        receipt = self._actual_v006_receipt()
        receipt["clone_semantic_fingerprint_normalization"] += " drift"
        with self.assertRaises(module.GuardError):
            module.validate_v006_semantic_fingerprint_contract(receipt)

    def test_v006_legacy_path_hashes_are_diagnostic_not_authority(self) -> None:
        receipt = self._actual_v006_receipt()
        receipt["source_path_keyed_visual_fingerprints_sha256"] = "1" * 64
        receipt["source_path_keyed_machinery_fingerprints_sha256"] = "2" * 64
        receipt["source_path_keyed_cargo_fingerprints_sha256"] = "3" * 64
        receipt["source_loaded_legacy_path_keyed_fingerprint_hashes"] = {
            key: format(index + 4, "x") * 64
            for index, key in enumerate(
                sorted(module.V006_LEGACY_PATH_GROUP_KEYS))
        }
        receipt["source_loaded_legacy_receipt_path_hash_matches"] = {
            key: True for key in module.V006_LEGACY_PATH_GROUP_KEYS
        }
        # Valid diagnostic shapes may drift; semantic equality remains the
        # sole preservation authority.
        module.validate_v006_semantic_fingerprint_contract(receipt)

    def test_route_profile_contract_distinguishes_legacy_and_v002(self) -> None:
        class Step:
            def __init__(self, **values: object) -> None:
                self.values = values

            def get_editor_property(self, name: str) -> object:
                return self.values[name]

        route = [Step(route_index=index, station_id="S{}".format(index),
                      semantic_stage="PRESSING", quality_gate=False)
                 for index in range(module.EXPECTED_ROUTE_COUNT)]
        route[5] = Step(
            route_index=5,
            station_id=module.EXPECTED_STATION_ROUTE_PREFIX[5],
            semantic_stage="PRESSING",
            quality_gate=False,
        )
        legacy = module.PROFILES["v003"]
        legacy_result = module.validate_route_profile_contract(
            legacy, route, "OF_RUNTIME_TOPOLOGY_V001_1234ABCD")
        self.assertFalse(legacy_result["inspection_step"]["quality_gate"])

        route[5] = Step(
            route_index=5,
            station_id=module.EXPECTED_STATION_ROUTE_PREFIX[5],
            semantic_stage="PRESS_PANEL_INSPECTION",
            quality_gate=True,
        )
        v004 = module.resolve_profile({
            module.PROFILE_ENV: "v004",
            module.RECEIPT_SHA_ENV: "a" * 64,
            module.MAP_SHA_ENV: "b" * 64,
        })
        v002_result = module.validate_route_profile_contract(
            v004, route, "OF_RUNTIME_TOPOLOGY_V002_1234ABCD")
        self.assertTrue(v002_result["inspection_step"]["quality_gate"])
        self.assertEqual(v002_result["inspection_step"]["semantic_stage"],
                         "PRESS_PANEL_INSPECTION")
        with self.assertRaises(module.GuardError):
            module.validate_route_profile_contract(
                legacy, route, "OF_RUNTIME_TOPOLOGY_V002_1234ABCD")

    def test_v002_quality_lifecycle_requires_hold_pass_and_dispatch_release(self) -> None:
        profile = module.resolve_profile({
            module.PROFILE_ENV: "v004",
            module.RECEIPT_SHA_ENV: "a" * 64,
            module.MAP_SHA_ENV: "b" * 64,
        })
        inspection = module.EXPECTED_STATION_ROUTE_PREFIX[5]
        dispatch = module.EXPECTED_STATION_ROUTE_PREFIX[6]
        in_cycle = {
            "station_id": inspection, "station_cursor": 5,
            "progress01": 0.6, "at_quality_gate": True,
            "awaiting_quality_result": False, "quality_state": "PENDING",
        }
        hold = {
            **in_cycle, "progress01": 1.0,
            "awaiting_quality_result": True,
        }
        after_pass = {
            **hold, "awaiting_quality_result": False,
            "quality_state": "PASSED",
        }
        released = {
            **after_pass, "station_id": dispatch, "station_cursor": 6,
            "progress01": 0.0, "at_quality_gate": False,
        }
        module.validate_quality_lifecycle_contract(
            profile, in_cycle, hold, after_pass, released)
        with self.assertRaises(module.GuardError):
            module.validate_quality_lifecycle_contract(
                profile, in_cycle, {**hold, "awaiting_quality_result": False},
                after_pass, released)
        with self.assertRaises(module.GuardError):
            module.validate_quality_lifecycle_contract(
                profile, in_cycle, hold, after_pass,
                {**released, "station_id": inspection})

    def test_actual_v003_receipt_and_map_match_frozen_contract(self) -> None:
        profile = module.resolve_profile({})
        receipt = module.load_and_validate_source_receipt(profile)
        self.assertEqual(receipt["cargo_layer_count"], 26)
        self.assertEqual(receipt["combined_visual_layer_count"], 146)
        self.assertFalse(receipt["collision_enabled_on_cargo_layers"])
        self.assertFalse(receipt["runtime_validated"])

    def test_cargo_contract_has_unique_complete_role_distribution(self) -> None:
        rows = module.CARGO_CONTRACT
        self.assertEqual(len(rows), 26)
        self.assertEqual(len({row[0] for row in rows}), 26)
        roles = {}
        for row in rows:
            roles[row[2]] = roles.get(row[2], 0) + 1
        self.assertEqual(roles, {
            "MOVING_OVERLAY": 14,
            "WORKPIECE": 7,
            "CYAN_TRANSFER": 5,
        })
        self.assertEqual(sum(1 for row in rows if row[5]), 14)
        self.assertEqual(len({row[1] for row in rows}), 14)

    def test_receipt_contract_detects_tampered_binding(self) -> None:
        profile = module.resolve_profile({})
        receipt = json.loads(profile.source_receipt.read_text(encoding="utf-8"))
        receipt["cargo_layers"][0]["metadata_readback"]["MachineId"] = "WRONG"
        with self.assertRaises(module.GuardError):
            module.validate_cargo_receipt_contract(receipt)

    def test_reflected_result_parsers_accept_supported_ue_shapes(self) -> None:
        self.assertEqual(module.parse_bool_reason(True, "x"), "")
        self.assertEqual(module.parse_bool_reason((True, "OK"), "x"), "OK")
        self.assertEqual(
            module.parse_payload_reason(("payload", "OK"), 1, "x"),
            ("payload",),
        )
        self.assertEqual(
            module.parse_payload_reason((True, "payload", "OK"), 1, "x"),
            ("payload",),
        )
        self.assertEqual(
            module.parse_payload_reason(([1, 2], "TOPO", "OK"), 2, "x"),
            ([1, 2], "TOPO"),
        )
        with self.assertRaises(module.GuardError):
            module.parse_bool_reason((False, "NO"), "x")

    def test_reflected_none_is_native_false_and_never_success(self) -> None:
        for parser in (
                lambda: module.parse_bool_reason(None, "ValidateRuntimeFactory"),
                lambda: module.parse_payload_reason(
                    None, 2, "GetConfiguredStationRoute")):
            with self.assertRaises(module.GuardError) as caught:
                parser()
            message = str(caught.exception)
            self.assertIn("returned native false", message)
            self.assertIn("bool+out-parameter", message)
            self.assertIn("suppresses OutReason", message)

    def test_runtime_drivers_freeze_before_warmup_and_read_back(self) -> None:
        class Coordinator:
            def __init__(self) -> None:
                self.values = {
                    "advance_started_vehicles_on_actor_tick": True,
                    "auto_dispatch_open_contracts": True,
                }

            def set_editor_property(self, name: str, value: object) -> None:
                self.values[name] = value

            def get_editor_property(self, name: str) -> object:
                return self.values[name]

        coordinator = Coordinator()
        readback = module.freeze_runtime_drivers(coordinator)
        self.assertEqual(readback, {
            "advance_started_vehicles_on_actor_tick": False,
            "auto_dispatch_open_contracts": False,
        })
        self.assertEqual(coordinator.values, readback)

    def test_checkpoint_plan_spans_cargo_machine_roles(self) -> None:
        ids = [row.checkpoint_id for row in module.CHECKPOINTS]
        self.assertEqual(len(ids), 11)
        self.assertEqual(len(set(ids)), 11)
        self.assertEqual(module.CHECKPOINTS[0].station_id,
                         module.EXPECTED_STATION_ROUTE_PREFIX[0])
        self.assertEqual(module.CHECKPOINTS[-1].station_id,
                         module.EXPECTED_STATION_ROUTE_PREFIX[6])
        self.assertIn("S04_CONTACT", ids)
        self.assertIn("S07_INSPECTION_SCAN", ids)
        self.assertIn("OUTBOUND_PANEL_STILLAGE_TRANSFER", ids)
        self.assertEqual(
            next(row for row in module.CHECKPOINTS
                 if row.checkpoint_id == "S07_INSPECTION_SCAN").expected_state,
            "INSPECT",
        )

    def test_motion_alpha_contracts_match_native_segments(self) -> None:
        by_id = {row.checkpoint_id: row for row in module.CHECKPOINTS}
        self.assertAlmostEqual(by_id["INBOUND_LORRY_UNLOAD"].expected_motion_alpha,
                               0.20 / 0.48)
        self.assertAlmostEqual(by_id["INBOUND_COIL_AGV_TRANSFER"].expected_motion_alpha,
                               (0.75 - 0.48) / 0.52)
        self.assertAlmostEqual(by_id["COIL_PREPARATION_TRANSFER"].expected_motion_alpha,
                               (0.90 - 0.38) / 0.62)
        self.assertAlmostEqual(by_id["S01_COIL_CART_MID_TRANSFER"].expected_motion_alpha,
                               0.5)
        self.assertAlmostEqual(by_id["S06_TO_INSPECTION_TRANSFER"].expected_motion_alpha,
                               0.95)

    def test_world_identity_accepts_pie_prefix_only_for_exact_leaf(self) -> None:
        class Outer:
            def __init__(self, name: str) -> None:
                self.name = name

            def get_name(self) -> str:
                return self.name

        class World:
            def __init__(self, name: str) -> None:
                self.outer = Outer(name)

            def get_outermost(self) -> Outer:
                return self.outer

            def get_path_name(self) -> str:
                return self.outer.name

            def get_name(self) -> str:
                return self.outer.name.rsplit("/", 1)[-1]

        profile = module.PROFILES["v003"]
        leaf = profile.target_map.rsplit("/", 1)[-1]
        self.assertTrue(module.world_is_exact_target(
            World("/Game/X/UEDPIE_0_" + leaf), profile.target_map))
        self.assertFalse(module.world_is_exact_target(
            World("/Game/X/UEDPIE_0_WRONG_MAP"), profile.target_map))

    def test_authority_hashes_are_all_lowercase_sha256(self) -> None:
        self.assertGreaterEqual(len(module.PROTECTED_AUTHORITY_FILES), 5)
        for path, value in module.PROTECTED_AUTHORITY_FILES.items():
            self.assertTrue(path.is_absolute())
            self.assertRegex(value, r"^[0-9a-f]{64}$")

    def test_native_player_activation_counts_wait_for_missing_and_reject_duplicates(self) -> None:
        counts = {
            "player_controller": 0,
            "runtime_coordinator": 1,
            "production": 1,
            "press": 0,
            "body_weld": 0,
            "paint": 0,
            "assembly": 0,
        }
        self.assertFalse(module.activation_counts_ready(counts))
        ready = {key: 1 for key in counts}
        self.assertTrue(module.activation_counts_ready(ready))
        with self.assertRaises(module.GuardError):
            module.activation_counts_ready({**ready, "press": 2})
        with self.assertRaises(module.GuardError):
            module.activation_counts_ready({**ready, "unexpected": 1})

    def test_native_player_activation_contract_requires_controller_commissioning_and_contracts(self) -> None:
        snapshot = {
            "actor_counts": {
                "player_controller": 1,
                "runtime_coordinator": 1,
                "production": 1,
                "press": 1,
                "body_weld": 1,
                "paint": 1,
                "assembly": 1,
            },
            "player_controller_class": module.PLAYER_CONTROLLER_CLASS,
            "primary_player_controller_matches": True,
            "layout_commissioned": {
                "press": True, "body_weld": True,
                "paint": True, "assembly": True,
            },
            "production_department_commissioned": {
                "press": True, "body": True,
                "paint": True, "assembly": True,
            },
            "starter_contract_ids": sorted(
                module.EXPECTED_STARTER_CONTRACT_IDS),
            "production_ledger_validated": True,
        }
        module.validate_native_player_activation_contract(snapshot)
        with self.assertRaises(module.GuardError):
            module.validate_native_player_activation_contract({
                **snapshot,
                "player_controller_class": "/Script/Engine.PlayerController",
            })
        with self.assertRaises(module.GuardError):
            module.validate_native_player_activation_contract({
                **snapshot,
                "layout_commissioned": {
                    **snapshot["layout_commissioned"], "paint": False,
                },
            })
        with self.assertRaises(module.GuardError):
            module.validate_native_player_activation_contract({
                **snapshot,
                "starter_contract_ids": ["CON_STARTER_1"],
            })

    def test_script_is_read_only_with_respect_to_project_content(self) -> None:
        source = SUBJECT.read_text(encoding="utf-8")
        forbidden = (
            "EditorAssetLibrary.save_",
            "EditorLoadingAndSavingUtils.save_",
            "save_current_level",
            "save_map",
            "AssetToolsHelpers",
            "import_asset_tasks",
            "AutomationTool.BuildCookRun",
            "BuildCookRun",
        )
        for token in forbidden:
            self.assertNotIn(token, source)
        self.assertIn("editor_request_begin_play", source)
        self.assertNotIn(".editor_play_simulate()", source)
        self.assertIn("refusing to overwrite exact-map PIE evidence", source)
        self.assertLess(
            source.index("coordinator.get_configured_station_route()"),
            source.index("coordinator.validate_runtime_factory()"),
        )
        self.assertLess(
            source.index("unreal.register_slate_post_tick_callback"),
            source.rindex("editor_request_begin_play"),
        )
        self.assertIn("REGULAR_PIE_NATIVE_PLAYER", source)
        self.assertIn("capture_native_player_activation", source)

    def test_honest_quality_gate_language_is_pinned(self) -> None:
        source = SUBJECT.read_text(encoding="utf-8")
        self.assertIn("LEGACY_PRESS_ROUTE_V001_NO_INSPECTION_GATE", source)
        self.assertIn("PRESS_INSPECTION_ROUTE_V002_QUALITY_GATE", source)
        self.assertIn("quality_gate_behavior_proved", source)
        self.assertIn("completed_hold", source)
        self.assertIn("quality_pass_evidence_id", source)
        self.assertIn("released_to_panel_dispatch", source)
        self.assertIn('hold_beacon != "WAITING"', source)
        self.assertIn("hold_amber_lamp_lit", source)
        self.assertIn("palletising_and_outbound_after_quality_release_proved", source)
        self.assertIn("historical v003 evidence", source)
        self.assertIn("packaged_build_validated\": False", source)
        self.assertIn("steam_capture_validated\": False", source)

    def test_main_is_not_executed_on_offline_import(self) -> None:
        self.assertTrue(callable(module.main))
        self.assertIsNone(module.unreal)


if __name__ == "__main__":
    unittest.main(verbosity=2)
