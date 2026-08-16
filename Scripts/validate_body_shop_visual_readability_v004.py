"""Fresh-process, read-only validator for Body Shop readability v004.

Required process environment variables:
  LB_BODYSHOP_VISUAL_V003_RECEIPT
  LB_BODYSHOP_HISM_VALIDATION_SUMMARY
  LB_BODYSHOP_VISUAL_V004_PATCH_RECEIPT
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
REPAIR_SCRIPT = PROJECT / "Scripts/repair_body_shop_visual_readability_v004.py"
AUDIT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/visual_readability_v004_validation.json"

MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
MAP_SHA256_V003 = "9766E686B5AA2B0F006C54CA4E578C37944A1CE4CE99C41F4EC3DFC009894D0A"
PRESS_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
PRESS_SHA256 = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
CGUN_FILE = PROJECT / "Content/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/SpotGun/SM_LB_WeldTool_SpotGun_v001.uasset"
CGUN_SHA256 = "79DAA22563EE54BC1F3C04C98B9CAEC7E22A1F01F7E65E9E76B147B4ABBC27BC"
LEGACY_FILES = {
    PROJECT / "Source/LineBossCarFactory/LBBodyWeldLineActor.cpp":
        "C06F7CF6FAECEE3C6B98EA2020226E961479BA04D2C35C4E8B290F3A0BE5C406",
    PROJECT / "Source/LineBossCarFactory/LBBodyWeldLineActor.h":
        "BDA985D627F0D3D4885632B9D777CE82071AF84AE036A39269E0F1754C8F46DE",
}
CAMPAIGN_SAVE_CANDIDATES = (
    PROJECT / "Saved/SaveGames/LineBossCampaign_v18.sav",
    PROJECT / "Saved/SaveGames/LineBoss_Campaign_v18.sav",
)

ACTIVE_RECT_COORDS = {
    (-6000, -1800), (-6000, 0),
    (-3000, -1800), (-3000, 0),
    (0, -1800), (0, 0),
}
TARGET_RECT_INTENSITY = 525.0
TARGET_DIRECTIONAL_INTENSITY = 0.80
TARGET_SKY_INTENSITY = 0.80
TARGET_EXPOSURE_BIAS = 0.0


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_VISUAL_READABILITY_V004_VALIDATION_FAIL: " + message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def close(actual: float, expected: float, tolerance: float = 0.0002) -> bool:
    return abs(float(actual) - float(expected)) <= tolerance


def receipt_from_env(env_name: str, schema: str, status: str) -> tuple[Path, dict]:
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        fail("required receipt parameter is unset: " + env_name)
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT / path
    path = path.resolve()
    if not path.is_file():
        fail("required receipt is missing: " + str(path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail("required receipt is not valid JSON: " + str(exc))
    if payload.get("$schema") != schema or payload.get("status") != status or payload.get("failures"):
        fail("required receipt did not pass its exact contract: " + str(path))
    return path, payload


def resolve_asset_file(asset_path: str) -> Path:
    if not asset_path.startswith("/Game/") or "." in asset_path:
        fail("protected asset path is not canonical package form: " + asset_path)
    return (PROJECT / "Content" / asset_path.removeprefix("/Game/")).with_suffix(".uasset")


def validate_prerequisite_chain() -> tuple[dict, dict, dict, dict]:
    visual_path, visual = receipt_from_env(
        "LB_BODYSHOP_VISUAL_V003_RECEIPT",
        "lineboss/audit/bodyshop/visual-readability-v003-validation/v1",
        "PASS__FRESH_RELOAD_BODYSHOP_VISUAL_READABILITY_V003")
    hism_path, hism = receipt_from_env(
        "LB_BODYSHOP_HISM_VALIDATION_SUMMARY",
        "lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-validation-summary-v001/v1",
        "PASS__FRESH_LIVE_PIE_LOG_HAS_NO_INSTANCED_STATIC_MESH_USAGE_WARNINGS")
    patch_path, patch = receipt_from_env(
        "LB_BODYSHOP_VISUAL_V004_PATCH_RECEIPT",
        "lineboss/audit/bodyshop/visual-readability-v004-patch/v1",
        "PASS__BODYSHOP_VISUAL_READABILITY_V004_MAP_PATCHED")

    ue_receipt_path = Path(str(hism.get("ue_receipt", ""))).resolve()
    validator_script = Path(str(hism.get("validator_script", ""))).resolve()
    if (hism.get("editor_exit_code") != 0
            or hism.get("missing_instanced_static_mesh_usage_warning_count") != 0
            or hism.get("pass_marker_count") != 1
            or hism.get("maps_materials_meshes_cgun_press_changed") is not False
            or not validator_script.is_file()
            or digest(validator_script) != hism.get("validator_script_sha256")
            or not ue_receipt_path.is_file()
            or digest(ue_receipt_path) != hism.get("ue_receipt_sha256")):
        fail("authoritative HISM summary integrity/live-log gate drift")
    ue_receipt = json.loads(ue_receipt_path.read_text(encoding="utf-8-sig"))
    protected = ue_receipt.get("protected_hashes_after", {})
    if (ue_receipt.get("$schema")
            != "lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-validation-v001/v1"
            or ue_receipt.get("status")
            != "PASS__FRESH_PROCESS_AND_LIVE_PIE_BODYSHOP_FUNCTIONAL_HISM_USAGE_V001"
            or ue_receipt.get("failures")
            or ue_receipt.get("live_pie", {}).get("passed") is not True
            or ue_receipt.get("functional_master_usage", {}).get("used_with_instanced_static_meshes") is not True
            or ue_receipt.get("protected_hashes_before") != protected
            or protected.get("body_shop_map") != MAP_SHA256_V003
            or protected.get("press_v913_map") != PRESS_SHA256
            or protected.get("cgun") != CGUN_SHA256
            or len(protected.get("materials_v002", {})) != 14
            or len(protected.get("all_9_final_meshes", {})) != 9):
        fail("linked HISM UE receipt does not bind the exact v004 pre-state")
    if (visual.get("map", {}).get("sha256") != MAP_SHA256_V003
            or visual.get("cream_material", {}).get("sha256")
            != protected.get("materials_v002", {}).get(
                "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_CreamPaint_v002")):
        fail("visual v003 receipt and HISM receipt do not share the exact pre-state")

    patch_prereqs = patch.get("prerequisites", {})
    if (patch.get("source_script_sha256") != digest(REPAIR_SCRIPT)
            or Path(str(patch.get("source_script", ""))).resolve() != REPAIR_SCRIPT.resolve()
            or patch.get("map", {}).get("sha256_before") != MAP_SHA256_V003
            or patch.get("map", {}).get("actors_added_or_removed") != 0
            or patch.get("content_packages_changed") != [MAP]
            or patch.get("materials_or_meshes_changed") != []
            or patch.get("gameplay_config_or_save_changes") != []
            or patch.get("camera_change_in_this_script") is not False
            or patch_prereqs.get("visual_v003", {}).get("sha256") != digest(visual_path)
            or patch_prereqs.get("functional_hism_validation_summary_v001", {}).get("sha256")
            != digest(hism_path)
            or patch_prereqs.get("functional_hism_validation_summary_v001", {}).get("ue_receipt_sha256")
            != digest(ue_receipt_path)):
        fail("v004 patch receipt integrity/scope/prerequisite binding drift")
    return (
        {"path": str(visual_path), "sha256": digest(visual_path)},
        {"path": str(hism_path), "sha256": digest(hism_path),
         "ue_receipt": str(ue_receipt_path), "ue_receipt_sha256": digest(ue_receipt_path)},
        {"path": str(patch_path), "sha256": digest(patch_path)},
        protected,
    )


def expected_protected_snapshot(hism_protected: dict) -> dict:
    rows = {
        str(PRESS_FILE): {"exists": True, "sha256": PRESS_SHA256},
        str(CGUN_FILE): {"exists": True, "sha256": CGUN_SHA256},
    }
    for path, expected in LEGACY_FILES.items():
        rows[str(path)] = {"exists": True, "sha256": expected}
    for path in CAMPAIGN_SAVE_CANDIDATES:
        rows[str(path)] = {"exists": False, "sha256": None}
    for asset_path, expected in hism_protected["materials_v002"].items():
        rows[str(resolve_asset_file(asset_path))] = {"exists": True, "sha256": expected}
    for asset_path, expected in hism_protected["all_9_final_meshes"].items():
        rows[str(resolve_asset_file(asset_path))] = {"exists": True, "sha256": expected}
    if len(rows) != 29:
        fail("protected inventory cardinality drift")
    return rows


def read_protected_snapshot(expected_rows: dict) -> dict:
    rows = {}
    for raw_path, contract in expected_rows.items():
        path = Path(raw_path)
        exists = path.is_file()
        actual = digest(path) if exists else None
        if exists is not contract["exists"] or actual != contract["sha256"]:
            fail("protected Press/campaign/legacy/material/mesh drift: " + raw_path)
        rows[raw_path] = {"exists": exists, "sha256": actual}
    return rows


def rect_coords(actor) -> tuple[int, int]:
    location = actor.get_actor_location()
    return int(round(float(location.x))), int(round(float(location.y)))


def validate_map_state(actors: list) -> dict:
    counts = Counter(actor.get_class().get_name() for actor in actors)
    expected_counts = {
        "CameraActor": 2,
        "DirectionalLight": 1,
        "LBBodyShopPrototypeWorldBootstrap": 1,
        "PlayerStart": 1,
        "PostProcessVolume": 1,
        "RectLight": 15,
        "SkyLight": 1,
        "StaticMeshActor": 314,
    }
    if dict(counts) != expected_counts:
        fail("Body Shop actor inventory drift: " + str(dict(counts)))
    by_label = {actor.get_actor_label(): actor for actor in actors}
    required = {"LB_BS_ENV_DirectionalLight", "LB_BS_ENV_SkyLight", "LB_BS_ENV_NeutralExposure"}
    if not required.issubset(by_label):
        fail("required saved lighting actor missing")
    active_rows = {}
    active_coords = set()
    for actor in (item for item in actors if isinstance(item, unreal.RectLight)):
        component = actor.get_component_by_class(unreal.RectLightComponent)
        if component is None:
            fail("RectLight component missing: " + actor.get_actor_label())
        coords = rect_coords(actor)
        active = coords in ACTIVE_RECT_COORDS
        intensity = round(float(component.get_editor_property("intensity")), 4)
        if (not close(intensity, TARGET_RECT_INTENSITY if active else 0.0)
                or bool(component.get_editor_property("visible")) is not active
                or bool(component.get_editor_property("hidden_in_game")) is active
                or bool(actor.get_editor_property("hidden")) is active
                or bool(component.get_editor_property("cast_shadows"))):
            fail("RectLight v004 state drift: " + actor.get_actor_label())
        if active:
            active_coords.add(coords)
            active_rows[actor.get_actor_label()] = {"coords_cm": list(coords), "intensity": intensity}
    if active_coords != ACTIVE_RECT_COORDS or len(active_rows) != 6:
        fail("exact six-light active inventory drift")
    sun = by_label["LB_BS_ENV_DirectionalLight"].get_component_by_class(unreal.DirectionalLightComponent)
    sky = by_label["LB_BS_ENV_SkyLight"].get_component_by_class(unreal.SkyLightComponent)
    settings = by_label["LB_BS_ENV_NeutralExposure"].get_editor_property("settings")
    if (sun is None or not close(sun.get_editor_property("intensity"), TARGET_DIRECTIONAL_INTENSITY)
            or not bool(sun.get_editor_property("cast_shadows"))
            or not close(sun.get_editor_property("light_source_angle"), 4.0)
            or sky is None or not close(sky.get_editor_property("intensity"), TARGET_SKY_INTENSITY)
            or not bool(settings.get_editor_property("override_auto_exposure_method"))
            or settings.get_editor_property("auto_exposure_method") != unreal.AutoExposureMethod.AEM_BASIC
            or not bool(settings.get_editor_property("override_auto_exposure_min_brightness"))
            or not bool(settings.get_editor_property("override_auto_exposure_max_brightness"))
            or not bool(settings.get_editor_property("override_auto_exposure_bias"))
            or not close(settings.get_editor_property("auto_exposure_min_brightness"), 1.0)
            or not close(settings.get_editor_property("auto_exposure_max_brightness"), 1.0)
            or not close(settings.get_editor_property("auto_exposure_bias"), TARGET_EXPOSURE_BIAS)):
        fail("directional/sky/fixed-exposure v004 contract drift")
    grid = [actor for actor in actors if "LB.BodyShop.Environment.Grid.100cm"
            in {str(tag) for tag in actor.tags}]
    if len(grid) != 272 or any(not bool(actor.get_editor_property("hidden")) for actor in grid):
        fail("runtime-hidden grid contract drift")
    return {
        "actor_count": len(actors),
        "class_counts": dict(counts),
        "active_rect_lights": active_rows,
        "directional_intensity": TARGET_DIRECTIONAL_INTENSITY,
        "sky_intensity": TARGET_SKY_INTENSITY,
        "fixed_exposure_bias": TARGET_EXPOSURE_BIAS,
        "grid_hidden_in_game_count": len(grid),
    }


def main() -> None:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    visual_gate, hism_gate, patch_gate, hism_protected = validate_prerequisite_chain()
    patch = json.loads(Path(patch_gate["path"]).read_text(encoding="utf-8-sig"))
    expected_map_hash = patch.get("map", {}).get("sha256_after")
    if not isinstance(expected_map_hash, str) or digest(MAP_FILE) != expected_map_hash:
        fail("Body Shop map is not the exact v004 patched package")
    expected_protected = expected_protected_snapshot(hism_protected)
    if patch.get("protected_hashes_before_and_after") != expected_protected:
        fail("v004 patch receipt protected inventory does not match independent HISM authority")
    protected_before = read_protected_snapshot(expected_protected)
    map_before = digest(MAP_FILE)

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        fail("could not fresh-load isolated Body Shop map")
    map_state = validate_map_state(list(actors_api.get_all_level_actors()))
    if digest(MAP_FILE) != map_before:
        fail("read-only fresh map load changed the v004 package")
    protected_after = read_protected_snapshot(expected_protected)
    if protected_after != protected_before:
        fail("protected set changed during fresh validation")

    payload = {
        "$schema": "lineboss/audit/bodyshop/visual-readability-v004-validation/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FRESH_RELOAD_BODYSHOP_VISUAL_READABILITY_V004",
        "prerequisites": {
            "visual_v003": visual_gate,
            "functional_hism_validation": hism_gate,
            "visual_v004_patch": patch_gate,
        },
        "map": {"asset": MAP, "sha256": map_before, "state": map_state},
        "cream_material": {
            "asset": "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_CreamPaint_v002",
            "sha256": hism_protected["materials_v002"][
                "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_CreamPaint_v002"],
            "unchanged_by_v004": True,
        },
        "protected_hashes": protected_after,
        "writes_to_content_source_config_or_saves": False,
        "materials_or_meshes_changed": [],
        "camera_changes_in_this_validator": [],
        "failures": [],
        "promotion_authorized": False,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_BODYSHOP_VISUAL_READABILITY_V004_VALIDATION_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
