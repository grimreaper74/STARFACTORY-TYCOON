"""Independent fresh-process validator for Paint readability v002.

This file intentionally does not import the repair implementation.  It binds
the frozen v001/release/calibration chain, immutable v002 patch receipt and
recoverable pre-patch backup, then performs a read-only fresh map load.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
SCRIPT = ROOT / "Scripts/validate_paint_shop_visual_readability_v002.py"
REPAIR_SCRIPT = ROOT / "Scripts/repair_paint_shop_visual_readability_v002.py"
REPAIR_SCRIPT_SHA256 = "2EA599FD11F804738943E39FABE6EFEBDD22830D773441E972B7AC7BEC7B7D10"

MAP = "/Game/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001"
MAP_FILE = ROOT / "Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap"
MAP_SHA256_BEFORE = "2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069"
PRESS_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
PRESS_SHA256 = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
BODY_FILE = ROOT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
BODY_SHA256 = "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F"

CREATE_RECEIPT = ROOT / "Saved/Audits/PaintShop/Experimental_v001/paint_shop_prototype_map_create_v001.json"
CREATE_SHA256 = "4E65E671CB25D8615F3A775B1697E7D72C523D58FFA7481356A5BF8D5941AC09"
VALIDATION_RECEIPT = ROOT / "Saved/Audits/PaintShop/Experimental_v001/paint_shop_prototype_map_validation_v001.json"
VALIDATION_SHA256 = "B452A68FF04B89BF6D6FD43486230692C05B1338368794570174150DFC90F136"
RELEASE_RECEIPT = ROOT / "Saved/Audits/PaintShop/Experimental_v001/ReleaseValidation/20260814T174958518Z/release_validation_summary_v001.json"
RELEASE_SHA256 = "660546CB5ABECB16A59C716F4D69DDAAE0DA143F70AA2685C43B9A4DB71AE1CB"
LIVE_RECEIPT = ROOT / "Saved/Audits/PaintShop/Experimental_v001/ReleaseValidation/20260814T174958518Z/live_pie_edcoat_validation_v001.json"
LIVE_SHA256 = "8E01A7635D968C95A89B8F8371129869D5BC8BF8DE20F05C86396437E571E4D4"
AUTOMATION_INDEX = ROOT / "Saved/Automation/PaintShop/Experimental_v001/ReleaseValidation_20260814T174958518Z/index.json"
AUTOMATION_SHA256 = "D9AB9A52221848CB9E7A75745F231A738A1EA2FA2F885EF9B717ED6B9A2B33BE"
CALIBRATION_RECEIPT = ROOT / "Saved/Audits/PaintShop/Experimental_v001/LightingCalibration_v001/20260814T175521Z/lighting_calibration_v001.json"
CALIBRATION_SHA256 = "1F287DD1D0758F37DD94F83737922B4282836E2BAB6506C27EED190E4117D766"
CALIBRATION_CAPTURE = ROOT / "Saved/Audits/PaintShop/Experimental_v001/LightingCalibration_v001/20260814T175521Z/02_B_stylized.png"
CALIBRATION_CAPTURE_SHA256 = "463F90CA7BA45EF45F4A0F594FBE429088813752CF3545976FBB7FB230041E58"
FACTORY_VISUAL_STANDARD = ROOT / "Docs/LINE_BOSS_FACTORY_VISUAL_STANDARD_v001.md"
FACTORY_VISUAL_STANDARD_SHA256 = "0E61306C437BCB587C82D6BF5609CAFDA1211E004CCFC86C6C4608CBA42A2971"
V002_RUNNER_SCRIPT = ROOT / "Scripts/run_paint_shop_visual_readability_v002.ps1"
FROZEN_DEPENDENCIES = {
    ROOT / "Scripts/create_paint_shop_prototype_map_v001.py":
        "6922346EA0BA04C8388BA808FF22D7A1FFCC932B87AA37AEBAA52D3A26645FCA",
    ROOT / "Scripts/validate_paint_shop_prototype_map_v001.py":
        "5A687A004DAD249B0BD28C2F2941FD3E5A6770D20B3D3DB25CC9A3EFBDA7CD74",
    ROOT / "Scripts/run_paint_shop_release_validation_v001.ps1":
        "D1B60EA0FADF0F32B636CCEDBD0147347F3EF9685F433B6B0DEF04F8DFF517B2",
    ROOT / "Scripts/validate_paint_shop_actual_player_edcoat_pie_v001.py":
        "CA1E5DA685F26B580C75DCBCC98C5D40E5FEC5A4DDDD655229E990B070E6747C",
    ROOT / "Scripts/calibrate_paint_shop_lighting_pie_v001.py":
        "9F6F6327A2369CB948CAEF6B6AB87F8FC30FB01A09EB28B49D13ED68050DB631",
}

PATCH_RECEIPT = ROOT / "Saved/Audits/PaintShop/Experimental_v001/VisualReadability_v002/paint_shop_visual_readability_v002_patch.json"
AUDIT = ROOT / "Saved/Audits/PaintShop/Experimental_v001/VisualReadability_v002/paint_shop_visual_readability_v002_validation.json"
BACKUP_ROOT = ROOT / "Saved/Quarantine/PaintShop/VisualReadability_v002_PrePatch"

MAP_TAG = "LB.PaintShop.Experimental.v001"
LIGHT_TAG = "LB.PaintShop.Environment.Lighting"
RECT_LABELS = (
    "LB_PS_ENV_Light_-1500_-850", "LB_PS_ENV_Light_-1500_+850",
    "LB_PS_ENV_Light_+0000_-850", "LB_PS_ENV_Light_+0000_+850",
    "LB_PS_ENV_Light_+1500_-850", "LB_PS_ENV_Light_+1500_+850",
)
SUN_LABEL = "LB_PS_ENV_DirectionalLight"
SKY_LABEL = "LB_PS_ENV_SkyLight"
EXPOSURE_LABEL = "LB_PS_ENV_NeutralExposure"
TARGET_RECT, TARGET_SUN, TARGET_SKY, TARGET_EXPOSURE = 1200.0, 0.3, 0.2, -0.5
EXPECTED_CLASSES = {
    "LB_PS_ENV_Floor_60m_x_40m": "StaticMeshActor",
    "LB_PS_ENV_Wall_North": "StaticMeshActor", "LB_PS_ENV_Wall_South": "StaticMeshActor",
    "LB_PS_ENV_Wall_West": "StaticMeshActor", "LB_PS_ENV_Wall_East": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_North": "StaticMeshActor", "LB_PS_ENV_EDCellBoundary_South": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_WestNorth": "StaticMeshActor", "LB_PS_ENV_EDCellBoundary_WestSouth": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_EastNorth": "StaticMeshActor", "LB_PS_ENV_EDCellBoundary_EastSouth": "StaticMeshActor",
    "LB_PS_INTERFACE_CarrierInput": "StaticMeshActor", "LB_PS_INTERFACE_CarrierOutput": "StaticMeshActor",
    "LB_PS_ENV_ServiceWalkway_North": "StaticMeshActor", SUN_LABEL: "DirectionalLight",
    SKY_LABEL: "SkyLight", EXPOSURE_LABEL: "PostProcessVolume",
    "LB_PaintShop_Prototype_PlayerStart_v001": "PlayerStart",
    "LB_PaintShop_PrototypeBootstrap_v001": "LBPaintShopPrototypeWorldBootstrap",
    "LB_PaintShop_ReviewCamera_Overview_v001": "CameraActor",
    "LB_PaintShop_ReviewCamera_EDCell_v001": "CameraActor",
    **{label: "RectLight" for label in RECT_LABELS},
}
FOUNDATION_CLASSES = {"WorldSettings", "DefaultPhysicsVolume"}


def fail(message: str) -> None:
    raise RuntimeError("PAINT_VISUAL_READABILITY_V002_VALIDATION_FAIL: " + message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def load_json(path: Path, expected_hash: str | None = None,
              schema: str | None = None, status: str | None = None) -> dict:
    if not path.is_file() or (expected_hash is not None and digest(path) != expected_hash):
        fail("missing or hash-drifted authority: " + str(path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"invalid JSON {path}: {exc}")
    if ((schema is not None and payload.get("$schema") != schema)
            or (status is not None and payload.get("status") != status)
            or payload.get("failures")):
        fail("schema/status/failures drift: " + str(path))
    return payload


def require_hash(path: Path, expected: str) -> None:
    if not path.is_file() or digest(path) != expected:
        fail("frozen hash drift: " + str(path))


def validate_frozen_authorities() -> dict:
    for path, expected in (
        (CREATE_RECEIPT, CREATE_SHA256), (VALIDATION_RECEIPT, VALIDATION_SHA256),
        (RELEASE_RECEIPT, RELEASE_SHA256), (LIVE_RECEIPT, LIVE_SHA256),
        (AUTOMATION_INDEX, AUTOMATION_SHA256), (CALIBRATION_RECEIPT, CALIBRATION_SHA256),
        (CALIBRATION_CAPTURE, CALIBRATION_CAPTURE_SHA256),
        (FACTORY_VISUAL_STANDARD, FACTORY_VISUAL_STANDARD_SHA256),
    ):
        require_hash(path, expected)
    for path, expected in FROZEN_DEPENDENCIES.items():
        require_hash(path, expected)
    create = load_json(CREATE_RECEIPT, CREATE_SHA256,
        "lineboss/audit/paint-shop/prototype-map-create-v001/v1",
        "PASS__ISOLATED_PAINT_SHOP_ONE_BOOTSTRAP_ZERO_MAP_OWNED_PRODUCTION")
    validation = load_json(VALIDATION_RECEIPT, VALIDATION_SHA256,
        "lineboss/audit/paint-shop/prototype-map-validation-v001/v1",
        "PASS__FRESH_RELOAD_PAINT_SHOP_PROTOTYPE_MAP_V001")
    release = load_json(RELEASE_RECEIPT, RELEASE_SHA256,
        "lineboss/audit/paint-shop/release-validation-run-v001/v1",
        "PASS__PAINT_SHOP_AUTOMATION_AND_ACTUAL_PLAYER_ED_COAT_PIE_V001")
    live = load_json(LIVE_RECEIPT, LIVE_SHA256,
        "lineboss/audit/paint-shop/actual-player-edcoat-pie-v001/v1",
        "PASS__PAINT_SHOP_ACTUAL_PLAYER_ED_COAT_PIE_V001")
    calibration = load_json(CALIBRATION_RECEIPT, CALIBRATION_SHA256,
        "lineboss/audit/paint-shop/lighting-calibration-v001/v1",
        "PASS__TRANSIENT_PAINT_SHOP_LIGHTING_CALIBRATION_V001")
    automation = load_json(AUTOMATION_INDEX, AUTOMATION_SHA256)
    option = [row for row in calibration.get("options", []) if row.get("name") == "B_stylized"]
    if (create.get("map_sha256") != MAP_SHA256_BEFORE
            or validation.get("map_sha256") != MAP_SHA256_BEFORE
            or validation.get("creation_receipt_sha256") != CREATE_SHA256
            or release.get("expected_map_sha256") != MAP_SHA256_BEFORE
            or release.get("automation", {}).get("index_sha256") != AUTOMATION_SHA256
            or release.get("automation", {}).get("failed") != 0
            or release.get("automation", {}).get("exact_leaf_count") != 27
            or release.get("live_pie", {}).get("receipt_sha256") != LIVE_SHA256
            or live.get("map_sha256_before") != MAP_SHA256_BEFORE
            or live.get("map_sha256_after") != MAP_SHA256_BEFORE
            or live.get("map_hash_unchanged") is not True or automation.get("failed") != 0
            or calibration.get("map_sha256_before") != MAP_SHA256_BEFORE
            or calibration.get("map_sha256_after") != MAP_SHA256_BEFORE
            or calibration.get("map_hash_unchanged") is not True or len(option) != 1
            or {key: option[0].get(key) for key in ("rect_lumens", "sun", "sky", "exposure_bias", "sha256")}
            != {"rect_lumens": TARGET_RECT, "sun": TARGET_SUN, "sky": TARGET_SKY,
                "exposure_bias": TARGET_EXPOSURE, "sha256": CALIBRATION_CAPTURE_SHA256}):
        fail("frozen authority semantic binding drift")
    return {"creation": CREATE_SHA256, "validation": VALIDATION_SHA256,
            "release": RELEASE_SHA256, "live_pie": LIVE_SHA256,
            "automation_index": AUTOMATION_SHA256, "calibration": CALIBRATION_SHA256,
            "factory_visual_standard": FACTORY_VISUAL_STANDARD_SHA256}


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def protected_paths() -> list[Path]:
    paths: set[Path] = {
        PRESS_FILE, BODY_FILE, CREATE_RECEIPT, VALIDATION_RECEIPT, RELEASE_RECEIPT,
        LIVE_RECEIPT, AUTOMATION_INDEX, CALIBRATION_RECEIPT, CALIBRATION_CAPTURE,
        FACTORY_VISUAL_STANDARD, REPAIR_SCRIPT, SCRIPT, V002_RUNNER_SCRIPT,
        ROOT / "Scripts/create_paint_shop_prototype_map_v001.py",
        ROOT / "Scripts/validate_paint_shop_prototype_map_v001.py",
        ROOT / "Scripts/run_paint_shop_release_validation_v001.ps1",
        ROOT / "Scripts/validate_paint_shop_actual_player_edcoat_pie_v001.py",
        ROOT / "Scripts/calibrate_paint_shop_lighting_pie_v001.py",
    }
    for base in (ROOT / "Config", ROOT / "Source"):
        if base.exists():
            paths.update(path for path in base.rglob("*") if path.is_file())
    saved = ROOT / "Saved"
    if saved.exists():
        paths.update(saved.rglob("*.sav"))
    for base in (ROOT / "Content/LineBoss/PaintShop", ROOT / "Content/LineBoss/Candidates/PaintShop"):
        if base.exists():
            paths.update(path for path in base.rglob("*") if path.is_file() and path.resolve() != MAP_FILE)
    return sorted(path.resolve() for path in paths)


def protected_snapshot() -> dict:
    require_hash(PRESS_FILE, PRESS_SHA256)
    require_hash(BODY_FILE, BODY_SHA256)
    rows = {relative(path): {"exists": True, "bytes": path.stat().st_size, "sha256": digest(path)}
            for path in protected_paths()}
    for candidate in (ROOT / "Saved/SaveGames/LineBossCampaign_v18.sav",
                      ROOT / "Saved/SaveGames/LineBoss_Campaign_v18.sav"):
        key = relative(candidate)
        if candidate.exists():
            fail("campaign v18 save unexpectedly exists: " + key)
        rows[key] = {"exists": False, "bytes": None, "sha256": None}
    return dict(sorted(rows.items()))


def f(value: float) -> float:
    return round(float(value), 5)


def object_path(value) -> str | None:
    return value.get_path_name() if value is not None else None


def semantic_snapshot(actors: list) -> dict:
    rows = {}
    for actor in actors:
        label = actor.get_actor_label()
        tags = sorted(str(tag) for tag in actor.get_editor_property("tags"))
        if MAP_TAG not in tags:
            continue
        location, rotation, scale = actor.get_actor_location(), actor.get_actor_rotation(), actor.get_actor_scale3d()
        row = {"class": actor.get_class().get_name(), "tags": tags,
               "transform": {"location": [f(location.x), f(location.y), f(location.z)],
                             "rotation": [f(rotation.pitch), f(rotation.yaw), f(rotation.roll)],
                             "scale": [f(scale.x), f(scale.y), f(scale.z)]}}
        if isinstance(actor, unreal.StaticMeshActor):
            component = actor.get_editor_property("static_mesh_component")
            row["static_mesh"] = {
                "mesh": object_path(component.get_editor_property("static_mesh")),
                "material_0": object_path(component.get_material(0)),
                "collision": str(component.get_collision_enabled()),
                "collision_profile": str(component.get_collision_profile_name()),
                "navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
                "cast_shadows": bool(component.get_editor_property("cast_shadow")),
                "visible": bool(component.get_editor_property("visible")),
                "hidden_in_game": bool(component.get_editor_property("hidden_in_game"))}
        elif isinstance(actor, unreal.RectLight):
            component = actor.get_component_by_class(unreal.RectLightComponent)
            row["light"] = {"intensity": f(component.get_editor_property("intensity")),
                            "units": str(component.get_editor_property("intensity_units")),
                            "attenuation_radius": f(component.get_editor_property("attenuation_radius")),
                            "source_width": f(component.get_editor_property("source_width")),
                            "source_height": f(component.get_editor_property("source_height")),
                            "use_temperature": bool(component.get_editor_property("use_temperature")),
                            "temperature": f(component.get_editor_property("temperature")),
                            "cast_shadows": bool(component.get_editor_property("cast_shadows")),
                            "visible": bool(component.get_editor_property("visible")),
                            "hidden_in_game": bool(component.get_editor_property("hidden_in_game"))}
        elif isinstance(actor, unreal.DirectionalLight):
            component = actor.get_component_by_class(unreal.DirectionalLightComponent)
            row["light"] = {"intensity": f(component.get_editor_property("intensity")),
                            "cast_shadows": bool(component.get_editor_property("cast_shadows"))}
        elif isinstance(actor, unreal.SkyLight):
            component = actor.get_component_by_class(unreal.SkyLightComponent)
            row["light"] = {"intensity": f(component.get_editor_property("intensity")),
                            "visible": bool(component.get_editor_property("visible"))}
        elif isinstance(actor, unreal.PostProcessVolume):
            settings = actor.get_editor_property("settings")
            row["exposure"] = {"unbound": bool(actor.get_editor_property("unbound")),
                "blend_weight": f(actor.get_editor_property("blend_weight")),
                "override_method": bool(settings.get_editor_property("override_auto_exposure_method")),
                "method": str(settings.get_editor_property("auto_exposure_method")),
                "override_min": bool(settings.get_editor_property("override_auto_exposure_min_brightness")),
                "override_max": bool(settings.get_editor_property("override_auto_exposure_max_brightness")),
                "min": f(settings.get_editor_property("auto_exposure_min_brightness")),
                "max": f(settings.get_editor_property("auto_exposure_max_brightness")),
                "override_bias": bool(settings.get_editor_property("override_auto_exposure_bias")),
                "bias": f(settings.get_editor_property("auto_exposure_bias"))}
        elif isinstance(actor, unreal.CameraActor):
            component = actor.get_editor_property("camera_component")
            row["camera"] = {"fov": f(component.get_editor_property("field_of_view")),
                             "aspect_ratio": f(component.get_editor_property("aspect_ratio")),
                             "constrain_aspect_ratio": bool(component.get_editor_property("constrain_aspect_ratio"))}
        if label in rows:
            fail("duplicate map-owned label: " + label)
        rows[label] = row
    return dict(sorted(rows.items()))


def validate_target_state(actors: list) -> dict:
    state = semantic_snapshot(actors)
    if {label: row["class"] for label, row in state.items()} != EXPECTED_CLASSES:
        fail("exact 27-actor Paint inventory/class contract drift")
    nonfoundation = [actor for actor in actors if actor.get_class().get_name() not in FOUNDATION_CLASSES]
    if len(nonfoundation) != len(EXPECTED_CLASSES):
        fail("untagged/unexpected non-foundation actor exists")
    for label in RECT_LABELS:
        row = state[label]
        if (LIGHT_TAG not in row["tags"] or row["light"]["intensity"] != TARGET_RECT
                or row["light"]["units"] != str(unreal.LightUnits.LUMENS)
                or row["light"]["attenuation_radius"] != 3200.0
                or row["light"]["source_width"] != 650.0 or row["light"]["source_height"] != 160.0
                or row["light"]["use_temperature"] is not True or row["light"]["temperature"] != 5000.0):
            fail("target RectLight contract drift: " + label)
    pp = state[EXPOSURE_LABEL]["exposure"]
    if (state[SUN_LABEL]["light"]["intensity"] != TARGET_SUN
            or state[SKY_LABEL]["light"]["intensity"] != TARGET_SKY
            or pp["unbound"] is not True or pp["blend_weight"] != 1.0
            or pp["override_method"] is not True or pp["method"] != str(unreal.AutoExposureMethod.AEM_BASIC)
            or pp["override_min"] is not True or pp["override_max"] is not True
            or pp["min"] != 1.0 or pp["max"] != 1.0
            or pp["override_bias"] is not True or pp["bias"] != TARGET_EXPOSURE):
        fail("target common factory-hall sun/sky/fixed-exposure contract drift")
    return state


def expected_deltas() -> list[dict]:
    rows = [{"path": f"{label}.light.intensity", "before": 12000.0, "after": TARGET_RECT}
            for label in RECT_LABELS]
    rows += [{"path": f"{SUN_LABEL}.light.intensity", "before": 0.8, "after": TARGET_SUN},
             {"path": f"{SKY_LABEL}.light.intensity", "before": 0.8, "after": TARGET_SKY},
             {"path": f"{EXPOSURE_LABEL}.exposure.bias", "before": 0.0, "after": TARGET_EXPOSURE}]
    return sorted(rows, key=lambda row: row["path"])


def flatten(value, prefix: str = "") -> dict:
    if isinstance(value, dict):
        output = {}
        for key in sorted(value):
            output.update(flatten(value[key], f"{prefix}.{key}" if prefix else str(key)))
        return output
    if isinstance(value, list):
        output = {}
        for index, item in enumerate(value):
            output.update(flatten(item, f"{prefix}[{index}]"))
        return output
    return {prefix: value}


def receipt_semantic_deltas(before: dict, after: dict) -> list[dict]:
    left, right = flatten(before), flatten(after)
    if set(left) != set(right):
        fail("patch semantic snapshot key-set changed")
    return [{"path": key, "before": left[key], "after": right[key]}
            for key in sorted(left) if left[key] != right[key]]


def validate_patch_and_backup() -> tuple[dict, dict]:
    require_hash(REPAIR_SCRIPT, REPAIR_SCRIPT_SHA256)
    patch = load_json(PATCH_RECEIPT, None,
        "lineboss/audit/paint-shop/visual-readability-v002-patch/v1",
        "PASS__PAINT_SHOP_VISUAL_READABILITY_V002_MAP_PATCHED")
    if (Path(str(patch.get("source_script", ""))).resolve() != REPAIR_SCRIPT
            or patch.get("source_script_sha256") != REPAIR_SCRIPT_SHA256
            or patch.get("map", {}).get("asset") != MAP
            or patch.get("map", {}).get("sha256_before") != MAP_SHA256_BEFORE
            or patch.get("map", {}).get("actors_added_or_removed") != 0
            or patch.get("allowed_actor_property_deltas") != expected_deltas()
            or patch.get("actual_actor_property_deltas") != expected_deltas()
            or patch.get("content_packages_changed") != [MAP]
            or patch.get("source_files_changed") != [] or patch.get("config_files_changed") != []
            or patch.get("save_files_changed") != [] or patch.get("materials_or_meshes_changed") != []
            or patch.get("other_shop_maps_changed") != [] or patch.get("promotion_authorized") is not False
            or patch.get("protected_snapshot_before") != patch.get("protected_snapshot_after")):
        fail("patch receipt scope/integrity binding drift")
    before_state = patch.get("semantic_state_before")
    after_state = patch.get("semantic_state_after")
    if (not isinstance(before_state, dict) or not isinstance(after_state, dict)
            or {label: row.get("class") for label, row in before_state.items()} != EXPECTED_CLASSES
            or {label: row.get("class") for label, row in after_state.items()} != EXPECTED_CLASSES
            or receipt_semantic_deltas(before_state, after_state) != expected_deltas()):
        fail("patch semantic snapshots do not independently prove the exact nine-property delta")
    reference = patch.get("factory_hall_reference", {})
    if (reference.get("selected_calibration") != "B_stylized"
            or reference.get("rect_lumens") != TARGET_RECT
            or reference.get("fixture_temperature_kelvin") != 5000.0
            or reference.get("directional_intensity") != TARGET_SUN
            or reference.get("sky_intensity") != TARGET_SKY
            or reference.get("fixed_exposure_bias") != TARGET_EXPOSURE
            or reference.get("common_across_departments")
            != ["fixed exposure", "5000K fixtures", "sun/sky", "material-luma targets"]
            or reference.get("allowed_department_variation") != ["fixture density", "local task lights"]):
        fail("shared factory-hall reference binding drift")
    expected_authorities = {"map_creation_v001": CREATE_SHA256,
        "map_validation_v001": VALIDATION_SHA256, "release_validation_v001": RELEASE_SHA256,
        "live_pie_v001": LIVE_SHA256, "automation_index": AUTOMATION_SHA256,
        "lighting_calibration_v001": CALIBRATION_SHA256,
        "selected_capture": CALIBRATION_CAPTURE_SHA256,
        "factory_visual_standard_v001": FACTORY_VISUAL_STANDARD_SHA256}
    for key, expected in expected_authorities.items():
        if patch.get("authorities", {}).get(key, {}).get("sha256") != expected:
            fail("patch authority binding drift: " + key)
    backup = patch.get("backup", {})
    backup_map = Path(str(backup.get("map", ""))).resolve()
    manifest_path = Path(str(backup.get("manifest", ""))).resolve()
    expected_backup = (BACKUP_ROOT / MAP_FILE.relative_to(ROOT)).resolve()
    if (backup_map != expected_backup or not backup_map.is_file() or digest(backup_map) != MAP_SHA256_BEFORE
            or backup.get("sha256") != MAP_SHA256_BEFORE or not manifest_path.is_file()
            or digest(manifest_path) != backup.get("manifest_sha256")):
        fail("recoverable pre-patch backup binding drift")
    manifest = load_json(manifest_path)
    if (manifest.get("$schema") != "lineboss/quarantine/paint-shop-visual-readability-v002-prepatch/v1"
            or manifest.get("status") != "RECOVERABLE_EXACT_PAINT_SHOP_V001_PREPATCH_MAP_BACKUP"
            or Path(str(manifest.get("backup", ""))).resolve() != expected_backup
            or manifest.get("sha256") != MAP_SHA256_BEFORE):
        fail("recoverable backup manifest contract drift")
    return patch, {"path": str(PATCH_RECEIPT), "sha256": digest(PATCH_RECEIPT)}


def main() -> None:
    if ROOT != EXPECTED_ROOT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    if AUDIT.exists():
        fail("refusing to overwrite immutable v002 validation receipt")
    authorities = validate_frozen_authorities()
    patch, patch_gate = validate_patch_and_backup()
    expected_map_hash = patch.get("map", {}).get("sha256_after")
    if not isinstance(expected_map_hash, str) or not MAP_FILE.is_file() or digest(MAP_FILE) != expected_map_hash:
        fail("current Paint map is not the exact v002 patched package")
    current_protected = protected_snapshot()
    if current_protected != patch.get("protected_snapshot_after"):
        fail("current protected snapshot differs from the patch receipt")
    map_before = digest(MAP_FILE)
    protected_before = protected_snapshot()
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if levels is None or actor_system is None or not levels.load_level(MAP):
        fail("could not independently fresh-load exact Paint map")
    state = validate_target_state(list(actor_system.get_all_level_actors()))
    if state != patch.get("semantic_state_after"):
        fail("fresh semantic state differs from patch receipt")
    if digest(MAP_FILE) != map_before:
        fail("read-only fresh load changed the Paint map package")
    protected_after = protected_snapshot()
    if protected_after != protected_before:
        fail("protected set changed during independent validation")
    payload = {
        "$schema": "lineboss/audit/paint-shop/visual-readability-v002-validation/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FRESH_RELOAD_PAINT_SHOP_VISUAL_READABILITY_V002",
        "validator_script": str(SCRIPT), "validator_script_sha256": digest(SCRIPT),
        "repair_script": str(REPAIR_SCRIPT), "repair_script_sha256": REPAIR_SCRIPT_SHA256,
        "frozen_authorities": authorities, "patch_receipt": patch_gate,
        "map": {"asset": MAP, "file": str(MAP_FILE), "sha256": map_before,
                "semantic_state": state, "read_only_load_hash_unchanged": True},
        "backup": patch.get("backup"), "protected_snapshot": protected_after,
        "writes_to_content_source_config_or_saves": False, "other_shop_maps_changed": [],
        "promotion_authorized": False, "failures": [],
    }
    if AUDIT.exists():
        fail("refusing late overwrite of immutable validation receipt")
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_PAINT_VISUAL_READABILITY_V002_VALIDATION_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
