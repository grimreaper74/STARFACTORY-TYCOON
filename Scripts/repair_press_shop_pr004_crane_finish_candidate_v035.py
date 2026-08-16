"""Repair v035 imported label-slot remap and add a clear management camera."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFinishCandidate_v035"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_finish_repair_v035.json"
PAPER = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v026/M_LB_CoilLabelPaper_v026"
LABEL = "LB_PR004_V035_CAM_CraneManagementSouthInteriorClear"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
paper = lib.load_asset(PAPER)
if paper is None:
    raise RuntimeError(f"Missing {PAPER}")

repaired = []
for actor in actors.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or "SM_LB_MasterCoil_Candidate_v004" not in mesh.get_path_name():
            continue
        # FBX join/remap placed portions of fixed label geometry in both the
        # nominal paper and ink slots. One controlled paper material across
        # both slots makes the physical panels blank for live Cairnwell text.
        component.set_material(8, paper)
        component.set_material(9, paper)
        repaired.append(f"{actor.get_actor_label()}:{component.get_name()}")
if len(repaired) != 15:
    raise RuntimeError(f"Expected 15 packaged components, found {len(repaired)}")

for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label() == LABEL:
        actors.destroy_actor(actor)
camera = actors.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(-4300.0, 430.0, 900.0), unreal.Rotator())
camera.set_actor_label(LABEL)
camera.tags = [unreal.Name(value) for value in (
    "LB.Camera.Validation", "LB.Camera.Fixed.PR004Crane.v035",
    "LB.Asset.Candidate.v035", "LB.Asset.CandidateNotPromoted")]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(-6200.0, -2650.0, 1180.0)), False)
component = camera.camera_component
component.set_editor_properties({"field_of_view": 70.0, "aspect_ratio": 16.0 / 9.0,
                                 "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
settings = component.get_editor_property("post_process_settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": -0.08,
})
component.set_editor_property("post_process_settings", settings)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-finish-repair-v035/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "IMPORTED_LABEL_SLOT_AND_CLEAR_CAMERA_REPAIR_BUILT__REGATES_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "repaired_package_component_count": len(repaired),
    "blanked_material_slots": [8, 9],
    "fixed_camera": LABEL,
    "primary_crane_geometry_changed": False,
    "support_crane_park_state_changed": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_V035_REPAIR_PASS coils={len(repaired)} camera={LABEL}")
unreal.SystemLibrary.quit_editor()
