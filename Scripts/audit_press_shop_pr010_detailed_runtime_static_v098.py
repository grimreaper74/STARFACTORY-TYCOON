"""Static authority, geometry, branding and candidate-scope gate for PR-010 v098."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010DetailedRuntimeCandidate_v098"
OUT = ROOT / "Saved/Audits/PR010_DetailedRuntime/pr010_static_gate_v098.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = actors_api.get_all_level_actors()
scope = [actor for actor in actors if "LB.Station.PR010" in {str(tag) for tag in actor.tags}]
native = [actor for actor in scope if isinstance(actor, unreal.LBPR010Station)]
lane_beds = [actor for actor in scope if "lane_bed" in {str(tag) for tag in actor.tags}]
carriers = [actor for actor in scope if "carrier_position" in {str(tag) for tag in actor.tags}]
shuttles = [actor for actor in scope if "moving_infeed_shuttle" in {str(tag) for tag in actor.tags}]
open_posts = [actor for actor in scope if "LB.Safety.OpenMesh.Post" in {str(tag) for tag in actor.tags}]
open_rails = [actor for actor in scope if "LB.Safety.OpenMesh.Rail" in {str(tag) for tag in actor.tags}]
scanners = [actor for actor in scope if "LB.Safety.Scanner" in {str(tag) for tag in actor.tags}]
tow_points = [actor for actor in scope if "LB.Service.TowPoint" in {str(tag) for tag in actor.tags}]
cameras = [actor for actor in scope if isinstance(actor, unreal.CameraActor) and "LB.Camera.Fixed.PR010.v098" in {str(tag) for tag in actor.tags}]
texts = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor)]
text_content = [str(actor.text_render.get_editor_property("text")) for actor in texts]
negative_scale = [actor.get_actor_label() for actor in scope if min(actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z) <= 0]
press_train_actors = [actor.get_actor_label() for actor in scope if "PRESS TRAIN" in actor.get_actor_label().upper() or "PT-A" in actor.get_actor_label().upper()]

failures = []
if len(native) != 1: failures.append(f"expected one native PR-010 authority, found {len(native)}")
elif native[0].get_actor_location().distance(unreal.Vector(1350, -2000, 0)) > 0.01: failures.append("native authority datum mismatch")
elif abs(native[0].get_actor_rotation().yaw - (-90.0)) > 0.01: failures.append("native authority yaw mismatch")
if len(lane_beds) != 4: failures.append(f"expected four lane beds, found {len(lane_beds)}")
if len(carriers) != 8: failures.append(f"expected eight carrier positions, found {len(carriers)}")
if len(shuttles) != 1 or abs(shuttles[0].get_actor_location().x - 1020.0) > 0.01: failures.append("PR-009 handoff datum mismatch")
if len(open_posts) != 16 or len(open_rails) != 8: failures.append(f"open guard cardinality mismatch posts={len(open_posts)} rails={len(open_rails)}")
if len(scanners) != 4 or len(tow_points) != 4: failures.append(f"scanner/tow-point cardinality mismatch {len(scanners)}/{len(tow_points)}")
if len(cameras) != 4: failures.append(f"expected four v098 cameras, found {len(cameras)}")
if not any("CAIRNWELL AUTOMOTIVE" in value for value in text_content): failures.append("Cairnwell identity missing")
if not any("MOORCROSS WORKS" in value for value in text_content): failures.append("Moorcross identity missing")
if any("LINE BOSS" in value.upper() for value in text_content): failures.append("working-title branding found in-world")
if negative_scale: failures.append(f"negative/zero scale actors: {len(negative_scale)}")
if press_train_actors: failures.append("press-train datum/actor was invented")

result = {
    "$schema": "cairnwell/audit/pr010-detailed-runtime-static-v098/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V098_STATIC_AUTHORITY_DIMENSIONS_OPEN_GUARDS_BRANDING__RUNTIME_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V098_STATIC__NOT_PROMOTED",
    "map": MAP,
    "scope_actor_count": len(scope),
    "native_station_count": len(native),
    "lane_bed_count": len(lane_beds),
    "carrier_position_count": len(carriers),
    "open_guard_post_count": len(open_posts),
    "open_guard_rail_count": len(open_rails),
    "scanner_count": len(scanners),
    "tow_point_count": len(tow_points),
    "camera_count": len(cameras),
    "identity_text": text_content,
    "press_train_datums": "TBC_NOT_INVENTED",
    "failures": failures,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR010_V098_STATIC {result['status']} {OUT}")
if failures:
    raise RuntimeError("; ".join(failures))
