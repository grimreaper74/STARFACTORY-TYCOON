"""Guarded one-shot lighting repair for Body Shop readability v004.

The only Content package this script may change is the isolated Body Shop map.
It reuses the existing fifteen RectLights, keeps exactly six active, and changes
only their enabled state/intensity plus the existing directional, sky and fixed
exposure values.  It requires explicitly supplied v003 and functional-HISM
receipts and fails closed on every protected package/source/save invariant.

Required process environment variables:
  LB_BODYSHOP_VISUAL_V003_RECEIPT
  LB_BODYSHOP_HISM_VALIDATION_SUMMARY
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
SCRIPT = PROJECT / "Scripts/repair_body_shop_visual_readability_v004.py"

MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
MAP_SHA256_BEFORE = "9766E686B5AA2B0F006C54CA4E578C37944A1CE4CE99C41F4EC3DFC009894D0A"
PRESS_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
PRESS_SHA256 = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
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
CGUN_FILE = PROJECT / "Content/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/SpotGun/SM_LB_WeldTool_SpotGun_v001.uasset"
CGUN_SHA256 = "79DAA22563EE54BC1F3C04C98B9CAEC7E22A1F01F7E65E9E76B147B4ABBC27BC"

MATERIAL_DIR = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002"
PROTECTED_MATERIAL_HASHES = {
    "M_LB_BodyShop_Functional_Master_v002": "F04868806F50DAEF5D1792649E7CCB0DFEC4D5333F340A8D6E6B8A65097EC82B",
    "M_LB_BodyShop_LayeredPaint_Master_v002": "10380C5D9DD24072C90999EBF8573E5BB4A6668FC5588C8950A41FF1BD175911",
    "MI_LB_BodyShop_BlackMotor_v002": "F0F5DB61EB363B2987992C4774F79C530CF7D0BBC72B4792EAC2067237DB8051",
    "MI_LB_BodyShop_BrushedSteel_v002": "A0F6B3A8B9B6928484526968E0A59845571C51023091C75A98E1B6DCA80A1E44",
    "MI_LB_BodyShop_CreamPaint_v002": "7FEAC6A1ED633AA6FB36D09BA74F144CD194FC5C60E11E189068E0C761509E25",
    "MI_LB_BodyShop_EmeraldPanel_v002": "F139E15987AA6D8807895CA490F0DEECDA1B106AFB392DC8166046A09373DE18",
    "MI_LB_BodyShop_GraphiteTooling_v002": "67B70AB8286E55A0CDD60D8B4F82C17355D66F5901AC9D6280BFC2CA0E0A91D3",
    "MI_LB_BodyShop_SafetyYellow_v002": "62538D9449AC456387B94116692A927BE6CDF93494DC109A4B9213D2288393DD",
    "MI_LB_BodyShop_ScannerLens_v002": "ABA56A12D79C0F7AD09FE1F668A2BD6BD6A5DAFEC085D69493B4C8DBB3DAEC40",
    "MI_LB_BodyShop_StatusAmber_v002": "2108F30645A41544D7C467F8E0EA43CD74379894C5DB93084D942E8310BB24FF",
    "MI_LB_BodyShop_StatusGreen_v002": "FD01422DD21BD311DBDA64E2145450DB86BABF56C4E3AFE2D6D0A5C97A6733D7",
    "MI_LB_BodyShop_StatusRed_v002": "F94C3D563424BFE79E759CD982EA2901D36EFD40762EA7973A99BD042E4CBC01",
    "MI_LB_BodyShop_StructuralLightGrey_v002": "B1609764D304E1B18E1C1131DFFF6BB03A33705AE81751720E4BBF5A7747847C",
    "MI_LB_BodyShop_VacuumRubber_v002": "BB71CFA36236CF592155C2641BE3E853CDA01A419BA1A49C79FEE2060D32D4EF",
}
MESH_ROOT = PROJECT / "Content/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001"
PROTECTED_MESH_HASHES = {
    "Fixture/SM_LB_BodyShop_UnderbodyFixture_v001": "262AB2C8F5289465DB3547BEA11DFCB072721C4A931E6EC81E9723CE2483BDAE",
    "Robot/SM_LB_BodyShopRobot_Base_v001": "9CBE6D27268C7B942F7271546B5EC678C063C7CFEE35BE6B7DE0F017FFC3FBB0",
    "Robot/SM_LB_BodyShopRobot_J1_v001": "4B81E41A999BCA1081EBDBE5FAAB76D4D5B19ECBC820FAD0D1B8B0C36D31E2E4",
    "Robot/SM_LB_BodyShopRobot_J2_v001": "D4607CB5481E2CC8B7FF23921DE202CCE80676057213653DF8BF2C4730CFB15F",
    "Robot/SM_LB_BodyShopRobot_J3_v001": "CE96B0591EFB8ABE3944658AA3A2ECF97E844B30C66C3ED49FE36B844AD6EE8A",
    "Robot/SM_LB_BodyShopRobot_J4_v001": "EC6CBF9447DB73AFF82B4ACB184BF9F663480DD48DF4F461B85C4E258070826D",
    "Robot/SM_LB_BodyShopRobot_J5_v001": "1C5A3E3F3411F066B4AB5A4B63738A63A2CC7D30916F246C193496DA5E40C534",
    "Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001": "61BF706DF4306873381566A56A0EDD9C1B1A0E7949A07C5928AE79A4F58657A2",
    "Vision/SM_LB_BodyShop_VisionGate_v001": "53D7443AA524CCF655AFA82BCD9C3950D9C559EA2F41D93E10309B74B0563C71",
}

ACTIVE_RECT_COORDS = {
    (-6000, -1800), (-6000, 0),
    (-3000, -1800), (-3000, 0),
    (0, -1800), (0, 0),
}
PRE_RECT_INTENSITY = 2400.0
TARGET_RECT_INTENSITY = 525.0
PRE_DIRECTIONAL_INTENSITY = 0.70
TARGET_DIRECTIONAL_INTENSITY = 0.80
PRE_SKY_INTENSITY = 0.55
TARGET_SKY_INTENSITY = 0.80
TARGET_EXPOSURE_BIAS = 0.0

AUDIT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/visual_readability_v004_patch.json"
BACKUP_ROOT = PROJECT / "Saved/Quarantine/BodyShop/VisualReadability_v004_PrePatch"


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_VISUAL_READABILITY_V004_REPAIR_FAIL: " + message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def close(actual: float, expected: float, tolerance: float = 0.0002) -> bool:
    return abs(float(actual) - float(expected)) <= tolerance


def required_receipt(env_name: str, schema: str, status: str) -> tuple[Path, dict]:
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


def validate_prerequisites() -> dict:
    visual_path, visual = required_receipt(
        "LB_BODYSHOP_VISUAL_V003_RECEIPT",
        "lineboss/audit/bodyshop/visual-readability-v003-validation/v1",
        "PASS__FRESH_RELOAD_BODYSHOP_VISUAL_READABILITY_V003")
    hism_path, hism = required_receipt(
        "LB_BODYSHOP_HISM_VALIDATION_SUMMARY",
        "lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-validation-summary-v001/v1",
        "PASS__FRESH_LIVE_PIE_LOG_HAS_NO_INSTANCED_STATIC_MESH_USAGE_WARNINGS")
    if (visual.get("map", {}).get("sha256") != MAP_SHA256_BEFORE
            or visual.get("cream_material", {}).get("sha256")
            != PROTECTED_MATERIAL_HASHES["MI_LB_BodyShop_CreamPaint_v002"]):
        fail("v003 receipt does not bind the exact v004 map/material pre-state")
    validator_script = Path(str(hism.get("validator_script", ""))).resolve()
    ue_receipt_path = Path(str(hism.get("ue_receipt", ""))).resolve()
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
    expected_receipt_materials = {
        "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/" + name: value
        for name, value in PROTECTED_MATERIAL_HASHES.items()
    }
    expected_receipt_meshes = {
        "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/" + name: value
        for name, value in PROTECTED_MESH_HASHES.items()
    }
    if (ue_receipt.get("$schema")
            != "lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-validation-v001/v1"
            or ue_receipt.get("status")
            != "PASS__FRESH_PROCESS_AND_LIVE_PIE_BODYSHOP_FUNCTIONAL_HISM_USAGE_V001"
            or ue_receipt.get("failures")
            or ue_receipt.get("live_pie", {}).get("passed") is not True
            or ue_receipt.get("functional_master_usage", {}).get("used_with_instanced_static_meshes") is not True
            or ue_receipt.get("functional_master_usage", {}).get("sha256")
            != PROTECTED_MATERIAL_HASHES["M_LB_BodyShop_Functional_Master_v002"]
            or ue_receipt.get("protected_hashes_before") != protected
            or protected.get("body_shop_map") != MAP_SHA256_BEFORE
            or protected.get("press_v913_map") != PRESS_SHA256
            or protected.get("cgun") != CGUN_SHA256
            or protected.get("materials_v002") != expected_receipt_materials
            or protected.get("all_9_final_meshes") != expected_receipt_meshes):
        fail("linked HISM UE receipt does not bind the exact v004 material/map pre-state")
    return {
        "visual_v003": {"path": str(visual_path), "sha256": digest(visual_path)},
        "functional_hism_validation_summary_v001": {
            "path": str(hism_path), "sha256": digest(hism_path),
            "ue_receipt": str(ue_receipt_path), "ue_receipt_sha256": digest(ue_receipt_path),
        },
    }


def protected_snapshot() -> dict:
    rows = {}
    fixed = {PRESS_FILE: PRESS_SHA256, CGUN_FILE: CGUN_SHA256, **LEGACY_FILES}
    for path, expected in fixed.items():
        if not path.is_file() or digest(path) != expected:
            fail("protected file hash drift: " + str(path))
        rows[str(path)] = {"exists": True, "sha256": expected}
    for path in CAMPAIGN_SAVE_CANDIDATES:
        if path.exists():
            fail("protected campaign v18 save unexpectedly exists: " + str(path))
        rows[str(path)] = {"exists": False, "sha256": None}
    for name, expected in PROTECTED_MATERIAL_HASHES.items():
        path = MATERIAL_DIR / (name + ".uasset")
        if not path.is_file() or digest(path) != expected:
            fail("protected material hash drift: " + name)
        rows[str(path)] = {"exists": True, "sha256": expected}
    for relative, expected in PROTECTED_MESH_HASHES.items():
        path = (MESH_ROOT / relative).with_suffix(".uasset")
        if not path.is_file() or digest(path) != expected:
            fail("protected mesh hash drift: " + relative)
        rows[str(path)] = {"exists": True, "sha256": expected}
    return rows


def rect_coords(actor) -> tuple[int, int]:
    location = actor.get_actor_location()
    return int(round(float(location.x))), int(round(float(location.y)))


def validate_map_state(actors: list, rect_intensity: float,
                       directional_intensity: float, sky_intensity: float) -> dict:
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
        if (not close(intensity, rect_intensity if active else 0.0)
                or bool(component.get_editor_property("visible")) is not active
                or bool(component.get_editor_property("hidden_in_game")) is active
                or bool(actor.get_editor_property("hidden")) is active
                or bool(component.get_editor_property("cast_shadows"))):
            fail("RectLight saved-state drift: " + actor.get_actor_label())
        if active:
            active_coords.add(coords)
            active_rows[actor.get_actor_label()] = {"coords_cm": list(coords), "intensity": intensity}
    if active_coords != ACTIVE_RECT_COORDS or len(active_rows) != 6:
        fail("exact six-light active inventory drift")
    sun = by_label["LB_BS_ENV_DirectionalLight"].get_component_by_class(unreal.DirectionalLightComponent)
    sky = by_label["LB_BS_ENV_SkyLight"].get_component_by_class(unreal.SkyLightComponent)
    settings = by_label["LB_BS_ENV_NeutralExposure"].get_editor_property("settings")
    if (sun is None or not close(sun.get_editor_property("intensity"), directional_intensity)
            or not bool(sun.get_editor_property("cast_shadows"))
            or not close(sun.get_editor_property("light_source_angle"), 4.0)
            or sky is None or not close(sky.get_editor_property("intensity"), sky_intensity)
            or not bool(settings.get_editor_property("override_auto_exposure_method"))
            or settings.get_editor_property("auto_exposure_method") != unreal.AutoExposureMethod.AEM_BASIC
            or not bool(settings.get_editor_property("override_auto_exposure_min_brightness"))
            or not bool(settings.get_editor_property("override_auto_exposure_max_brightness"))
            or not bool(settings.get_editor_property("override_auto_exposure_bias"))
            or not close(settings.get_editor_property("auto_exposure_min_brightness"), 1.0)
            or not close(settings.get_editor_property("auto_exposure_max_brightness"), 1.0)
            or not close(settings.get_editor_property("auto_exposure_bias"), TARGET_EXPOSURE_BIAS)):
        fail("directional/sky/fixed-exposure contract drift")
    grid = [actor for actor in actors if "LB.BodyShop.Environment.Grid.100cm"
            in {str(tag) for tag in actor.tags}]
    if len(grid) != 272 or any(not bool(actor.get_editor_property("hidden")) for actor in grid):
        fail("runtime-hidden grid contract drift")
    return {
        "actor_count": len(actors),
        "class_counts": dict(counts),
        "active_rect_lights": active_rows,
        "directional_intensity": directional_intensity,
        "sky_intensity": sky_intensity,
        "fixed_exposure_bias": TARGET_EXPOSURE_BIAS,
        "grid_hidden_in_game_count": len(grid),
    }


def backup_map() -> dict:
    if BACKUP_ROOT.exists():
        fail("refusing to overwrite recoverable v004 pre-patch backup")
    target = BACKUP_ROOT / MAP_FILE.relative_to(PROJECT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MAP_FILE, target)
    if digest(target) != MAP_SHA256_BEFORE:
        fail("recoverable map backup hash mismatch")
    manifest = {
        "$schema": "lineboss/quarantine/bodyshop-visual-readability-v004-prepatch/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "RECOVERABLE_EXACT_V003_MAP_BACKUP",
        "source": str(MAP_FILE),
        "backup": str(target),
        "sha256": MAP_SHA256_BEFORE,
        "restore_policy": "Restore only with Unreal closed and after explicit review.",
    }
    manifest_path = BACKUP_ROOT / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"map": str(target), "sha256": digest(target),
            "manifest": str(manifest_path), "manifest_sha256": digest(manifest_path)}


def patch_existing_lighting(actors: list) -> None:
    by_label = {actor.get_actor_label(): actor for actor in actors}
    for actor in (item for item in actors if isinstance(item, unreal.RectLight)):
        component = actor.get_component_by_class(unreal.RectLightComponent)
        active = rect_coords(actor) in ACTIVE_RECT_COORDS
        component.set_intensity(TARGET_RECT_INTENSITY if active else 0.0)
        component.set_visibility(active, True)
        component.set_hidden_in_game(not active, True)
        component.set_cast_shadows(False)
        actor.set_actor_hidden_in_game(not active)
    by_label["LB_BS_ENV_DirectionalLight"].get_component_by_class(
        unreal.DirectionalLightComponent).set_editor_property("intensity", TARGET_DIRECTIONAL_INTENSITY)
    by_label["LB_BS_ENV_SkyLight"].get_component_by_class(
        unreal.SkyLightComponent).set_editor_property("intensity", TARGET_SKY_INTENSITY)
    exposure = by_label["LB_BS_ENV_NeutralExposure"]
    settings = exposure.get_editor_property("settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": TARGET_EXPOSURE_BIAS,
    })
    exposure.set_editor_property("settings", settings)


def main() -> None:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    if AUDIT.exists() or BACKUP_ROOT.exists():
        fail("v004 one-shot output or backup already exists")
    prerequisites = validate_prerequisites()
    if not MAP_FILE.is_file() or digest(MAP_FILE) != MAP_SHA256_BEFORE:
        fail("Body Shop map is not the exact independently validated v003/HISM pre-state")
    protected_before = protected_snapshot()

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        fail("could not load isolated Body Shop map")
    actors = list(actors_api.get_all_level_actors())
    before_state = validate_map_state(
        actors, PRE_RECT_INTENSITY, PRE_DIRECTIONAL_INTENSITY, PRE_SKY_INTENSITY)
    backup = backup_map()
    patch_existing_lighting(actors)
    if not levels.save_current_level():
        fail("isolated Body Shop map save failed")
    after_state = validate_map_state(
        list(actors_api.get_all_level_actors()), TARGET_RECT_INTENSITY,
        TARGET_DIRECTIONAL_INTENSITY, TARGET_SKY_INTENSITY)
    map_after = digest(MAP_FILE)
    if map_after == MAP_SHA256_BEFORE:
        fail("expected v004 map mutation did not persist")
    protected_after = protected_snapshot()
    if protected_after != protected_before:
        fail("protected Press/campaign/legacy/material/mesh set changed")

    payload = {
        "$schema": "lineboss/audit/bodyshop/visual-readability-v004-patch/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__BODYSHOP_VISUAL_READABILITY_V004_MAP_PATCHED",
        "source_script": str(SCRIPT),
        "source_script_sha256": digest(SCRIPT),
        "prerequisites": prerequisites,
        "map": {
            "asset": MAP,
            "sha256_before": MAP_SHA256_BEFORE,
            "sha256_after": map_after,
            "state_before": before_state,
            "state_after": after_state,
            "actors_added_or_removed": 0,
        },
        "recoverable_backup": backup,
        "protected_hashes_before_and_after": protected_after,
        "content_packages_changed": [MAP],
        "materials_or_meshes_changed": [],
        "gameplay_config_or_save_changes": [],
        "camera_change_in_this_script": False,
        "failures": [],
        "promotion_authorized": False,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_BODYSHOP_VISUAL_READABILITY_V004_MAP_PATCH_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
