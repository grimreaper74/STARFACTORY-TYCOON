"""Merge retained v141 powered-hook geometry into retained v180 lighting branch."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190"
HOOK_ASSET = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/PoweredCHook/Candidate_v035/SM_LB_Crane_PoweredCHook_Candidate_v035"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr003_pr004_hook_lighting_merge_build_v190.json"
PROTECTED = {
    "v124": ROOT / "Content/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124.umap",
    "v180": ROOT / "Content/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180.umap",
    "v141_hook": ROOT / "Content/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v141.umap",
    "v143_hook_proof": ROOT / "Content/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v143.umap",
}
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


hashes_before = {key: sha256(path) for key, path in PROTECTED.items()}
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create {MAP} from {BASE}")

mesh = library.load_asset(HOOK_ASSET)
if mesh is None:
    raise RuntimeError(f"missing retained hook asset {HOOK_ASSET}")
bounds = mesh.get_bounds().box_extent * 2.0
if not (382.0 <= bounds.x <= 390.0 and 119.0 <= bounds.y <= 124.0 and 273.0 <= bounds.z <= 279.0):
    raise RuntimeError(f"retained hook bounds changed: {[bounds.x, bounds.y, bounds.z]}")

old_hooks = [actor for actor in actors.get_all_level_actors()
             if "LB.Module.PoweredCHook" in {str(tag) for tag in actor.tags}
             and "LB.Crane.40T" in {str(tag) for tag in actor.tags}]
if len(old_hooks) != 1:
    raise RuntimeError(f"expected one active inherited hook, found {len(old_hooks)}")
old = old_hooks[0]
transform = old.get_actor_transform()
old.set_is_temporarily_hidden_in_editor(True)
old.set_actor_hidden_in_game(True)
old.tags = [tag for tag in old.tags if str(tag) not in {
    "LB.Motion.CHook", "LB.Animation.Pivot.CHook", "LB.Crane.40T"}]

hook = actors.spawn_actor_from_class(
    unreal.StaticMeshActor, transform.translation, transform.rotation.rotator())
hook.set_actor_label("LB_PR004_V190_40T_PoweredCHook_ManufacturerNeutral")
hook.set_actor_scale3d(transform.scale3d)
hook.tags = [unreal.Name(value) for value in (
    "LB.Motion.CHook", "LB.Animation.Pivot.CHook", "LB.Crane.40T",
    "LB.Safety.Padded", "LB.Module.PoweredCHook",
    "LB.Reference.OfficialManufacturerTypology", "LB.Capacity.TBC",
    "LB.Asset.Candidate.v190", "LB.Asset.CandidateNotPromoted",
    "LB.Integration.SourceHook.v141", "LB.Integration.SourceLighting.v180")]
hook.static_mesh_component.set_static_mesh(mesh)
hook.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
hook.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
hook.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
hook.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)

hoist = next((actor for actor in actors.get_all_level_actors()
              if actor.get_actor_label() == "LB_INT_FRONT_40T_HoistBlock"), None)
if hoist is None:
    raise RuntimeError("missing 40T hoist block")
hook_origin, hook_extent = hook.get_actor_bounds(False, False)
hoist_origin, hoist_extent = hoist.get_actor_bounds(False, False)
vertical_clearance = (hoist_origin.z - hoist_extent.z) - (hook_origin.z + hook_extent.z)
if vertical_clearance < 35.0:
    raise RuntimeError(f"hook-to-hoist visual clearance fail {vertical_clearance}")


def add_proof_camera(label, location, target, fov):
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label("LB_PR004_V190_CAM_" + label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0,
    })
    settings = camera.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": 1.25,
    })
    camera.camera_component.set_editor_property("post_process_settings", settings)
    camera.tags = [unreal.Name(value) for value in (
        "LB.Camera.Validation", "LB.Camera.Fixed.PoweredCHook.v190",
        "LB.Asset.Candidate.v190", "LB.Asset.CandidateNotPromoted")]
    return camera


cameras = [
    add_proof_camera("PoweredCHookFullSide", (-6800, -430, 1160), (-5050, -2030, 760), 43.0),
    add_proof_camera("PoweredCHookTrueBoreAxis", (-5050, 250, 760), (-5050, -2050, 750), 44.0),
    add_proof_camera("PoweredCHookLoadArmOblique", (-6550, -650, 600), (-5050, -2020, 680), 45.0),
]

failures = []
if not levels.save_current_level():
    failures.append("could not save v190")
hashes_after = {key: sha256(path) for key, path in PROTECTED.items()}
if hashes_before != hashes_after:
    failures.append("protected retained lineage changed")
payload = {
    "$schema": "cairnwell/audit/press-shop-pr003-pr004-hook-lighting-merge-build-v190/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__RETAINED_V141_HOOK_GEOMETRY_MERGED_INTO_RETAINED_V180_LIGHTING__FULL_VISUAL_AND_EXACT_REGATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V190_MERGE__NOT_PROMOTED",
    "source_map": BASE, "map": MAP,
    "hook_asset": HOOK_ASSET,
    "hook_mesh_bounds_cm": [bounds.x, bounds.y, bounds.z],
    "hook_actor": hook.get_actor_label(),
    "hook_to_hoist_vertical_clearance_cm": vertical_clearance,
    "old_v034_hook_hidden_and_unbound": True,
    "sheet2_layout_or_coil_lighting_changed": False,
    "agv_crane_navigation_or_gameplay_authority_changed": False,
    "fixed_proof_cameras": [camera.get_actor_label() for camera in cameras],
    "protected_hashes_before": hashes_before,
    "protected_hashes_after": hashes_after,
    "engineering_values": "TBC_NOT_INVENTED",
    "promotion_authorized": False,
    "press_shop_complete": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
