"""Guarded visual-readability repair for the isolated Body Shop slice.

This one-shot patch changes exactly two existing packages:

* the Body Shop cream robot material instance, using parameter-only overrides;
* the isolated Body Shop prototype map, using existing light actors only.

It does not create/reparent materials, alter meshes, add actors, touch gameplay,
or write config/save data.  The exact pre-state is required, both changed files
are backed up under Saved, and every protected package is re-hashed afterward.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
SCRIPT = PROJECT / "Scripts/repair_body_shop_visual_readability_v003.py"

MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
MAP_SHA256_BEFORE = "F2BC85FBF6AC5B542A61D56444A6865DD3FAAF8DF1AF6E2BAE2A1C18CA9C3098"
PRESS_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
PRESS_SHA256 = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
CGUN_FILE = PROJECT / "Content/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/SpotGun/SM_LB_WeldTool_SpotGun_v001.uasset"
CGUN_SHA256 = "79DAA22563EE54BC1F3C04C98B9CAEC7E22A1F01F7E65E9E76B147B4ABBC27BC"

MATERIAL_ROOT = "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002"
CREAM = MATERIAL_ROOT + "/MI_LB_BodyShop_CreamPaint_v002"
CREAM_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_CreamPaint_v002.uasset"
CREAM_SHA256_BEFORE = "155155693B0ED97DE8D85F7C3D630EA8C9960B71D29BF3FD4703F79FF3704F0E"
LAYERED_MASTER = MATERIAL_ROOT + "/M_LB_BodyShop_LayeredPaint_Master_v002.M_LB_BodyShop_LayeredPaint_Master_v002"
CREAM_COLOUR = (0.637596874, 0.571124829, 0.381326011)

SCALARS_BEFORE = {
    "TextureScale": 18.0,
    "WearContrast": 2.45,
    "PaintCoverageBias": 0.93,
    "DustAmount": 0.035,
    "NormalStrength": 0.05,
    "BaseRoughness": 0.54,
    "RoughnessVariation": 0.28,
}
SCALARS_AFTER = {
    "TextureScale": 18.0,
    "WearContrast": 0.0,
    "PaintCoverageBias": 1.0,
    "DustAmount": 0.0,
    "NormalStrength": 0.02,
    "BaseRoughness": 0.58,
    "RoughnessVariation": 0.06,
}

# The other thirteen validated material packages must remain byte-identical.
PROTECTED_MATERIAL_HASHES = {
    "MI_LB_BodyShop_BlackMotor_v002": "F0F5DB61EB363B2987992C4774F79C530CF7D0BBC72B4792EAC2067237DB8051",
    "MI_LB_BodyShop_BrushedSteel_v002": "A0F6B3A8B9B6928484526968E0A59845571C51023091C75A98E1B6DCA80A1E44",
    "MI_LB_BodyShop_EmeraldPanel_v002": "F139E15987AA6D8807895CA490F0DEECDA1B106AFB392DC8166046A09373DE18",
    "MI_LB_BodyShop_GraphiteTooling_v002": "67B70AB8286E55A0CDD60D8B4F82C17355D66F5901AC9D6280BFC2CA0E0A91D3",
    "MI_LB_BodyShop_SafetyYellow_v002": "62538D9449AC456387B94116692A927BE6CDF93494DC109A4B9213D2288393DD",
    "MI_LB_BodyShop_ScannerLens_v002": "ABA56A12D79C0F7AD09FE1F668A2BD6BD6A5DAFEC085D69493B4C8DBB3DAEC40",
    "MI_LB_BodyShop_StatusAmber_v002": "2108F30645A41544D7C467F8E0EA43CD74379894C5DB93084D942E8310BB24FF",
    "MI_LB_BodyShop_StatusGreen_v002": "FD01422DD21BD311DBDA64E2145450DB86BABF56C4E3AFE2D6D0A5C97A6733D7",
    "MI_LB_BodyShop_StatusRed_v002": "F94C3D563424BFE79E759CD982EA2901D36EFD40762EA7973A99BD042E4CBC01",
    "MI_LB_BodyShop_StructuralLightGrey_v002": "B1609764D304E1B18E1C1131DFFF6BB03A33705AE81751720E4BBF5A7747847C",
    "MI_LB_BodyShop_VacuumRubber_v002": "BB71CFA36236CF592155C2641BE3E853CDA01A419BA1A49C79FEE2060D32D4EF",
    "M_LB_BodyShop_Functional_Master_v002": "DCC55743B2292200943113DB32E1B31867DD1372ED66C733814B455A73D5F287",
    "M_LB_BodyShop_LayeredPaint_Master_v002": "10380C5D9DD24072C90999EBF8573E5BB4A6668FC5588C8950A41FF1BD175911",
}

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
MESH_ROOT = PROJECT / "Content/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001"

CURRENT_ACTIVE_RECT_COORDS = {(-6000, -1800), (-3000, -1800), (0, -1800)}
TARGET_ACTIVE_RECT_COORDS = {
    (-6000, -1800), (-6000, 0),
    (-3000, -1800), (-3000, 0),
    (0, -1800), (0, 0),
}
CURRENT_RECT_INTENSITY = 1050.0
TARGET_RECT_INTENSITY = 2400.0
CURRENT_DIRECTIONAL_INTENSITY = 1.2
TARGET_DIRECTIONAL_INTENSITY = 0.70
CURRENT_SKY_INTENSITY = 1.1
TARGET_SKY_INTENSITY = 0.55
CURRENT_EXPOSURE_BIAS = 0.25
TARGET_EXPOSURE_BIAS = 0.0

AUDIT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/visual_readability_v003_patch.json"
FAILED_ATTEMPT_BACKUP = PROJECT / "Saved/Quarantine/BodyShop/VisualReadability_v003_PrePatch"
BACKUP_ROOT = PROJECT / "Saved/Quarantine/BodyShop/VisualReadability_v003_PrePatch_Retry1"

lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_VISUAL_READABILITY_V003_REPAIR_FAIL: " + message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def close(actual: float, expected: float, tolerance: float = 0.0002) -> bool:
    return abs(float(actual) - float(expected)) <= tolerance


def colour_close(actual, expected) -> bool:
    return all(close(value, target) for value, target in
               zip((actual.r, actual.g, actual.b), expected))


def material_file(name: str) -> Path:
    return PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002" / (name + ".uasset")


def rect_coords(actor) -> tuple[int, int]:
    location = actor.get_actor_location()
    return int(round(float(location.x))), int(round(float(location.y)))


def read_scalars(instance, names) -> dict[str, float]:
    return {name: round(float(mel.get_material_instance_scalar_parameter_value(instance, name)), 6)
            for name in names}


def assert_protected_hashes() -> dict:
    rows = {}
    if digest(PRESS_FILE) != PRESS_SHA256:
        fail("Press Shop v913 hash drift")
    if digest(CGUN_FILE) != CGUN_SHA256:
        fail("protected C-gun hash drift")
    rows["press_v913"] = PRESS_SHA256
    rows["cgun"] = CGUN_SHA256
    for name, expected in PROTECTED_MATERIAL_HASHES.items():
        path = material_file(name)
        if not path.is_file() or digest(path) != expected:
            fail("protected material hash drift: " + name)
        rows["material:" + name] = expected
    for relative, expected in PROTECTED_MESH_HASHES.items():
        path = (MESH_ROOT / relative).with_suffix(".uasset")
        if not path.is_file() or digest(path) != expected:
            fail("protected mesh hash drift: " + relative)
        rows["mesh:" + relative] = expected
    return rows


def require_map_pre_state(actors: list) -> None:
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
        fail("required lighting actor missing")
    rects = [actor for actor in actors if isinstance(actor, unreal.RectLight)]
    active = set()
    for actor in rects:
        component = actor.get_component_by_class(unreal.RectLightComponent)
        coords = rect_coords(actor)
        if component is None:
            fail("RectLight component missing: " + actor.get_actor_label())
        intensity = float(component.get_editor_property("intensity"))
        visible = bool(component.get_editor_property("visible"))
        hidden = bool(component.get_editor_property("hidden_in_game"))
        actor_hidden = bool(actor.get_editor_property("hidden"))
        is_active = coords in CURRENT_ACTIVE_RECT_COORDS
        if (not close(intensity, CURRENT_RECT_INTENSITY if is_active else 0.0)
                or visible is not is_active or hidden is is_active or actor_hidden is is_active
                or bool(component.get_editor_property("cast_shadows"))):
            fail("RectLight pre-state drift: " + actor.get_actor_label())
        if is_active:
            active.add(coords)
    if active != CURRENT_ACTIVE_RECT_COORDS:
        fail("active RectLight pre-state inventory drift")
    sun = by_label["LB_BS_ENV_DirectionalLight"].get_component_by_class(unreal.DirectionalLightComponent)
    sky = by_label["LB_BS_ENV_SkyLight"].get_component_by_class(unreal.SkyLightComponent)
    settings = by_label["LB_BS_ENV_NeutralExposure"].get_editor_property("settings")
    if (sun is None or not close(sun.get_editor_property("intensity"), CURRENT_DIRECTIONAL_INTENSITY)
            or sky is None or not close(sky.get_editor_property("intensity"), CURRENT_SKY_INTENSITY)
            or not close(settings.get_editor_property("auto_exposure_bias"), CURRENT_EXPOSURE_BIAS)
            or not close(settings.get_editor_property("auto_exposure_min_brightness"), 1.0)
            or not close(settings.get_editor_property("auto_exposure_max_brightness"), 1.0)):
        fail("directional/sky/exposure pre-state drift")


def patch_map(actors: list) -> None:
    by_label = {actor.get_actor_label(): actor for actor in actors}
    for actor in (item for item in actors if isinstance(item, unreal.RectLight)):
        component = actor.get_component_by_class(unreal.RectLightComponent)
        active = rect_coords(actor) in TARGET_ACTIVE_RECT_COORDS
        component.set_intensity(TARGET_RECT_INTENSITY if active else 0.0)
        component.set_visibility(active, True)
        component.set_hidden_in_game(not active, True)
        component.set_cast_shadows(False)
        actor.set_actor_hidden_in_game(not active)
    sun = by_label["LB_BS_ENV_DirectionalLight"].get_component_by_class(unreal.DirectionalLightComponent)
    sky = by_label["LB_BS_ENV_SkyLight"].get_component_by_class(unreal.SkyLightComponent)
    sun.set_editor_property("intensity", TARGET_DIRECTIONAL_INTENSITY)
    sky.set_editor_property("intensity", TARGET_SKY_INTENSITY)
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


def assert_map_post_state(actors: list) -> dict:
    by_label = {actor.get_actor_label(): actor for actor in actors}
    active_rows = {}
    for actor in (item for item in actors if isinstance(item, unreal.RectLight)):
        component = actor.get_component_by_class(unreal.RectLightComponent)
        coords = rect_coords(actor)
        active = coords in TARGET_ACTIVE_RECT_COORDS
        intensity = round(float(component.get_editor_property("intensity")), 4)
        if (not close(intensity, TARGET_RECT_INTENSITY if active else 0.0)
                or bool(component.get_editor_property("visible")) is not active
                or bool(component.get_editor_property("hidden_in_game")) is active
                or bool(actor.get_editor_property("hidden")) is active
                or bool(component.get_editor_property("cast_shadows"))):
            fail("RectLight post-state drift: " + actor.get_actor_label())
        if active:
            active_rows[actor.get_actor_label()] = {"coords_cm": list(coords), "intensity": intensity}
    if len(active_rows) != len(TARGET_ACTIVE_RECT_COORDS):
        fail("active RectLight post-state count drift")
    sun = by_label["LB_BS_ENV_DirectionalLight"].get_component_by_class(unreal.DirectionalLightComponent)
    sky = by_label["LB_BS_ENV_SkyLight"].get_component_by_class(unreal.SkyLightComponent)
    settings = by_label["LB_BS_ENV_NeutralExposure"].get_editor_property("settings")
    if (not close(sun.get_editor_property("intensity"), TARGET_DIRECTIONAL_INTENSITY)
            or not close(sky.get_editor_property("intensity"), TARGET_SKY_INTENSITY)
            or not close(settings.get_editor_property("auto_exposure_bias"), TARGET_EXPOSURE_BIAS)):
        fail("directional/sky/exposure post-state drift")
    return {
        "active_rect_lights": active_rows,
        "directional_intensity": TARGET_DIRECTIONAL_INTENSITY,
        "sky_intensity": TARGET_SKY_INTENSITY,
        "fixed_exposure_bias": TARGET_EXPOSURE_BIAS,
    }


def backup_changed_files() -> dict:
    if BACKUP_ROOT.exists():
        fail("refusing to overwrite recoverable visual-readability backup")
    records = {}
    for source in (CREAM_FILE, MAP_FILE):
        target = BACKUP_ROOT / source.relative_to(PROJECT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if digest(source) != digest(target):
            fail("backup hash mismatch: " + str(source))
        records[str(source)] = {"backup": str(target), "sha256": digest(target)}
    manifest = {
        "$schema": "lineboss/quarantine/bodyshop-visual-readability-v003-prepatch/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "RECOVERABLE_EXACT_PREPATCH_BACKUP",
        "files": records,
        "restore_policy": "Restore only with Unreal closed and after explicit review.",
    }
    manifest_path = BACKUP_ROOT / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    records["manifest"] = {"path": str(manifest_path), "sha256": digest(manifest_path)}
    return records


def main() -> None:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    if AUDIT.exists() or BACKUP_ROOT.exists():
        fail("visual-readability v003 output already exists")
    if digest(MAP_FILE) != MAP_SHA256_BEFORE or digest(CREAM_FILE) != CREAM_SHA256_BEFORE:
        fail("map or cream material is not the exact validated pre-state")
    protected_before = assert_protected_hashes()

    cream = lib.load_asset(CREAM)
    if not isinstance(cream, unreal.MaterialInstanceConstant):
        fail("cream MIC missing")
    parent = cream.get_editor_property("parent")
    if parent is None or parent.get_path_name() != LAYERED_MASTER:
        fail("cream MIC parent drift")
    if not colour_close(mel.get_material_instance_vector_parameter_value(cream, "PaintColour"), CREAM_COLOUR):
        fail("cream colour drift")
    before_scalars = read_scalars(cream, SCALARS_BEFORE)
    if any(not close(before_scalars[name], expected) for name, expected in SCALARS_BEFORE.items()):
        fail("cream parameter pre-state drift: " + str(before_scalars))

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        fail("could not load isolated Body Shop map")
    actors = list(actors_api.get_all_level_actors())
    require_map_pre_state(actors)
    backups = backup_changed_files()

    for name, value in SCALARS_AFTER.items():
        changed = mel.set_material_instance_scalar_parameter_value(cream, name, float(value))
        # UE returns false for a valid no-op (TextureScale deliberately remains
        # 18).  Fail only when the call neither changed nor achieved the value.
        readback = mel.get_material_instance_scalar_parameter_value(cream, name)
        if not changed and not close(readback, value):
            fail("could not set cream scalar: " + name)
    mel.update_material_instance(cream)
    if not lib.save_loaded_asset(cream, only_if_is_dirty=False):
        fail("cream MIC save failed")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

    patch_map(actors)
    if not levels.save_current_level():
        fail("isolated Body Shop map save failed")

    after_scalars = read_scalars(cream, SCALARS_AFTER)
    if any(not close(after_scalars[name], expected) for name, expected in SCALARS_AFTER.items()):
        fail("cream parameter post-state drift: " + str(after_scalars))
    lighting = assert_map_post_state(list(actors_api.get_all_level_actors()))
    if digest(CREAM_FILE) == CREAM_SHA256_BEFORE or digest(MAP_FILE) == MAP_SHA256_BEFORE:
        fail("expected cream/map package mutation did not persist")
    protected_after = assert_protected_hashes()
    if protected_after != protected_before:
        fail("protected package set changed")

    payload = {
        "$schema": "lineboss/audit/bodyshop/visual-readability-v003-patch/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__BODYSHOP_VISUAL_READABILITY_V003_PATCHED",
        "source_script": str(SCRIPT),
        "source_script_sha256": digest(SCRIPT),
        "diagnosis": {
            "cream": "generic paint-chip colour breakup was too coarse/noisy on per-link UV islands",
            "hall": "three-lamp lane plus high global fill produced hot floor bands and weak depth",
        },
        "cream_material": {
            "asset": CREAM,
            "parent_unchanged": LAYERED_MASTER,
            "paint_colour_unchanged_linear": list(CREAM_COLOUR),
            "sha256_before": CREAM_SHA256_BEFORE,
            "sha256_after": digest(CREAM_FILE),
            "scalars_before": before_scalars,
            "scalars_after": after_scalars,
        },
        "map": {
            "asset": MAP,
            "sha256_before": MAP_SHA256_BEFORE,
            "sha256_after": digest(MAP_FILE),
            "lighting": lighting,
            "actors_added_or_removed": 0,
        },
        "protected_hashes_before_and_after": protected_after,
        "recoverable_backup": backups,
        "retained_failed_attempt_backup": str(FAILED_ATTEMPT_BACKUP),
        "content_packages_changed": [CREAM, MAP],
        "meshes_changed": [],
        "gameplay_config_or_save_changes": [],
        "camera_changes": [],
        "failures": [],
        "promotion_authorized": False,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_BODYSHOP_VISUAL_READABILITY_V003_PATCH_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
