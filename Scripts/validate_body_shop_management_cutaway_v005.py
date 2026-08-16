"""Independent fresh-load validator for Body Shop management cutaway v005.

Required process environment variable:
  LB_BODYSHOP_MANAGEMENT_CUTAWAY_V005_PATCH_RECEIPT

This validator is intentionally independent of the repair module.  It never
saves a level or writes Content, Source, Config, or campaign-save state.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
SCRIPT = PROJECT / "Scripts/validate_body_shop_management_cutaway_v005.py"
REPAIR_SCRIPT = PROJECT / "Scripts/repair_body_shop_management_cutaway_v005.py"
MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
MAP_SHA256_V004 = "6921968DE25E48497491F58E098CF870519A4E17F0C40A13EE88A9E99D155FC9"
V004_RECEIPT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/visual_readability_v004_validation.json"
V004_RECEIPT_SHA256 = "956E08511F2AA840D71B94E07217DBA357EA955B701BA3A8C9F744AAAC11757E"
PATCH_RECEIPT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/management_cutaway_v005_patch.json"
AUDIT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/management_cutaway_v005_validation.json"
BACKUP_ROOT = PROJECT / "Saved/Quarantine/BodyShop/ManagementCutaway_v005_PrePatch"

MAP_TAG = "LB.BodyShop.Experimental.v001"
ENV_TAG = "LB.BodyShop.Environment"
SHELL_TAG = "LB.BodyShop.Environment.Shell"
STRUCTURE_TAG = "LB.BodyShop.Environment.Structure"
GRID_TAG = "LB.BodyShop.Environment.Grid.100cm"
CUTAWAY_TAG = "LB.BodyShop.Environment.ManagementCutaway"

EXPECTED_CLASS_COUNTS = {
    "CameraActor": 2,
    "DirectionalLight": 1,
    "LBBodyShopPrototypeWorldBootstrap": 1,
    "PlayerStart": 1,
    "PostProcessVolume": 1,
    "RectLight": 15,
    "SkyLight": 1,
    "StaticMeshActor": 314,
}
ACTIVE_RECT_COORDS = {
    (-6000, -1800), (-6000, 0),
    (-3000, -1800), (-3000, 0),
    (0, -1800), (0, 0),
}
CAMERA_SPECS = {
    "LB_BodyShop_Prototype_ReviewCamera_Overview_v001": {
        "location": (-7200.0, -4000.0, 1050.0),
        "target": (-4450.0, -1800.0, 180.0),
        "fov": 50.0,
    },
    "LB_BodyShop_Prototype_ReviewCamera_Flow_v001": {
        "location": (-5250.0, -3300.0, 900.0),
        "target": (-4500.0, -1800.0, 140.0),
        "fov": 46.0,
    },
}
EXPECTED_CONFIG_HASHES = {
    "Config/DefaultEditor.ini": "BBE05501998265524E8ACD5319DBC42E748DDE39FB25463C8BB0D431AC746D16",
    "Config/DefaultEditorPerProjectUserSettings.ini": "9255BE413FFFB3970BAD3C921E8E5BFE3DD41A0B01F45348354FCAAC01E9E6D4",
    "Config/DefaultEngine.ini": "A1A3B4E5EC0327BB9AD05B094B7749CE9CE9795B1D065CFA4196C1AD3EFB82D3",
    "Config/DefaultGame.ini": "1DE2055DB7A0F4EA1653E9656A33EE692CBEF133B8761A08A31B090B3832484C",
    "Config/DefaultGameUserSettings.ini": "D4E55BBFC7F843097D40E3335B1FE57AE12F804D981564F904AEBCDA34F35F3E",
    "Config/DefaultInput.ini": "8DCE19104C744A1DA03413EC234CF9D0BAD1BF40BD718C1F770D68CBD42D2F00",
}


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_MANAGEMENT_CUTAWAY_V005_VALIDATION_FAIL: " + message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def close(actual: float, expected: float, tolerance: float = 0.02) -> bool:
    return abs(float(actual) - float(expected)) <= tolerance


def scalar(value: float) -> float:
    rounded = round(float(value), 4)
    return 0.0 if abs(rounded) < 0.00005 else rounded


def vec(value) -> list[float]:
    return [scalar(value.x), scalar(value.y), scalar(value.z)]


def rot(value) -> list[float]:
    return [scalar(value.pitch), scalar(value.yaw), scalar(value.roll)]


def tags_of(actor) -> set[str]:
    return {str(tag) for tag in actor.get_editor_property("tags")}


def component_path(value) -> str | None:
    return value.get_path_name() if value is not None else None


def expected_actor_labels() -> set[str]:
    labels = {
        "LB_BS_ENV_Floor_180m_x_90m",
        "LB_BS_ENV_Wall_North", "LB_BS_ENV_Wall_South",
        "LB_BS_ENV_Wall_West", "LB_BS_ENV_Wall_East",
        "LB_BS_ENV_BuildArea_North", "LB_BS_ENV_BuildArea_South",
        "LB_BS_ENV_BuildArea_West", "LB_BS_ENV_BuildArea_East",
        "LB_BS_ENV_PedestrianProtectedLane", "LB_BS_ENV_FLTProtectedRoute",
        "LB_BS_ENV_NorthServiceBoundary", "LB_BS_ENV_SouthServiceBoundary",
        "LB_BS_INTERFACE_InputDockDatum", "LB_BS_INTERFACE_EDOutputDatum",
        "LB_BS_ENV_DirectionalLight", "LB_BS_ENV_SkyLight",
        "LB_BS_ENV_NeutralExposure", "LB_BodyShop_Prototype_PlayerStart_v001",
        "LB_BodyShop_Prototype_ReviewCamera_Overview_v001",
        "LB_BodyShop_Prototype_ReviewCamera_Flow_v001",
        "LB_BodyShop_PrototypeBootstrap_v001",
    }
    labels.update(f"LB_BS_ENV_GridX_{x:+05d}" for x in range(-9000, 9001, 100))
    labels.update(f"LB_BS_ENV_GridY_{y:+05d}" for y in range(-4500, 4501, 100))
    for x in range(-8000, 8001, 2000):
        labels.update({
            f"LB_BS_ENV_Column_North_{x:+05d}",
            f"LB_BS_ENV_Column_South_{x:+05d}",
            f"LB_BS_ENV_Truss_{x:+05d}",
        })
    for x in (-6000, -3000, 0, 3000, 6000):
        for y in (-1800, 0, 1800):
            labels.add(f"LB_BS_ENV_Light_{x:+05d}_{y:+05d}")
    return labels


def cutaway_specs() -> dict[str, dict]:
    rows = {}
    for x in range(-8000, 8001, 2000):
        rows[f"LB_BS_ENV_Truss_{x:+05d}"] = {
            "kind": "truss",
            "location_cm": [float(x), 0.0, 1600.0],
            "scale": [0.45, 80.5, 0.45],
            "bounds_origin_cm": [float(x), 0.0, 1600.0],
            "bounds_extent_cm": [22.5, 4025.0, 22.5],
        }
        rows[f"LB_BS_ENV_Column_South_{x:+05d}"] = {
            "kind": "south_column",
            "location_cm": [float(x), -4050.0, 825.0],
            "scale": [0.55, 0.55, 16.5],
            "bounds_origin_cm": [float(x), -4050.0, 825.0],
            "bounds_extent_cm": [27.5, 27.5, 825.0],
        }
    return rows


CUTAWAY_SPECS = cutaway_specs()
CUTAWAY_LABELS = set(CUTAWAY_SPECS)


def config_snapshot() -> dict[str, str]:
    files = {
        path.relative_to(PROJECT).as_posix(): path
        for path in (PROJECT / "Config").rglob("*") if path.is_file()
    }
    if set(files) != set(EXPECTED_CONFIG_HASHES):
        fail("Config file inventory drift: " + str(sorted(files)))
    rows = {name: digest(files[name]) for name in sorted(files)}
    if rows != EXPECTED_CONFIG_HASHES:
        fail("Config hash drift")
    return rows


def protected_snapshot(expected: dict) -> dict:
    rows = {}
    for raw_path, contract in sorted(expected.items()):
        path = Path(raw_path)
        row = {"exists": path.is_file(), "sha256": digest(path) if path.is_file() else None}
        if row != contract:
            fail("protected Press/C-gun/material/mesh/legacy/campaign drift: " + raw_path)
        rows[raw_path] = row
    return rows


def load_authorities() -> tuple[dict, dict, dict]:
    if not V004_RECEIPT.is_file() or digest(V004_RECEIPT) != V004_RECEIPT_SHA256:
        fail("pinned v004 validation authority path/hash drift")
    v004 = json.loads(V004_RECEIPT.read_text(encoding="utf-8-sig"))
    if (v004.get("$schema") != "lineboss/audit/bodyshop/visual-readability-v004-validation/v1"
            or v004.get("status") != "PASS__FRESH_RELOAD_BODYSHOP_VISUAL_READABILITY_V004"
            or v004.get("failures")
            or v004.get("map", {}).get("sha256") != MAP_SHA256_V004
            or len(v004.get("protected_hashes", {})) != 29):
        fail("pinned v004 validation authority contract drift")

    raw = os.environ.get("LB_BODYSHOP_MANAGEMENT_CUTAWAY_V005_PATCH_RECEIPT", "").strip()
    if not raw or Path(raw).resolve() != PATCH_RECEIPT or not PATCH_RECEIPT.is_file():
        fail("management-cutaway v005 patch authority path is unset or wrong")
    patch_hash = digest(PATCH_RECEIPT)
    patch = json.loads(PATCH_RECEIPT.read_text(encoding="utf-8-sig"))
    if (patch.get("$schema") != "lineboss/audit/bodyshop/management-cutaway-v005-patch/v1"
            or patch.get("status") != "PASS__BODYSHOP_MANAGEMENT_CUTAWAY_V005_MAP_PATCHED"
            or patch.get("failures")):
        fail("management-cutaway v005 patch authority contract drift")
    expected_v004_gate = {"path": str(V004_RECEIPT), "sha256": V004_RECEIPT_SHA256}
    if patch.get("prerequisite", {}).get("visual_readability_v004_validation") != expected_v004_gate:
        fail("patch prerequisite chain drift")
    if (patch.get("source_script") != str(REPAIR_SCRIPT)
            or patch.get("source_script_sha256") != digest(REPAIR_SCRIPT)):
        fail("patch source-script identity drift")
    return ({"path": str(V004_RECEIPT), "sha256": V004_RECEIPT_SHA256},
            {"path": str(PATCH_RECEIPT), "sha256": patch_hash}, patch)


def validate_patch_contract(patch: dict, expected_protected: dict) -> str:
    map_row = patch.get("map", {})
    expected_after = map_row.get("sha256_after")
    before_state = map_row.get("state_before", {})
    after_state = map_row.get("state_after", {})
    expected_labels = sorted(CUTAWAY_LABELS)
    before_rows = before_state.get("cutaway_actors", {})
    after_rows = after_state.get("cutaway_actors", {})
    if set(before_rows) != CUTAWAY_LABELS or set(after_rows) != CUTAWAY_LABELS:
        fail("patch before/after cutaway actor evidence inventory drift")
    normalized_before_state = json.loads(json.dumps(before_state))
    normalized_after_state = json.loads(json.dumps(after_state))
    for label in expected_labels:
        before_actor = normalized_before_state["cutaway_actors"][label]
        after_actor = normalized_after_state["cutaway_actors"][label]
        if (before_actor.get("hidden_in_game") is not False
                or CUTAWAY_TAG in before_actor.get("tags", [])
                or after_actor.get("hidden_in_game") is not True
                or CUTAWAY_TAG not in after_actor.get("tags", [])):
            fail("patch cutaway transition evidence drift: " + label)
        after_actor["hidden_in_game"] = False
        after_actor["tags"] = [tag for tag in after_actor["tags"] if tag != CUTAWAY_TAG]
    if normalized_before_state != normalized_after_state:
        fail("patch receipt state changed beyond exact cutaway tag/HiddenInGame transition")
    if (map_row.get("asset") != MAP
            or map_row.get("sha256_before") != MAP_SHA256_V004
            or not isinstance(expected_after, str) or len(expected_after) != 64
            or expected_after == MAP_SHA256_V004
            or map_row.get("actors_added_or_removed") != 0
            or not isinstance(map_row.get("normalized_invariant_fingerprint_before"), str)
            or len(map_row.get("normalized_invariant_fingerprint_before")) != 64
            or map_row.get("normalized_invariant_fingerprint_before")
            != map_row.get("normalized_invariant_fingerprint_after")
            or before_state.get("actor_count") != 336
            or after_state.get("actor_count") != 336
            or before_state.get("cutaway_actor_count") != 18
            or after_state.get("cutaway_actor_count") != 18
            or patch.get("changed_actor_labels") != expected_labels
            or patch.get("changed_actor_count") != 18
            or patch.get("allowed_actor_changes")
            != ["append durable management-cutaway tag", "HiddenInGame false -> true"]
            or patch.get("protected_hashes_before_and_after") != expected_protected
            or patch.get("config_hashes_before_and_after") != EXPECTED_CONFIG_HASHES
            or patch.get("content_packages_changed") != [MAP]
            or patch.get("actor_count_lights_exposure_materials_meshes_cameras_gameplay_unchanged") is not True
            or patch.get("materials_or_meshes_changed") != []
            or patch.get("camera_changes") != []
            or patch.get("gameplay_source_config_or_save_changes") != []
            or patch.get("promotion_authorized") is not False):
        fail("patch exact-change contract drift")

    backup = patch.get("recoverable_backup", {})
    expected_backup = BACKUP_ROOT / MAP_FILE.relative_to(PROJECT)
    expected_manifest = BACKUP_ROOT / "MANIFEST.json"
    if (backup.get("map") != str(expected_backup)
            or backup.get("sha256") != MAP_SHA256_V004
            or backup.get("manifest") != str(expected_manifest)
            or not expected_backup.is_file() or digest(expected_backup) != MAP_SHA256_V004
            or not expected_manifest.is_file() or digest(expected_manifest) != backup.get("manifest_sha256")):
        fail("recoverable exact pre-map backup contract drift")
    manifest = json.loads(expected_manifest.read_text(encoding="utf-8-sig"))
    if (manifest.get("$schema") != "lineboss/quarantine/bodyshop-management-cutaway-v005-prepatch/v1"
            or manifest.get("status") != "RECOVERABLE_EXACT_BODYSHOP_VISUAL_V004_MAP_BACKUP"
            or manifest.get("source") != str(MAP_FILE)
            or manifest.get("backup") != str(expected_backup)
            or manifest.get("sha256") != MAP_SHA256_V004):
        fail("recoverable pre-map backup manifest drift")
    return expected_after


def actor_signature(actor, normalize_cutaway: bool) -> dict:
    label = actor.get_actor_label()
    origin, extent = actor.get_actor_bounds(False, False)
    actor_tags = sorted(tags_of(actor))
    hidden = bool(actor.get_editor_property("hidden"))
    if normalize_cutaway and label in CUTAWAY_LABELS:
        actor_tags = [tag for tag in actor_tags if tag != CUTAWAY_TAG]
        hidden = False
    row = {
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": vec(actor.get_actor_location()),
        "rotation": rot(actor.get_actor_rotation()),
        "scale": vec(actor.get_actor_scale3d()),
        "bounds_origin_cm": vec(origin),
        "bounds_extent_cm": vec(extent),
        "tags": actor_tags,
        "hidden_in_game": hidden,
    }
    static = actor.get_component_by_class(unreal.StaticMeshComponent)
    if static is not None:
        row["static_mesh"] = component_path(static.get_editor_property("static_mesh"))
        row["materials"] = [component_path(static.get_material(index))
                            for index in range(int(static.get_num_materials()))]
        row["collision"] = str(static.get_collision_enabled())
        row["cast_shadow"] = bool(static.get_editor_property("cast_shadow"))
        row["component_visible"] = bool(static.get_editor_property("visible"))
        row["component_hidden_in_game"] = bool(static.get_editor_property("hidden_in_game"))
    rect_light = actor.get_component_by_class(unreal.RectLightComponent)
    if rect_light is not None:
        row["rect_light"] = {
            "intensity": scalar(rect_light.get_editor_property("intensity")),
            "attenuation_radius": scalar(rect_light.get_editor_property("attenuation_radius")),
            "source_width": scalar(rect_light.get_editor_property("source_width")),
            "source_height": scalar(rect_light.get_editor_property("source_height")),
            "visible": bool(rect_light.get_editor_property("visible")),
            "hidden_in_game": bool(rect_light.get_editor_property("hidden_in_game")),
            "cast_shadows": bool(rect_light.get_editor_property("cast_shadows")),
        }
    directional = actor.get_component_by_class(unreal.DirectionalLightComponent)
    if directional is not None:
        row["directional_light"] = {
            "intensity": scalar(directional.get_editor_property("intensity")),
            "cast_shadows": bool(directional.get_editor_property("cast_shadows")),
            "source_angle": scalar(directional.get_editor_property("light_source_angle")),
        }
    sky = actor.get_component_by_class(unreal.SkyLightComponent)
    if sky is not None:
        row["sky_light"] = {"intensity": scalar(sky.get_editor_property("intensity"))}
    camera = actor.get_component_by_class(unreal.CameraComponent)
    if camera is not None:
        row["camera"] = {
            "fov": scalar(camera.get_editor_property("field_of_view")),
            "aspect_ratio": scalar(camera.get_editor_property("aspect_ratio")),
            "constrain_aspect_ratio": bool(camera.get_editor_property("constrain_aspect_ratio")),
        }
    if isinstance(actor, unreal.PostProcessVolume):
        settings = actor.get_editor_property("settings")
        row["post_process"] = {
            "unbound": bool(actor.get_editor_property("unbound")),
            "blend_weight": scalar(actor.get_editor_property("blend_weight")),
            "override_auto_exposure_method": bool(settings.get_editor_property("override_auto_exposure_method")),
            "auto_exposure_method": str(settings.get_editor_property("auto_exposure_method")),
            "override_auto_exposure_min_brightness": bool(settings.get_editor_property("override_auto_exposure_min_brightness")),
            "min_brightness": scalar(settings.get_editor_property("auto_exposure_min_brightness")),
            "override_auto_exposure_max_brightness": bool(settings.get_editor_property("override_auto_exposure_max_brightness")),
            "max_brightness": scalar(settings.get_editor_property("auto_exposure_max_brightness")),
            "override_auto_exposure_bias": bool(settings.get_editor_property("override_auto_exposure_bias")),
            "bias": scalar(settings.get_editor_property("auto_exposure_bias")),
        }
    if actor.get_class().get_name() == "LBBodyShopPrototypeWorldBootstrap":
        row["bootstrap"] = {
            "prototype_enabled": bool(actor.get_editor_property("prototype_enabled")),
            "reject_legacy_authorities": bool(actor.get_editor_property("reject_legacy_authorities")),
            "spawn_runtime_on_begin_play": bool(actor.get_editor_property("spawn_runtime_on_begin_play")),
            "use_experimental_save_only": bool(actor.get_editor_property("use_experimental_save_only")),
            "require_prototype_game_mode": bool(actor.get_editor_property("require_prototype_game_mode")),
            "request_initial_underbody_slice": bool(actor.get_editor_property("request_initial_underbody_slice")),
            "show_prototype_hud": bool(actor.get_editor_property("show_prototype_hud")),
            "prototype_build_origin": vec(actor.get_editor_property("prototype_build_origin")),
            "prototype_grid_size_cm": scalar(actor.get_editor_property("prototype_grid_size_cm")),
        }
    return row


def normalized_map_fingerprint(actors: list) -> str:
    rows = sorted((actor_signature(actor, True) for actor in actors), key=lambda row: row["label"])
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def validate_cutaway(actor, spec: dict) -> dict:
    origin, extent = actor.get_actor_bounds(False, False)
    static = actor.get_component_by_class(unreal.StaticMeshComponent)
    row = {
        "label": actor.get_actor_label(),
        "kind": spec["kind"],
        "location_cm": vec(actor.get_actor_location()),
        "rotation": rot(actor.get_actor_rotation()),
        "scale": vec(actor.get_actor_scale3d()),
        "bounds_origin_cm": vec(origin),
        "bounds_extent_cm": vec(extent),
        "tags": sorted(tags_of(actor)),
        "hidden_in_game": bool(actor.get_editor_property("hidden")),
        "mesh": component_path(static.get_editor_property("static_mesh")) if static else None,
        "materials": ([component_path(static.get_material(index))
                       for index in range(int(static.get_num_materials()))] if static else []),
        "collision": str(static.get_collision_enabled()) if static else None,
        "cast_shadow": bool(static.get_editor_property("cast_shadow")) if static else None,
    }
    expected_tags = {MAP_TAG, ENV_TAG, SHELL_TAG, STRUCTURE_TAG, CUTAWAY_TAG}
    checks = (
        row["location_cm"] == spec["location_cm"],
        row["rotation"] == [0.0, 0.0, 0.0],
        row["scale"] == spec["scale"],
        all(close(a, b, 0.25) for a, b in zip(row["bounds_origin_cm"], spec["bounds_origin_cm"])),
        all(close(a, b, 0.25) for a, b in zip(row["bounds_extent_cm"], spec["bounds_extent_cm"])),
        set(row["tags"]) == expected_tags,
        row["hidden_in_game"] is True,
        row["mesh"] == "/Engine/BasicShapes/Cube.Cube",
        row["materials"] == ["/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal"],
        "QUERY_AND_PHYSICS" in str(row["collision"]).upper(),
        row["cast_shadow"] is True,
    )
    if not all(checks):
        fail("fresh cutaway actor contract drift: " + row["label"] + ":" + str(row))
    return row


def rect_coords(actor) -> tuple[int, int]:
    location = actor.get_actor_location()
    return int(round(float(location.x))), int(round(float(location.y)))


def validate_map_state(actors: list) -> dict:
    counts = dict(Counter(actor.get_class().get_name() for actor in actors))
    labels = [actor.get_actor_label() for actor in actors]
    if counts != EXPECTED_CLASS_COUNTS:
        fail("fresh actor class inventory drift: " + str(counts))
    if len(labels) != len(set(labels)) or set(labels) != expected_actor_labels():
        fail("fresh actor label inventory drift")
    if any(MAP_TAG not in tags_of(actor) for actor in actors):
        fail("map-owned actor tag drift")
    by_label = {actor.get_actor_label(): actor for actor in actors}

    cutaway_rows = {
        label: validate_cutaway(by_label[label], spec)
        for label, spec in sorted(CUTAWAY_SPECS.items())
    }
    tagged = {actor.get_actor_label() for actor in actors if CUTAWAY_TAG in tags_of(actor)}
    if tagged != CUTAWAY_LABELS:
        fail("durable management-cutaway tag scope drift")

    grid = [actor for actor in actors if GRID_TAG in tags_of(actor)]
    if len(grid) != 272 or any(not bool(actor.get_editor_property("hidden")) for actor in grid):
        fail("runtime-hidden 100 cm grid contract drift")
    active_rows = {}
    inactive_labels = set()
    for actor in (item for item in actors if isinstance(item, unreal.RectLight)):
        component = actor.get_component_by_class(unreal.RectLightComponent)
        coords = rect_coords(actor)
        active = coords in ACTIVE_RECT_COORDS
        if (component is None
                or not close(component.get_editor_property("intensity"), 525.0 if active else 0.0, 0.0002)
                or bool(component.get_editor_property("visible")) is not active
                or bool(component.get_editor_property("hidden_in_game")) is active
                or bool(actor.get_editor_property("hidden")) is active
                or bool(component.get_editor_property("cast_shadows"))):
            fail("fresh v004 RectLight state drift: " + actor.get_actor_label())
        if active:
            active_rows[actor.get_actor_label()] = {"coords_cm": list(coords), "intensity": 525.0}
        else:
            inactive_labels.add(actor.get_actor_label())
    if len(active_rows) != 6 or {tuple(row["coords_cm"]) for row in active_rows.values()} != ACTIVE_RECT_COORDS:
        fail("fresh exact six-light active inventory drift")

    # The map-authored bootstrap is an AInfo authority and intentionally
    # nonvisual/hidden. It belongs to the exact baseline hidden set.
    hidden_expected = (
        {actor.get_actor_label() for actor in grid}
        | inactive_labels
        | {"LB_BodyShop_PrototypeBootstrap_v001"}
        | CUTAWAY_LABELS
    )
    hidden_actual = {actor.get_actor_label() for actor in actors if bool(actor.get_editor_property("hidden"))}
    if hidden_actual != hidden_expected:
        fail("fresh map HiddenInGame scope drift")

    sun = by_label["LB_BS_ENV_DirectionalLight"].get_component_by_class(unreal.DirectionalLightComponent)
    sky = by_label["LB_BS_ENV_SkyLight"].get_component_by_class(unreal.SkyLightComponent)
    exposure = by_label["LB_BS_ENV_NeutralExposure"]
    settings = exposure.get_editor_property("settings")
    if (sun is None or not close(sun.get_editor_property("intensity"), 0.8, 0.0002)
            or not bool(sun.get_editor_property("cast_shadows"))
            or not close(sun.get_editor_property("light_source_angle"), 4.0, 0.0002)
            or sky is None or not close(sky.get_editor_property("intensity"), 0.8, 0.0002)
            or not bool(exposure.get_editor_property("unbound"))
            or not close(exposure.get_editor_property("blend_weight"), 1.0, 0.0002)
            or not bool(settings.get_editor_property("override_auto_exposure_method"))
            or settings.get_editor_property("auto_exposure_method") != unreal.AutoExposureMethod.AEM_BASIC
            or not bool(settings.get_editor_property("override_auto_exposure_min_brightness"))
            or not bool(settings.get_editor_property("override_auto_exposure_max_brightness"))
            or not bool(settings.get_editor_property("override_auto_exposure_bias"))
            or not close(settings.get_editor_property("auto_exposure_min_brightness"), 1.0, 0.0002)
            or not close(settings.get_editor_property("auto_exposure_max_brightness"), 1.0, 0.0002)
            or not close(settings.get_editor_property("auto_exposure_bias"), 0.0, 0.0002)):
        fail("fresh directional/sky/fixed-exposure drift")

    cameras = {}
    for label, spec in CAMERA_SPECS.items():
        actor = by_label[label]
        component = actor.get_component_by_class(unreal.CameraComponent)
        expected_rotation = unreal.MathLibrary.find_look_at_rotation(
            unreal.Vector(*spec["location"]), unreal.Vector(*spec["target"]))
        if (component is None or vec(actor.get_actor_location()) != list(spec["location"])
                or any(not close(a, b) for a, b in zip(rot(actor.get_actor_rotation()), rot(expected_rotation)))
                or not close(component.get_editor_property("field_of_view"), spec["fov"], 0.0002)
                or not close(component.get_editor_property("aspect_ratio"), 16.0 / 9.0, 0.0002)
                or not bool(component.get_editor_property("constrain_aspect_ratio"))):
            fail("fresh saved review-camera drift: " + label)
        cameras[label] = actor_signature(actor, False)["camera"]

    world = unreal.EditorLevelLibrary.get_editor_world()
    game_mode = world.get_world_settings().get_editor_property("default_game_mode") if world else None
    bootstrap = actor_signature(by_label["LB_BodyShop_PrototypeBootstrap_v001"], False).get("bootstrap", {})
    if (game_mode is None
            or game_mode.get_path_name() != "/Script/LineBossCarFactory.LBBodyShopPrototypeGameMode"
            or not all(bootstrap.get(name) is True for name in (
                "prototype_enabled", "reject_legacy_authorities", "spawn_runtime_on_begin_play",
                "use_experimental_save_only", "require_prototype_game_mode",
                "request_initial_underbody_slice", "show_prototype_hud"))
            or bootstrap.get("prototype_build_origin") != [0.0, 0.0, 0.0]
            or bootstrap.get("prototype_grid_size_cm") != 100.0):
        fail("fresh isolated gameplay/bootstrap contract drift")

    north_labels = {f"LB_BS_ENV_Column_North_{x:+05d}" for x in range(-8000, 8001, 2000)}
    if any(bool(by_label[label].get_editor_property("hidden")) or CUTAWAY_TAG in tags_of(by_label[label])
           for label in north_labels):
        fail("north-column visibility/tag scope drift")
    return {
        "actor_count": len(actors),
        "class_counts": counts,
        "cutaway_actor_count": len(cutaway_rows),
        "cutaway_actors": cutaway_rows,
        "north_columns_visible_count": len(north_labels),
        "grid_hidden_in_game_count": len(grid),
        "active_rect_lights": active_rows,
        "directional_intensity": 0.8,
        "sky_intensity": 0.8,
        "fixed_exposure_bias": 0.0,
        "review_cameras": cameras,
        "game_mode": game_mode.get_path_name(),
        "bootstrap": bootstrap,
    }


def main() -> None:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    if AUDIT.exists():
        fail("refusing to overwrite immutable v005 validation output")
    if not SCRIPT.is_file() or not REPAIR_SCRIPT.is_file() or not MAP_FILE.is_file():
        fail("required v005 validator/repair/map input missing")

    v004_gate, patch_gate, patch = load_authorities()
    v004 = json.loads(V004_RECEIPT.read_text(encoding="utf-8-sig"))
    expected_protected = v004["protected_hashes"]
    expected_map_hash = validate_patch_contract(patch, expected_protected)
    if digest(MAP_FILE) != expected_map_hash:
        fail("Body Shop map is not the exact v005 patched package")
    protected_before = protected_snapshot(expected_protected)
    config_before = config_snapshot()
    map_before = digest(MAP_FILE)

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        fail("could not fresh-load isolated Body Shop map")
    actors = list(actors_api.get_all_level_actors())
    state = validate_map_state(actors)
    normalized = normalized_map_fingerprint(actors)
    if normalized != patch["map"]["normalized_invariant_fingerprint_after"]:
        fail("fresh normalized map invariant fingerprint drift")
    if digest(MAP_FILE) != map_before:
        fail("read-only fresh map load changed the v005 package")
    protected_after = protected_snapshot(expected_protected)
    config_after = config_snapshot()
    if protected_after != protected_before or config_after != config_before:
        fail("protected asset/source/save/config set changed during validation")

    payload = {
        "$schema": "lineboss/audit/bodyshop/management-cutaway-v005-validation/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FRESH_RELOAD_BODYSHOP_MANAGEMENT_CUTAWAY_V005",
        "source_script": str(SCRIPT),
        "source_script_sha256": digest(SCRIPT),
        "prerequisites": {
            "visual_readability_v004_validation": v004_gate,
            "management_cutaway_v005_patch": patch_gate,
        },
        "map": {
            "asset": MAP,
            "sha256": map_before,
            "state": state,
            "normalized_invariant_fingerprint": normalized,
            "read_only_fresh_load_hash_unchanged": True,
        },
        "recoverable_backup": patch["recoverable_backup"],
        "protected_hashes": protected_after,
        "config_hashes": config_after,
        "writes_to_content_source_config_or_saves": False,
        "materials_or_meshes_changed": [],
        "camera_changes_in_this_validator": [],
        "gameplay_changes_in_this_validator": [],
        "failures": [],
        "promotion_authorized": False,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_BODYSHOP_MANAGEMENT_CUTAWAY_V005_VALIDATION_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
