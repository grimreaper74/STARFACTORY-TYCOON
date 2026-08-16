"""Reveal authored robot detail slots hidden by the original material consolidation."""
from datetime import datetime, timezone
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
IMPORT = json.loads((ROOT / "Saved/Audits/pr004_unreal_import_candidate_v003.json").read_text(encoding="utf-8"))
AUDIT = ROOT / "Saved/Audits/press_shop_pr004_authored_details_candidate_v009.json"
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR004AuthoredDetailsCandidate_v009"
MAT_ROOT = "/Game/LineBoss/Stations/Press/PR004/Candidate_v009/MaterialsAuthoredDetail_v009"
MASTER = "/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003"
PREFIX = "LB_INT_PR004_V009_robot_v002_"

# Match exact authored Blender material slots. This restores intentional detail
# geometry lost during broad material-family consolidation.
DETAILS = {
    "EdgeWear": ("metal", (0.23, 0.115, 0.035, 1), .24, 7.0, .54, .25, .70, .15),
    "WarningLabel": ("nonmetal", (0.62, 0.115, 0.012, 1), .12, 6.0, .60, .15, 0.0, .08),
    "HydraulicIDBlue": ("nonmetal", (0.012, 0.115, 0.30, 1), .10, 7.0, .48, .12, 0.0, .08),
    "GreaseResidue": ("nonmetal", (0.009, 0.004, 0.0015, 1), .18, 6.0, .28, .20, 0.0, .12),
    "ServiceLabel": ("nonmetal", (0.43, 0.44, 0.41, 1), .08, 6.0, .62, .10, 0.0, .05),
}

def instance(key, spec):
    kind, tint, tex, scale, rough, rough_tex, metallic, normal = spec
    parent = unreal.load_asset(f"{MASTER}/M_LB_PR004_{'MetalPBR' if kind == 'metal' else 'NonmetalPBR'}_Master_v003")
    name = f"MI_LB_PR004_Authored_{key}_v009"
    path = f"{MAT_ROOT}/{name}"
    mi = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MAT_ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_vector_parameter_value(mi, "SurfaceTint", unreal.LinearColor(*tint))
    for p, v in (("TextureInfluence", tex), ("TextureScale", scale), ("BaseRoughness", rough), ("RoughTextureInfluence", rough_tex), ("Metallic", metallic), ("NormalStrength", normal)):
        mel.set_material_instance_scalar_parameter_value(mi, p, v)
    mel.update_material_instance(mi); unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
    return mi

lib = unreal.EditorAssetLibrary
if lib.does_asset_exist(DEST):
    raise RuntimeError(f"Candidate already exists; refusing destructive replacement: {DEST}")
if not lib.duplicate_asset(BASE, DEST): raise RuntimeError("Map duplication failed")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(DEST): raise RuntimeError("Candidate load failed")
mesh_records = {r["asset"].rsplit("/", 1)[-1].split(".", 1)[0]: r for r in IMPORT["imported_assets"] if r["family"] == "robot_v002"}
mats = {k: instance(k, v) for k, v in DETAILS.items()}
rows = []
for actor in actor_sub.get_all_level_actors():
    if not actor.get_actor_label().startswith(PREFIX): continue
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    record = mesh_records.get(comp.static_mesh.get_name()) if comp and comp.static_mesh else None
    if not record: continue
    changed = []
    for slot, assignment in enumerate(record["opaque_material_assignments"]):
        slot_name = assignment["slot"]
        match = next((key for key in DETAILS if key in slot_name), None)
        if match:
            comp.set_material(slot, mats[match]); changed.append({"slot": slot, "source_slot": slot_name, "restored_detail": match})
    rows.append({"actor": actor.get_actor_label(), "module": record["module_id"], "detail_overrides": changed})
if len(rows) != 28: raise RuntimeError(f"Expected 28 modules, found {len(rows)}")

# Audit camera derived from the known-valid PR004 close camera, not guessed
# from master-plan coordinates.
camera = actor_sub.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-5300.0, -1200.0, 470.0), unreal.Rotator())
camera.set_actor_label("LB_AUDIT_PR004_RobotAuthoredDetails_v009")
target = unreal.Vector(-4700.0, -2150.0, 155.0)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), target), False)
camera.camera_component.set_editor_property("field_of_view", 46.0)
levels.save_current_level()
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-authored-details-v009/v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CANDIDATE_NOT_PROMOTED", "base_map": BASE, "candidate_map": DEST,
    "source_geometry_preserved": True, "layout_and_pivots_preserved": True,
    "robot_modules_checked": len(rows), "detail_slot_overrides": sum(len(r["detail_overrides"]) for r in rows),
    "materials": {k: v.get_path_name() for k, v in mats.items()}, "actors": rows,
    "camera_basis": "derived from audited v006 PR004 close camera", "promotion_authorized": False,
    "visual_gate": "PENDING_FRESH_FIXED_CAMERA_REVIEW", "collision_gate": "COMPLEX_AS_SIMPLE_REMAINS_RELEASE_BLOCKER"
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PR004_AUTHORED_DETAILS_V009_PASS")
unreal.SystemLibrary.quit_editor()
