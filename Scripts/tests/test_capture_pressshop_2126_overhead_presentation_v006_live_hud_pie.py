"""Adversarial offline tests for the v006 regular-PIE live-HUD capture lane."""

from __future__ import annotations

import ast
import copy
import importlib.util
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SUBJECT = (
    PROJECT
    / "Tools/capture_pressshop_2126_overhead_presentation_v006_live_hud_pie.py"
)
SPEC = importlib.util.spec_from_file_location("v006_live_hud_capture", SUBJECT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)

MAP_SHA = "0123456789abcdef" * 4
RECEIPT_SHA = "fedcba9876543210" * 4


def exact_install_receipt() -> dict:
    protected = {
        "Content/LineBoss/Factory/OneFactory/v001/Maps/authority.umap": {
            "sha256": "1" * 64,
            "bytes": 123,
        }
    }
    mutations = [
        {
            "id": "steam_hero",
            "kind": "camera",
            "actor_path": "/Game/V006.V006:PersistentLevel.CameraActor_0",
            "label": module.STEAM_HERO_LABEL,
            "location_cm": list(module.STEAM_HERO_LOCATION),
            "ortho_width_cm": module.STEAM_HERO_ORTHO_WIDTH,
            "role_tag": module.STEAM_HERO_ROLE_TAG,
        }
    ]
    mutations.extend(
        {"id": "presentation_{:03d}".format(index), "kind": "presentation"}
        for index in range(82)
    )
    return {
        "schema": module.INSTALL_SCHEMA,
        "status": module.INSTALL_STATUS,
        "candidate_only": True,
        "target_map": module.TARGET_MAP,
        "target_map_sha256": MAP_SHA,
        "combined_visual_layer_count": 146,
        "machinery_visual_layer_count": 120,
        "cargo_layer_count": 26,
        "machinery_actor_mutated_count": 0,
        "cargo_actor_mutated_count": 0,
        "machine_or_cargo_transform_mutations": 0,
        "new_machinery_geometry": 0,
        "new_cargo_geometry": 0,
        "native_cpp_modified": False,
        "game_mode_after": module.GAME_MODE_CLASS,
        "protected_hashes_before": protected,
        "protected_hashes_after": copy.deepcopy(protected),
        "runtime_validated": False,
        "pie_validated": False,
        "presentation_mutations": mutations,
    }


def exact_activation() -> dict:
    result = {
        "counts": {
            "game_mode": 1,
            "player_controller": 1,
            "pawn": 1,
            "hud": 1,
            "bootstrap": 1,
            "runtime_coordinator": 1,
            "production": 1,
            "press": 1,
            "body_weld": 1,
            "paint": 1,
            "assembly": 1,
            "presentation": 1,
            "top_bar": 1,
            "flow_strip": 1,
        },
        "classes": {
            "game_mode": module.GAME_MODE_CLASS,
            "player_controller": module.PLAYER_CONTROLLER_CLASS,
            "pawn": module.PAWN_CLASS,
            "hud": module.HUD_CLASS,
            "bootstrap": module.BOOTSTRAP_CLASS,
        },
        "route_count": 57,
        "press_route_prefix": list(module.EXPECTED_PRESS_PREFIX),
        "topology_id": module.EXPECTED_TOPOLOGY_PREFIX + "A1B2C3D4",
        "starter_contract_ids": list(module.EXPECTED_CONTRACT_IDS),
        "unit_count_before_player_order": 0,
    }
    for flag in (
        "controller_is_primary",
        "controller_possesses_pawn",
        "controller_views_pawn_before_capture",
        "controller_owns_hud",
        "game_mode_shell_valid",
        "game_mode_runtime_backbone_valid",
        "game_mode_binds_bootstrap",
        "game_mode_binds_coordinator",
        "game_mode_binds_production",
        "bootstrap_ready",
        "all_layouts_commissioned",
        "all_departments_commissioned",
        "ledger_valid",
        "runtime_factory_valid",
        "top_bar_visible",
        "flow_strip_visible",
        "widgets_owned_by_player",
        "natural_actor_tick_enabled",
        "automatic_contract_dispatch_disabled",
    ):
        result[flag] = True
    return result


