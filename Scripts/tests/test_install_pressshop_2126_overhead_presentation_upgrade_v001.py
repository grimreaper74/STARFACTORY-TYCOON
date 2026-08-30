"""Offline guards for the Press Shop 2126 v005 presentation-upgrade lane.

The suite imports the one-shot installer in ordinary CPython and validates
immutable receipts/packages, pure layout arithmetic, exact presentation-only
selectors, adversarial tamper rejection, and source-code safety properties.
It never launches Unreal, creates assets, clones/saves a map, or writes a
receipt.
"""

from __future__ import annotations

import copy
import importlib.util
import inspect
import unittest
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
INSTALLER = (
    PROJECT
    / "Tools"
    / "install_pressshop_2126_overhead_presentation_upgrade_v001.py"
)


def load_installer_module():
    spec = importlib.util.spec_from_file_location(
        "pressshop_overhead_presentation_upgrade_v001_test_subject",
        INSTALLER,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MODULE = load_installer_module()


def mutation_index(plan):
    return {row["id"]: row for row in plan["mutations"]}


def addition_index(plan):
    return {row["id"]: row for row in plan["additions"]}


class FrozenInputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = MODULE.validate_offline_contract()

    def test_v004_source_and_v005_target_are_exact_fresh_and_disjoint(self):
        self.assertEqual(
            MODULE.SOURCE_MAP,
            "/Game/LineBoss/Candidates/PressShop/"
            "PressShop2126_OverheadPresentation_v004/Maps/"
            "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004",
        )
        self.assertEqual(
            MODULE.TARGET_MAP,
            "/Game/LineBoss/Candidates/PressShop/"
            "PressShop2126_OverheadPresentation_v005/Maps/"
            "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v005",
        )
        self.assertNotEqual(MODULE.SOURCE_MAP, MODULE.TARGET_MAP)
        self.assertFalse(MODULE.TARGET_ROOT_DISK.exists())
        self.assertFalse(MODULE.INSTALL_RECEIPT.exists())
        self.assertEqual(MODULE.SOURCE_FILE.stat().st_size, 1_211_122)
        self.assertEqual(
            MODULE.digest(MODULE.SOURCE_FILE),
            "ab77d9bc327e65fa5bf8b8efd4d6666252247be1420070563f83bb099d98fe9f",
        )

    def test_v004_receipt_and_capture_evidence_are_exact(self):
        source = self.contract["source_receipt"]
        capture = self.contract["source_capture_receipt"]
        self.assertEqual(MODULE.digest(MODULE.SOURCE_RECEIPT), MODULE.SOURCE_RECEIPT_SHA256)
        self.assertEqual(source["schema"], MODULE.SOURCE_RECEIPT_SCHEMA)
        self.assertEqual(source["status"], MODULE.SOURCE_RECEIPT_STATUS)
        self.assertEqual(source["target_map_sha256"], MODULE.SOURCE_FILE_SHA256)
        self.assertEqual(source["final_actor_count"], 247)
        self.assertEqual(source["combined_visual_layer_count"], 146)
        self.assertEqual(source["cargo_layer_count"], 26)
        self.assertEqual(capture["schema"], MODULE.SOURCE_CAPTURE_SCHEMA)
        self.assertEqual(capture["status"], MODULE.SOURCE_CAPTURE_STATUS)
        self.assertEqual(len(capture["captures"]), 3)
        for name, lock in MODULE.SOURCE_CAPTURE_LOCKS.items():
            path = MODULE.SOURCE_CAPTURE_ROOT / name
            self.assertEqual(path.stat().st_size, lock["bytes"])
            self.assertEqual(MODULE.digest(path), lock["sha256"])

    def test_v003_v002_and_cargo_import_chain_is_relocked(self):
        v003 = self.contract["v003_receipt"]
        v002 = self.contract["v002_receipt"]
        cargo_import = self.contract["cargo_import_receipt"]
        self.assertEqual(MODULE.digest(MODULE.V003_FILE), MODULE.V003_FILE_SHA256)
        self.assertEqual(MODULE.digest(MODULE.V003_RECEIPT), MODULE.V003_RECEIPT_SHA256)
        self.assertEqual(v003["status"], MODULE.V003_RECEIPT_STATUS)
        self.assertEqual(len(v003["cargo_layers"]), 26)
        self.assertEqual(MODULE.digest(MODULE.V002_FILE), MODULE.V002_FILE_SHA256)
        self.assertEqual(MODULE.digest(MODULE.V002_RECEIPT), MODULE.V002_RECEIPT_SHA256)
        self.assertEqual(v002["created_actor_count"], 82)
        self.assertEqual(len(cargo_import["created_uasset_sha256"]), 30)
        for asset_path, expected_hash in cargo_import["created_uasset_sha256"].items():
            self.assertEqual(
                MODULE.digest(MODULE.virtual_to_uasset(asset_path)), expected_hash
            )

    def test_all_five_reused_material_packages_and_colours_are_exact(self):
        self.assertEqual(len(self.contract["material_hashes"]), 5)
        self.assertEqual(
            MODULE.REUSED_MATERIAL_SRGB_HEX,
            {
                MODULE.CHARCOAL_MATERIAL: "#171D21",
                MODULE.ZONE_MATERIAL: "#91AA9C",
                MODULE.CREAM_MATERIAL: "#E8DEC2",
                MODULE.YELLOW_MATERIAL: "#E1B94F",
                MODULE.SLATE_MATERIAL: "#36534F",
            },
        )
        for asset_path, lock in MODULE.REUSED_MATERIAL_LOCKS.items():
            disk = MODULE.virtual_to_uasset(asset_path)
            self.assertEqual(disk.stat().st_size, lock["bytes"])
            self.assertEqual(MODULE.digest(disk), lock["sha256"])

    def test_every_protected_map_hash_is_current(self):
        snapshot = self.contract["protected_hashes"]
        self.assertEqual(set(snapshot), set(MODULE.PROTECTED_MAPS))
        self.assertEqual(len(snapshot), 7)
        self.assertEqual(
            snapshot["source_overhead_presentation_v005_parent"],
            MODULE.SOURCE_FILE_SHA256,
        )
        self.assertEqual(snapshot["source_overhead_cargo_v003"], MODULE.V003_FILE_SHA256)


class ReviewedUpgradePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = MODULE.validate_offline_contract()
        cls.plan = cls.contract["plan"]
        cls.validation = cls.contract["validation"]
        cls.by_id = mutation_index(cls.plan)
        cls.added = addition_index(cls.plan)

    def test_rebuilt_v004_catalog_and_v005_counts_are_exact(self):
        catalog = self.plan["catalog"]
        self.assertEqual(len(catalog["box"]), 67)
        self.assertEqual(len(catalog["text"]), 15)
        self.assertEqual(len(catalog["camera"]), 3)
        self.assertEqual(len(self.plan["mutations"]), 61)
        self.assertEqual(len(self.plan["additions"]), 55)
        self.assertEqual(self.validation["box_mutation_count"], 43)
        self.assertEqual(self.validation["text_mutation_count"], 15)
        self.assertEqual(self.validation["camera_mutation_count"], 3)
        self.assertEqual(self.validation["final_actor_count"], 302)
        self.assertEqual(self.validation["final_presentation_actor_count"], 140)
        self.assertEqual(self.validation["unchanged_presentation_actor_count"], 24)
        self.assertEqual(self.validation["v005_provenance_actor_count"], 116)
        self.assertEqual(
            self.validation["source_presentation_catalog_sha256"],
            "bc31d992193a81ef4a94eb8f83a382570e9f4ecc6b71734ee725c491538fbabf",
        )

    def test_plan_selects_presentation_only_and_preserves_all_flow_arrows(self):
        source_labels = [row["source"]["label"] for row in self.plan["mutations"]]
        self.assertFalse(any(label.startswith(("VIS | ", "CARGO | ")) for label in source_labels))
        mutation_ids = set(self.by_id)
        self.assertFalse(any(item_id.startswith("FLOW_ARROW_") for item_id in mutation_ids))
        arrows = [
            row for row in self.plan["catalog"]["box"].values()
            if row["id"].startswith("FLOW_ARROW_")
        ]
        self.assertEqual(len(arrows), 24)
        self.assertEqual(
            {MODULE._asset_path(row["material"]) for row in arrows},
            {MODULE.YELLOW_MATERIAL},
        )

    def test_enlarged_deck_backs_every_camera_and_overview_flow_is_unclipped(self):
        deck = self.by_id["DECK_BASE"]["target"]
        self.assertEqual(deck["dimensions_cm"], [9700.0, 17400.0, 20.0])
        self.assertEqual(MODULE._asset_path(deck["material"]), MODULE.SLATE_MATERIAL)
        self.assertTrue(self.validation["overview_complete_flow_unclipped"])
        for metrics in self.validation["camera_metrics"].values():
            self.assertEqual(metrics["projected_exterior_fraction"], 0.0)
            self.assertEqual(metrics["projected_deck_fraction"], 1.0)
        self.assertGreaterEqual(
            self.validation["overview_enlarged_deck_visible_fraction"], 0.98
        )
        self.assertEqual(
            [self.by_id[item_id]["target"]["ortho_width_cm"]
             for item_id in ("overview", "press_spine", "steam_hero")],
            [17200.0, 10800.0, 6000.0],
        )
        for item_id in ("overview", "press_spine", "steam_hero"):
            camera = self.by_id[item_id]["target"]
            self.assertEqual(camera["rotation_deg_pitch_yaw_roll"], [-90.0, 0.0, 0.0])
            self.assertEqual(camera["projection"], "ORTHOGRAPHIC")
            self.assertEqual(camera["aspect_ratio"], 16.0 / 9.0)

    def test_hero_zone_occupancy_is_large_and_fully_contained(self):
        self.assertGreaterEqual(
            self.validation["hero_s03_s06_frame_width_fraction"], 0.80
        )
        self.assertGreaterEqual(
            self.validation["hero_s03_s06_frame_height_fraction"], 0.55
        )
        self.assertAlmostEqual(
            self.validation["hero_s03_s06_frame_width_fraction"], 0.912
        )
        self.assertAlmostEqual(
            self.validation["hero_s03_s06_frame_height_fraction"],
            0.6222222222222222,
        )
        self.assertTrue(self.validation["hero_group_fully_contained"])
        self.assertIn("presentation-zone", self.validation["hero_metric_basis"])

    def test_black_bar_is_replaced_by_dual_cream_rail_teal_route(self):
        lane = self.by_id["FLOW_LANE"]["target"]
        self.assertEqual(lane["role"], "DualRailRouteBed")
        self.assertEqual(MODULE._asset_path(lane["material"]), MODULE.ROUTE_TEAL_MATERIAL)
        self.assertEqual(lane["dimensions_cm"], [520.0, 15500.0, 0.6])
        for item_id, x_value in (
            ("FLOW_EDGE_WEST", -6700.0),
            ("FLOW_EDGE_EAST", -6300.0),
        ):
            rail = self.by_id[item_id]["target"]
            self.assertEqual(MODULE._asset_path(rail["material"]), MODULE.CREAM_MATERIAL)
            self.assertEqual(rail["location_cm"][0], x_value)
            self.assertEqual(rail["dimensions_cm"], [54.0, 15500.0, 0.24])
        self.assertEqual(self.validation["empty_shuttle_carrier_count"], 3)
        self.assertEqual(self.validation["empty_shuttle_pieces_per_carrier"], 3)
        carriers = [row for row in self.plan["additions"] if row["id"].startswith("EMPTY_SHUTTLE_")]
        self.assertEqual(len(carriers), 9)
        self.assertFalse(any("CARGO" in row["role"].upper() or "WIP" in row["role"].upper()
                             for row in carriers))

    def test_all_twelve_teal_branches_are_continuous_to_cream_ports(self):
        self.assertEqual(self.validation["station_port_count"], 12)
        self.assertEqual(self.validation["station_connector_max_gap_cm"], 0.0)
        self.assertEqual(set(self.validation["station_connector_gaps_cm"]),
                         {row["id"] for row in MODULE.STATION_ROWS})
        for station_id, gap in self.validation["station_connector_gaps_cm"].items():
            self.assertLessEqual(gap, 10.0, station_id)
            port = self.added["STATION_PORT_CAP_" + station_id]
            self.assertEqual(port["role"], "StationPortCap")
            self.assertEqual(MODULE._asset_path(port["material"]), MODULE.CREAM_MATERIAL)
        self.assertEqual(
            {row["id"] for row in self.plan["additions"] if row["role"] == "StationRouteBranch"},
            {"FLOW_BRANCH_IN02", "FLOW_BRANCH_IN03", "FLOW_BRANCH_S01"},
        )

    def test_each_station_zone_is_a_three_box_pale_green_footprint(self):
        self.assertEqual(self.validation["station_zone_piece_count"], 36)
        self.assertEqual(
            self.validation["station_zone_footprint_depth_cm"],
            {"nonpress": 2300.0, "press": 2100.0},
        )
        for station in MODULE.STATION_ROWS:
            station_id = station["id"]
            body = self.by_id["PAD_" + station_id]["target"]
            west = self.added["ZONE_WING_{}_WEST".format(station_id)]
            east = self.added["ZONE_WING_{}_EAST".format(station_id)]
            self.assertEqual(
                {body["role"], west["role"], east["role"]},
                {"StationZoneBody", "StationZoneWestWing", "StationZoneEastPortWing"},
            )
            self.assertEqual(
                {MODULE._asset_path(row["material"]) for row in (body, west, east)},
                {MODULE.ZONE_MATERIAL},
            )

    def test_floor_is_unlit_banded_restrained_and_uses_no_external_texture(self):
        roles = self.validation["addition_role_counts"]
        self.assertEqual(roles["FloorBandLongitudinal"], 2)
        self.assertEqual(roles["FloorBandTransverse"], 5)
        self.assertLessEqual(self.validation["floor_band_area_fraction_upper_bound"], 0.05)
        floor_bands = [row for row in self.plan["additions"] if row["id"].startswith("FLOOR_BAND_")]
        self.assertEqual(len(floor_bands), 7)
        self.assertEqual(
            {MODULE._asset_path(row["material"]) for row in floor_bands},
            {MODULE.FLOOR_BAND_MATERIAL},
        )
        self.assertFalse(self.validation["external_assets_required"])
        self.assertFalse(self.validation["external_textures_required"])
        self.assertEqual(self.validation["lights_created"], 0)
        self.assertEqual(self.validation["roofs_created"], 0)

    def test_two_new_unlit_material_colours_are_exact(self):
        self.assertEqual(
            [(row["srgb_hex"], row["shading_model"])
             for row in self.validation["new_materials"]],
            [("#294A46", "UNLIT"), ("#3B8177", "UNLIT")],
        )
        self.assertTrue(all(row["asset"].startswith(MODULE.TARGET_MATERIAL_ROOT + "/")
                            for row in self.validation["new_materials"]))

    def test_labels_are_capture_proven_readable_high_contrast_and_large_enough(self):
        self.assertEqual(MODULE.TEXT_ROTATION, (90.0, 180.0, 0.0))
        self.assertGreaterEqual(
            self.validation["minimum_station_label_projected_height_px_1920x1080"],
            14.0,
        )
        self.assertGreaterEqual(
            self.validation["cream_on_charcoal_label_contrast_ratio"], 4.5
        )
        for station in MODULE.STATION_ROWS:
            station_id = station["id"]
            text = self.by_id["LABEL_" + station_id]["target"]
            plaque = self.by_id["PAD_KEY_" + station_id]["target"]
            self.assertEqual(text["rotation_deg_pitch_yaw_roll"], [90.0, 180.0, 0.0])
            self.assertEqual(text["world_size_cm"], 128.0)
            self.assertEqual(text["colour_rgba"], [232, 222, 194, 255])
            self.assertEqual(MODULE._asset_path(plaque["material"]), MODULE.CHARCOAL_MATERIAL)
            self.assertEqual(text["location_cm"][:2], plaque["location_cm"][:2])
            self.assertGreater(
                text["location_cm"][2],
                plaque["location_cm"][2] + plaque["dimensions_cm"][2] / 2.0,
            )
        self.assertEqual(
            self.validation["source_text_colour_readback_contract"],
            {
                "frozen_authoring_call": "unreal.Color(R,G,B,A) positional",
                "ue_5_8_constructor_order": ["B", "G", "R", "A"],
                "immutable_source_readback_order": ["B", "G", "R", "A"],
                "v005_target_authoring": "unreal.Color(b=,g=,r=,a=) keyword",
                "target_readback_order": ["R", "G", "B", "A"],
            },
        )


class AdversarialPlanRejectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = MODULE.validate_offline_contract()
        cls.base = cls.contract["plan"]

    def assert_rejected(self, editor):
        plan = copy.deepcopy(self.base)
        editor(plan)
        with self.assertRaises(MODULE.PresentationUpgradeGuardError):
            MODULE.validate_upgrade_plan(plan)

    def test_rejects_deck_or_camera_black_surround_regressions(self):
        self.assert_rejected(
            lambda plan: mutation_index(plan)["DECK_BASE"]["target"]["dimensions_cm"].__setitem__(0, 9000.0)
        )
        self.assert_rejected(
            lambda plan: mutation_index(plan)["overview"]["target"]["location_cm"].__setitem__(0, -12000.0)
        )
        self.assert_rejected(
            lambda plan: mutation_index(plan)["steam_hero"]["target"].__setitem__("ortho_width_cm", 9000.0)
        )

    def test_rejects_route_rail_cap_bar_or_carrier_tampering(self):
        self.assert_rejected(
            lambda plan: mutation_index(plan)["FLOW_LANE"]["target"].__setitem__("material", MODULE.CHARCOAL_MATERIAL)
        )
        self.assert_rejected(
            lambda plan: mutation_index(plan)["FLOW_EDGE_INBOUND"]["target"]["location_cm"].__setitem__(0, 999999.0)
        )
        self.assert_rejected(
            lambda plan: addition_index(plan)["EMPTY_SHUTTLE_01_CHASSIS"]["location_cm"].__setitem__(1, 50000.0)
        )
        self.assert_rejected(
            lambda plan: plan.__setitem__("additions", plan["additions"][:-1])
        )

    def test_rejects_connector_gap_or_missing_station_port(self):
        self.assert_rejected(
            lambda plan: mutation_index(plan)["FLOW_CONNECTOR_01"]["target"]["dimensions_cm"].__setitem__(0, 1000.0)
        )
        self.assert_rejected(
            lambda plan: addition_index(plan)["FLOW_BRANCH_IN02"]["location_cm"].__setitem__(0, -7000.0)
        )
        self.assert_rejected(
            lambda plan: addition_index(plan)["STATION_PORT_CAP_S04"]["location_cm"].__setitem__(1, 10500.0)
        )

    def test_rejects_disconnected_zone_or_noncharcoal_plaque(self):
        self.assert_rejected(
            lambda plan: addition_index(plan)["ZONE_WING_S03_EAST"]["dimensions_cm"].__setitem__(0, 100.0)
        )
        self.assert_rejected(
            lambda plan: addition_index(plan)["ZONE_WING_IN01_WEST"]["location_cm"].__setitem__(1, 50000.0)
        )
        self.assert_rejected(
            lambda plan: mutation_index(plan)["PAD_KEY_IN01"]["target"].__setitem__("material", MODULE.ZONE_MATERIAL)
        )

    def test_rejects_label_rotation_visibility_or_placement_regressions(self):
        self.assert_rejected(
            lambda plan: mutation_index(plan)["LABEL_S03"]["target"].__setitem__(
                "rotation_deg_pitch_yaw_roll", [90.0, 0.0, 0.0]
            )
        )
        self.assert_rejected(
            lambda plan: mutation_index(plan)["LABEL_TITLE"]["target"]["location_cm"].__setitem__(0, 999999.0)
        )
        self.assert_rejected(
            lambda plan: mutation_index(plan)["LABEL_INBOUND"]["target"].__setitem__(
                "colour_rgba", [0, 0, 0, 0]
            )
        )

    def test_rejects_offdeck_floor_band_and_new_light_roof_machine_or_cargo(self):
        self.assert_rejected(
            lambda plan: addition_index(plan)["FLOOR_BAND_LONG_01"]["location_cm"].__setitem__(0, 999999.0)
        )
        for forbidden_role in ("Roof", "B_stylizedLight", "Machine", "Cargo"):
            def add_forbidden(plan, role=forbidden_role):
                plan["additions"] = tuple(plan["additions"]) + ({
                    "kind": "box", "id": "FORBIDDEN_" + role,
                    "label": "forbidden", "role": role,
                    "material": MODULE.CHARCOAL_MATERIAL,
                    "location_cm": [0.0, 0.0, 0.0],
                    "dimensions_cm": [1.0, 1.0, 1.0], "yaw_deg": 0.0,
                },)
            self.assert_rejected(add_forbidden)

    def test_rejects_machine_cargo_selection_and_out_of_scope_fields(self):
        self.assert_rejected(
            lambda plan: mutation_index(plan)["PAD_S03"]["source"].__setitem__(
                "label", "VIS | S03 machine"
            )
        )
        self.assert_rejected(
            lambda plan: mutation_index(plan)["PAD_S03"]["target"].__setitem__(
                "mesh_asset", "/Game/Forbidden/Machine"
            )
        )
        self.assert_rejected(
            lambda plan: mutation_index(plan)["LABEL_S03"]["target"].__setitem__(
                "text", "INVENTED PROCESS"
            )
        )
        self.assert_rejected(
            lambda plan: mutation_index(plan)["LABEL_IN01"]["source"].__setitem__(
                "colour_rgba", [0, 0, 0, 0]
            )
        )
        def tamper_source_and_catalog(plan):
            mutation_index(plan)["LABEL_IN01"]["source"]["colour_rgba"] = [0, 0, 0, 0]
            plan["catalog"]["text"]["LABEL_IN01"]["colour_rgba"] = [0, 0, 0, 0]
        self.assert_rejected(tamper_source_and_catalog)

    def test_rejects_target_role_or_actor_label_scope_impersonation(self):
        self.assert_rejected(
            lambda plan: mutation_index(plan)["DECK_BASE"]["target"].__setitem__(
                "role", "MachineGeometry"
            )
        )
        self.assert_rejected(
            lambda plan: mutation_index(plan)["DECK_BORDER_WEST"]["target"].__setitem__(
                "role", "CargoGeometry"
            )
        )
        for item_id in ("DECK_BASE", "FLOW_LANE", "LABEL_S03", "LABEL_TITLE"):
            self.assert_rejected(
                lambda plan, selected=item_id: mutation_index(plan)[selected]["target"].__setitem__(
                    "label", "CARGO | impersonation"
                )
            )
        for deceptive in (
            " CARGO | leading whitespace",
            "CARGO| missing delimiter space",
            "MACHINERY | deceptive",
            "arbitrary unreviewed rename",
        ):
            self.assert_rejected(
                lambda plan, value=deceptive: mutation_index(plan)["DECK_BASE"]["target"].__setitem__(
                    "label", value
                )
            )


class RuntimeSourceSafetyTests(unittest.TestCase):
    def test_import_is_offline_and_main_fails_before_any_mutation_in_cpython(self):
        self.assertIsNone(MODULE.unreal)
        with self.assertRaises(MODULE.PresentationUpgradeGuardError):
            MODULE.main()

    def test_new_box_collision_order_and_strict_readbacks_are_present(self):
        configure = inspect.getsource(MODULE._configure_and_verify_no_collision)
        profile = configure.index("set_collision_profile_name")
        all_channels = configure.index("set_collision_response_to_all_channels")
        each_channel = configure.index("set_collision_response_to_channel")
        disabled = configure.index("set_collision_enabled")
        readback = configure.index("_readback_no_collision")
        self.assertLess(profile, all_channels)
        self.assertLess(all_channels, each_channel)
        self.assertLess(each_channel, disabled)
        self.assertLess(disabled, readback)
        strict = inspect.getsource(MODULE._readback_no_collision)
        for token in (
            "get_actor_enable_collision", "get_collision_enabled",
            "get_collision_response_to_channel", "generate_overlap_events",
            "can_ever_affect_navigation",
        ):
            self.assertIn(token, strict)
        spawn = inspect.getsource(MODULE._spawn_presentation_box)
        self.assertIn("_actor_transform_record", spawn)
        self.assertIn("_rotation_close", spawn)
        self.assertIn("_close(transform[\"scale3d\"]", spawn)
        verify = inspect.getsource(MODULE._verify_target_actor)
        self.assertIn('"collision_readback": collision_readback', verify)
        self.assertIn("mutated v005 box", verify)
        self.assertIn("mutated v005 TextRender", verify)

    def test_mutated_and_spawned_boxes_have_exact_role_tag_readback(self):
        replace = inspect.getsource(MODULE._replace_exact_role_tag)
        self.assertIn("not str(tag).startswith(prefix)", replace)
        self.assertIn("role_tags != [expected]", replace)
        apply_box = inspect.getsource(MODULE._apply_box_mutation)
        spawn = inspect.getsource(MODULE._spawn_presentation_box)
        verify = inspect.getsource(MODULE._verify_target_actor)
        self.assertIn("_replace_exact_role_tag", apply_box)
        self.assertIn("_replace_exact_role_tag", spawn)
        self.assertIn("retained a stale role tag", verify)

    def test_text_colour_uses_ue58_bgra_source_readback_and_keyword_target_write(self):
        self.assertEqual(
            MODULE._legacy_positional_unreal_color_readback_rgba([23, 29, 33, 255]),
            [33, 29, 23, 255],
        )
        self.assertEqual(
            MODULE._legacy_positional_unreal_color_readback_rgba([232, 222, 194, 255]),
            [194, 222, 232, 255],
        )
        stub = (PROJECT / "Intermediate/PythonStub/unreal.py").read_text(
            encoding="utf-8"
        )
        color_start = stub.index("class Color(StructBase):")
        color_end = stub.index("class DateTime(StructBase):", color_start)
        color_stub = stub[color_start:color_end]
        self.assertIn(
            "def __init__(self, b: int = 0, g: int = 0, r: int = 0, a: int = 0)",
            color_stub,
        )
        writer = inspect.getsource(MODULE._unreal_color_from_rgba)
        self.assertIn("b=int(authored_rgba[2])", writer)
        self.assertIn("g=int(authored_rgba[1])", writer)
        self.assertIn("r=int(authored_rgba[0])", writer)
        self.assertIn("a=int(authored_rgba[3])", writer)
        apply_text = inspect.getsource(MODULE._apply_text_mutation)
        self.assertIn("_unreal_color_from_rgba", apply_text)
        source_guard = inspect.getsource(MODULE._assert_source_actor)
        self.assertIn("_legacy_positional_unreal_color_readback_rgba", source_guard)
        self.assertIn("legacy colour readback changed", source_guard)

    def test_material_compilation_is_stabilized_before_final_save(self):
        source = inspect.getsource(MODULE._create_unlit_material)
        first_compile = source.index("recompile_material")
        stabilization_save = source.index("stabilization save")
        second_compile = source.index("recompile_material", first_compile + 1)
        bounded_save = source.index("while final_save_attempts < 2")
        self.assertLess(first_compile, stabilization_save)
        self.assertLess(stabilization_save, second_compile)
        self.assertLess(second_compile, bounded_save)
        self.assertIn("asset_dirty", source)
        self.assertIn('get_editor_property("shading_model")', source)
        self.assertIn('expression.get_editor_property("constant")', source)
        self.assertIn("linear_rgb_readback", source)

    def test_material_dirty_checkpoint_accepts_only_two_safe_states(self):
        self.assertEqual(
            MODULE._validate_post_material_dirty_packages(
                {"content": [], "maps": []}, "test"
            ),
            {"content": [], "maps": []},
        )
        self.assertEqual(
            MODULE._validate_post_material_dirty_packages(
                {"content": [], "maps": [MODULE.TARGET_MAP]}, "test"
            ),
            {"content": [], "maps": [MODULE.TARGET_MAP]},
        )
        for dirty in (
            {"content": [MODULE.FLOOR_BAND_MATERIAL], "maps": []},
            {"content": [], "maps": [MODULE.SOURCE_MAP]},
            {"content": [], "maps": [MODULE.TARGET_MAP, MODULE.SOURCE_MAP]},
        ):
            with self.assertRaises(MODULE.PresentationUpgradeGuardError):
                MODULE._validate_post_material_dirty_packages(dirty, "test")

    def test_installer_has_no_destructive_or_source_save_api(self):
        source = INSTALLER.read_text(encoding="utf-8")
        for forbidden in (
            "delete_asset(", "delete_directory(", "rename_asset(",
            "destroy_actor(", "save_directory(", "save_asset(SOURCE",
            "save_loaded_asset(SOURCE", "load_level(SOURCE_MAP",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("new_level_from_template(TARGET_MAP, SOURCE_MAP)", source)
        self.assertEqual(source.count("save_current_level()"), 1)
        self.assertIn('with path.open("xb")', source)

    def test_receipt_schema_and_honest_pending_gates_are_explicit(self):
        self.assertEqual(
            MODULE.INSTALL_RECEIPT_SCHEMA,
            "cairnwell.press_shop.overhead_presentation_upgrade_install_receipt.v001",
        )
        self.assertEqual(
            MODULE.INSTALL_STATUS,
            "PASS_CANDIDATE_PRESENTATION_UPGRADE_APPLIED__"
            "V004_FINGERPRINTS_PRESERVED__VISUAL_CAPTURE_AND_PIE_PENDING",
        )
        main_source = inspect.getsource(MODULE.main)
        for token in (
            '"runtime_validated": False', '"pie_validated": False',
            '"cook_validated": False', '"packaged_build_validated": False',
            '"visual_capture_validated": False',
            '"steam_visual_quality_human_approved": False',
            '"source_map_mutated": False', '"new_machinery_geometry": 0',
            '"new_cargo_geometry": 0',
            '"mutated_primitive_collision_readback_count": len(mutated_primitive_records)',
            '"collision_enabled_on_mutated_presentation_primitives": False',
        ):
            self.assertIn(token, main_source)


if __name__ == "__main__":
    unittest.main()
