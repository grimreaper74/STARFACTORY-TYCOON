"""Separate the 13 m fixed shuttle envelope from its 2.4 m moving carriage."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099"
OUT = ROOT / "Saved/Audits/PR010_CollisionNavigation/infeed_shuttle_correction_v099.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if not levels.load_level(MAP): raise RuntimeError(MAP)

for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label() == "LB_PR010_V099_PR010_M01_InfeedCarriage": actors_api.destroy_actor(actor)

bed = next((actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == "LB_PR010_V097_PR010_M01_InfeedShuttle"), None)
if bed is None: raise RuntimeError("missing authored 13 m shuttle bed")
bed_tags = [str(tag) for tag in bed.tags if str(tag) != "moving_infeed_shuttle"]
bed_tags.extend(("fixed", "LB.PR010.Shuttle.FixedRailBed", "LB.Asset.Candidate.v099"))
bed.tags = [unreal.Name(value) for value in dict.fromkeys(bed_tags)]
bed.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
bed.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"))
bed.static_mesh_component.set_editor_property("can_ever_affect_navigation", True)

carrier_mesh = library.load_asset("/Engine/BasicShapes/Cube.Cube")
if carrier_mesh is None: raise RuntimeError("missing transfer-cradle primitive")
reference_carrier = next((actor for actor in actors_api.get_all_level_actors() if "carrier_position" in {str(tag) for tag in actor.tags}), None)
if reference_carrier is None: raise RuntimeError("missing carrier material reference")
carriage = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(1020, -2000, 69), unreal.Rotator(yaw=-90))
carriage.set_actor_label("LB_PR010_V099_PR010_M01_InfeedCarriage")
carriage.tags = [unreal.Name(value) for value in (
    "moving_infeed_shuttle", "M01", "LB.Station.PR010", "LB.Asset.Candidate.v099",
    "LB.Asset.CandidateNotPromoted", "LB.Control.ControlRoomOnly", "LB.PR010.Shuttle.MovingCarriage")]
carriage.static_mesh_component.set_static_mesh(carrier_mesh)
carriage.static_mesh_component.set_world_scale3d(unreal.Vector(2.4, 0.8, 0.18))
carriage.static_mesh_component.set_material(0, reference_carrier.static_mesh_component.get_material(0))
carriage.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
carriage.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
carriage.static_mesh_component.set_collision_profile_name(unreal.Name("OverlapAllDynamic"))
carriage.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)

# The v098 provisional posts were inside the authoritative M01 sweep. Move
# them to the outside edges of each 2.4 m carrier envelope with 150 mm lateral
# clearance, and move the infeed line 350 mm downstream of the cradle face.
lane_centres = {"LaneA": -4500, "LaneB": -1500, "LaneC": 1500, "LaneD": 4500}
guard_relocations = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    lane = next((name for name in lane_centres if name in label), None)
    if lane is None or not ("GuardPost_" in label or "GuardRail_" in label): continue
    local_y = -2600 if "_In" in label else 2950
    world_x = 1350 + local_y / 10.0
    if "GuardPost_" in label:
        offset = -1350 if label.endswith("_L") else 1350
        world_y = -2000 - (lane_centres[lane] + offset) / 10.0
        location = actor.get_actor_location(); actor.set_actor_location(unreal.Vector(world_x, world_y, location.z), False, False)
    else:
        world_y = -2000 - lane_centres[lane] / 10.0
        location = actor.get_actor_location(); actor.set_actor_location(unreal.Vector(world_x, world_y, location.z), False, False)
        actor.set_actor_scale3d(unreal.Vector(2.7, 0.08, 0.06))
    guard_relocations.append({"label": label, "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z]})

old = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR010Station)]
if len(old) != 1: raise RuntimeError(f"expected one authority, found {len(old)}")
actors_api.destroy_actor(old[0])
station = actors_api.spawn_actor_from_class(unreal.LBPR010Station, unreal.Vector(1350, -2000, 0), unreal.Rotator(yaw=-90))
station.set_actor_label("LB_PR010_V099_StationAuthority")
station.tags = [unreal.Name(value) for value in (
    "LB.Station.PR010", "LB.Asset.Candidate.v099", "LB.Asset.CandidateNotPromoted",
    "LB.Control.ControlRoomOnly", "LB.Runtime.NativeAuthority", "LB.Save.PR010",
    "LB.RemoteAuthority.CW.MW.CONTROL_ROOM")]
roles = ("moving_infeed_shuttle", "moving_carrier_roller", "moving_stop_pin", "moving_reservation_gate", "moving_quality_spur")
bound = []
for actor in actors_api.get_all_level_actors():
    actor_tags = {str(tag) for tag in actor.tags}
    role = next((value for value in roles if value in actor_tags), None)
    if role and station.bind_presentation_actor(unreal.Name(actor.get_actor_label()), unreal.Name(role), actor):
        bound.append({"label": actor.get_actor_label(), "role": role})

failures = []
if len(bound) != 74: failures.append(f"expected 74 bindings, found {len(bound)}")
if len(guard_relocations) != 24: failures.append(f"expected 24 guard relocations, found {len(guard_relocations)}")
origin, extent = carriage.get_actor_bounds(False, False)
size = [extent.x*2, extent.y*2, extent.z*2]
if any(abs(value-expected) > 1.0 for value, expected in zip(size, (80.0, 240.0, 18.0))):
    failures.append(f"moving carriage dimensions mismatch after yaw: {size}")
if not levels.save_current_level(): failures.append("could not save v099 shuttle correction")

payload = {
    "$schema": "cairnwell/audit/pr010-infeed-shuttle-correction-v099/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V099_FIXED_13M_SHUTTLE_ENVELOPE_AND_2P4M_MOVING_CARRIAGE_SEPARATED__RUNTIME_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V099_SHUTTLE_CORRECTION__NOT_PROMOTED",
    "map": MAP,
    "authority_basis": {
        "sheet_03_item_05_envelope_mm": [13000, 1000, 650],
        "sheet_03_m01_motion_mm": [-5000, 5000],
        "moving_transfer_cradle_mm": [2400, 800, 180],
        "cradle_depth_basis": "inside authoritative 1000 mm M01 envelope; 100 mm clearance each side",
    },
    "fixed_bed": bed.get_actor_label(), "moving_carriage": carriage.get_actor_label(),
    "moving_carriage_world_size_cm": size, "binding_count": len(bound),
    "guard_relocation_count": len(guard_relocations), "guard_relocations": guard_relocations,
    "failures": failures, "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures: raise RuntimeError("; ".join(failures))