def exact_camera() -> dict:
    return {
        "path": "/Game/V006.V006:PersistentLevel.CameraActor_0",
        "class": module.CAMERA_CLASS,
        "label": module.STEAM_HERO_LABEL,
        "tags": [module.STEAM_HERO_CAMERA_TAG, module.STEAM_HERO_ROLE_TAG],
        "location_cm": list(module.STEAM_HERO_LOCATION),
        "rotation_pitch_yaw_roll": list(module.STEAM_HERO_ROTATION),
        "projection": "CameraProjectionMode.ORTHOGRAPHIC",
        "ortho_width_cm": module.STEAM_HERO_ORTHO_WIDTH,
        "aspect_ratio": module.STEAM_HERO_ASPECT,
        "constrain_aspect_ratio": True,
    }


def exact_press(progress: float = 0.49) -> dict:
    return {
        "station_id": module.PRESS_STATION_ID,
        "station_cursor": module.PRESS_ROUTE_INDEX,
        "progress01": progress,
        "started": True,
        "completed": False,
        "dispatched": False,
        "awaiting_quality_result": False,
        "machine_id": module.TARGET_PRESS_MACHINE,
        "visible_frame": "DESCENDING",
        "visible_frame_count": 1,
        "beacon_state": "RUNNING",
        "bound_visual_layer_count": 146,
        "status_beacon_count": 14,
        "task_light_count": 4,
    }


