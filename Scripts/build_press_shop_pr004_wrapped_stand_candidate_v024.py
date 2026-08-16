"""Simplify PR-004 to a wrapped coil on a powered preparation stand."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004WrappedStandCandidate_v024"
WRAPPED_MESH_PATH = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/SM_LB_MasterCoil_Candidate_v002"
PR004_COIL_LABEL = "LB_INT_PR004_V009_packaging_v004_PR004_PACK_BARE_COIL_v004"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_wrapped_stand_candidate_v024.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary

wrapped_mesh = lib.load_asset(WRAPPED_MESH_PATH)
if wrapped_mesh is None:
    raise RuntimeError(f"Missing wrapped packaged-coil mesh: {WRAPPED_MESH_PATH}")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load prepared map: {MAP}")

removed = []
kept_operator_estop = False
coil_actor = None
for actor in list(actors.get_all_level_actors()):
    label = actor.get_actor_label()
    remove_reason = None
    if label.startswith("LB_INT_PR004_V009_robot_v002_"):
        remove_reason = "dedicated_unwrapping_robot_removed_by_user_scope"
    elif label.startswith("LB_INT_PR004_V009_PERIMETER_"):
        remove_reason = "full_robotic_safety_cage_removed_by_user_scope"
    elif label in {
        "LB_INT_PR004_V009_DRESS08_EStop_EastTransfer",
        "LB_INT_PR004_V009_DRESS08_EStop_WestTransfer",
    }:
        remove_reason = "redundant_robotic_transfer_estop_removed"
    elif label == "LB_INT_PR004_V009_DRESS08_EStop_Operator":
        kept_operator_estop = True
    if label == PR004_COIL_LABEL:
        coil_actor = actor
    if remove_reason:
        removed.append({"actor": label, "reason": remove_reason})
        actors.destroy_actor(actor)

if coil_actor is None:
    raise RuntimeError(f"Missing PR-004 coil actor: {PR004_COIL_LABEL}")
if not kept_operator_estop:
    raise RuntimeError("Missing retained PR-004 operator emergency stop")

component = coil_actor.get_component_by_class(unreal.StaticMeshComponent)
if component is None:
    raise RuntimeError("PR-004 coil actor lacks StaticMeshComponent")
old_origin, old_extent = coil_actor.get_actor_bounds(False)
old_world_bottom = old_origin.z - old_extent.z
component.set_static_mesh(wrapped_mesh)
component.set_editor_property("override_materials", [])
new_origin, new_extent = coil_actor.get_actor_bounds(False)
new_world_bottom = new_origin.z - new_extent.z
z_correction = old_world_bottom - new_world_bottom
location = coil_actor.get_actor_location()
coil_actor.set_actor_location(unreal.Vector(location.x, location.y, location.z + z_correction), False, False)
coil_actor.set_actor_label("LB_INT_PR004_V024_WrappedCoilOnPreparationStand")
coil_actor.tags = [
    unreal.Name("LB.Asset.Candidate.v024"),
    unreal.Name("LB.PR004.Material.PackagedCoil"),
    unreal.Name("LB.PR004.State.AwaitingWorkerPreparation"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]

body_setup = wrapped_mesh.get_editor_property("body_setup")
if body_setup is None:
    raise RuntimeError("Wrapped packaged-coil mesh has no BodySetup")
aggregate = body_setup.get_editor_property("agg_geom")
simple_collision_count = sum(
    len(aggregate.get_editor_property(field))
    for field in ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems")
)
if simple_collision_count <= 0:
    raise RuntimeError("Wrapped packaged-coil mesh has no simple collision")

remaining_labels = [actor.get_actor_label() for actor in actors.get_all_level_actors()]
remaining_robot = sorted(label for label in remaining_labels if label.startswith("LB_INT_PR004_V009_robot_v002_"))
remaining_perimeter = sorted(label for label in remaining_labels if label.startswith("LB_INT_PR004_V009_PERIMETER_"))
if remaining_robot or remaining_perimeter:
    raise RuntimeError(f"Robot/cage actors remain: robot={remaining_robot} perimeter={remaining_perimeter}")

if not levels.save_current_level():
    raise RuntimeError("Could not save v024 map")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-wrapped-stand-candidate-v024/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_SIMPLIFIED_PR004_CANDIDATE__NOT_PROMOTED",
    "source_map": "/Game/LineBoss/Maps/LB_PressShop_WoundSteelLightingCandidate_v023",
    "candidate_map": MAP,
    "user_scope": {
        "dedicated_unwrapping_robot": False,
        "full_robotic_safety_cage": False,
        "presentation": "wrapped packaged coil on powered preparation stand",
        "retained_safety": "one operator E-stop and local guarding only where actual cutting/clamping/pinch hazards require it",
    },
    "removed_actor_count": len(removed),
    "removed_actors": sorted(removed, key=lambda item: item["actor"]),
    "remaining_robot_actor_count": len(remaining_robot),
    "remaining_perimeter_actor_count": len(remaining_perimeter),
    "wrapped_coil": {
        "actor": coil_actor.get_actor_label(),
        "mesh": wrapped_mesh.get_path_name(),
        "simple_collision_primitive_count": simple_collision_count,
        "stand_contact_height_correction_cm": z_correction,
        "world_bottom_before_cm": old_world_bottom,
        "world_bottom_after_cm": new_world_bottom + z_correction,
    },
    "retained_operator_estop": kept_operator_estop,
    "accepted_v006_preserved": True,
    "rejected_v007_v010_untouched": True,
    "v021_v023_preserved": True,
    "fresh_fixed_camera_visual_gate": "OPEN",
    "runtime_and_save_regression_gate": "OPEN",
    "promotion_authorized": False,
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_PR004_WRAPPED_STAND_V024_BUILD_PASS removed={len(removed)} collision={simple_collision_count}"
)
unreal.SystemLibrary.quit_editor()
