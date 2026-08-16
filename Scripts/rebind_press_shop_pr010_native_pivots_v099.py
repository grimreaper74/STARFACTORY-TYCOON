"""Replace only v099 PR-010 authority so new per-actor pivots serialize in the map."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099"
OUT = ROOT / "Saved/Audits/PR010_CollisionNavigation/native_pivot_rebind_v099.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
old = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR010Station)]
if len(old) != 1: raise RuntimeError(f"expected one prior authority, found {len(old)}")
old_label = old[0].get_actor_label()
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
if len(bound) != 74: raise RuntimeError(f"expected 74 bindings, found {len(bound)}")
if not levels.save_current_level(): raise RuntimeError("could not save v099 pivot rebind")
OUT.write_text(json.dumps({
    "$schema": "cairnwell/audit/pr010-native-pivot-rebind-v099/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V099_NATIVE_AUTHORITY_REBOUND_WITH_PER_ACTOR_ROLLER_AND_GATE_PIVOTS__RUNTIME_GATE_REQUIRED__NOT_PROMOTED",
    "map": MAP, "replaced_authority": old_label, "new_authority": station.get_actor_label(),
    "binding_count": len(bound), "bindings": bound, "promotion_authorized": False,
}, indent=2), encoding="utf-8")
