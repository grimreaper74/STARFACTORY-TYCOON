"""Build the isolated 2126 true-overhead playable Press Shop successor.

This is deliberately a *consumer* of a completed runtime pack.  It does not
import textures, create materials, repair source art, or guess animation
bindings.  The unified runtime manifest and the animation/effects contract are
fully validated before Unreal is allowed to create the target map package.

Run this only from an unrelated, clean editor world.  The hash-locked
OneFactory source is duplicated while unopened, then only the duplicate is
loaded and edited.  Existing GameMode and runtime-authority actors are retained;
only explicitly declared presentation-only actors are hidden.  The only assets
saved by this script are the target map and its JSON receipt.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CODEX_OUTPUTS = Path(r"C:\Users\greg_\Documents\Codex\2026-08-22\ca\outputs")

SOURCE_MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
TARGET_MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPlayable_v001/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001"

SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Factory" / "OneFactory" / "v001" / "Maps" / "LB_MoorcrossWorks_OneFactory_v001.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_OverheadPlayable_v001" / "Maps" / "LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001.umap"
SOURCE_FILE_SHA256 = "f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c"

RUNTIME_MANIFEST = CODEX_OUTPUTS / "PressShop_OverheadRuntime_v001" / "PRESS_SHOP_OVERHEAD_RUNTIME_MANIFEST_v001.json"
RUNTIME_MANIFEST_SCHEMA = "cairnwell.press_shop.overhead_runtime.v001"
RUNTIME_MANIFEST_STATUS = "PASS_RUNTIME_READY__TRUE_OVERHEAD_LAYERED_PLAYABLE"

ANIMATION_CONTRACT = CODEX_OUTPUTS / "PressShop_AnimationEffectsContract_v001" / "PRESS_SHOP_ANIMATION_EFFECTS_CONTRACT_v001.json"
ANIMATION_CONTRACT_SHA256 = "a57d3b16fb69be6379574342f435ce6f43a5cb597e75a6de435eb180e701dc2c"
ANIMATION_CONTRACT_ID = "CA_MW_PRESSSHOP_2126_ANIMFX_V001"

DEFAULT_ENGINE_INI = PROJECT / "Config" / "DefaultEngine.ini"
DEFAULT_ENGINE_INI_SHA256 = "b5bbc12da59d06f2ed5958ce06b70963ad991d8a8747a98c6102a771d30a0827"

RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "OverheadPlayable_v001" / "build_receipt_v001.json"

PROTECTED_MAPS = {
    SOURCE_FILE: SOURCE_FILE_SHA256,
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap":
        "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap":
        "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_IndividualSprites_v007" / "Maps" / "LB_PressShop_Factorio2p5D_IndividualSprites_v007.umap":
        "0e1bc9ddbf753a790955375eba8d0b274eb7d48cb336a84a82df431f85aa9624",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_FullHall_v001" / "Maps" / "LB_PressShop_2126_FullHall_v001.umap":
        "37fc7af541675f4f38afd816d7d4552628d1deaf22b0abe01d6830907a62349f",
}

PROTECTED_NATIVE_BEACON_SOURCES = {
    PROJECT / "Source" / "LineBossCarFactory" / "LBStatusBeaconComponent.h":
        "5ab9fb4245de1a9981201d555c310ceb4fdf793419171856f3503aa246c744b7",
    PROJECT / "Source" / "LineBossCarFactory" / "LBStatusBeaconComponent.cpp":
        "c80e7a096b3f91fa927db16469267cacdeea397664498c16f0bf211debc10a2d",
}

REQUIRED_ASSEMBLY_IDS = {
    "IN01_ARTICULATED_CARRIER",
    "IN02_COIL_HANDLER_AGV",
    "IN03_COIL_STORAGE",
    "IN04_DEPACK_AND_INSPECTION",
    "IN05_DECOILER_STRAIGHTENER_FEED",
    "S01_DESTACK_AND_LOAD",
    "S02_TO_S06_PRESS_STATIONS",
    "S07_UNLOAD_INSPECT_STACK",
    "SUPPORT_FLEET_AND_OVERHEAD_HANDLING",
}

REQUIRED_EFFECTS_BY_ASSEMBLY = {
    "IN01_ARTICULATED_CARRIER": {
        "turn_signal_emissive", "brake_emissive", "soft_route_guidance", "electric_drive_audio",
    },
    "IN02_COIL_HANDLER_AGV": {
        "directional_route_strip", "green_amber_red_beacon", "deck_lock_flash", "servo_audio", "arrival_chime",
    },
    "IN03_COIL_STORAGE": {
        "occupied_socket_indicator", "reserved_socket_pulse", "inventory_count_label",
    },
    "IN04_DEPACK_AND_INSPECTION": {
        "cyan_scan_line", "pass_fail_beacon", "film_specular_scroll", "servo_audio",
    },
    "IN05_DECOILER_STRAIGHTENER_FEED": {
        "feed_ready_beacon", "strip_edge_highlight", "motor_audio", "low_tension_warning",
    },
    "S01_DESTACK_AND_LOAD": {
        "vacuum_pick_indicator", "ready_beacon", "pneumatic_audio",
    },
    "S02_TO_S06_PRESS_STATIONS": {
        "brief_contact_flash", "subtle_hydraulic_mist_only_where_justified", "running_beacon",
        "fault_beacon", "press_impact_audio", "hydraulic_loop", "transfer_servo_audio",
    },
    "S07_UNLOAD_INSPECT_STACK": {
        "inspection_light_sweep", "pass_green_or_reject_red", "robot_servo_audio", "stack_complete_chime",
    },
    "SUPPORT_FLEET_AND_OVERHEAD_HANDLING": {
        "route_projection", "service_beacons", "charging_pulse", "cleaning_pass_decal", "motor_audio",
    },
}

CYAN_STATE_EFFECTS = {
    "soft_route_guidance",
    "directional_route_strip",
    "cyan_scan_line",
    "inspection_light_sweep",
    "route_projection",
}

BEACON_STATE_MAPPING = {
    "green": {"Ready", "Running"},
    "amber": {"Idle", "Waiting", "Moving"},
    "red": {"Stopped", "Fault", "Emergency"},
}
NATIVE_BEACON_COMPONENT_CLASS = "LBStatusBeaconComponent"
NATIVE_BEACON_VISUAL_CONTRACT = "ULBStatusBeaconComponent_MID_PLUS_RESTRAINED_POINT_LIGHT"

ALLOWED_LAYER_KINDS = {
    "base",
    "moving_overlay",
    "cargo",
    "effect_mask",
    "status_overlay",
    "contact_shadow",
    "frame_state",
}
MOVING_LAYER_KINDS = {"moving_overlay", "cargo", "effect_mask", "status_overlay", "frame_state"}
PRESS_FRAME_STATIONS = {"S02", "S03", "S04", "S05", "S06"}
PRESS_FRAME_STATES = ("open", "descending", "contact", "rising")
TRUE_OVERHEAD_ANGLE_TOLERANCE_DEG = 0.001
NUMERIC_TOLERANCE = 0.000001
LAYER_TAG = "LB.PressShop.Overhead.VisualLayer"


def fail(message: str) -> None:
    raise RuntimeError("PRESSSHOP_2126_OVERHEAD_PLAYABLE_V001_BUILD_FAIL: " + message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def require_mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        fail("{} must be a JSON object".format(context))
    return value


def require_list(value: Any, context: str, *, nonempty: bool = True) -> List[Any]:
    if not isinstance(value, list) or (nonempty and not value):
        fail("{} must be {}JSON array".format(context, "a non-empty " if nonempty else "a "))
    return value


def require_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail("{} must be a non-empty string".format(context))
    return value.strip()


def require_bool(value: Any, expected: bool, context: str) -> None:
    if value is not expected:
        fail("{} must be {}".format(context, expected))


def numeric_tuple(value: Any, size: int, context: str) -> Tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != size:
        fail("{} must contain exactly {} numbers".format(context, size))
    try:
        result = tuple(float(item) for item in value)
    except (TypeError, ValueError):
        fail("{} contains a non-numeric value".format(context))
    if not all(math.isfinite(item) for item in result):
        fail("{} contains a non-finite value".format(context))
    return result


def load_json(path: Path, context: str) -> Tuple[Dict[str, Any], str]:
    if not path.is_file():
        fail("{} is missing: {}".format(context, path))
    file_hash = digest(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        fail("{} is unreadable: {}".format(context, error))
    return dict(require_mapping(data, context)), file_hash


def validate_animation_contract_data(contract: Mapping[str, Any]) -> Dict[str, Any]:
    if contract.get("contract_id") != ANIMATION_CONTRACT_ID:
        fail("animation contract ID changed")
    if contract.get("status") != "AUTHORITATIVE_BUILD_REQUIREMENT":
        fail("animation contract is not authoritative")

    view = require_mapping(contract.get("view"), "animation contract view")
    if view.get("projection") != "fixed_orthographic_overhead":
        fail("animation contract is not fixed orthographic overhead")
    if view.get("visual_strategy") != "dimension_registered_layered_sprites_over_hidden_native_gameplay_proxies":
        fail("animation contract visual strategy changed")
    if view.get("rule") != "never_flatten_a_moving_machine_into_one_unanimated_sprite":
        fail("animation contract no-flattening rule changed")

    global_rules = set(require_list(contract.get("global_rules"), "animation contract global rules"))
    required_rules = {
        "all motion is driven by authoritative gameplay state",
        "true-overhead Z-axis travel uses gameplay-timed open descending contact rising frame states because world Z has zero screen-plane displacement",
        "frame-state animation must preserve the exact footprint anchor and may only change the open die aperture shadow workpiece and contact layers",
        "cargo, blanks, panels and stillages remain separate actors",
        "save and load restores the gameplay phase first and reconstructs the matching visual pose",
    }
    if not required_rules.issubset(global_rules):
        fail("animation contract lost gameplay-authoritative global rules")

    assemblies = require_list(contract.get("assemblies"), "animation contract assemblies")
    by_id: Dict[str, Mapping[str, Any]] = {}
    for row in assemblies:
        row = require_mapping(row, "animation assembly")
        assembly_id = require_string(row.get("id"), "animation assembly id")
        if assembly_id in by_id:
            fail("duplicate animation assembly: {}".format(assembly_id))
        for key in ("authority", "layers", "motion", "effects"):
            if key == "authority":
                require_string(row.get(key), "{} authority".format(assembly_id))
            else:
                require_list(row.get(key), "{} {}".format(assembly_id, key))
        if assembly_id in REQUIRED_EFFECTS_BY_ASSEMBLY and set(row["effects"]) != REQUIRED_EFFECTS_BY_ASSEMBLY[assembly_id]:
            fail("{} animation effects changed: {}".format(assembly_id, sorted(row["effects"])))
        by_id[assembly_id] = row
    if set(by_id) != REQUIRED_ASSEMBLY_IDS:
        fail("animation contract assembly coverage changed: {}".format(sorted(by_id)))
    press_motion = set(by_id["S02_TO_S06_PRESS_STATIONS"]["motion"])
    if "phase_accurate_open_descending_contact_rising_sprite_sequence_for_Z_stroke" not in press_motion:
        fail("animation contract lost the true-overhead press frame-state sequence")
    if "upper_die_frame_state_follows_authoritative_slide_progress" not in press_motion:
        fail("animation contract lost authoritative slide-progress frame binding")

    native = require_mapping(contract.get("unreal_native_requirements"), "native animation requirements")
    forbidden = set(require_list(native.get("forbidden_shortcuts"), "forbidden animation shortcuts"))
    required_forbidden = {
        "one flattened press-train image",
        "baked cargo on trailers or AGVs",
        "collision derived from transparent sprite bounds",
        "visual state saved independently from gameplay authority",
    }
    if not required_forbidden.issubset(forbidden):
        fail("animation contract lost a required forbidden shortcut")
    preferred = set(require_list(native.get("preferred_components"), "preferred native animation components"))
    if "gameplay-timed texture-frame or layer-opacity sequence for true-overhead Z-axis press states" not in preferred:
        fail("animation contract lost the native true-overhead frame-state requirement")
    require_list(contract.get("evidence_gate"), "animation evidence gate")
    return {"assemblies": by_id, "view": view}


def validate_runtime_manifest_data(
    manifest: Mapping[str, Any],
    animation_contract_hash: str,
) -> Dict[str, Any]:
    if manifest.get("schema") != RUNTIME_MANIFEST_SCHEMA:
        fail("unified runtime manifest schema changed")
    if manifest.get("status") != RUNTIME_MANIFEST_STATUS:
        fail("unified runtime manifest is not runtime-ready")
    require_bool(manifest.get("runtime_ready"), True, "runtime_ready")

    map_contract = require_mapping(manifest.get("map_contract"), "runtime map contract")
    if map_contract.get("source_map") != SOURCE_MAP or map_contract.get("target_map") != TARGET_MAP:
        fail("runtime map contract does not name this isolated source/target lane")
    require_bool(map_contract.get("duplicate_source_while_unloaded"), True, "duplicate_source_while_unloaded")

    animation_link = require_mapping(manifest.get("animation_contract"), "runtime animation link")
    if animation_link.get("contract_id") != ANIMATION_CONTRACT_ID:
        fail("runtime manifest links the wrong animation contract")
    if str(animation_link.get("sha256", "")).lower() != animation_contract_hash:
        fail("runtime manifest animation-contract hash does not match the validated file")
    require_bool(animation_link.get("all_assemblies_bound"), True, "animation all_assemblies_bound")

    view = require_mapping(manifest.get("view"), "runtime view")
    if view.get("projection") != "orthographic" or view.get("view_mode") != "TRUE_OVERHEAD":
        fail("runtime view is not true-overhead orthographic")
    rotation = numeric_tuple(view.get("rotation_deg"), 3, "runtime camera rotation")
    expected_rotation = (-90.0, 0.0, 0.0)
    if any(abs(actual - expected) > TRUE_OVERHEAD_ANGLE_TOLERANCE_DEG for actual, expected in zip(rotation, expected_rotation)):
        fail("runtime camera rotation is not exactly true-overhead: {}".format(rotation))
    camera_location = numeric_tuple(view.get("location_cm"), 3, "runtime camera location")
    if camera_location[2] <= 0.0:
        fail("runtime camera must be above the factory floor")
    try:
        ortho_width = float(view.get("ortho_width_cm"))
        aspect_ratio = float(view.get("aspect_ratio"))
    except (TypeError, ValueError):
        fail("runtime camera width/aspect must be numeric")
    if not math.isfinite(ortho_width) or ortho_width <= 0.0:
        fail("runtime camera orthographic width is invalid")
    if not math.isfinite(aspect_ratio) or abs(aspect_ratio - (16.0 / 9.0)) > NUMERIC_TOLERANCE:
        fail("runtime camera aspect ratio must be 16:9")
    camera_label = require_string(view.get("camera_actor_label"), "runtime camera actor label")

    preservation = require_mapping(manifest.get("runtime_preservation"), "runtime preservation contract")
    for key in ("preserve_game_mode", "preserve_existing_runtime_actors"):
        require_bool(preservation.get(key), True, key)
    require_bool(preservation.get("spawn_duplicate_controllers"), False, "spawn_duplicate_controllers")
    required_authorities_raw = require_list(
        preservation.get("required_authority_actors"),
        "required runtime authority actors",
    )
    required_authorities: Dict[str, Dict[str, str]] = {}
    for row in required_authorities_raw:
        row = require_mapping(row, "runtime authority actor")
        label = require_string(row.get("actor_label"), "runtime authority actor label")
        class_name = require_string(row.get("class_name"), "{} class".format(label))
        assembly_id = require_string(row.get("assembly_id"), "{} assembly".format(label))
        if assembly_id not in REQUIRED_ASSEMBLY_IDS:
            fail("runtime authority {} names unknown assembly {}".format(label, assembly_id))
        if label in required_authorities:
            fail("duplicate runtime authority actor label: {}".format(label))
        required_authorities[label] = {
            "class_name": class_name,
            "assembly_id": assembly_id,
        }
    if {row["assembly_id"] for row in required_authorities.values()} != REQUIRED_ASSEMBLY_IDS:
        fail("runtime authority actors do not cover every animation assembly")
    controller_classes = {
        require_string(value, "controller class name")
        for value in require_list(preservation.get("controller_class_names"), "controller class names")
    }

    hide = require_mapping(manifest.get("presentation_hide"), "presentation hide contract")
    if hide.get("mode") != "EXPLICIT_LABELS_ONLY":
        fail("presentation hiding must use explicit labels only")
    require_bool(hide.get("presentation_only_confirmed"), True, "presentation_only_confirmed")
    require_bool(hide.get("disable_collision"), True, "presentation disable_collision")
    hide_labels = [require_string(value, "presentation actor label") for value in require_list(hide.get("actor_labels"), "presentation actor labels")]
    if len(hide_labels) != len(set(hide_labels)):
        fail("presentation hide labels contain duplicates")
    if set(hide_labels).intersection(required_authorities):
        fail("runtime authority actor was included in presentation hiding")
    if camera_label in hide_labels:
        fail("runtime camera label was included in presentation hiding")

    assembly_rows = require_list(manifest.get("assemblies"), "runtime visual assemblies")
    assemblies: Dict[str, Mapping[str, Any]] = {}
    layers: List[Dict[str, Any]] = []
    beacon_bindings: List[Dict[str, Any]] = []
    effect_bindings: List[Dict[str, Any]] = []
    layer_ids: set[str] = set()
    actor_labels: set[str] = set()
    beacon_keys: set[Tuple[str, str]] = set()
    effect_ids: set[str] = set()
    for assembly in assembly_rows:
        assembly = require_mapping(assembly, "runtime visual assembly")
        assembly_id = require_string(assembly.get("id"), "runtime visual assembly id")
        if assembly_id not in REQUIRED_ASSEMBLY_IDS or assembly_id in assemblies:
            fail("runtime visual assembly is unexpected or duplicated: {}".format(assembly_id))
        require_bool(assembly.get("runtime_ready"), True, "{} runtime_ready".format(assembly_id))
        layer_rows = require_list(assembly.get("layers"), "{} layers".format(assembly_id))
        assembly_layer_ids: set[str] = set()
        for raw_layer in layer_rows:
            raw_layer = require_mapping(raw_layer, "{} layer".format(assembly_id))
            layer_id = require_string(raw_layer.get("id"), "{} layer id".format(assembly_id))
            actor_label = require_string(raw_layer.get("actor_label"), "{} actor label".format(layer_id))
            kind = require_string(raw_layer.get("kind"), "{} kind".format(layer_id))
            if kind not in ALLOWED_LAYER_KINDS:
                fail("{} has unsupported layer kind {}".format(layer_id, kind))
            if layer_id in layer_ids or actor_label in actor_labels:
                fail("duplicate layer id or actor label: {} / {}".format(layer_id, actor_label))
            if actor_label in hide_labels or actor_label in required_authorities or actor_label == camera_label:
                fail("{} collides with a retained/hide/camera actor label".format(actor_label))
            mesh_asset = require_string(raw_layer.get("mesh_asset"), "{} mesh asset".format(layer_id))
            material_asset = require_string(raw_layer.get("material_asset"), "{} material asset".format(layer_id))
            transform = require_mapping(raw_layer.get("transform"), "{} transform".format(layer_id))
            location = numeric_tuple(transform.get("location_cm"), 3, "{} location".format(layer_id))
            rotation_layer = numeric_tuple(transform.get("rotation_deg"), 3, "{} rotation".format(layer_id))
            scale = numeric_tuple(transform.get("scale"), 3, "{} scale".format(layer_id))
            if min(scale) <= 0.0:
                fail("{} scale must be positive".format(layer_id))
            if abs(rotation_layer[0]) > NUMERIC_TOLERANCE or abs(rotation_layer[1]) > NUMERIC_TOLERANCE:
                fail("{} sprite plane must remain horizontal in true-overhead view".format(layer_id))
            require_bool(raw_layer.get("collision_enabled"), False, "{} collision_enabled".format(layer_id))
            require_bool(raw_layer.get("asset_package_ready"), True, "{} asset_package_ready".format(layer_id))
            tags = [require_string(value, "{} tag".format(layer_id)) for value in require_list(raw_layer.get("tags"), "{} tags".format(layer_id))]
            if LAYER_TAG not in tags:
                fail("{} is missing the canonical overhead visual tag".format(layer_id))
            binding = raw_layer.get("runtime_binding")
            if kind in MOVING_LAYER_KINDS:
                binding = require_mapping(binding, "{} runtime binding".format(layer_id))
                require_bool(binding.get("ready"), True, "{} binding ready".format(layer_id))
                authority_label = require_string(binding.get("authority_actor_label"), "{} binding authority".format(layer_id))
                if authority_label not in required_authorities:
                    fail("{} binds to an undeclared runtime authority".format(layer_id))
                require_string(binding.get("motion_channel"), "{} motion channel".format(layer_id))
                require_string(binding.get("binding_tag"), "{} binding tag".format(layer_id))
            elif binding is not None:
                binding = require_mapping(binding, "{} optional runtime binding".format(layer_id))
                if binding.get("ready") is not True:
                    fail("{} optional runtime binding is present but not ready".format(layer_id))
            source_sha = str(raw_layer.get("source_sha256", "")).lower()
            if len(source_sha) != 64 or any(character not in "0123456789abcdef" for character in source_sha):
                fail("{} source_sha256 is invalid".format(layer_id))
            initial_visibility = raw_layer.get("initially_visible", True)
            if not isinstance(initial_visibility, bool):
                fail("{} initially_visible must be boolean".format(layer_id))
            frame_state = None
            anchor_px = None
            if kind == "frame_state":
                frame_state = require_string(raw_layer.get("frame_state"), "{} frame_state".format(layer_id))
                if frame_state not in PRESS_FRAME_STATES:
                    fail("{} has unknown press frame state {}".format(layer_id, frame_state))
                anchor_px = numeric_tuple(raw_layer.get("anchor_px"), 2, "{} exact anchor".format(layer_id))
                if str(binding.get("motion_channel", "")).lower().find("screen_translation") >= 0:
                    fail("{} incorrectly uses screen translation for a true-overhead Z stroke".format(layer_id))
            layers.append({
                "assembly_id": assembly_id,
                "id": layer_id,
                "actor_label": actor_label,
                "kind": kind,
                "mesh_asset": mesh_asset,
                "material_asset": material_asset,
                "location": location,
                "rotation": rotation_layer,
                "scale": scale,
                "tags": tags,
                "runtime_binding": dict(binding) if isinstance(binding, dict) else None,
                "source_sha256": source_sha,
                "casts_shadow": raw_layer.get("casts_shadow") is True,
                "initially_visible": initial_visibility,
                "frame_state": frame_state,
                "anchor_px": anchor_px,
            })
            layer_ids.add(layer_id)
            actor_labels.add(actor_label)
            assembly_layer_ids.add(layer_id)

        machine_ids = [
            require_string(value, "{} machine id".format(assembly_id))
            for value in require_list(assembly.get("machines"), "{} placed machines".format(assembly_id))
        ]
        if len(machine_ids) != len(set(machine_ids)):
            fail("{} placed machine IDs contain duplicates".format(assembly_id))
        if assembly_id == "S02_TO_S06_PRESS_STATIONS" and set(machine_ids) != PRESS_FRAME_STATIONS:
            fail("S02-S06 assembly must declare exactly one placed machine per press station")

        raw_beacons = require_list(assembly.get("status_beacons"), "{} native status beacons".format(assembly_id))
        beacon_machine_ids: set[str] = set()
        for raw_beacon in raw_beacons:
            raw_beacon = require_mapping(raw_beacon, "{} status beacon".format(assembly_id))
            machine_id = require_string(raw_beacon.get("machine_id"), "{} beacon machine id".format(assembly_id))
            if machine_id not in machine_ids or machine_id in beacon_machine_ids:
                fail("{} beacon machine is missing, unknown, or duplicated: {}".format(assembly_id, machine_id))
            authority_label = require_string(raw_beacon.get("authority_actor_label"), "{} beacon authority".format(machine_id))
            if authority_label not in required_authorities:
                fail("{} beacon binds to an undeclared runtime authority".format(machine_id))
            component_class = require_string(raw_beacon.get("component_class"), "{} beacon component class".format(machine_id))
            if component_class != NATIVE_BEACON_COMPONENT_CLASS:
                fail("{} beacon is not a native ULBStatusBeaconComponent".format(machine_id))
            component_name = require_string(raw_beacon.get("component_name"), "{} beacon component name".format(machine_id))
            beacon_key = (authority_label, component_name)
            if beacon_key in beacon_keys:
                fail("duplicate native status-beacon component binding: {}".format(beacon_key))
            anchor = numeric_tuple(raw_beacon.get("anchor_relative_cm"), 3, "{} beacon anchor".format(machine_id))
            state_source = require_string(raw_beacon.get("state_source"), "{} beacon state source".format(machine_id))
            if raw_beacon.get("visual_contract") != NATIVE_BEACON_VISUAL_CONTRACT:
                fail("{} beacon does not require emissive MID plus restrained point lights".format(machine_id))
            for key, expected in (
                ("uses_emissive_mid", True),
                ("uses_point_light_glow", True),
                ("point_light_glow_restrained", True),
                ("gameplay_state_driven", True),
                ("baked_colour_only", False),
                ("decorative_loop", False),
            ):
                require_bool(raw_beacon.get(key), expected, "{} beacon {}".format(machine_id, key))
            mapping = require_mapping(raw_beacon.get("state_mapping"), "{} beacon state mapping".format(machine_id))
            if set(mapping) != set(BEACON_STATE_MAPPING):
                fail("{} beacon state mapping must contain green/amber/red".format(machine_id))
            for colour, expected_states in BEACON_STATE_MAPPING.items():
                states = {
                    require_string(value, "{} {} beacon state".format(machine_id, colour))
                    for value in require_list(mapping.get(colour), "{} {} beacon states".format(machine_id, colour))
                }
                if states != expected_states:
                    fail("{} {} beacon authority mapping changed".format(machine_id, colour))
            beacon_bindings.append({
                "assembly_id": assembly_id,
                "machine_id": machine_id,
                "authority_actor_label": authority_label,
                "component_class": component_class,
                "component_name": component_name,
                "anchor_relative_cm": anchor,
                "state_source": state_source,
                "visual_contract": NATIVE_BEACON_VISUAL_CONTRACT,
            })
            beacon_machine_ids.add(machine_id)
            beacon_keys.add(beacon_key)
        if beacon_machine_ids != set(machine_ids):
            fail("{} does not provide exactly one native state beacon per placed machine".format(assembly_id))

        raw_effects = require_list(assembly.get("effect_bindings"), "{} effect bindings".format(assembly_id))
        contract_effects: set[str] = set()
        for raw_effect in raw_effects:
            raw_effect = require_mapping(raw_effect, "{} effect binding".format(assembly_id))
            effect_id = require_string(raw_effect.get("id"), "{} effect id".format(assembly_id))
            if effect_id in effect_ids:
                fail("duplicate effect binding id: {}".format(effect_id))
            contract_effect = require_string(raw_effect.get("contract_effect"), "{} contract effect".format(effect_id))
            if contract_effect in contract_effects or contract_effect not in REQUIRED_EFFECTS_BY_ASSEMBLY[assembly_id]:
                fail("{} effect is unknown or duplicated: {}".format(assembly_id, contract_effect))
            machine_id = require_string(raw_effect.get("machine_id"), "{} effect machine".format(effect_id))
            if machine_id not in machine_ids:
                fail("{} effect names an unknown placed machine".format(effect_id))
            authority_label = require_string(raw_effect.get("authority_actor_label"), "{} effect authority".format(effect_id))
            if authority_label not in required_authorities:
                fail("{} effect binds to an undeclared runtime authority".format(effect_id))
            state_source = require_string(raw_effect.get("state_source"), "{} effect state source".format(effect_id))
            implementation = require_string(raw_effect.get("implementation"), "{} implementation".format(effect_id))
            anchor = numeric_tuple(raw_effect.get("anchor_relative_cm"), 3, "{} effect anchor".format(effect_id))
            anchor_tag = require_string(raw_effect.get("effect_anchor_tag"), "{} effect anchor tag".format(effect_id))
            for key, expected in (
                ("gameplay_state_driven", True),
                ("decorative_loop", False),
                ("baked_only", False),
            ):
                require_bool(raw_effect.get(key), expected, "{} {}".format(effect_id, key))
            colour_role = raw_effect.get("colour_role")
            if contract_effect in CYAN_STATE_EFFECTS:
                if colour_role != "cyan" or implementation == "baked_texture":
                    fail("{} must be a state-driven cyan runtime effect, never baked-only".format(effect_id))
            layer_id = raw_effect.get("layer_id")
            if layer_id is not None:
                layer_id = require_string(layer_id, "{} layer id".format(effect_id))
                if layer_id not in assembly_layer_ids:
                    fail("{} effect anchor references an unknown assembly layer".format(effect_id))
                layer = next(item for item in layers if item["id"] == layer_id)
                if anchor_tag not in layer["tags"]:
                    fail("{} effect anchor tag is absent from its visual layer".format(effect_id))
            if contract_effect in CYAN_STATE_EFFECTS and layer_id is None:
                fail("{} requires an explicit dynamic cyan visual layer anchor".format(effect_id))
            effect_bindings.append({
                "assembly_id": assembly_id,
                "id": effect_id,
                "contract_effect": contract_effect,
                "machine_id": machine_id,
                "authority_actor_label": authority_label,
                "state_source": state_source,
                "implementation": implementation,
                "anchor_relative_cm": anchor,
                "effect_anchor_tag": anchor_tag,
                "colour_role": colour_role,
                "layer_id": layer_id,
            })
            contract_effects.add(contract_effect)
            effect_ids.add(effect_id)
        if contract_effects != REQUIRED_EFFECTS_BY_ASSEMBLY[assembly_id]:
            fail("{} effect bindings do not cover the authoritative animation contract".format(assembly_id))
        assemblies[assembly_id] = assembly
    if set(assemblies) != REQUIRED_ASSEMBLY_IDS:
        fail("runtime manifest does not cover all required assemblies")
    if not any(layer["kind"] in ("moving_overlay", "frame_state") for layer in layers):
        fail("runtime manifest contains no moving overlay layers")

    press_assembly = assemblies["S02_TO_S06_PRESS_STATIONS"]
    frame_sets = require_list(press_assembly.get("frame_state_sets"), "S02-S06 press frame-state sets")
    layers_by_id = {layer["id"]: layer for layer in layers}
    seen_stations: set[str] = set()
    for raw_set in frame_sets:
        raw_set = require_mapping(raw_set, "press frame-state set")
        station = require_string(raw_set.get("station"), "press frame-state station")
        if station not in PRESS_FRAME_STATIONS or station in seen_stations:
            fail("press frame-state station is unexpected or duplicated: {}".format(station))
        if raw_set.get("mode") != "GAMEPLAY_TIMED_EXACT_ANCHOR_FRAME_STATES":
            fail("{} frame-state mode is not gameplay-timed exact-anchor".format(station))
        require_bool(raw_set.get("exact_anchor_all_states"), True, "{} exact_anchor_all_states".format(station))
        require_bool(
            raw_set.get("world_z_screen_translation_forbidden"),
            True,
            "{} world_z_screen_translation_forbidden".format(station),
        )
        require_string(raw_set.get("authoritative_phase_source"), "{} authoritative phase source".format(station))
        states = require_mapping(raw_set.get("states"), "{} frame states".format(station))
        if set(states) != set(PRESS_FRAME_STATES):
            fail("{} must map exactly open/descending/contact/rising states".format(station))
        anchors = []
        for state in PRESS_FRAME_STATES:
            layer_id = require_string(states[state], "{} {} frame layer".format(station, state))
            layer = layers_by_id.get(layer_id)
            if layer is None or layer["assembly_id"] != "S02_TO_S06_PRESS_STATIONS":
                fail("{} {} references an unknown press layer".format(station, state))
            if layer["kind"] != "frame_state" or layer["frame_state"] != state:
                fail("{} {} does not reference a matching frame-state layer".format(station, state))
            if bool(layer["initially_visible"]) != (state == "open"):
                fail("{} must start with only its open frame visible".format(station))
            anchors.append(layer["anchor_px"])
        if any(anchor != anchors[0] for anchor in anchors[1:]):
            fail("{} frame-state layers do not preserve the exact anchor".format(station))
        seen_stations.add(station)
    if seen_stations != PRESS_FRAME_STATIONS:
        fail("press frame-state sets do not cover S02-S06")

    return {
        "view": {
            "camera_actor_label": camera_label,
            "location": camera_location,
            "rotation": rotation,
            "ortho_width_cm": ortho_width,
            "aspect_ratio": aspect_ratio,
        },
        "authorities": required_authorities,
        "controller_classes": controller_classes,
        "hide_labels": hide_labels,
        "layers": layers,
        "beacons": beacon_bindings,
        "effects": effect_bindings,
        "assemblies": assemblies,
    }


def load_and_validate_inputs() -> Tuple[Dict[str, Any], str, Dict[str, Any], str, Dict[str, Any]]:
    animation_contract, animation_hash = load_json(ANIMATION_CONTRACT, "animation/effects contract")
    if animation_hash != ANIMATION_CONTRACT_SHA256:
        fail("animation/effects contract hash changed: {}".format(animation_hash))
    animation_info = validate_animation_contract_data(animation_contract)

    runtime_manifest, runtime_hash = load_json(RUNTIME_MANIFEST, "unified true-overhead runtime manifest")
    runtime_info = validate_runtime_manifest_data(runtime_manifest, animation_hash)
    return runtime_manifest, runtime_hash, animation_contract, animation_hash, {
        "animation": animation_info,
        "runtime": runtime_info,
    }


def protected_snapshot() -> Dict[str, str]:
    result: Dict[str, str] = {}
    for path, expected_hash in PROTECTED_MAPS.items():
        if not path.is_file():
            fail("protected map is missing: {}".format(path))
        actual_hash = digest(path)
        if actual_hash != expected_hash:
            fail("protected map hash changed: {} = {}".format(path, actual_hash))
        result[str(path)] = actual_hash
    for path, expected_hash in PROTECTED_NATIVE_BEACON_SOURCES.items():
        if not path.is_file():
            fail("native status-beacon source is missing: {}".format(path))
        actual_hash = digest(path)
        if actual_hash != expected_hash:
            fail("native status-beacon source contract changed: {} = {}".format(path, actual_hash))
        result[str(path)] = actual_hash
    if not DEFAULT_ENGINE_INI.is_file():
        fail("DefaultEngine.ini is missing")
    config_hash = digest(DEFAULT_ENGINE_INI)
    if config_hash != DEFAULT_ENGINE_INI_SHA256:
        fail("DefaultEngine.ini hash changed: {}".format(config_hash))
    result[str(DEFAULT_ENGINE_INI)] = config_hash
    return result


def asset_package_path(value: Any) -> str | None:
    if value is None:
        return None
    outermost = value.get_outermost() if hasattr(value, "get_outermost") else None
    if outermost is not None and hasattr(outermost, "get_path_name"):
        return str(outermost.get_path_name())
    if hasattr(value, "get_path_name"):
        path = str(value.get_path_name())
        return path.split(".", 1)[0]
    return None


def actor_class_name(actor: Any) -> str:
    actor_class = actor.get_class()
    return str(actor_class.get_name())


def actor_fingerprint(actor: Any) -> Dict[str, Any]:
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    return {
        "label": actor.get_actor_label(),
        "class": actor_class_name(actor),
        "location_cm": [location.x, location.y, location.z],
        "rotation_deg": [rotation.pitch, rotation.yaw, rotation.roll],
        "scale": [scale.x, scale.y, scale.z],
        "tags": sorted(str(tag) for tag in list(actor.tags or [])),
        "hidden_in_game": bool(actor.is_hidden()),
        "collision_enabled": bool(actor.get_actor_enable_collision()),
    }


def world_game_mode_path(world: Any) -> str | None:
    settings = world.get_world_settings()
    game_mode = settings.get_editor_property("default_game_mode")
    return str(game_mode.get_path_name()) if game_mode is not None else None


def index_actors(actors: Iterable[Any]) -> Dict[str, List[Any]]:
    result: Dict[str, List[Any]] = {}
    for actor in actors:
        result.setdefault(actor.get_actor_label(), []).append(actor)
    return result


def resolve_one(actor_index: Mapping[str, Sequence[Any]], label: str, context: str) -> Any:
    matches = list(actor_index.get(label, []))
    if len(matches) != 1:
        fail("{} expected exactly one actor labelled {!r}; found {}".format(context, label, len(matches)))
    return matches[0]


def dirty_package_paths() -> Dict[str, List[str]]:
    dirty_maps = sorted(
        package.get_path_name()
        for package in list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() or [])
    )
    dirty_content = sorted(
        package.get_path_name()
        for package in list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages() or [])
    )
    return {"maps": dirty_maps, "content": dirty_content}


def preflight_runtime_assets(layers: Sequence[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for layer in layers:
        for key, expected_type in (
            ("mesh_asset", unreal.StaticMesh),
            ("material_asset", unreal.MaterialInterface),
        ):
            asset_path = str(layer[key])
            if asset_path not in result:
                asset = unreal.load_asset(asset_path)
                if not isinstance(asset, expected_type):
                    fail("runtime layer asset is missing or wrong type: {}".format(asset_path))
                result[asset_path] = {
                    "asset": asset,
                    "class": asset.get_class().get_name(),
                }
    return result


def preflight_native_beacon_class() -> Any:
    beacon_class = getattr(unreal, NATIVE_BEACON_COMPONENT_CLASS, None)
    if beacon_class is None:
        fail("native ULBStatusBeaconComponent is unavailable; build the game module first")
    return beacon_class


def verify_native_beacon_bindings(
    authority_actors: Mapping[str, Any],
    beacon_specs: Sequence[Mapping[str, Any]],
    beacon_class: Any,
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for spec in beacon_specs:
        authority = authority_actors[str(spec["authority_actor_label"])]
        components = list(authority.get_components_by_class(beacon_class) or [])
        matches = [component for component in components if component.get_name() == spec["component_name"]]
        if len(matches) != 1:
            fail(
                "{} expected one native beacon component {} on {}; found {}".format(
                    spec["machine_id"],
                    spec["component_name"],
                    spec["authority_actor_label"],
                    len(matches),
                )
            )
        component = matches[0]
        location = component.get_relative_location()
        actual_anchor = (float(location.x), float(location.y), float(location.z))
        expected_anchor = tuple(spec["anchor_relative_cm"])
        if any(abs(actual - expected) > NUMERIC_TOLERANCE for actual, expected in zip(actual_anchor, expected_anchor)):
            fail(
                "{} native beacon anchor changed: {} != {}".format(
                    spec["machine_id"], actual_anchor, expected_anchor
                )
            )
        lights = []
        for getter_name, colour in (
            ("get_green_light", "green"),
            ("get_amber_light", "amber"),
            ("get_red_light", "red"),
        ):
            getter = getattr(component, getter_name, None)
            light = getter() if callable(getter) else None
            if not isinstance(light, unreal.PointLightComponent):
                fail("{} native beacon is missing its restrained {} point light".format(spec["machine_id"], colour))
            lights.append(light.get_name())
        records.append({
            "assembly_id": spec["assembly_id"],
            "machine_id": spec["machine_id"],
            "authority_actor_label": spec["authority_actor_label"],
            "component_name": component.get_name(),
            "component_class": component.get_class().get_name(),
            "anchor_relative_cm": list(actual_anchor),
            "state_source": spec["state_source"],
            "visual_contract": spec["visual_contract"],
            "real_point_lights": lights,
            "emissive_mid_contract_source_hash_locked": True,
        })
    return records


def configure_camera(view: Mapping[str, Any], existing_labels: Mapping[str, Sequence[Any]]) -> Any:
    label = str(view["camera_actor_label"])
    if existing_labels.get(label):
        fail("target already contains the reserved overhead camera label: {}".format(label))
    location = view["location"]
    rotation = view["rotation"]
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor,
        unreal.Vector(*location),
        unreal.Rotator(*rotation),
    )
    if camera is None:
        fail("could not spawn the true-overhead camera")
    camera.set_actor_label(label)
    component = camera.get_component_by_class(unreal.CameraComponent)
    if component is None:
        fail("true-overhead camera has no CameraComponent")
    component.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    component.set_editor_property("ortho_width", float(view["ortho_width_cm"]))
    component.set_editor_property("constrain_aspect_ratio", True)
    component.set_editor_property("aspect_ratio", float(view["aspect_ratio"]))
    camera.set_editor_property("tags", [unreal.Name("LB.PressShop.Overhead.Camera")])
    return camera


def hide_presentation_actors(
    actor_index: Mapping[str, Sequence[Any]],
    hide_labels: Sequence[str],
) -> List[Dict[str, Any]]:
    hidden: List[Dict[str, Any]] = []
    for label in hide_labels:
        actor = resolve_one(actor_index, label, "presentation hide")
        before = actor_fingerprint(actor)
        actor.set_actor_hidden_in_game(True)
        actor.set_actor_enable_collision(False)
        for component in list(actor.get_components_by_class(unreal.PrimitiveComponent) or []):
            component.set_visibility(False, True)
            component.set_hidden_in_game(True, True)
            component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        hidden.append({"before": before, "label": label})
    return hidden


def spawn_visual_layers(
    layers: Sequence[Mapping[str, Any]],
    loaded_assets: Mapping[str, Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for layer in layers:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(*layer["location"]),
            unreal.Rotator(*layer["rotation"]),
        )
        if actor is None:
            fail("could not spawn visual layer {}".format(layer["id"]))
        actor.set_actor_label(str(layer["actor_label"]))
        actor.set_actor_scale3d(unreal.Vector(*layer["scale"]))
        actor.set_actor_enable_collision(False)

        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        if component is None:
            fail("visual layer {} has no StaticMeshComponent".format(layer["id"]))
        mesh = loaded_assets[str(layer["mesh_asset"])]["asset"]
        material = loaded_assets[str(layer["material_asset"])]["asset"]
        component.set_static_mesh(mesh)
        component.set_material(0, material)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_generate_overlap_events(False)
        component.set_cast_shadow(bool(layer["casts_shadow"]))
        component.set_visibility(bool(layer["initially_visible"]), True)
        component.set_hidden_in_game(not bool(layer["initially_visible"]), True)

        tags = list(layer["tags"])
        tags.extend((
            "LB.Assembly.{}".format(layer["assembly_id"]),
            "LB.Layer.{}".format(layer["id"]),
            "LB.LayerKind.{}".format(layer["kind"]),
        ))
        binding = layer.get("runtime_binding")
        if binding:
            tags.extend((
                str(binding["binding_tag"]),
                "LB.AuthorityLabel.{}".format(binding["authority_actor_label"]),
                "LB.MotionChannel.{}".format(binding["motion_channel"]),
            ))
        actor.set_editor_property("tags", [unreal.Name(value) for value in sorted(set(tags))])
        records.append({
            "assembly_id": layer["assembly_id"],
            "layer_id": layer["id"],
            "actor_label": actor.get_actor_label(),
            "actor_class": actor_class_name(actor),
            "mesh_asset": str(layer["mesh_asset"]),
            "material_asset": str(layer["material_asset"]),
            "source_sha256": layer["source_sha256"],
            "runtime_binding": binding,
            "initially_visible": bool(layer["initially_visible"]),
            "frame_state": layer["frame_state"],
            "anchor_px": list(layer["anchor_px"]) if layer["anchor_px"] is not None else None,
            "collision_enabled": actor.get_actor_enable_collision(),
        })
    return records


def main() -> None:
    # The two documents are loaded and completely validated first.  In
    # particular, a missing/incomplete pack cannot create the target map.
    runtime_manifest, runtime_hash, animation_contract, animation_hash, validated = load_and_validate_inputs()
    runtime_info = validated["runtime"]

    if not SOURCE_FILE.is_file() or digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("hash-locked OneFactory source is missing or changed")
    if TARGET_FILE.exists() or unreal.EditorAssetLibrary.does_asset_exist(TARGET_MAP):
        fail("target already exists; refusing to overwrite: {}".format(TARGET_MAP))
    protected_before = protected_snapshot()

    # Asset loading is read-only and occurs before map creation so a missing
    # material/mesh cannot leave a partially staged target.
    loaded_assets = preflight_runtime_assets(runtime_info["layers"])
    native_beacon_class = preflight_native_beacon_class()

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_registry.scan_paths_synchronous(
        [
            "/Game/LineBoss/Factory/OneFactory/v001",
            "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPlayable_v001",
        ],
        force_rescan=True,
        ignore_deny_list_scan_filters=False,
    )
    if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE_MAP):
        fail("asset registry cannot resolve the unopened OneFactory source map")

    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if editor_subsystem is None:
        fail("UnrealEditorSubsystem is unavailable")
    current_world = editor_subsystem.get_editor_world()
    current_world_package = asset_package_path(current_world)
    if current_world_package in (SOURCE_MAP, TARGET_MAP):
        fail("switch to an unrelated clean editor world before running; current={}".format(current_world_package))
    dirty_before = dirty_package_paths()
    if dirty_before["maps"] or dirty_before["content"]:
        fail("unrelated editor world is not clean: {}".format(dirty_before))

    source_asset_data = list(
        asset_registry.get_assets_by_package_name(
            unreal.Name(SOURCE_MAP),
            include_only_on_disk_assets=False,
        )
        or []
    )
    if len(source_asset_data) != 1:
        fail("expected one on-disk OneFactory World asset; found {}".format(len(source_asset_data)))
    if source_asset_data[0].is_asset_loaded():
        fail("OneFactory source package is already loaded; refusing in-memory duplication")

    # Isolation rule: duplicate the unopened source package first, then load
    # only the target.  There is no save-as or source-world fallback.
    if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE_MAP, TARGET_MAP):
        fail("native Unreal duplication of unopened OneFactory source failed")
    if not unreal.EditorLoadingAndSavingUtils.load_map(TARGET_MAP):
        fail("could not load the isolated overhead target map")

    target_world = editor_subsystem.get_editor_world()
    if asset_package_path(target_world) != TARGET_MAP:
        fail("loaded editor world is not the isolated target")
    game_mode_before = world_game_mode_path(target_world)
    target_actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    actor_index = index_actors(target_actors)

    authority_actors: Dict[str, Any] = {}
    for label, spec in runtime_info["authorities"].items():
        actor = resolve_one(actor_index, label, "runtime authority preservation")
        actual_class = actor_class_name(actor)
        if actual_class != spec["class_name"]:
            fail("runtime authority {} class changed: {} != {}".format(label, actual_class, spec["class_name"]))
        authority_actors[label] = actor
    authority_before = {label: actor_fingerprint(actor) for label, actor in authority_actors.items()}
    native_beacon_records = verify_native_beacon_bindings(
        authority_actors,
        runtime_info["beacons"],
        native_beacon_class,
    )
    controller_counts_before = {
        class_name: sum(1 for actor in target_actors if actor_class_name(actor) == class_name)
        for class_name in runtime_info["controller_classes"]
    }
    if any(count != 1 for count in controller_counts_before.values()):
        fail("expected exactly one of every declared controller before staging: {}".format(controller_counts_before))

    reserved_labels = set(runtime_info["hide_labels"])
    reserved_labels.update(layer["actor_label"] for layer in runtime_info["layers"])
    reserved_labels.add(runtime_info["view"]["camera_actor_label"])
    for label in reserved_labels:
        if label not in runtime_info["hide_labels"] and actor_index.get(label):
            fail("reserved new actor label already exists in target: {}".format(label))
    # Resolve every hide label before changing the first actor.
    for label in runtime_info["hide_labels"]:
        resolve_one(actor_index, label, "presentation hide preflight")

    hidden_records = hide_presentation_actors(actor_index, runtime_info["hide_labels"])
    layer_records = spawn_visual_layers(runtime_info["layers"], loaded_assets)
    camera = configure_camera(runtime_info["view"], actor_index)

    actors_after_staging = list(unreal.EditorLevelLibrary.get_all_level_actors())
    authority_after = {label: actor_fingerprint(actor) for label, actor in authority_actors.items()}
    if authority_after != authority_before:
        fail("a retained gameplay-authority actor changed while staging visuals")
    controller_counts_after = {
        class_name: sum(1 for actor in actors_after_staging if actor_class_name(actor) == class_name)
        for class_name in runtime_info["controller_classes"]
    }
    if controller_counts_after != controller_counts_before:
        fail("controller count changed; duplicate controller creation is forbidden")
    game_mode_after = world_game_mode_path(target_world)
    if game_mode_after != game_mode_before:
        fail("target GameMode changed while staging overhead presentation")

    dirty_before_save = dirty_package_paths()
    unexpected_dirty_maps = [path for path in dirty_before_save["maps"] if path != TARGET_MAP]
    if unexpected_dirty_maps or dirty_before_save["content"]:
        fail("staging dirtied packages other than the target map: {}".format(dirty_before_save))
    if not unreal.EditorLevelLibrary.save_current_level():
        fail("could not save isolated overhead target")
    if not TARGET_FILE.is_file():
        fail("isolated overhead target file was not written")

    protected_after = protected_snapshot()
    if protected_after != protected_before:
        fail("a protected map or DefaultEngine.ini changed during the build")

    receipt = {
        "status": "PASS__PRESSSHOP_2126_OVERHEAD_PLAYABLE_V001_BUILT",
        "source_map": SOURCE_MAP,
        "source_map_sha256": SOURCE_FILE_SHA256,
        "source_map_explicitly_loaded": False,
        "source_package_loaded_before_duplicate": False,
        "preduplicate_editor_world": current_world_package,
        "preduplicate_editor_world_clean": True,
        "target_map": TARGET_MAP,
        "target_file": str(TARGET_FILE),
        "target_sha256": digest(TARGET_FILE),
        "runtime_manifest": str(RUNTIME_MANIFEST),
        "runtime_manifest_sha256": runtime_hash,
        "runtime_manifest_status": runtime_manifest["status"],
        "animation_contract": str(ANIMATION_CONTRACT),
        "animation_contract_sha256": animation_hash,
        "animation_contract_id": animation_contract["contract_id"],
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "default_engine_ini_unchanged": True,
        "game_mode_before": game_mode_before,
        "game_mode_after": game_mode_after,
        "runtime_authority_fingerprints_unchanged": authority_after,
        "controller_counts_before": controller_counts_before,
        "controller_counts_after": controller_counts_after,
        "duplicate_controllers_spawned": False,
        "presentation_hidden": hidden_records,
        "visual_layers": layer_records,
        "native_status_beacons": native_beacon_records,
        "state_effect_bindings": runtime_info["effects"],
        "baked_only_beacon_colours": False,
        "decorative_effect_loops": False,
        "true_overhead_camera": actor_fingerprint(camera),
        "save_scope": [TARGET_MAP, str(RECEIPT)],
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    unreal.log("PRESSSHOP_2126_OVERHEAD_PLAYABLE_V001_BUILD_PASS=" + json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
