"""Measure the installed PR-010 v097 Unreal blockout against fixed authority."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010BlockoutCandidate_v097"
OUT = ROOT / "Saved/Audits/PR010_Blockout/pr010_static_gate_v097.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
actors = actors_api.get_all_level_actors()
scope = [actor for actor in actors if actor.get_actor_label().startswith("LB_PR010_V097_")]


def tagged(value):
    return [actor for actor in scope if value in [str(tag) for tag in actor.tags]]


def bounds_row(actor):
    origin, extent = actor.get_actor_bounds(False, False)
    return {
        "label": actor.get_actor_label(),
        "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "size_cm": [extent.x * 2, extent.y * 2, extent.z * 2],
    }


lane_beds = sorted((bounds_row(actor) for actor in tagged("lane_bed")), key=lambda row: row["location_cm"][1], reverse=True)
carriers = [bounds_row(actor) for actor in tagged("carrier_position")]
shuttles = [bounds_row(actor) for actor in tagged("moving_infeed_shuttle")]
decks = [bounds_row(actor) for actor in tagged("deck")]
cameras = [actor for actor in scope if isinstance(actor, unreal.CameraActor)]
texts = [actor for actor in scope if isinstance(actor, unreal.TextRenderActor)]
negative_scale = [actor.get_actor_label() for actor in scope if min(actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z) <= 0]
candidate_tags = sum(str(tag) == "LB.Asset.CandidateNotPromoted" for actor in scope for tag in actor.tags)
lineboss_text = [actor.get_actor_label() for actor in texts if "LINE BOSS" in str(actor.text_render.get_editor_property("text")).upper()]
press_train_actors = [actor.get_actor_label() for actor in scope if "PRESS TRAIN" in actor.get_actor_label().upper() or "PT-A" in actor.get_actor_label().upper()]
pr009_authorities = [actor for actor in actors if isinstance(actor, unreal.LBPR009Station)]

failures = []
if len(scope) != 149: failures.append(f"expected 149 PR-010 blockout actors including identity/cameras, found {len(scope)}")
if len(lane_beds) != 4: failures.append(f"expected four lane beds, found {len(lane_beds)}")
expected_world_y = [-1550.0, -1850.0, -2150.0, -2450.0]
actual_world_y = [round(row["location_cm"][1], 3) for row in lane_beds]
if actual_world_y != expected_world_y: failures.append(f"lane centres mismatch: {actual_world_y}")
if len(carriers) != 8: failures.append(f"expected eight carrier positions, found {len(carriers)}")
if len(shuttles) != 1 or abs(shuttles[0]["location_cm"][0] - 1020.0) > 0.01: failures.append("shuttle handoff is not world X 1020 cm")
if len(decks) != 1: failures.append(f"expected one equipment deck, found {len(decks)}")
elif any(abs(a-b) > 1.0 for a,b in zip(decks[0]["size_cm"], [840.0, 1400.0, 8.0])):
    failures.append(f"equipment deck dimensions do not prove 8400 x 14000 x 80 mm after yaw: {decks[0]['size_cm']}")
if len(cameras) != 4: failures.append(f"expected four fixed cameras, found {len(cameras)}")
if len(texts) != 3: failures.append(f"expected three identity text actors, found {len(texts)}")
if candidate_tags != len(scope): failures.append(f"candidate tag cardinality mismatch: {candidate_tags}/{len(scope)}")
if negative_scale: failures.append(f"negative/zero scale actors: {len(negative_scale)}")
if lineboss_text: failures.append("Line Boss in-world text found")
if press_train_actors: failures.append("press-train datum/actor was invented")
if len(pr009_authorities) != 1: failures.append(f"accepted parent PR-009 authority cardinality changed: {len(pr009_authorities)}")

result = {
    "$schema": "cairnwell/audit/pr010-static-blockout-v097/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V097_DIMENSIONS_LANES_HANDOFF_IDENTITY__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V097_STATIC_BLOCKOUT__NOT_PROMOTED",
    "map": MAP,
    "scope_actor_count": len(scope),
    "lane_beds": lane_beds,
    "carrier_position_count": len(carriers),
    "shuttle": shuttles,
    "equipment_deck": decks,
    "camera_count": len(cameras),
    "identity_text_count": len(texts),
    "candidate_tag_count": candidate_tags,
    "negative_scale_count": len(negative_scale),
    "pr009_authority_count": len(pr009_authorities),
    "press_train_datums": "TBC_NOT_INVENTED",
    "failures": failures,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR010_STATIC {result['status']} {OUT}")
if failures: raise RuntimeError("; ".join(failures))
