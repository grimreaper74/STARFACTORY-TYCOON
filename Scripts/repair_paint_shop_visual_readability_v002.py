"""One-shot, fail-closed Paint Shop factory-hall readability patch v002.

This script may save exactly one existing package: the isolated Paint Shop map.
It changes nine already-authored scalar lighting properties to the selected,
real-RHI calibrated option B.  It creates no actors or assets and takes a
recoverable byte-for-byte map backup before the first mutation.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
SCRIPT = ROOT / "Scripts/repair_paint_shop_visual_readability_v002.py"

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

BUILDER_SCRIPT = ROOT / "Scripts/create_paint_shop_prototype_map_v001.py"
BUILDER_SHA256 = "6922346EA0BA04C8388BA808FF22D7A1FFCC932B87AA37AEBAA52D3A26645FCA"
BASE_VALIDATOR_SCRIPT = ROOT / "Scripts/validate_paint_shop_prototype_map_v001.py"
BASE_VALIDATOR_SHA256 = "5A687A004DAD249B0BD28C2F2941FD3E5A6770D20B3D3DB25CC9A3EFBDA7CD74"
RELEASE_RUNNER_SCRIPT = ROOT / "Scripts/run_paint_shop_release_validation_v001.ps1"
RELEASE_RUNNER_SHA256 = "D1B60EA0FADF0F32B636CCEDBD0147347F3EF9685F433B6B0DEF04F8DFF517B2"
LIVE_VALIDATOR_SCRIPT = ROOT / "Scripts/validate_paint_shop_actual_player_edcoat_pie_v001.py"
LIVE_VALIDATOR_SHA256 = "CA1E5DA685F26B580C75DCBCC98C5D40E5FEC5A4DDDD655229E990B070E6747C"
CALIBRATION_SCRIPT = ROOT / "Scripts/calibrate_paint_shop_lighting_pie_v001.py"
CALIBRATION_SCRIPT_SHA256 = "9F6F6327A2369CB948CAEF6B6AB87F8FC30FB01A09EB28B49D13ED68050DB631"
FACTORY_VISUAL_STANDARD = ROOT / "Docs/LINE_BOSS_FACTORY_VISUAL_STANDARD_v001.md"
FACTORY_VISUAL_STANDARD_SHA256 = "0E61306C437BCB587C82D6BF5609CAFDA1211E004CCFC86C6C4608CBA42A2971"
V002_VALIDATOR_SCRIPT = ROOT / "Scripts/validate_paint_shop_visual_readability_v002.py"
V002_RUNNER_SCRIPT = ROOT / "Scripts/run_paint_shop_visual_readability_v002.ps1"

AUDIT = ROOT / "Saved/Audits/PaintShop/Experimental_v001/VisualReadability_v002/paint_shop_visual_readability_v002_patch.json"
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
PRE_RECT = 12000.0
TARGET_RECT = 1200.0
PRE_SUN = 0.8
TARGET_SUN = 0.3
PRE_SKY = 0.8
TARGET_SKY = 0.2
PRE_EXPOSURE = 0.0
TARGET_EXPOSURE = -0.5

EXPECTED_CLASSES = {
    "LB_PS_ENV_Floor_60m_x_40m": "StaticMeshActor",
    "LB_PS_ENV_Wall_North": "StaticMeshActor", "LB_PS_ENV_Wall_South": "StaticMeshActor",
    "LB_PS_ENV_Wall_West": "StaticMeshActor", "LB_PS_ENV_Wall_East": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_North": "StaticMeshActor", "LB_PS_ENV_EDCellBoundary_South": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_WestNorth": "StaticMeshActor", "LB_PS_ENV_EDCellBoundary_WestSouth": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_EastNorth": "StaticMeshActor", "LB_PS_ENV_EDCellBoundary_EastSouth": "StaticMeshActor",
    "LB_PS_INTERFACE_CarrierInput": "StaticMeshActor", "LB_PS_INTERFACE_CarrierOutput": "StaticMeshActor",
    "LB_PS_ENV_ServiceWalkway_North": "StaticMeshActor",
    SUN_LABEL: "DirectionalLight", SKY_LABEL: "SkyLight", EXPOSURE_LABEL: "PostProcessVolume",
    "LB_PaintShop_Prototype_PlayerStart_v001": "PlayerStart",
    "LB_PaintShop_PrototypeBootstrap_v001": "LBPaintShopPrototypeWorldBootstrap",
    "LB_PaintShop_ReviewCamera_Overview_v001": "CameraActor",
    "LB_PaintShop_ReviewCamera_EDCell_v001": "CameraActor",
    **{label: "RectLight" for label in RECT_LABELS},
}
FOUNDATION_CLASSES = {"WorldSettings", "DefaultPhysicsVolume"}


def fail(message: str) -> None:
    raise RuntimeError("PAINT_VISUAL_READABILITY_V002_REPAIR_FAIL: " + message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def load_json(path: Path, expected_hash: str, schema: str | None = None,
              status: str | None = None) -> dict:
    if not path.is_file() or digest(path) != expected_hash:
        fail("frozen authority hash drift: " + str(path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"invalid authority JSON {path}: {exc}")
    if ((schema is not None and payload.get("$schema") != schema)
            or (status is not None and payload.get("status") != status)
            or payload.get("failures")):
        fail("authority schema/status/failures drift: " + str(path))
    return payload


def require_hash(path: Path, expected: str) -> None:
    if not path.is_file() or digest(path) != expected:
        fail("frozen dependency hash drift: " + str(path))


def validate_authority_chain() -> dict:
    for path, expected in (
        (BUILDER_SCRIPT, BUILDER_SHA256), (BASE_VALIDATOR_SCRIPT, BASE_VALIDATOR_SHA256),
        (RELEASE_RUNNER_SCRIPT, RELEASE_RUNNER_SHA256), (LIVE_VALIDATOR_SCRIPT, LIVE_VALIDATOR_SHA256),
        (CALIBRATION_SCRIPT, CALIBRATION_SCRIPT_SHA256), (CALIBRATION_CAPTURE, CALIBRATION_CAPTURE_SHA256),
        (FACTORY_VISUAL_STANDARD, FACTORY_VISUAL_STANDARD_SHA256),
    ):
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
    if (create.get("map") != MAP or create.get("map_sha256") != MAP_SHA256_BEFORE
            or create.get("builder_script_sha256") != BUILDER_SHA256):
        fail("creation authority does not bind the exact pre-patch map/builder")
    if (validation.get("map") != MAP or validation.get("map_sha256") != MAP_SHA256_BEFORE
            or validation.get("creation_receipt_sha256") != CREATE_SHA256
            or validation.get("builder_script_sha256") != BUILDER_SHA256
            or validation.get("validator_script_sha256") != BASE_VALIDATOR_SHA256):
        fail("independent map validation authority binding drift")
    release_auto = release.get("automation", {})
    release_live = release.get("live_pie", {})
    if (release.get("expected_map_sha256") != MAP_SHA256_BEFORE
            or release.get("runner_script_sha256") != RELEASE_RUNNER_SHA256
            or release.get("validator_script_sha256") != LIVE_VALIDATOR_SHA256
            or release_auto.get("index_sha256") != AUTOMATION_SHA256
            or release_auto.get("failed") != 0 or release_auto.get("not_run") != 0
            or release_auto.get("in_process") != 0 or release_auto.get("exact_leaf_count") != 27
            or release_live.get("receipt_sha256") != LIVE_SHA256
            or release_live.get("map_sha256_before") != MAP_SHA256_BEFORE
            or release_live.get("map_sha256_after") != MAP_SHA256_BEFORE
            or release_live.get("map_hash_unchanged") is not True
            or release_live.get("screenshot_count") != 6):
        fail("release-validation authority binding drift")
    if (automation.get("failed") != 0 or len(release_auto.get("exact_leaf_names", [])) != 27
            or live.get("map") != MAP or live.get("map_sha256_before") != MAP_SHA256_BEFORE
            or live.get("map_sha256_after") != MAP_SHA256_BEFORE
            or live.get("map_hash_unchanged") is not True or len(live.get("screenshots", {})) != 6):
        fail("automation/live-PIE authority integrity drift")
    selected = [row for row in calibration.get("options", []) if row.get("name") == "B_stylized"]
    if (calibration.get("map_sha256_before") != MAP_SHA256_BEFORE
            or calibration.get("map_sha256_after") != MAP_SHA256_BEFORE
            or calibration.get("map_hash_unchanged") is not True or len(selected) != 1):
        fail("calibration authority pre-state/selection drift")
    option = selected[0]
    if (option.get("rect_lumens") != TARGET_RECT or option.get("sun") != TARGET_SUN
            or option.get("sky") != TARGET_SKY or option.get("exposure_bias") != TARGET_EXPOSURE
            or option.get("sha256") != CALIBRATION_CAPTURE_SHA256
            or option.get("bytes") != 2108029 or option.get("dimensions") != [1920, 1080]
            or Path(str(option.get("path", ""))).resolve() != CALIBRATION_CAPTURE):
        fail("selected calibration B values/capture drift")
    return {
        "map_creation_v001": {"path": str(CREATE_RECEIPT), "sha256": CREATE_SHA256},
        "map_validation_v001": {"path": str(VALIDATION_RECEIPT), "sha256": VALIDATION_SHA256},
        "release_validation_v001": {"path": str(RELEASE_RECEIPT), "sha256": RELEASE_SHA256},
        "live_pie_v001": {"path": str(LIVE_RECEIPT), "sha256": LIVE_SHA256},
        "automation_index": {"path": str(AUTOMATION_INDEX), "sha256": AUTOMATION_SHA256, "leaf_tests": 27},
        "lighting_calibration_v001": {"path": str(CALIBRATION_RECEIPT), "sha256": CALIBRATION_SHA256},
        "selected_capture": {"path": str(CALIBRATION_CAPTURE), "sha256": CALIBRATION_CAPTURE_SHA256,
                             "dimensions": [1920, 1080]},
        "factory_visual_standard_v001": {"path": str(FACTORY_VISUAL_STANDARD),
                                          "sha256": FACTORY_VISUAL_STANDARD_SHA256},
    }


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def protected_paths() -> list[Path]:
    paths: set[Path] = {
        PRESS_FILE, BODY_FILE, CREATE_RECEIPT, VALIDATION_RECEIPT, RELEASE_RECEIPT,
        LIVE_RECEIPT, AUTOMATION_INDEX, CALIBRATION_RECEIPT, CALIBRATION_CAPTURE,
        BUILDER_SCRIPT, BASE_VALIDATOR_SCRIPT, RELEASE_RUNNER_SCRIPT,
        LIVE_VALIDATOR_SCRIPT, CALIBRATION_SCRIPT, FACTORY_VISUAL_STANDARD,
        SCRIPT, V002_VALIDATOR_SCRIPT, V002_RUNNER_SCRIPT,
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
    for candidate in (
        ROOT / "Saved/SaveGames/LineBossCampaign_v18.sav",
        ROOT / "Saved/SaveGames/LineBoss_Campaign_v18.sav",
    ):
        key = relative(candidate)
        if candidate.exists():
            fail("protected campaign v18 save unexpectedly exists: " + key)
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
        if MAP_TAG not in {str(tag) for tag in actor.get_editor_property("tags")}:
            continue
        location, rotation, scale = actor.get_actor_location(), actor.get_actor_rotation(), actor.get_actor_scale3d()
        row = {
            "class": actor.get_class().get_name(),
            "tags": sorted(str(tag) for tag in actor.get_editor_property("tags")),
            "transform": {
                "location": [f(location.x), f(location.y), f(location.z)],
                "rotation": [f(rotation.pitch), f(rotation.yaw), f(rotation.roll)],
                "scale": [f(scale.x), f(scale.y), f(scale.z)],
            },
        }
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
                "hidden_in_game": bool(component.get_editor_property("hidden_in_game")),
            }
        elif isinstance(actor, unreal.RectLight):
            component = actor.get_component_by_class(unreal.RectLightComponent)
            row["light"] = {
                "intensity": f(component.get_editor_property("intensity")),
                "units": str(component.get_editor_property("intensity_units")),
                "attenuation_radius": f(component.get_editor_property("attenuation_radius")),
                "source_width": f(component.get_editor_property("source_width")),
                "source_height": f(component.get_editor_property("source_height")),
                "use_temperature": bool(component.get_editor_property("use_temperature")),
                "temperature": f(component.get_editor_property("temperature")),
                "cast_shadows": bool(component.get_editor_property("cast_shadows")),
                "visible": bool(component.get_editor_property("visible")),
                "hidden_in_game": bool(component.get_editor_property("hidden_in_game")),
            }
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
            row["exposure"] = {
                "unbound": bool(actor.get_editor_property("unbound")),
                "blend_weight": f(actor.get_editor_property("blend_weight")),
                "override_method": bool(settings.get_editor_property("override_auto_exposure_method")),
                "method": str(settings.get_editor_property("auto_exposure_method")),
                "override_min": bool(settings.get_editor_property("override_auto_exposure_min_brightness")),
                "override_max": bool(settings.get_editor_property("override_auto_exposure_max_brightness")),
                "min": f(settings.get_editor_property("auto_exposure_min_brightness")),
                "max": f(settings.get_editor_property("auto_exposure_max_brightness")),
                "override_bias": bool(settings.get_editor_property("override_auto_exposure_bias")),
                "bias": f(settings.get_editor_property("auto_exposure_bias")),
            }
        elif isinstance(actor, unreal.CameraActor):
            component = actor.get_editor_property("camera_component")
            row["camera"] = {"fov": f(component.get_editor_property("field_of_view")),
                             "aspect_ratio": f(component.get_editor_property("aspect_ratio")),
                             "constrain_aspect_ratio": bool(component.get_editor_property("constrain_aspect_ratio"))}
        if label in rows:
            fail("duplicate map-owned actor label: " + label)
        rows[label] = row
    return dict(sorted(rows.items()))


def validate_state(actors: list, rect: float, sun: float, sky: float, exposure: float) -> dict:
    state = semantic_snapshot(actors)
    actual_classes = {label: row["class"] for label, row in state.items()}
    if actual_classes != EXPECTED_CLASSES:
        fail("exact 27-actor Paint map inventory/class contract drift")
    for label in RECT_LABELS:
        row = state[label]
        if (LIGHT_TAG not in row["tags"] or row["light"]["intensity"] != f(rect)
                or row["light"]["units"] != str(unreal.LightUnits.LUMENS)
                or row["light"]["attenuation_radius"] != 3200.0
                or row["light"]["source_width"] != 650.0 or row["light"]["source_height"] != 160.0
                or row["light"]["use_temperature"] is not True or row["light"]["temperature"] != 5000.0):
            fail("RectLight contract drift: " + label)
    if state[SUN_LABEL]["light"]["intensity"] != f(sun) or state[SKY_LABEL]["light"]["intensity"] != f(sky):
        fail("factory-hall sun/sky contract drift")
    pp = state[EXPOSURE_LABEL]["exposure"]
    if (pp["unbound"] is not True or pp["blend_weight"] != 1.0
            or pp["override_method"] is not True or pp["method"] != str(unreal.AutoExposureMethod.AEM_BASIC)
            or pp["override_min"] is not True or pp["override_max"] is not True
            or pp["min"] != 1.0 or pp["max"] != 1.0
            or pp["override_bias"] is not True or pp["bias"] != f(exposure)):
        fail("fixed-exposure contract drift")
    nonfoundation = [actor for actor in actors if actor.get_class().get_name() not in FOUNDATION_CLASSES]
    if len(nonfoundation) != len(EXPECTED_CLASSES):
        fail("untagged/unexpected non-foundation actor exists")
    return state


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


def exact_deltas(before: dict, after: dict) -> list[dict]:
    left, right = flatten(before), flatten(after)
    if set(left) != set(right):
        fail("semantic snapshot key-set changed")
    return [{"path": key, "before": left[key], "after": right[key]}
            for key in sorted(left) if left[key] != right[key]]


def expected_deltas() -> list[dict]:
    rows = [{"path": f"{label}.light.intensity", "before": PRE_RECT, "after": TARGET_RECT}
            for label in RECT_LABELS]
    rows += [
        {"path": f"{SUN_LABEL}.light.intensity", "before": PRE_SUN, "after": TARGET_SUN},
        {"path": f"{SKY_LABEL}.light.intensity", "before": PRE_SKY, "after": TARGET_SKY},
        {"path": f"{EXPOSURE_LABEL}.exposure.bias", "before": PRE_EXPOSURE, "after": TARGET_EXPOSURE},
    ]
    return sorted(rows, key=lambda row: row["path"])


def backup_map() -> dict:
    if BACKUP_ROOT.exists():
        fail("refusing to overwrite recoverable v002 backup")
    target = BACKUP_ROOT / MAP_FILE.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=False)
    shutil.copy2(MAP_FILE, target)
    if digest(target) != MAP_SHA256_BEFORE:
        fail("recoverable backup hash mismatch")
    manifest = {
        "$schema": "lineboss/quarantine/paint-shop-visual-readability-v002-prepatch/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "RECOVERABLE_EXACT_PAINT_SHOP_V001_PREPATCH_MAP_BACKUP",
        "source": str(MAP_FILE), "backup": str(target), "sha256": MAP_SHA256_BEFORE,
        "restore_policy": "Restore only with Unreal closed and after explicit review.",
    }
    manifest_path = BACKUP_ROOT / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"map": str(target), "sha256": digest(target), "manifest": str(manifest_path),
            "manifest_sha256": digest(manifest_path)}


def patch_lighting(by_label: dict) -> None:
    for label in RECT_LABELS:
        by_label[label].get_component_by_class(unreal.RectLightComponent).set_editor_property("intensity", TARGET_RECT)
    by_label[SUN_LABEL].get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity", TARGET_SUN)
    by_label[SKY_LABEL].get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", TARGET_SKY)
    actor = by_label[EXPOSURE_LABEL]
    settings = actor.get_editor_property("settings")
    settings.set_editor_property("auto_exposure_bias", TARGET_EXPOSURE)
    actor.set_editor_property("settings", settings)


def main() -> None:
    if ROOT != EXPECTED_ROOT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    if AUDIT.exists() or BACKUP_ROOT.exists():
        fail("immutable v002 output or backup already exists")
    if not MAP_FILE.is_file() or digest(MAP_FILE) != MAP_SHA256_BEFORE:
        fail("Paint map is not the exact frozen v001 pre-state")
    authorities = validate_authority_chain()
    protected_before = protected_snapshot()
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if levels is None or actor_system is None or not levels.load_level(MAP):
        fail("could not load exact isolated Paint map")
    actors = list(actor_system.get_all_level_actors())
    before = validate_state(actors, PRE_RECT, PRE_SUN, PRE_SKY, PRE_EXPOSURE)
    backup = backup_map()
    patch_lighting({actor.get_actor_label(): actor for actor in actors})
    if not levels.save_current_level():
        fail("Paint map save failed")
    if not levels.load_level(MAP):
        fail("could not fresh-reload patched Paint map")
    after = validate_state(list(actor_system.get_all_level_actors()), TARGET_RECT, TARGET_SUN, TARGET_SKY, TARGET_EXPOSURE)
    deltas = exact_deltas(before, after)
    if deltas != expected_deltas():
        fail("actual actor-property deltas exceed the exact nine-value allowlist: " + json.dumps(deltas))
    map_after = digest(MAP_FILE)
    if map_after == MAP_SHA256_BEFORE:
        fail("expected map mutation did not persist")
    protected_after = protected_snapshot()
    if protected_after != protected_before:
        fail("protected Content/Config/Source/save snapshot changed")
    payload = {
        "$schema": "lineboss/audit/paint-shop/visual-readability-v002-patch/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__PAINT_SHOP_VISUAL_READABILITY_V002_MAP_PATCHED",
        "source_script": str(SCRIPT), "source_script_sha256": digest(SCRIPT),
        "authorities": authorities,
        "factory_hall_reference": {
            "selected_calibration": "B_stylized", "rect_lumens": TARGET_RECT,
            "fixture_temperature_kelvin": 5000.0, "directional_intensity": TARGET_SUN,
            "sky_intensity": TARGET_SKY, "fixed_exposure_bias": TARGET_EXPOSURE,
            "common_across_departments": ["fixed exposure", "5000K fixtures", "sun/sky", "material-luma targets"],
            "allowed_department_variation": ["fixture density", "local task lights"],
            "capture_acceptance": {"mean_rec709_luma": [0.35, 0.48],
                                   "black_clip_luma_le_0_01_max_fraction": 0.01,
                                   "white_clip_luma_ge_0_99_max_fraction": 0.005},
        },
        "map": {"asset": MAP, "file": str(MAP_FILE), "sha256_before": MAP_SHA256_BEFORE,
                "sha256_after": map_after, "actors_added_or_removed": 0},
        "backup": backup,
        "allowed_actor_property_deltas": expected_deltas(), "actual_actor_property_deltas": deltas,
        "semantic_state_before": before, "semantic_state_after": after,
        "protected_snapshot_before": protected_before, "protected_snapshot_after": protected_after,
        "content_packages_changed": [MAP], "source_files_changed": [], "config_files_changed": [],
        "save_files_changed": [], "materials_or_meshes_changed": [], "other_shop_maps_changed": [],
        "promotion_authorized": False, "failures": [],
    }
    if AUDIT.exists():
        fail("refusing late overwrite of immutable patch receipt")
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_PAINT_VISUAL_READABILITY_V002_PATCH_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