class LiveHudV006OfflineTests(unittest.TestCase):
    def test_frozen_target_and_ui_contract(self) -> None:
        self.assertTrue(module.TARGET_MAP.endswith("OverheadPresentation_v006"))
        self.assertEqual(module.SCREENSHOT_SIZE, (1920, 1080))
        self.assertEqual(module.STEAM_HERO_ORTHO_WIDTH, 5700.0)
        self.assertEqual(module.STEAM_HERO_ROTATION, (-90.0, 0.0, 0.0))
        self.assertEqual(
            module.STEAM_HERO_ROLE_TAG,
            "LB.PressShop.OverheadDeck.Camera.SteamHero.v006",
        )
        self.assertEqual(module.EXPECTED_ROUTE_COUNT, 57)

    def test_both_reviewed_lowercase_hashes_are_mandatory(self) -> None:
        for environment in (
            {},
            {module.MAP_SHA_ENV: MAP_SHA},
            {module.MAP_SHA_ENV: MAP_SHA.upper(), module.RECEIPT_SHA_ENV: RECEIPT_SHA},
            {module.MAP_SHA_ENV: "0" * 64, module.RECEIPT_SHA_ENV: RECEIPT_SHA},
            {module.MAP_SHA_ENV: MAP_SHA, module.RECEIPT_SHA_ENV: "a" * 64},
        ):
            with self.assertRaises(module.CaptureGuardError):
                module.required_guard_hashes(environment)
        self.assertEqual(
            module.required_guard_hashes(
                {module.MAP_SHA_ENV: MAP_SHA, module.RECEIPT_SHA_ENV: RECEIPT_SHA}
            ),
            (MAP_SHA, RECEIPT_SHA),
        )

    def test_exact_install_receipt_passes(self) -> None:
        contract = module.validate_install_receipt(exact_install_receipt(), MAP_SHA)
        self.assertEqual(contract["mutation_count"], 83)
        self.assertEqual(contract["steam_hero"]["role_tag"], module.STEAM_HERO_ROLE_TAG)

    def test_install_receipt_adversarial_drift_fails(self) -> None:
        cases = {
            "schema": "wrong",
            "status": "wrong",
            "candidate_only": False,
            "target_map": "/Game/Wrong",
            "target_map_sha256": "1" * 64,
            "combined_visual_layer_count": 145,
            "machinery_visual_layer_count": 119,
            "cargo_layer_count": 25,
            "machinery_actor_mutated_count": 1,
            "cargo_actor_mutated_count": 1,
            "machine_or_cargo_transform_mutations": 1,
            "new_machinery_geometry": 1,
            "new_cargo_geometry": 1,
            "native_cpp_modified": True,
            "game_mode_after": "/Script/Engine.GameModeBase",
            "runtime_validated": True,
            "pie_validated": True,
        }
        for key, value in cases.items():
            with self.subTest(key=key):
                receipt = exact_install_receipt()
                receipt[key] = value
                with self.assertRaises(module.CaptureGuardError):
                    module.validate_install_receipt(receipt, MAP_SHA)
        receipt = exact_install_receipt()
        receipt["protected_hashes_after"]["changed"] = {}
        with self.assertRaises(module.CaptureGuardError):
            module.validate_install_receipt(receipt, MAP_SHA)

    def test_install_receipt_steam_camera_and_inventory_drift_fail(self) -> None:
        for key, value in (
            ("label", "wrong"),
            ("role_tag", "LB_PRESENTATION_CAMERA_STEAM_HERO"),
            ("location_cm", [-8855.75, 11092.0, 14000.0]),
            ("ortho_width_cm", 6000.0),
            ("kind", "box"),
        ):
            with self.subTest(key=key):
                receipt = exact_install_receipt()
                receipt["presentation_mutations"][0][key] = value
                with self.assertRaises(module.CaptureGuardError):
                    module.validate_install_receipt(receipt, MAP_SHA)
        receipt = exact_install_receipt()
        receipt["presentation_mutations"].pop()
        with self.assertRaises(module.CaptureGuardError):
            module.validate_install_receipt(receipt, MAP_SHA)
        receipt = exact_install_receipt()
        receipt["presentation_mutations"].append(copy.deepcopy(receipt["presentation_mutations"][0]))
        with self.assertRaises(module.CaptureGuardError):
            module.validate_install_receipt(receipt, MAP_SHA)

    def test_reflection_parsers_fail_closed_on_native_false(self) -> None:
        with self.assertRaises(module.CaptureGuardError):
            module.parse_bool_reason(None, "ValidateRuntimeFactory")
        with self.assertRaises(module.CaptureGuardError):
            module.parse_bool_reason((False, "NO"), "ValidateRuntimeFactory")
        with self.assertRaises(module.CaptureGuardError):
            module.parse_payload_reason(None, 2, "GetConfiguredStationRoute")
        with self.assertRaises(module.CaptureGuardError):
            module.parse_payload_reason((False, [], "", "NO"), 2, "route")
        self.assertEqual(module.parse_bool_reason((True, "OK"), "x"), "OK")
        self.assertEqual(module.parse_payload_reason(("payload", "OK"), 1, "x"), ("payload",))
        self.assertEqual(
            module.parse_payload_reason((True, [1], "TOPO", "OK"), 2, "x"),
            ([1], "TOPO"),
        )

    def test_exact_activation_passes_and_each_authority_is_fail_closed(self) -> None:
        module.validate_activation_snapshot(exact_activation())
        mutations = [
            ("route_count", 56),
            ("press_route_prefix", ["WRONG"]),
            ("topology_id", "OF_RUNTIME_TOPOLOGY_V001_BAD"),
            ("starter_contract_ids", ["CON_STARTER_1"]),
            ("unit_count_before_player_order", 1),
            ("top_bar_visible", False),
            ("flow_strip_visible", False),
            ("natural_actor_tick_enabled", False),
            ("automatic_contract_dispatch_disabled", False),
        ]
        for key, value in mutations:
            with self.subTest(key=key):
                snapshot = exact_activation()
                snapshot[key] = value
                with self.assertRaises(module.CaptureGuardError):
                    module.validate_activation_snapshot(snapshot)
        snapshot = exact_activation()
        snapshot["counts"]["pawn"] = 2
        with self.assertRaises(module.CaptureGuardError):
            module.validate_activation_snapshot(snapshot)
        snapshot = exact_activation()
        snapshot["classes"]["hud"] = "/Script/Engine.HUD"
        with self.assertRaises(module.CaptureGuardError):
            module.validate_activation_snapshot(snapshot)

    def test_slate_paint_visibility_accepts_click_through_roots_only(self) -> None:
        for state in (
            "VISIBLE",
            "ESlateVisibility.HIT_TEST_INVISIBLE",
            "ESlateVisibility.SELF_HIT_TEST_INVISIBLE",
        ):
            with self.subTest(state=state):
                self.assertTrue(
                    module.widget_is_paint_visible(
                        {"in_viewport": True, "visibility": state}
                    )
                )

        for state in ("HIDDEN", "COLLAPSED", "", None, "NOT_A_SLATE_STATE"):
            with self.subTest(state=state):
                self.assertFalse(
                    module.widget_is_paint_visible(
                        {"in_viewport": True, "visibility": state}
                    )
                )
        self.assertFalse(
            module.widget_is_paint_visible(
                {"in_viewport": False, "visibility": "VISIBLE"}
            )
        )

    def test_native_widget_sources_deliberately_use_click_through_visibility(self) -> None:
        for relative in (
            "Source/LineBossCarFactory/LBOneFactoryTopBarWidget.cpp",
            "Source/LineBossCarFactory/LBOneFactoryFlowStripWidget.cpp",
        ):
            source = (PROJECT / relative).read_text(encoding="utf-8")
            self.assertIn(
                "SetVisibility(ESlateVisibility::SelfHitTestInvisible);", source
            )

    def test_visual_layer_visibility_uses_supported_actor_and_component_seam(self) -> None:
        class Component:
            def __init__(self, visible=True, hidden=False) -> None:
                self.visible = visible
                self.hidden = hidden

            def is_visible(self):
                return self.visible

            def get_editor_property(self, name):
                if name == "hidden_in_game":
                    return self.hidden
                raise AttributeError(name)

        class Actor:
            def __init__(self, actor_hidden=False, component=None) -> None:
                self.actor_hidden = actor_hidden
                self.static_mesh_component = component or Component()

            def get_editor_property(self, name):
                if name == "hidden":
                    return self.actor_hidden
                raise AttributeError(name)

        self.assertTrue(module._actor_visible(Actor()))
        self.assertFalse(module._actor_visible(Actor(actor_hidden=True)))
        self.assertFalse(module._actor_visible(Actor(component=Component(False, False))))
        self.assertFalse(module._actor_visible(Actor(component=Component(True, True))))

        class ActorWithoutHiddenReflection:
            def __init__(self, component) -> None:
                self.static_mesh_component = component

            def get_editor_property(self, name):
                raise AttributeError(name)

        self.assertTrue(
            module._actor_visible(ActorWithoutHiddenReflection(Component(True, False)))
        )
        self.assertFalse(
            module._actor_visible(ActorWithoutHiddenReflection(Component(True, True)))
        )

    def test_failure_path_view_restore_is_proven_and_fail_closed(self) -> None:
        pawn = object()
        other_view = object()

        class Controller:
            def __init__(self, possession, view) -> None:
                self.possession = possession
                self.view = view
                self.set_calls = 0

            def get_controlled_pawn(self):
                return self.possession

            def get_view_target(self):
                return self.view

            def set_view_target_with_blend(self, value, blend_time):
                self.assert_zero_blend = blend_time
                self.set_calls += 1
                self.view = value

        already = Controller(pawn, pawn)
        self.assertTrue(module.ensure_possessed_pawn_view_target(already, pawn))
        self.assertEqual(already.set_calls, 0)

        restored = Controller(pawn, other_view)
        self.assertTrue(module.ensure_possessed_pawn_view_target(restored, pawn))
        self.assertIs(restored.view, pawn)
        self.assertEqual(restored.set_calls, 1)
        self.assertEqual(restored.assert_zero_blend, 0.0)

        wrong_possession = Controller(object(), other_view)
        self.assertFalse(
            module.ensure_possessed_pawn_view_target(wrong_possession, pawn)
        )
        self.assertEqual(wrong_possession.set_calls, 0)

        class RefusesViewTarget(Controller):
            def set_view_target_with_blend(self, value, blend_time):
                self.assert_zero_blend = blend_time
                self.set_calls += 1

        refuses = RefusesViewTarget(pawn, other_view)
        self.assertFalse(module.ensure_possessed_pawn_view_target(refuses, pawn))
        self.assertEqual(refuses.set_calls, 1)
        self.assertEqual(refuses.assert_zero_blend, 0.0)

    def test_camera_finalization_ignores_only_unobserved_pie_duplicate(self) -> None:
        editor = exact_camera()
        self.assertFalse(
            module.saved_camera_contract_changed(editor, copy.deepcopy(editor), None)
        )

        editor_drift = copy.deepcopy(editor)
        editor_drift["ortho_width_cm"] += 1.0
        self.assertTrue(
            module.saved_camera_contract_changed(editor_drift, editor, None)
        )

        pie_drift = copy.deepcopy(editor)
        pie_drift["location_cm"][0] += 1.0
        self.assertTrue(
            module.saved_camera_contract_changed(editor, editor, pie_drift)
        )

    def test_saved_camera_exactness_and_pie_path_semantics(self) -> None:
        camera = exact_camera()
        module.validate_camera_snapshot(camera)
        pie_camera = copy.deepcopy(camera)
        pie_camera["path"] = (
            "/Game/V006/UEDPIE_0_V006.UEDPIE_0_V006:PersistentLevel.CameraActor_0"
        )
        self.assertEqual(
            module.camera_contract_snapshot(camera),
            module.camera_contract_snapshot(pie_camera),
        )
        for key, value in (
            ("class", "/Script/Engine.SceneCapture2D"),
            ("label", "wrong"),
            ("projection", "PERSPECTIVE"),
            ("location_cm", [0.0, 0.0, 0.0]),
            ("rotation_pitch_yaw_roll", [-89.0, 0.0, 0.0]),
            ("ortho_width_cm", 6000.0),
            ("aspect_ratio", 1.0),
            ("constrain_aspect_ratio", False),
        ):
            with self.subTest(key=key):
                drift = exact_camera()
                drift[key] = value
                with self.assertRaises(module.CaptureGuardError):
                    module.validate_camera_snapshot(drift)
        drift = exact_camera()
        drift["tags"].append("LB.PressShop.OverheadDeck.Camera.SteamHero.v005")
        with self.assertRaises(module.CaptureGuardError):
            module.validate_camera_snapshot(drift)

    def test_natural_s04_review_window_and_live_completion_window(self) -> None:
        module.validate_natural_press_snapshot(exact_press())
        module.validate_natural_press_snapshot(
            exact_press(0.53), require_capture_window=False
        )
        with self.assertRaises(module.CaptureGuardError):
            module.validate_natural_press_snapshot(exact_press(0.53))
        for progress in (
            module.S04_ACTIVE_PROGRESS_MIN - 0.0001,
            module.S04_ACTIVE_PROGRESS_MAX,
            float("nan"),
        ):
            with self.subTest(progress=progress):
                with self.assertRaises(module.CaptureGuardError):
                    module.validate_natural_press_snapshot(
                        exact_press(progress), require_capture_window=False
                    )

    def test_natural_s04_visual_or_runtime_drift_fails(self) -> None:
        cases = {
            "station_id": "WRONG",
            "station_cursor": 3,
            "started": False,
            "completed": True,
            "dispatched": True,
            "awaiting_quality_result": True,
            "machine_id": "S03_FORM",
            "visible_frame": "OPEN",
            "visible_frame_count": 2,
            "beacon_state": "READY",
            "bound_visual_layer_count": 145,
            "status_beacon_count": 13,
            "task_light_count": 3,
        }
        for key, value in cases.items():
            with self.subTest(key=key):
                snapshot = exact_press()
                snapshot[key] = value
                with self.assertRaises(module.CaptureGuardError):
                    module.validate_natural_press_snapshot(snapshot)

    def test_world_identity_accepts_only_exact_editor_or_uedpie_package(self) -> None:
        class Outer:
            def __init__(self, name: str) -> None:
                self.name = name

            def get_name(self) -> str:
                return self.name

        class World:
            def __init__(self, name: str) -> None:
                self.outer = Outer(name)

            def get_outermost(self):
                return self.outer

        parent, leaf = module.TARGET_MAP.rsplit("/", 1)
        self.assertTrue(module.world_is_exact_target(World(module.TARGET_MAP)))
        self.assertTrue(
            module.world_is_exact_target(World(parent + "/UEDPIE_0_" + leaf))
        )
        for wrong in (
            parent + "/UEDPIE_0_WRONG",
            "/Temp/PIE_0_" + module.TARGET_MAP,
            module.TARGET_MAP.replace("v006", "v005"),
            module.TARGET_MAP + "_copy",
        ):
            self.assertFalse(module.world_is_exact_target(World(wrong)), wrong)

    def test_append_only_json_and_png_dimension_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt = root / "receipt.json"
            module.write_json_new(receipt, {"status": "FIRST"})
            with self.assertRaises(FileExistsError):
                module.write_json_new(receipt, {"status": "SECOND"})
            png = root / "shot.png"
            header = (
                b"\x89PNG\r\n\x1a\n"
                + b"\x00\x00\x00\x0dIHDR"
                + (1920).to_bytes(4, "big")
                + (1080).to_bytes(4, "big")
            )
            png.write_bytes(header + b"\x00" * module.MIN_SCREENSHOT_BYTES)
            self.assertEqual(module.png_dimensions(png), (1920, 1080))
            self.assertTrue(module.file_ready(png))

    def test_run_stamp_is_path_safe(self) -> None:
        self.assertEqual(module.safe_stamp("20260824T010203123456Z"), "20260824T010203123456Z")
        for value in ("", "../escape", "20260824T010203Z", "20260824t010203123456z"):
            with self.assertRaises(module.CaptureGuardError):
                module.safe_stamp(value)

    def test_source_uses_only_real_player_regular_pie_native_ui_capture(self) -> None:
        tree = ast.parse(SUBJECT.read_text(encoding="utf-8"))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        attributes = [
            node.func.attr
            for node in calls
            if isinstance(node.func, ast.Attribute)
        ]
        self.assertEqual(attributes.count("editor_request_begin_play"), 1)
        self.assertEqual(attributes.count("place_order"), 1)
        self.assertEqual(attributes.count("request_pie_restricted_ui_screenshot"), 1)
        self.assertGreaterEqual(attributes.count("set_view_target_with_blend"), 3)
        self.assertNotIn("set_view_target", attributes)
        forbidden_attributes = {
            "take_high_res_screenshot",
            "spawn_actor_from_class",
            "set_editor_property",
            "set_actor_location",
            "set_actor_rotation",
            "set_actor_scale3d",
            "set_actor_hidden_in_game",
            "set_presentation_enabled",
            "refresh_from_runtime",
            "tick_vehicle",
            "tick_automatic_flow",
            "dispatch_next_open_contract",
            "create_runtime_vehicle_order",
            "save_current_level",
            "save_loaded_asset",
            "save_directory",
            "import_asset_tasks",
            "build_light_maps",
            "cook_content",
        }
        self.assertFalse(forbidden_attributes.intersection(attributes))

    def test_capture_request_phase_guard_precedes_loading_flush_and_native_request(self) -> None:
        tree = ast.parse(SUBJECT.read_text(encoding="utf-8"))
        runner = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "LiveHudCaptureRunner"
        )
        start = next(
            node
            for node in runner.body
            if isinstance(node, ast.FunctionDef) and node.name == "start_ui_capture"
        )
        phase_assignments = [
            node
            for node in ast.walk(start)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
                and target.attr == "phase"
                for target in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ]
        requesting = next(
            node for node in phase_assignments if node.value.value == "REQUESTING_CAPTURE"
        )
        waiting = next(
            node for node in phase_assignments if node.value.value == "WAIT_CAPTURE"
        )
        calls = [node for node in ast.walk(start) if isinstance(node, ast.Call)]
        loading_flush = next(
            node
            for node in calls
            if isinstance(node.func, ast.Attribute)
            and node.func.attr == "finish_loading_before_screenshot"
        )
        post_flush_size = next(
            node
            for node in calls
            if isinstance(node.func, ast.Attribute)
            and node.func.attr == "get_pie_game_widget_draw_size"
        )
        native_request = next(
            node
            for node in calls
            if isinstance(node.func, ast.Attribute)
            and node.func.attr == "request_pie_restricted_ui_screenshot"
        )
        self.assertLess(requesting.lineno, loading_flush.lineno)
        self.assertLess(loading_flush.lineno, post_flush_size.lineno)
        self.assertLess(post_flush_size.lineno, native_request.lineno)
        self.assertLess(native_request.lineno, waiting.lineno)

    def test_requesting_capture_tick_is_an_explicit_reentry_noop(self) -> None:
        tree = ast.parse(SUBJECT.read_text(encoding="utf-8"))
        runner = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "LiveHudCaptureRunner"
        )
        tick = next(
            node
            for node in runner.body
            if isinstance(node, ast.FunctionDef) and node.name == "tick"
        )
        guarded_returns = []
        for node in ast.walk(tick):
            if not isinstance(node, ast.If) or not node.body:
                continue
            comparison = node.test
            if not (
                isinstance(comparison, ast.Compare)
                and isinstance(comparison.left, ast.Attribute)
                and isinstance(comparison.left.value, ast.Name)
                and comparison.left.value.id == "self"
                and comparison.left.attr == "phase"
                and len(comparison.ops) == 1
                and isinstance(comparison.ops[0], ast.Eq)
                and len(comparison.comparators) == 1
                and isinstance(comparison.comparators[0], ast.Constant)
                and comparison.comparators[0].value == "REQUESTING_CAPTURE"
            ):
                continue
            guarded_returns.extend(
                statement for statement in node.body if isinstance(statement, ast.Return)
            )
        self.assertEqual(len(guarded_returns), 1)

    def test_loading_flush_reentry_submits_exactly_one_native_request(self) -> None:
        """Model Slate pumping the registered tick during the loading flush."""

        class FakePackage:
            @staticmethod
            def get_name() -> str:
                return module.TARGET_MAP

        class FakeWorld:
            @staticmethod
            def get_outermost() -> FakePackage:
                return FakePackage()

        with tempfile.TemporaryDirectory() as folder:
            runner = module.LiveHudCaptureRunner.__new__(module.LiveHudCaptureRunner)
            runner.screenshot = Path(folder) / "live_hud.png"
            runner.phase = "WAIT_CAMERA_VIEW"
            runner.phase_started = time.monotonic()
            runner.started = time.monotonic()
            runner.finished = False
            runner.game_world_seen = time.monotonic()
            runner.editor_worlds = SimpleNamespace(get_game_world=lambda: FakeWorld())
            runner.payload = {"runtime": {}}
            runner.capture_started = None
            trace = []

            class FakeAutomationLibrary:
                @staticmethod
                def finish_loading_before_screenshot() -> None:
                    trace.append(("flush", runner.phase))
                    # The production callback is registered with Slate.  This
                    # nested tick used to re-enter start_ui_capture().
                    runner.tick(0.0)

            class FakeCaptureBridge:
                @staticmethod
                def get_pie_game_widget_draw_size(world: object) -> object:
                    trace.append(("size", runner.phase))
                    return SimpleNamespace(
                        x=module.SCREENSHOT_SIZE[0], y=module.SCREENSHOT_SIZE[1]
                    )

                @staticmethod
                def request_pie_restricted_ui_screenshot(
                    world: object, filename: str, width: int, height: int
                ) -> bool:
                    trace.append(("request", runner.phase, filename, width, height))
                    return True

            fake_unreal = SimpleNamespace(
                AutomationLibrary=FakeAutomationLibrary,
                LBOneFactoryCaptureBridge=FakeCaptureBridge,
            )
            with mock.patch.object(module, "unreal", fake_unreal):
                runner.start_ui_capture(FakeWorld(), time.monotonic())

            self.assertEqual(trace[0], ("flush", "REQUESTING_CAPTURE"))
            self.assertEqual(trace[1], ("size", "REQUESTING_CAPTURE"))
            requests = [entry for entry in trace if entry[0] == "request"]
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0][1], "REQUESTING_CAPTURE")
            self.assertEqual(requests[0][3:], module.SCREENSHOT_SIZE)
            self.assertEqual(runner.phase, "WAIT_CAPTURE")
            self.assertEqual(
                runner.payload["native_ui_screenshot_request_call_count"], 1
            )
            self.assertTrue(runner.payload["runtime"]["native_capture_request_accepted"])

    def test_post_flush_size_drift_fails_before_native_request(self) -> None:
        class FakeAutomationLibrary:
            @staticmethod
            def finish_loading_before_screenshot() -> None:
                return None

        class FakeCaptureBridge:
            calls = 0

            @staticmethod
            def get_pie_game_widget_draw_size(world: object) -> object:
                return SimpleNamespace(x=1919, y=1080)

            @classmethod
            def request_pie_restricted_ui_screenshot(
                cls, world: object, filename: str, width: int, height: int
            ) -> bool:
                cls.calls += 1
                return True

        fake_unreal = SimpleNamespace(
            AutomationLibrary=FakeAutomationLibrary,
            LBOneFactoryCaptureBridge=FakeCaptureBridge,
        )
        with tempfile.TemporaryDirectory() as folder:
            runner = module.LiveHudCaptureRunner.__new__(module.LiveHudCaptureRunner)
            runner.screenshot = Path(folder) / "live_hud.png"
            runner.phase = "WAIT_CAMERA_VIEW"
            runner.phase_started = time.monotonic()
            runner.payload = {"runtime": {}}
            with mock.patch.object(module, "unreal", fake_unreal):
                with self.assertRaisesRegex(
                    module.CaptureGuardError, "changed size during screenshot loading flush"
                ):
                    runner.start_ui_capture(object(), time.monotonic())
        self.assertEqual(FakeCaptureBridge.calls, 0)

    def test_source_contains_no_scene_capture_or_coordinator_forcing(self) -> None:
        tree = ast.parse(SUBJECT.read_text(encoding="utf-8"))
        identifiers = {
            node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
        }
        identifiers.update(
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        )
        for forbidden in (
            "SceneCapture2D",
            "EditorPlaySimulate",
            "take_high_res_screenshot",
            "dispatch_next_open_contract",
            "create_runtime_vehicle_order",
            "tick_vehicle",
            "tick_automatic_flow",
        ):
            self.assertNotIn(forbidden, identifiers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
