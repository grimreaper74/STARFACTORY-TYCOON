"""Adversarial offline tests for the guarded Press Shop 2126 v006 installer."""

from __future__ import annotations

import copy
import importlib.util
import inspect
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(
    r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Tools"
    r"\install_pressshop_2126_overhead_presentation_correction_v001.py"
)
PROBE = SCRIPT.with_name("probe_pressshop_2126_v005_loaded_fingerprints_v001.py")
SPEC = importlib.util.spec_from_file_location("pressshop_presentation_correction_v006", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PressShopPresentationCorrectionV006Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inputs = MODULE.validate_offline_contract(require_fresh_target=True)
        cls.receipt = cls.inputs["source_receipt"]
        cls.plan = cls.inputs["plan"]
        cls.validation = cls.inputs["validation"]

    def assert_guard(self, callback, fragment: str) -> None:
        with self.assertRaises(MODULE.PresentationCorrectionGuardError) as caught:
            callback()
        self.assertIn(fragment, str(caught.exception))

    def fresh_plan(self):
        return copy.deepcopy(self.plan)

    def row(self, item_id: str, plan=None):
        source = self.plan if plan is None else plan
        return next(row for row in source["mutations"] if row["id"] == item_id)

    def test_01_module_is_offline_importable_and_main_is_unreal_only(self) -> None:
        self.assertIsNone(MODULE.unreal)
        self.assert_guard(MODULE.main, "main must run inside UnrealEditor Python")

    def test_02_locked_offline_contract_passes(self) -> None:
        result = MODULE.validate_offline_contract(require_fresh_target=True)
        self.assertEqual(result["source_receipt"]["target_map"], MODULE.SOURCE_MAP)
        self.assertEqual(result["validation"]["mutation_count"], 83)

    def test_03_source_map_is_exactly_hash_and_byte_locked(self) -> None:
        self.assertEqual(MODULE.SOURCE_FILE.stat().st_size, MODULE.SOURCE_FILE_BYTES)
        self.assertEqual(MODULE.digest(MODULE.SOURCE_FILE), MODULE.SOURCE_FILE_SHA256)

    def test_04_v005_helper_is_exactly_locked_before_import(self) -> None:
        self.assertEqual(MODULE.V005_HELPER.stat().st_size, MODULE.V005_HELPER_BYTES)
        self.assertEqual(MODULE._bootstrap_digest(MODULE.V005_HELPER), MODULE.V005_HELPER_SHA256)

    def test_05_install_and_capture_receipts_are_hash_locked(self) -> None:
        self.assertEqual(MODULE.digest(MODULE.SOURCE_RECEIPT), MODULE.SOURCE_RECEIPT_SHA256)
        self.assertEqual(MODULE.digest(MODULE.SOURCE_CAPTURE_RECEIPT), MODULE.SOURCE_CAPTURE_RECEIPT_SHA256)

    def test_06_all_three_v005_capture_pngs_are_byte_and_hash_locked(self) -> None:
        for filename, lock in MODULE.SOURCE_CAPTURE_LOCKS.items():
            disk = MODULE.SOURCE_CAPTURE_ROOT / filename
            self.assertEqual(disk.stat().st_size, lock["bytes"])
            self.assertEqual(MODULE.digest(disk), lock["sha256"])

    def test_07_every_protected_map_is_current(self) -> None:
        snapshot = MODULE.protected_snapshot()
        self.assertEqual(set(snapshot), set(MODULE.PROTECTED_MAPS))
        self.assertEqual(snapshot["source_overhead_presentation_v005"], MODULE.SOURCE_FILE_SHA256)

    def test_08_all_reused_materials_are_current(self) -> None:
        self.assertEqual(set(MODULE.validate_material_locks()), set(MODULE.REUSED_MATERIAL_LOCKS))

    def test_09_candidate_materials_are_isolated_exact_unlit_colours(self) -> None:
        self.assertEqual(MODULE.CANDIDATE_MATERIAL_SPECS[MODULE.ZONE_MUTED_MATERIAL]["srgb_hex"], "#7A9588")
        self.assertEqual(MODULE.CANDIDATE_MATERIAL_SPECS[MODULE.ROUTE_MUTED_MATERIAL]["srgb_hex"], "#3F8F82")
        self.assertTrue(all(path.startswith(MODULE.TARGET_ROOT + "/Materials/")
                            for path in MODULE.CANDIDATE_MATERIAL_SPECS))

    def test_10_only_presentation_text_camera_and_boxes_are_mutated(self) -> None:
        kinds = [row["kind"] for row in self.plan["mutations"]]
        self.assertEqual(kinds.count("text"), 15)
        self.assertEqual(kinds.count("camera"), 3)
        self.assertEqual(kinds.count("box"), 65)
        self.assertEqual(set(kinds), {"text", "camera", "box"})
        self.assertEqual(self.validation["machine_or_cargo_actor_mutations"], 0)

    def test_11_no_actor_is_added_or_removed(self) -> None:
        self.assertEqual(self.plan["additions"], [])
        self.assertEqual(MODULE.EXPECTED_FINAL_ACTOR_COUNT, MODULE.EXPECTED_SOURCE_ACTOR_COUNT)
        self.assertEqual(MODULE.EXPECTED_FINAL_PRESENTATION_COUNT,
                         MODULE.EXPECTED_SOURCE_PRESENTATION_COUNT)

    def test_12_zone_inventory_area_and_fraction_are_exact(self) -> None:
        self.assertEqual(self.validation["zone_geometry_mutation_count"], 36)
        self.assertEqual(self.validation["station_zone_area_cm2"], 14775200.0)
        self.assertAlmostEqual(self.validation["station_zone_deck_fraction"], 0.08754117786467591)
        self.assertEqual(self.validation["station_zone_area_reduction_fraction_vs_v005"], 0.359)

    def test_13_every_pad_uses_the_audited_depth_and_keeps_xy_lane_alignment(self) -> None:
        for station, spec in MODULE.ZONE_DEPTH_SPECS.items():
            row = self.row("PAD_" + station)
            self.assertEqual(row["target"]["location_cm"], row["source"]["location_cm"])
            self.assertEqual(row["target"]["location_cm"][0], -8990.75)
            self.assertEqual(row["target"]["dimensions_cm"][0], spec["pad_depth"])
            self.assertEqual(row["target"]["dimensions_cm"][1:], row["source"]["dimensions_cm"][1:])
            self.assertEqual(row["target"]["material"], MODULE.ZONE_MUTED_MATERIAL)

    def test_14_every_zone_is_contiguous_from_west_edge_to_exact_port(self) -> None:
        for station in MODULE.STATION_IDS:
            pad = self.row("PAD_" + station)["target"]
            west = self.row(f"ZONE_WING_{station}_WEST")["target"]
            east = self.row(f"ZONE_WING_{station}_EAST")["target"]
            self.assertAlmostEqual(west["location_cm"][0] + west["dimensions_cm"][0] / 2,
                                   pad["location_cm"][0] - pad["dimensions_cm"][0] / 2)
            self.assertAlmostEqual(pad["location_cm"][0] + pad["dimensions_cm"][0] / 2,
                                   east["location_cm"][0] - east["dimensions_cm"][0] / 2)
            self.assertAlmostEqual(east["location_cm"][0] + east["dimensions_cm"][0] / 2,
                                   self.row("STATION_PORT_CAP_" + station)["target"]["location_cm"][0])

    def test_15_zone_wings_keep_y_length_z_and_role(self) -> None:
        for row in self.plan["mutations"]:
            if row.get("group") != "zone" or row["id"].startswith("PAD_"):
                continue
            self.assertEqual(row["target"]["location_cm"][1:], row["source"]["location_cm"][1:])
            self.assertEqual(row["target"]["dimensions_cm"][1:], row["source"]["dimensions_cm"][1:])
            self.assertEqual(row["target"]["role"], row["source"]["role"])

    def test_16_audited_machine_depth_occupancy_acceptance_is_recorded(self) -> None:
        self.assertGreaterEqual(self.validation["audited_median_machine_bbox_depth_occupancy"], 0.65)
        self.assertGreaterEqual(self.validation["audited_minimum_station_machine_bbox_depth_occupancy"], 0.30)

    def test_17_route_lane_is_thinned_to_360_and_muted_teal(self) -> None:
        lane = self.row("FLOW_LANE")
        self.assertEqual(lane["target"]["location_cm"], lane["source"]["location_cm"])
        self.assertEqual(lane["target"]["dimensions_cm"], [360.0, 15500.0, 0.6])
        self.assertEqual(lane["target"]["material"], MODULE.ROUTE_MUTED_MATERIAL)

    def test_18_long_and_end_rails_use_exact_reduced_widths(self) -> None:
        west, east = self.row("FLOW_EDGE_WEST")["target"], self.row("FLOW_EDGE_EAST")["target"]
        self.assertEqual((west["location_cm"][0], west["dimensions_cm"][0]), (-6650.0, 36.0))
        self.assertEqual((east["location_cm"][0], east["dimensions_cm"][0]), (-6350.0, 36.0))
        for item_id in ("FLOW_EDGE_INBOUND", "FLOW_EDGE_OUTBOUND"):
            self.assertEqual(self.row(item_id)["target"]["dimensions_cm"][:2], [360.0, 36.0])

    def test_19_all_twelve_branches_keep_length_centre_and_use_56cm_teal(self) -> None:
        branches = [row for row in self.plan["mutations"]
                    if row.get("group") == "route"
                    and (row["id"].startswith("FLOW_CONNECTOR")
                         or row["target"].get("role") == "StationRouteBranch")]
        self.assertEqual(len(branches), 12)
        for row in branches:
            self.assertEqual(row["target"]["location_cm"], row["source"]["location_cm"])
            self.assertEqual(row["target"]["dimensions_cm"][0], row["source"]["dimensions_cm"][0])
            self.assertEqual(row["target"]["dimensions_cm"][1], 56.0)
            self.assertEqual(row["target"]["material"], MODULE.ROUTE_MUTED_MATERIAL)

    def test_20_port_caps_keep_transform_and_dimensions_but_become_safety_yellow(self) -> None:
        for station in MODULE.STATION_IDS:
            row = self.row("STATION_PORT_CAP_" + station)
            self.assertEqual(row["target"]["location_cm"], row["source"]["location_cm"])
            self.assertEqual(row["target"]["dimensions_cm"], row["source"]["dimensions_cm"])
            self.assertEqual(row["target"]["material"], MODULE.YELLOW_MATERIAL)

    def test_21_all_twelve_route_ports_remain_exact_zero_gap(self) -> None:
        self.assertEqual(self.validation["station_port_count"], 12)
        self.assertEqual(self.validation["station_branch_count"], 12)
        self.assertEqual(self.validation["station_connector_max_gap_cm"], 0.0)

    def test_22_all_labels_use_exact_depth_size_and_high_contrast(self) -> None:
        labels = [row for row in self.plan["mutations"] if row["kind"] == "text"]
        self.assertEqual(len(labels), 15)
        for row in labels:
            self.assertEqual(row["target"]["location_cm"][2], 12.0)
            self.assertEqual(row["target"]["world_size_cm"],
                             260.0 if row["id"] == "LABEL_TITLE" else 164.0)
        self.assertGreater(self.validation["station_label_contrast_ratio"], 12.0)
        self.assertGreater(self.validation["flow_label_contrast_ratio"], 7.0)

    def test_23_title_and_direction_labels_match_audit_targets(self) -> None:
        self.assertEqual(self.row("LABEL_TITLE")["target"]["location_cm"][0], -4900.0)
        self.assertEqual(self.row("LABEL_INBOUND")["target"]["colour_rgba"], list(MODULE.FLOW_TEXT_RGBA))
        self.assertEqual(self.row("LABEL_OUTBOUND")["target"]["colour_rgba"], list(MODULE.FLOW_TEXT_RGBA))

    def test_24_all_three_cameras_match_exact_true_overhead_targets(self) -> None:
        for item_id, expected in MODULE.CAMERA_TARGETS.items():
            target = self.row(item_id)["target"]
            self.assertEqual(target["location_cm"], expected["location_cm"])
            self.assertEqual(target["ortho_width_cm"], expected["ortho_width_cm"])
            self.assertEqual(target["rotation_deg_pitch_yaw_roll"], list(MODULE.CAMERA_ROTATION))

    def test_25_overview_has_zero_positive_x_exterior_and_route_is_40ish_pixels(self) -> None:
        overview = self.validation["camera_metrics"]["overview"]
        self.assertAlmostEqual(overview["max_x"], MODULE.DECK_RECT["max_x"])
        self.assertGreaterEqual(self.validation["overview_route_width_pixels_at_1080"], 40.0)
        self.assertLessEqual(self.validation["overview_route_width_pixels_at_1080"], 45.0)

    def test_26_overview_keeps_route_caps_and_hero_keeps_press_group(self) -> None:
        overview = self.validation["camera_metrics"]["overview"]
        self.assertLessEqual(overview["min_y"], 1090.2182808269426)
        self.assertGreaterEqual(overview["max_y"], 16590.218280826943)
        hero = self.validation["camera_metrics"]["steam_hero"]
        self.assertLessEqual(hero["min_y"], 8356.0)
        self.assertGreaterEqual(hero["max_y"], 13828.0)

    def test_27_all_146_visuals_are_path_keyed_source_fingerprint_locked(self) -> None:
        self.assertEqual(self.receipt["visual_layer_actor_fingerprints_after_sha256"],
                         MODULE.EXPECTED_SOURCE_HASHES["combined_visual"])
        self.assertEqual(self.receipt["machinery_actor_fingerprints_after_sha256"],
                         MODULE.EXPECTED_SOURCE_HASHES["machinery_visual"])
        self.assertEqual(self.receipt["cargo_actor_fingerprints_after_sha256"],
                         MODULE.EXPECTED_SOURCE_HASHES["cargo_visual"])

    def semantic_rows(self):
        motion_start = (
            "<Struct 'Transform' (0x000001CEDC4CA720) {rotation: {x: 0.000000, "
            "y: -0.000000, z: 0.707107, w: 0.707107}, translation: {x: -8985.977840, "
            "y: 5369.163885, z: 4.200000}, scale3d: {x: 1.728003, y: 1.728003, "
            "z: 1.000000}}>"
        )
        motion_end = (
            "<Struct 'Transform' (0x000001CEDC4CA780) {rotation: {x: 0.000000, "
            "y: -0.000000, z: 0.707107, w: 0.707107}, translation: {x: -8910.750000, "
            "y: 5644.187195, z: 4.200000}, scale3d: {x: 1.728003, y: 1.728003, "
            "z: 1.000000}}>"
        )
        base = {
            "path": "/Game/V005.Map:PersistentLevel.Actor_1", "label": "unique actor",
            "class_path": "/Script/Engine.StaticMeshActor", "tags": ["presentation"],
            "actor_collision_enabled": False, "location_cm": [1.0, 2.0, 3.0],
            "rotation_deg_pitch_yaw_roll": [0.0, 0.0, 0.0], "scale3d": [1.0, 1.0, 1.0],
            "static_mesh_component": {"static_mesh": "/Engine/BasicShapes/Cube.Cube",
                                      "materials": ["/Game/M"], "visible": True,
                                      "hidden_in_game": False, "collision_enabled": "NO_COLLISION",
                                      "collision_profile": "Custom"},
            "visual_metadata": {
                "MotionStart": motion_start,
                "MotionEnd": motion_end,
                "MotionMode": "LINEAR",
            },
        }
        clone = copy.deepcopy(base)
        clone["path"] = "/Game/V006.Map:PersistentLevel.StaticMeshActor_999"
        return base, clone

    def test_28_clone_semantics_remove_only_ephemeral_package_object_path(self) -> None:
        source, clone = self.semantic_rows()
        MODULE._assert_semantic_records_equal(MODULE._semantic_records_from_rows([source]),
                                              MODULE._semantic_records_from_rows([clone]), "test")

    def assert_semantic_tamper(self, mutator) -> None:
        source, clone = self.semantic_rows()
        mutator(clone)
        self.assert_guard(lambda: MODULE._assert_semantic_records_equal(
            MODULE._semantic_records_from_rows([source]),
            MODULE._semantic_records_from_rows([clone]), "test"), "semantic actor keys changed")

    def test_29_clone_semantics_do_not_ignore_material_changes(self) -> None:
        self.assert_semantic_tamper(lambda row: row["static_mesh_component"].update(
            {"materials": ["/Game/Changed"]}))

    def test_30_clone_semantics_do_not_ignore_transform_changes(self) -> None:
        self.assert_semantic_tamper(lambda row: row.update({"location_cm": [2.0, 2.0, 3.0]}))

    def test_31_clone_semantics_do_not_ignore_collision_changes(self) -> None:
        self.assert_semantic_tamper(lambda row: row["static_mesh_component"].update(
            {"collision_enabled": "QUERY_ONLY"}))

    def test_32_clone_semantics_do_not_ignore_tag_changes(self) -> None:
        self.assert_semantic_tamper(lambda row: row.update({"tags": ["presentation", "changed"]}))

    def test_33_clone_semantics_preserve_duplicate_labels_and_multiplicity(self) -> None:
        source, clone = self.semantic_rows()
        source_duplicate, clone_duplicate = copy.deepcopy(source), copy.deepcopy(clone)
        source_duplicate["path"] = "/Game/V005.Map:PersistentLevel.Actor_2"
        clone_duplicate["path"] = "/Game/V006.Map:PersistentLevel.Actor_442"
        expected = MODULE._semantic_records_from_rows([source, source_duplicate])
        actual = MODULE._semantic_records_from_rows([clone, clone_duplicate])
        self.assertEqual(len(expected), 2)
        MODULE._assert_semantic_records_equal(expected, actual, "duplicate multiset")

    def test_33b_clone_semantics_fail_when_one_duplicate_is_deleted(self) -> None:
        source, clone = self.semantic_rows()
        source_duplicate = copy.deepcopy(source)
        source_duplicate["path"] = "/Game/V005.Map:PersistentLevel.Actor_2"
        self.assert_guard(lambda: MODULE._assert_semantic_records_equal(
            MODULE._semantic_records_from_rows([source, source_duplicate]),
            MODULE._semantic_records_from_rows([clone]), "duplicate deletion"),
            "semantic actor keys changed")

    def test_33c_motion_transform_process_addresses_are_normalized(self) -> None:
        source, clone = self.semantic_rows()
        clone["visual_metadata"]["MotionStart"] = clone["visual_metadata"][
            "MotionStart"
        ].replace("0x000001CEDC4CA720", "0x0000025E529F34C0")
        clone["visual_metadata"]["MotionEnd"] = clone["visual_metadata"][
            "MotionEnd"
        ].replace("0x000001CEDC4CA780", "0x0000025E529F3520")
        MODULE._assert_semantic_records_equal(
            MODULE._semantic_records_from_rows([source]),
            MODULE._semantic_records_from_rows([clone]), "process address normalization",
        )

    def test_33d_motion_transform_numeric_endpoint_change_fails_closed(self) -> None:
        def mutate(row):
            row["visual_metadata"]["MotionEnd"] = row["visual_metadata"][
                "MotionEnd"
            ].replace("x: -8910.750000", "x: -8910.500000")
        self.assert_semantic_tamper(mutate)

    def test_33e_malformed_motion_transform_repr_fails_closed(self) -> None:
        source, _clone = self.semantic_rows()
        source["visual_metadata"]["MotionStart"] = "<unstable or truncated transform>"
        self.assert_guard(lambda: MODULE._semantic_records_from_rows([source]),
                          "unexpected Unreal Transform repr")

    def test_34_source_map_hash_tamper_fails_closed(self) -> None:
        original = MODULE.digest
        with mock.patch.object(MODULE, "digest", side_effect=lambda path:
                               "0" * 64 if Path(path) == MODULE.SOURCE_FILE else original(Path(path))):
            self.assert_guard(lambda: MODULE.validate_offline_contract(True), "source map hash changed")

    def test_35_source_receipt_hash_tamper_fails_closed(self) -> None:
        original = MODULE.digest
        with mock.patch.object(MODULE, "digest", side_effect=lambda path:
                               "1" * 64 if Path(path) == MODULE.SOURCE_RECEIPT else original(Path(path))):
            self.assert_guard(MODULE.validate_source_receipt, "install receipt hash changed")

    def test_36_capture_receipt_hash_tamper_fails_closed(self) -> None:
        original = MODULE.digest
        with mock.patch.object(MODULE, "digest", side_effect=lambda path:
                               "2" * 64 if Path(path) == MODULE.SOURCE_CAPTURE_RECEIPT else original(Path(path))):
            self.assert_guard(MODULE.validate_source_capture, "capture receipt hash changed")

    def test_37_capture_png_hash_tamper_fails_closed(self) -> None:
        filename = next(iter(MODULE.SOURCE_CAPTURE_LOCKS))
        victim, original = MODULE.SOURCE_CAPTURE_ROOT / filename, MODULE.digest
        with mock.patch.object(MODULE, "digest", side_effect=lambda path:
                               "3" * 64 if Path(path) == victim else original(Path(path))):
            self.assert_guard(MODULE.validate_source_capture, "captured PNG changed")

    def test_38_existing_target_root_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(MODULE, "TARGET_ROOT_DISK", Path(folder)):
                self.assert_guard(lambda: MODULE.validate_offline_contract(True), "target already exists")

    def test_39_existing_install_receipt_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            receipt = Path(folder) / "receipt.json"
            receipt.write_text("{}", encoding="utf-8")
            with mock.patch.object(MODULE, "INSTALL_RECEIPT", receipt):
                self.assert_guard(lambda: MODULE.validate_offline_contract(True),
                                  "install receipt already exists")

    def test_40_fingerprint_receipt_tamper_fails_closed(self) -> None:
        changed = copy.deepcopy(self.receipt)
        changed["visual_layer_actor_fingerprints_after_sha256"] = "4" * 64
        with mock.patch.object(MODULE, "_load_locked_json", return_value=changed):
            self.assert_guard(MODULE.validate_source_receipt, "fingerprint evidence changed")

    def test_41_missing_mutation_fails_closed(self) -> None:
        changed = self.fresh_plan()
        changed["mutations"].pop()
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "mutation count changed")

    def test_42_duplicate_mutation_id_fails_closed(self) -> None:
        changed = self.fresh_plan()
        changed["mutations"][1]["id"] = changed["mutations"][0]["id"]
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "duplicate ids")

    def test_43_new_presentation_actor_fails_closed(self) -> None:
        changed = self.fresh_plan()
        changed["additions"].append({"id": "unexpected", "label": "unexpected"})
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "must not add presentation actors")

    def test_44_pad_depth_tamper_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("PAD_S03", changed)["target"]["dimensions_cm"][0] += 10.0
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "station body contract changed")

    def test_45_zone_wing_x_tamper_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("ZONE_WING_S04_EAST", changed)["target"]["location_cm"][0] += 1.0
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "station east wing contract changed")

    def test_46_zone_material_tamper_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("PAD_IN01", changed)["target"]["material"] = MODULE.ZONE_MATERIAL
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "station body contract changed")

    def test_47_route_branch_thickness_tamper_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("FLOW_CONNECTOR_01", changed)["target"]["dimensions_cm"][1] = 74.0
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "branch hierarchy changed")

    def test_48_port_transform_tamper_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("STATION_PORT_CAP_IN01", changed)["target"]["location_cm"][0] += 1.0
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "port cap contract changed")

    def test_49_port_material_tamper_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("STATION_PORT_CAP_S06", changed)["target"]["material"] = MODULE.CREAM_MATERIAL
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "port cap contract changed")

    def test_50_zero_gap_branch_tamper_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("FLOW_CONNECTOR_01", changed)["target"]["location_cm"][0] += 5.0
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "zero-gap")

    def test_51_label_z_fighting_regression_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("LABEL_S03", changed)["target"]["location_cm"][2] = 0.2
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "safe depth separation")

    def test_52_label_size_tamper_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("LABEL_S01", changed)["target"]["world_size_cm"] = 128.0
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "label size changed")

    def test_53_title_x_tamper_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("LABEL_TITLE", changed)["target"]["location_cm"][0] = -4500.0
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "title placement changed")

    def test_54_camera_framing_tamper_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("overview", changed)["target"]["location_cm"][0] += 1.0
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "camera framing target changed")

    def test_55_non_overhead_camera_fails_closed(self) -> None:
        changed = self.fresh_plan()
        self.row("steam_hero", changed)["target"]["rotation_deg_pitch_yaw_roll"] = [-75.0, 0.0, 0.0]
        self.assert_guard(lambda: MODULE.validate_correction_plan(changed, self.receipt),
                          "not true overhead")

    def test_56_installer_validates_locked_source_before_template_clone(self) -> None:
        source = inspect.getsource(MODULE.main)
        source_load = source.index("level_subsystem.load_level(SOURCE_MAP)")
        loaded_inventory = source.index("_validate_loaded_source_actor_groups(source_actors)")
        route_preflight = source.index("_assert_source_route_actor(matches[0], row, station)")
        material_creation = source.index("_create_candidate_unlit_material(asset_path, spec)")
        template_clone = source.index(
            "level_subsystem.new_level_from_template(TARGET_MAP, SOURCE_MAP)"
        )
        self.assertLess(source_load, loaded_inventory)
        self.assertLess(loaded_inventory, route_preflight)
        self.assertLess(route_preflight, material_creation)
        self.assertLess(material_creation, template_clone)
        self.assertIn("_assert_semantic_records_equal(source_semantic, clone_semantic", source)

    def test_56b_loaded_source_legacy_path_hash_is_diagnostic_not_authority(self) -> None:
        source = inspect.getsource(MODULE._validate_loaded_source_actor_groups)
        self.assertIn("legacy_path_hash_matches", source)
        self.assertIn("semantic_groups", source)
        self.assertIn("exact_tags", source)
        self.assertNotIn("legacy_path_hashes[name] != EXPECTED_SOURCE_HASHES", source)
        self.assertNotIn("legacy_path_hash_matches[name] is False", source)

    def test_56c_candidate_content_is_not_created_before_every_source_preflight(self) -> None:
        source = inspect.getsource(MODULE.main)
        creation = source.index("_create_candidate_unlit_material(asset_path, spec)")
        required_preflights = (
            "validate_offline_contract(require_fresh_target=True)",
            "protected_snapshot() != protected_before",
            "_validate_loaded_source_actor_groups(source_actors)",
            "_assert_source_text(actor, row[\"source\"]",
            "_assert_source_camera(actor, row[\"source\"]",
            "_assert_source_box(actor, row[\"source\"]",
            "_assert_source_route_actor(matches[0], row, station)",
            "read-only v005 source validation dirtied packages",
        )
        for token in required_preflights:
            self.assertLess(source.index(token), creation, token)

    def test_57_capture_receipt_proves_v005_layout_material_collision_evidence(self) -> None:
        capture = self.inputs["source_capture_receipt"]
        self.assertTrue(capture["layout_material_collision_fingerprint_unchanged"])
        self.assertFalse(capture["saved_actor_layout_mutated"])
        self.assertFalse(capture["saved_actor_material_assignment_mutated"])
        self.assertFalse(capture["saved_actor_collision_mutated"])
        self.assertEqual(capture["continuous_station_port_max_gap_cm"], 0.0)

    def test_58_honest_runtime_and_steam_gates_remain_false_in_source(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for token in ('"runtime_validated": False', '"pie_validated": False',
                      '"steam_visual_quality_human_approved": False'):
            self.assertIn(token, source)

    def test_59_read_only_probe_cannot_mutate_content_or_save_maps(self) -> None:
        source = PROBE.read_text(encoding="utf-8")
        self.assertIn("subsystem.load_level(contract._v005.SOURCE_MAP)", source)
        self.assertIn("subsystem.load_level(contract.SOURCE_MAP)", source)
        self.assertIn("_assert_semantic_records_equal", source)
        for forbidden in (
            "new_level_from_template(", "create_asset(", "save_current_level(",
            "save_loaded_asset(", "delete_asset(", "rename_asset(",
            "import_asset_tasks(", "spawn_actor_from_class(",
        ):
            self.assertNotIn(forbidden, source)

    def test_60_receipt_documents_narrow_semantic_normalization(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("semantic-row-hash multiset", source)
        self.assertIn("all ten parsed", source)
        self.assertIn("duplicate labels and multiplicity", source)
        self.assertIn("source_loaded_legacy_receipt_path_hash_matches", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
