"""Offline guards for the Press Shop 2126 v004 presentation-polish lane.

These tests import the installer in ordinary CPython.  They inspect frozen
receipts and package hashes plus pure plan arithmetic and source-code mutation
guards.  They do not launch Unreal, clone or save a map, create the v004 slate
material, mutate an actor, or write an install receipt.
"""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import unittest
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
INSTALLER = (
    PROJECT
    / "Tools"
    / "install_pressshop_2126_overhead_presentation_polish_v001.py"
)


def load_installer_module():
    spec = importlib.util.spec_from_file_location(
        "pressshop_overhead_presentation_polish_v001_test_subject",
        INSTALLER,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MODULE = load_installer_module()


def mutation_index(plan):
    return {row["id"]: row for row in plan["mutations"]}


class FrozenInputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = MODULE.validate_offline_contract()

    def test_frozen_v003_source_and_new_v004_target_are_exact_and_disjoint(self):
        self.assertEqual(
            MODULE.SOURCE_MAP,
            "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadCargo_v003/"
            "Maps/LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003",
        )
        self.assertEqual(
            MODULE.TARGET_MAP,
            "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPresentation_v004/"
            "Maps/LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004",
        )
        self.assertNotEqual(MODULE.SOURCE_MAP, MODULE.TARGET_MAP)
        self.assertEqual(MODULE.SOURCE_FILE.stat().st_size, 1_175_784)
        self.assertEqual(
            MODULE.digest(MODULE.SOURCE_FILE),
            "5eae51f2a7d3e1c72deb4fd455d57a6339dee061840b7d062c5ddf680ab6100f",
        )
        self.assertEqual(
            MODULE.digest(MODULE.SOURCE_RECEIPT),
            "0d58168d05869693aef7aaac8ddd4d5bac3e7e71785b4b4db6d6f32cd6569619",
        )
        self.assertEqual(
            MODULE.digest(MODULE.V002_FILE),
            "58fe57f3af0dfcf4021d6bbcd3a52d7d66de22187b561fb2db41becd83023275",
        )

    def test_v003_integration_receipt_is_honest_and_cargo_inventory_is_exact(self):
        receipt = self.contract["source_receipt"]
        self.assertEqual(receipt["schema"], MODULE.SOURCE_RECEIPT_SCHEMA)
        self.assertEqual(receipt["status"], MODULE.SOURCE_RECEIPT_STATUS)
        self.assertTrue(receipt["candidate_only"])
        self.assertEqual(receipt["cargo_layer_count"], 26)
        self.assertEqual(receipt["combined_visual_layer_count"], 146)
        self.assertEqual(len(receipt["cargo_layers"]), 26)
        labels = [row["actor"]["label"] for row in receipt["cargo_layers"]]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertTrue(all(label.startswith("CARGO | ") for label in labels))
        self.assertFalse(receipt["source_map_mutated"])
        self.assertFalse(receipt["protected_authority_map_mutated"])
        self.assertFalse(receipt["runtime_validated"])
        self.assertFalse(receipt["visual_capture_validated"])
        self.assertFalse(receipt["steam_capture_validated"])

    def test_v002_presentation_and_all_reused_assets_are_hash_locked(self):
        receipt = self.contract["v002_receipt"]
        self.assertEqual(MODULE.digest(MODULE.V002_RECEIPT), MODULE.V002_RECEIPT_SHA256)
        self.assertEqual(receipt["created_actor_count"], 82)
        self.assertEqual(len(receipt["created_boxes"]), 64)
        self.assertEqual(len(receipt["created_texts"]), 15)
        self.assertEqual(len(receipt["cameras"]), 3)
        self.assertEqual(len(self.contract["material_hashes"]), 4)
        for asset, expected in MODULE.MATERIAL_LOCKS.items():
            disk = MODULE.virtual_to_uasset(asset)
            self.assertEqual(disk.stat().st_size, expected["bytes"])
            self.assertEqual(MODULE.digest(disk), expected["sha256"])
        cargo_import = self.contract["cargo_import_receipt"]
        self.assertEqual(len(cargo_import["created_uasset_sha256"]), 30)
        self.assertEqual(
            sorted(cargo_import["created_assets"]),
            sorted(cargo_import["created_uasset_sha256"]),
        )

    def test_every_protected_map_hash_is_current(self):
        snapshot = self.contract["protected_hashes"]
        self.assertEqual(set(snapshot), set(MODULE.PROTECTED_MAPS))
        self.assertEqual(len(snapshot), 6)
        self.assertEqual(snapshot["source_overhead_cargo_v003"], MODULE.SOURCE_FILE_SHA256)
        self.assertEqual(snapshot["source_overhead_presentation_v002"], MODULE.V002_FILE_SHA256)


class ReviewedPresentationPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v002 = MODULE.validate_v002_receipt()
        cls.plan = MODULE.build_polish_plan(cls.v002)
        cls.validation = MODULE.validate_polish_plan(cls.plan)
        cls.by_id = mutation_index(cls.plan)

    def test_plan_has_only_the_exact_reviewed_presentation_surface(self):
        self.assertEqual(len(self.plan["mutations"]), 38)
        self.assertEqual(len(self.plan["new_connectors"]), 3)
        self.assertEqual(self.validation["box_mutation_count"], 20)
        self.assertEqual(self.validation["text_mutation_count"], 15)
        self.assertEqual(self.validation["camera_mutation_count"], 3)
        labels = [row["source"]["label"] for row in self.plan["mutations"]]
        self.assertFalse(any(label.startswith(("VIS | ", "CARGO | ")) for label in labels))
        self.assertEqual(
            {row["kind"] for row in self.plan["new_connectors"]},
            {"box"},
        )
        self.assertEqual(MODULE.EXPECTED_FINAL_ACTOR_COUNT, 247)

    def test_slate_deck_colour_is_exact_and_lane_remains_charcoal(self):
        deck = self.by_id["DECK_BASE"]["target"]
        lane = self.by_id["FLOW_LANE"]["target"]
        self.assertEqual(deck["material"], MODULE.SLATE_DECK_MATERIAL)
        self.assertTrue(MODULE.SLATE_DECK_MATERIAL.startswith(MODULE.TARGET_ROOT + "/"))
        self.assertEqual(MODULE.SLATE_DECK_SRGB_HEX, "#36534F")
        self.assertEqual(
            MODULE.srgb_hex_to_linear("#36534F"),
            (
                0.03688945040110004,
                0.08650046203654976,
                0.07818742180518633,
            ),
        )
        self.assertEqual(lane["material"], MODULE.DECK_MATERIAL)
        self.assertEqual(lane["dimensions_cm"], [500.0, 15500.0, 0.6])
        self.assertEqual(
            self.validation["slate_deck_material"],
            {
                "asset": MODULE.SLATE_DECK_MATERIAL,
                "srgb_hex": "#36534F",
                "linear_rgb": list(MODULE.srgb_hex_to_linear("#36534F")),
                "shading_model": "UNLIT",
            },
        )

    def test_flow_edges_are_narrow_yellow_and_arrows_are_not_mutated(self):
        expected = {
            "FLOW_EDGE_WEST": ([-6750.0, MODULE.FLOW_LANE_CENTER_Y, -0.3], [28.0, 15500.0, 0.4]),
            "FLOW_EDGE_EAST": ([-6250.0, MODULE.FLOW_LANE_CENTER_Y, -0.3], [28.0, 15500.0, 0.4]),
            "FLOW_EDGE_INBOUND": (
                [-6500.0, MODULE.FLOW_LANE_CENTER_Y - MODULE.FLOW_LANE_LENGTH_Y / 2.0, -0.3],
                [500.0, 28.0, 0.4],
            ),
            "FLOW_EDGE_OUTBOUND": (
                [-6500.0, MODULE.FLOW_LANE_CENTER_Y + MODULE.FLOW_LANE_LENGTH_Y / 2.0, -0.3],
                [500.0, 28.0, 0.4],
            ),
        }
        for item_id, (location, dimensions) in expected.items():
            target = self.by_id[item_id]["target"]
            self.assertEqual(target["location_cm"], location)
            self.assertEqual(target["dimensions_cm"], dimensions)
            self.assertEqual(MODULE._asset_path(target["material"]), MODULE.YELLOW_MATERIAL)
        mutation_ids = set(self.by_id)
        self.assertFalse(any(item_id.startswith("FLOW_ARROW_") for item_id in mutation_ids))
        arrows = [
            row for row in self.v002["created_boxes"]
            if str(row["id"]).startswith("FLOW_ARROW_")
        ]
        self.assertEqual(len(arrows), 24)
        self.assertEqual({MODULE._asset_path(row["material"]) for row in arrows}, {MODULE.YELLOW_MATERIAL})

    def test_only_s03_through_s06_pads_tighten_and_stay_pale_green(self):
        selected_pad_ids = {
            item_id.removeprefix("PAD_")
            for item_id in self.by_id
            if item_id.startswith("PAD_") and not item_id.startswith("PAD_KEY_")
        }
        self.assertEqual(selected_pad_ids, {"S03", "S04", "S05", "S06"})
        ranges = []
        for station_id, length in MODULE.PRESS_PAD_LENGTHS_Y.items():
            pad = self.by_id["PAD_" + station_id]["target"]
            key = self.by_id["PAD_KEY_" + station_id]["target"]
            self.assertEqual(pad["dimensions_cm"], [1800.0, length, 0.8])
            self.assertEqual(MODULE._asset_path(pad["material"]), MODULE.ZONE_MATERIAL)
            self.assertEqual(key["dimensions_cm"], [42.0, length - 100.0, 0.4])
            self.assertEqual(key["location_cm"][0], -9858.75)
            y = pad["location_cm"][1]
            ranges.append((y - length / 2.0, y + length / 2.0))
        ranges.sort()
        gutters = [right[0] - left[1] for left, right in zip(ranges, ranges[1:])]
        self.assertEqual(gutters, [250.0, 250.0, 175.0])
        untouched_pads = {
            row["id"] for row in self.v002["created_boxes"]
            if row["role"] == "StationPad" and row["id"] not in {"PAD_" + value for value in selected_pad_ids}
        }
        self.assertEqual(len(untouched_pads), 8)

    def test_labels_use_capture_proven_readable_rotation_and_reviewed_inset(self):
        self.assertEqual(MODULE.TEXT_ROTATION, (90.0, 180.0, 0.0))
        station_rows = {row["id"]: row for row in MODULE.STATION_ROWS}
        for item_id, mutation in self.by_id.items():
            if mutation["kind"] != "text":
                continue
            source = mutation["source"]
            target = mutation["target"]
            self.assertEqual(target["rotation_deg_pitch_yaw_roll"], [90.0, 180.0, 0.0])
            self.assertEqual(target["text"], source["text"])
            self.assertEqual(target["world_size_cm"], source["world_size_cm"])
            station_id = item_id.removeprefix("LABEL_")
            if station_id in station_rows:
                expected_x = -9690.75 if station_rows[station_id]["press_safe"] else -9940.75
                self.assertEqual(target["location_cm"][:2], [expected_x, station_rows[station_id]["center_y"]])
            else:
                self.assertEqual(target["location_cm"], source["location_cm"])
        self.assertEqual(
            self.validation["capture_rejected_text_rotations"],
            {
                "mirrored_backface": [-90.0, 180.0, 0.0],
                "horizontal_mirrored": [-90.0, 0.0, 0.0],
                "nonmirrored_upside_down": [90.0, 0.0, 0.0],
            },
        )

    def test_corrected_connectors_cover_s03_through_s06_at_exact_geometry(self):
        nonpress = self.by_id["FLOW_CONNECTOR_01"]["target"]
        press = self.by_id["FLOW_CONNECTOR_04"]["target"]
        self.assertEqual(nonpress["location_cm"], [-7295.375, 2200.0, -0.25])
        self.assertEqual(nonpress["dimensions_cm"], [1090.75, 58.0, 0.3])
        self.assertEqual(press["location_cm"], [-7420.375, 10400.0, -0.25])
        self.assertEqual(press["dimensions_cm"], [1340.75, 58.0, 0.3])
        new_by_id = {row["id"]: row for row in self.plan["new_connectors"]}
        self.assertEqual(
            set(new_by_id),
            {"FLOW_CONNECTOR_PRESS_S03", "FLOW_CONNECTOR_PRESS_S05", "FLOW_CONNECTOR_PRESS_S06"},
        )
        for station_id, y in MODULE.NEW_PRESS_CONNECTOR_Y.items():
            row = new_by_id["FLOW_CONNECTOR_PRESS_" + station_id]
            self.assertEqual(row["location_cm"], [-7420.375, y, -0.25])
            self.assertEqual(row["dimensions_cm"], [1340.75, 58.0, 0.3])
            self.assertEqual(row["material"], MODULE.CREAM_MATERIAL)
        self.assertEqual(self.validation["press_connector_y_cm"], [8950.0, 10400.0, 11850.0, 13300.0])

    def test_saved_cameras_are_true_overhead_and_improved(self):
        expected = {
            "overview": ([-7730.645880159617, 8840.218280826943, 21712.544], 16800.0),
            "press_spine": ([-8450.0, 10450.0, 21712.544], 8900.0),
            "steam_hero": ([-8990.75, 11125.0, 21712.544], 6300.0),
        }
        for item_id, (location, width) in expected.items():
            target = self.by_id[item_id]["target"]
            self.assertEqual(target["location_cm"], location)
            self.assertEqual(target["rotation_deg_pitch_yaw_roll"], [-90.0, 0.0, 0.0])
            self.assertEqual(target["ortho_width_cm"], width)
            self.assertIn("v004", target["label"])
            self.assertTrue(target["role_tag"].endswith(".v004"))


class FailClosedPlanTamperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = MODULE.build_polish_plan(MODULE.validate_v002_receipt())

    def assert_rejected(self, modifier):
        plan = copy.deepcopy(self.original)
        modifier(plan, mutation_index(plan))
        with self.assertRaises(MODULE.PresentationPolishGuardError):
            MODULE.validate_polish_plan(plan)

    def test_capture_rejected_text_transforms_are_rejected(self):
        self.assertTrue(MODULE._rotation_close([90.0, -180.0, 0.0], MODULE.TEXT_ROTATION))
        self.assertTrue(MODULE._rotation_close([90.0, 0.0, 180.0], MODULE.TEXT_ROTATION))
        for rotation in ([90.0, 0.0, 0.0], [-90.0, 180.0, 0.0], [-90.0, 0.0, 0.0]):
            with self.subTest(rotation=rotation):
                self.assert_rejected(
                    lambda plan, rows, rotation=rotation: rows["LABEL_S04"]["target"].__setitem__(
                        "rotation_deg_pitch_yaw_roll", list(rotation)
                    )
                )

    def test_visual_hierarchy_geometry_and_camera_tampering_is_rejected(self):
        cases = {
            "slate deck": lambda plan, rows: rows["DECK_BASE"]["target"].__setitem__("material", MODULE.DECK_MATERIAL),
            "cream lane": lambda plan, rows: rows["FLOW_LANE"]["target"].__setitem__("material", MODULE.CREAM_MATERIAL),
            "wide edge": lambda plan, rows: rows["FLOW_EDGE_WEST"]["target"]["dimensions_cm"].__setitem__(0, 80.0),
            "label inset": lambda plan, rows: rows["LABEL_S03"]["target"]["location_cm"].__setitem__(0, -9900.0),
            "pad move": lambda plan, rows: rows["PAD_S04"]["target"]["location_cm"].__setitem__(1, 9600.0),
            "old connector": lambda plan, rows: rows["FLOW_CONNECTOR_04"]["target"]["dimensions_cm"].__setitem__(0, 1090.75),
            "new connector": lambda plan, rows: plan["new_connectors"][0]["dimensions_cm"].__setitem__(0, 1300.0),
            "hero width": lambda plan, rows: rows["steam_hero"]["target"].__setitem__("ortho_width_cm", 6900.0),
        }
        for name, modifier in cases.items():
            with self.subTest(name=name):
                self.assert_rejected(modifier)

    def test_missing_press_connector_is_rejected(self):
        def remove_connector(plan, _rows):
            plan["new_connectors"] = tuple(plan["new_connectors"][:-1])

        self.assert_rejected(remove_connector)


class InstallerMutationSurfaceTests(unittest.TestCase):
    def test_cube_asset_object_and_package_paths_normalise_identically(self):
        class AssetReadback:
            def __init__(self, path):
                self.path = path

            def get_path_name(self):
                return self.path

        expected = "/Engine/BasicShapes/Cube"
        self.assertEqual(MODULE._asset_path(MODULE.CUBE_ASSET), expected)
        self.assertEqual(MODULE._asset_path(AssetReadback(expected)), expected)
        self.assertEqual(
            MODULE._asset_path(AssetReadback("/Engine/BasicShapes/Cube.Cube")),
            expected,
        )
        source = inspect.getsource(MODULE._assert_source_actor)
        self.assertIn("!= _asset_path(CUBE_ASSET)", source)
        self.assertNotIn("!= CUBE_ASSET", source)

    def test_installer_contains_no_source_destructive_or_overwrite_api(self):
        source = INSTALLER.read_text(encoding="utf-8")
        for forbidden in (
            "destroy_actor(",
            "delete_asset(",
            "delete_directory(",
            "rename_asset(",
            "save_asset(SOURCE_MAP",
            "save_loaded_asset(SOURCE",
            "load_level(SOURCE_MAP",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        self.assertIn("new_level_from_template(TARGET_MAP, SOURCE_MAP)", source)
        self.assertEqual(source.count("save_current_level()"), 1)
        self.assertIn('with path.open("xb")', source)
        self.assertIn("TARGET_FILE.exists() or TARGET_ROOT_DISK.exists()", source)

    def test_new_connector_collision_configuration_overrides_profile_and_is_strict(self):
        source = inspect.getsource(MODULE._verify_no_collision)
        profile = source.index("component.set_collision_profile_name")
        response = source.index("component.set_collision_response_to_all_channels")
        per_channel = source.index("component.set_collision_response_to_channel")
        enabled = source.index("component.set_collision_enabled")
        self.assertLess(profile, response)
        self.assertLess(response, per_channel)
        self.assertLess(per_channel, enabled)
        self.assertIn('normalised_profile not in {"nocollision", "custom"}', source)
        self.assertIn('"CustomWithNoCollisionAndIgnoreAll"', source)
        self.assertEqual(len(MODULE.COLLISION_CHANNEL_NAMES), 8)

    def test_collision_emulation_proves_profile_first_ignore_all_readback(self):
        class FakeCollisionChannel:
            pass

        for channel_name in MODULE.COLLISION_CHANNEL_NAMES:
            setattr(FakeCollisionChannel, channel_name, channel_name)

        class FakeUnreal:
            Name = staticmethod(str)
            CollisionChannel = FakeCollisionChannel

            class CollisionResponseType:
                ECR_IGNORE = "ECR_IGNORE"

            class CollisionEnabled:
                NO_COLLISION = "NO_COLLISION"

        class FakeActor:
            def __init__(self):
                self.enabled = True

            def set_actor_enable_collision(self, enabled):
                self.enabled = enabled

            def get_actor_enable_collision(self):
                return self.enabled

        class FakeComponent:
            def __init__(self):
                self.calls = []
                self.profile = "BlockAll"
                self.enabled = "QUERY_AND_PHYSICS"
                self.responses = {
                    channel: "ECR_BLOCK" for channel in MODULE.COLLISION_CHANNEL_NAMES
                }

            def set_collision_profile_name(self, profile, update_overlaps=False):
                self.calls.append(("profile", profile, update_overlaps))
                self.profile = profile
                self.responses = {
                    channel: "ECR_BLOCK" for channel in MODULE.COLLISION_CHANNEL_NAMES
                }

            def set_collision_response_to_all_channels(self, response):
                self.calls.append(("response_all", response))
                self.profile = "Custom"
                self.responses = {
                    channel: response for channel in MODULE.COLLISION_CHANNEL_NAMES
                }

            def set_collision_response_to_channel(self, channel, response):
                self.calls.append(("response_channel", channel, response))
                self.profile = "Custom"
                self.responses[channel] = response

            def set_collision_enabled(self, enabled):
                self.calls.append(("enabled", enabled))
                self.profile = "Custom"
                self.enabled = enabled

            def set_editor_property(self, name, value):
                self.calls.append(("property", name, value))

            def get_collision_enabled(self):
                return self.enabled

            def get_collision_profile_name(self):
                return self.profile

            def get_collision_response_to_channel(self, channel):
                return self.responses[channel]

        previous = MODULE.unreal
        MODULE.unreal = FakeUnreal()
        try:
            actor = FakeActor()
            component = FakeComponent()
            result = MODULE._verify_no_collision(actor, component, "TEST_CONNECTOR")
            call_names = [row[0] for row in component.calls]
            self.assertEqual(call_names[0:2], ["profile", "response_all"])
            self.assertEqual(call_names[2:10], ["response_channel"] * 8)
            self.assertEqual(call_names[10], "enabled")
            self.assertFalse(result["actor_collision_enabled"])
            self.assertEqual(result["component_collision_enabled"], "NO_COLLISION")
            self.assertEqual(result["collision_profile"], "Custom")
            self.assertEqual(
                result["profile_acceptance"],
                "CustomWithNoCollisionAndIgnoreAll",
            )
            self.assertEqual(result["ignored_channels"], list(MODULE.COLLISION_CHANNEL_NAMES))

            class StubbornComponent(FakeComponent):
                def get_collision_response_to_channel(self, channel):
                    if channel == "ECC_WORLD_STATIC":
                        return "ECR_BLOCK"
                    return super().get_collision_response_to_channel(channel)

            with self.assertRaisesRegex(
                MODULE.PresentationPolishGuardError,
                "does not ignore ECC_WORLD_STATIC",
            ):
                MODULE._verify_no_collision(
                    FakeActor(), StubbornComponent(), "STUBBORN_CONNECTOR"
                )
        finally:
            MODULE.unreal = previous

    def test_slate_material_compile_and_save_order_is_stabilized_and_bounded(self):
        source = inspect.getsource(MODULE._create_slate_deck_material)
        compile_token = "ue.MaterialEditingLibrary.recompile_material(material)"
        save_token = "ue.EditorAssetLibrary.save_loaded_asset("

        def positions(token):
            result = []
            cursor = 0
            while True:
                found = source.find(token, cursor)
                if found < 0:
                    return result
                result.append(found)
                cursor = found + len(token)

        compile_positions = positions(compile_token)
        save_positions = positions(save_token)
        self.assertEqual(len(compile_positions), 2)
        self.assertEqual(len(save_positions), 2)
        self.assertLess(compile_positions[0], save_positions[0])
        self.assertLess(save_positions[0], compile_positions[1])
        self.assertLess(compile_positions[1], save_positions[1])
        self.assertIn("while final_save_attempts < 2", source)
        self.assertIn("dirty_after_attempt = dirty_package_paths()", source)
        self.assertIn("SLATE_DECK_MATERIAL in dirty_after_attempt", source)
        self.assertIn('"material_recompile_passes": 2', source)
        self.assertIn('"final_save_attempts": final_save_attempts', source)

    def test_dirty_package_guards_report_exact_expected_and_actual_sets(self):
        helper = inspect.getsource(MODULE._assert_dirty_packages)
        self.assertIn("expected_dirty={}; actual_dirty={}", helper)
        self.assertIn("json.dumps(normalised_expected", helper)
        self.assertIn("json.dumps(actual", helper)
        main_source = inspect.getsource(MODULE.main)
        self.assertGreaterEqual(main_source.count("_assert_dirty_packages("), 4)
        self.assertIn("_validate_post_slate_dirty_packages(dirty_package_paths())", main_source)
        self.assertIn('"only the v004 target map may be dirty before save"', main_source)
        self.assertIn('"candidate packages remain dirty after explicit save"', main_source)

    def test_post_slate_checkpoint_accepts_only_clean_or_target_map_dirty(self):
        allowed = (
            {"content": [], "maps": []},
            {"content": [], "maps": [MODULE.TARGET_MAP]},
        )
        for state in allowed:
            with self.subTest(allowed=state):
                self.assertEqual(
                    MODULE._validate_post_slate_dirty_packages(state),
                    state,
                )

        rejected = (
            {"content": [MODULE.SLATE_DECK_MATERIAL], "maps": []},
            {"content": [], "maps": ["/Game/Foreign/Map"]},
            {"content": [], "maps": [MODULE.TARGET_MAP, "/Game/Foreign/Map"]},
            {"content": [MODULE.SLATE_DECK_MATERIAL], "maps": [MODULE.TARGET_MAP]},
            {"content": ["/Game/Foreign/Asset"], "maps": ["/Game/Foreign/Map"]},
        )
        for state in rejected:
            with self.subTest(rejected=state):
                with self.assertRaisesRegex(
                    MODULE.PresentationPolishGuardError,
                    "unsafe dirty packages after slate material save",
                ):
                    MODULE._validate_post_slate_dirty_packages(state)

    def test_receipt_contract_is_candidate_only_and_keeps_pending_gates_honest(self):
        self.assertEqual(
            MODULE.INSTALL_STATUS,
            "PASS_CANDIDATE_PRESENTATION_POLISH_APPLIED__"
            "CARGO_PRESERVED__PIE_CAPTURE_PENDING",
        )
        source = inspect.getsource(MODULE.main)
        self.assertIn('"cargo_actor_mutated_count": 0', source)
        self.assertIn('"machinery_actor_mutated_count": 0', source)
        self.assertIn('"source_actor_removed_count": 0', source)
        self.assertIn('"new_machinery_geometry": 0', source)
        self.assertIn('"new_cargo_geometry": 0', source)
        for field in (
            "runtime_validated",
            "packaged_build_validated",
            "visual_capture_validated",
            "steam_capture_validated",
        ):
            self.assertIn('"{}": False'.format(field), source)
        self.assertIn('"created_materials": [slate_material_record]', source)
        self.assertIn('"full_deck_srgb_hex": SLATE_DECK_SRGB_HEX', source)

    def test_ordinary_cpython_cannot_enter_the_unreal_mutation_lane(self):
        self.assertIsNone(MODULE.unreal)
        with self.assertRaisesRegex(
            MODULE.PresentationPolishGuardError,
            "main must run inside UnrealEditor Python",
        ):
            MODULE.main()


if __name__ == "__main__":
    unittest.main()
