"""Build a non-destructive, authored mothballed PR-004 robot candidate."""

from datetime import datetime, timezone
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
IMPORT_AUDIT = ROOT / "Saved/Audits/pr004_unreal_import_candidate_v003.json"
AUDIT = ROOT / "Saved/Audits/press_shop_pr004_mothballed_candidate_v008.json"
BASE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
DEST_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004MothballedCandidate_v008b"
DEST_MATS = "/Game/LineBoss/Stations/Press/PR004/Candidate_v009/MaterialsMothballed_v008"
MASTER = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003"
PREFIX = "LB_INT_PR004_V009_robot_v002_"

# These are deliberately readable at the close management camera. The variation
# is by functional module, not random noise, so the machine still reads as one asset.
PALETTES = {
    "lower": {
        "SafetyYellow": ((0.43, 0.205, 0.018, 1), .43, 5.5, .73, .42, 0.0, .24),
        "CastIron": ((0.025, 0.034, 0.040, 1), .38, 6.0, .71, .38, .72, .24),
        "MachinedSteel": ((0.23, 0.255, 0.27, 1), .28, 7.0, .46, .30, .86, .18),
    },
    "upper": {
        "SafetyYellow": ((0.55, 0.285, 0.026, 1), .34, 5.0, .67, .36, 0.0, .20),
        "CastIron": ((0.037, 0.047, 0.052, 1), .30, 6.5, .65, .32, .68, .20),
        "MachinedSteel": ((0.30, 0.33, 0.35, 1), .22, 7.5, .39, .24, .92, .15),
    },
    "service": {
        "SafetyYellow": ((0.49, 0.245, 0.020, 1), .38, 5.0, .70, .40, 0.0, .22),
        "CastIron": ((0.030, 0.039, 0.044, 1), .34, 6.0, .68, .36, .70, .22),
        "MachinedSteel": ((0.26, 0.285, 0.30, 1), .25, 7.0, .43, .28, .89, .17),
    },
}
COMMON = {
    "MachineDark": ((0.018, 0.024, 0.029, 1), .30, 6.0, .74, .34, .42, .20),
    "Rubber": ((0.008, 0.010, 0.012, 1), .16, 7.0, .88, .18, 0.0, .10),
    "HoseCable": ((0.008, 0.011, 0.014, 1), .18, 7.5, .80, .20, 0.0, .11),
    "GreaseResidue": ((0.010, 0.006, 0.003, 1), .34, 5.0, .30, .30, 0.0, .18),
    "ServiceLabel": ((0.33, 0.34, 0.33, 1), .16, 5.0, .76, .18, 0.0, .10),
    "WarningRed": ((0.34, 0.010, 0.006, 1), .24, 5.5, .67, .26, 0.0, .14),
    "ReadyGreen": ((0.018, 0.25, 0.05, 1), .18, 6.0, .61, .20, 0.0, .10),
    "SensorBlue": ((0.018, 0.095, 0.20, 1), .17, 6.0, .49, .18, .12, .09),
    "OpaqueSensorLens": ((0.012, 0.035, 0.060, 1), .10, 5.0, .38, .14, 0.0, .05),
}

LOWER = {"base", "j1", "j2", "dress_lower"}
SERVICE = {"tool_rack", "band_tool", "wrap_tool", "edge_tool", "inspection_tool",
           "band_left_capture", "band_right_capture", "band_cutter", "band_roll_left",
           "band_roll_right", "wrap_vacuum_carrier", "wrap_peel_roll", "edge_left_jaw",
           "edge_right_jaw", "inspection_bore_camera", "inspection_shutter"}

def make_mi(name, key, values):
    tint, tex, scale, rough, rough_tex, metallic, normal = values
    parent_kind = "MetalPBR" if key in {"SafetyYellow", "CastIron", "MachinedSteel", "MachineDark", "WarningRed", "ReadyGreen", "SensorBlue"} else "NonmetalPBR"
    parent = unreal.load_asset(f"{MASTER}/M_LB_PR004_{parent_kind}_Master_v003")
    path = f"{DEST_MATS}/{name}"
    mi = unreal.EditorAssetLibrary.load_asset(path)
    if mi is None:
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, DEST_MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_vector_parameter_value(mi, "SurfaceTint", unreal.LinearColor(*tint))
    for p, v in (("TextureInfluence", tex), ("TextureScale", scale), ("BaseRoughness", rough),
                 ("RoughTextureInfluence", rough_tex), ("Metallic", metallic), ("NormalStrength", normal)):
        mel.set_material_instance_scalar_parameter_value(mi, p, v)
    mel.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
    return mi

library = unreal.EditorAssetLibrary
if library.does_asset_exist(DEST_MAP):
    library.delete_asset(DEST_MAP)
if not library.duplicate_asset(BASE_MAP, DEST_MAP):
    raise RuntimeError("Could not duplicate v006 baseline")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(DEST_MAP):
    raise RuntimeError("Could not load v008 candidate")

source = json.loads(IMPORT_AUDIT.read_text(encoding="utf-8"))
records_by_mesh = {r["asset"].rsplit("/", 1)[-1].split(".", 1)[0]: r for r in source["imported_assets"] if r["family"] == "robot_v002"}
cache = {}
changed = []
for actor in actors.get_all_level_actors():
    if not actor.get_actor_label().startswith(PREFIX):
        continue
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    record = records_by_mesh.get(comp.static_mesh.get_name()) if comp and comp.static_mesh else None
    if not record:
        continue
    module = record["module_id"]
    zone = "lower" if module in LOWER else ("service" if module in SERVICE else "upper")
    applied = []
    for slot, assignment in enumerate(record["opaque_material_assignments"]):
        key = assignment["material_key"]
        values = PALETTES[zone].get(key, COMMON.get(key))
        if values is None:
            continue
        cache_key = (zone if key in PALETTES[zone] else "common", key)
        if cache_key not in cache:
            cache[cache_key] = make_mi(f"MI_LB_PR004_Mothballed_{cache_key[0]}_{key}_v008", key, values)
        comp.set_material(slot, cache[cache_key])
        applied.append({"slot": slot, "surface": key, "variant": cache_key[0]})
    changed.append({"actor": actor.get_actor_label(), "module": module, "condition_zone": zone, "assignments": applied})

if len(changed) != 28:
    raise RuntimeError(f"Expected 28 robot modules, found {len(changed)}")

# Retain the gameplay camera; add a fixed audit-only camera that can actually
# resolve the authored robot modules. It is excluded from normal play.
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(3750.0, 5480.0, 410.0), unreal.Rotator())
camera.set_actor_label("LB_AUDIT_PR004_RobotCondition_Close_v008")
target = unreal.Vector(4010.0, 5960.0, 170.0)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), target), False)
camera.camera_component.set_editor_property("field_of_view", 42.0)
levels.save_current_level()

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-mothballed-v008/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CONDITION_CANDIDATE_NOT_PROMOTED",
    "base_map": BASE_MAP, "candidate_map": DEST_MAP,
    "source_geometry_preserved": True, "layout_and_pivots_preserved": True,
    "robot_modules_conditioned": len(changed), "condition_material_count": len(cache),
    "audit_camera": camera.get_actor_label(), "actors": changed,
    "collision_gate": "SOURCE_COMPLEX_AS_SIMPLE_REMAINS_RELEASE_BLOCKER",
    "promotion_authorized": False, "visual_gate": "PENDING_FIXED_CAMERA_REVIEW"
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_MOTHBALLED_V008_PASS modules={len(changed)} materials={len(cache)}")
unreal.SystemLibrary.quit_editor()
