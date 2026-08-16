"""Build an isolated PR-004 CCTV stage and stream it into control-room v020."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_STAGE = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
STAGE = "/Game/LineBoss/Maps/LB_PR004_CCTVStageCandidate_v001"
SOURCE_CONTROL = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004ConsoleCandidate_v020"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004LiveCCTVCandidate_v021"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_pr004_live_cctv_build_v021.json"
STAGE_OFFSET = unreal.Vector(200000.0, 0.0, 0.0)
SOURCE_CAMERA_LOCATION = unreal.Vector(-5850.0, -330.0, 720.0)
SOURCE_CAMERA_ROTATION = unreal.Rotator(pitch=-17.953, yaw=-64.404, roll=0.0)

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
failures = []

for asset in (STAGE, MAP):
    if library.does_asset_exist(asset):
        raise RuntimeError(f"refusing to overwrite {asset}")

# Preserve v026 and create a CCTV-only derivative with global lighting disabled.
if not levels.new_level_from_template(STAGE, SOURCE_STAGE):
    raise RuntimeError(f"could not derive {STAGE}")

disabled_global_actors = []
for actor in actors_api.get_all_level_actors():
    if isinstance(actor, (unreal.DirectionalLight, unreal.SkyLight)):
        actor.set_actor_hidden_in_game(True)
        light_component = actor.get_component_by_class(unreal.LightComponentBase)
        if light_component:
            light_component.set_visibility(False, True)
        disabled_global_actors.append(actor.get_actor_label())
    elif isinstance(actor, unreal.PostProcessVolume):
        actor.set_editor_property("enabled", False)
        disabled_global_actors.append(actor.get_actor_label())

stage_station = next((a for a in actors_api.get_all_level_actors()
                      if a.get_class().get_name() == "LBPR004Station"), None)
if stage_station is None:
    failures.append("PR-004 authority station missing from v026 stage derivative")
levels.save_current_level()

# Build the persistent control room and attach the isolated stage as always loaded.
if not levels.new_level_from_template(MAP, SOURCE_CONTROL):
    raise RuntimeError(f"could not derive {MAP}")
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
stage_transform = unreal.Transform(location=STAGE_OFFSET)
streaming = unreal.EditorLevelUtils.add_level_to_world_with_transform(
    world, STAGE, unreal.LevelStreamingAlwaysLoaded, stage_transform)
if streaming is None:
    failures.append("could not add PR-004 CCTV stage as always-loaded sublevel")
else:
    streaming.set_editor_property("should_be_loaded", True)
    streaming.set_editor_property("should_be_visible", True)
    streaming.set_editor_property("should_block_on_load", True)

console = next((a for a in actors_api.get_all_level_actors()
                if a.get_class().get_name() == "LBControlRoomPR004Console"), None)
if console is None:
    failures.append("v020 PR-004 control-room console missing")
else:
    console.set_editor_property("spawn_authority_if_missing", False)
    console.set_actor_label("LB_MCR_V021_PR004_AuthorityConsole")
    console.tags = [unreal.Name("LB.ControlRoom.v021"), unreal.Name("LB.PR004.AuthorityConsole"),
                    unreal.Name("LB.Asset.CandidateNotPromoted")]

feed_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBControlRoomCCTVFeed")
if feed_class is None:
    failures.append("compiled ALBControlRoomCCTVFeed class unavailable")
    feed = None
else:
    # Overlay the authored CAMERA OVERVIEW panel by 1.5 cm toward the player.
    feed = actors_api.spawn_actor_from_class(feed_class, unreal.Vector(68.0, -312.5, 170.0), unreal.Rotator())
    if feed is None:
        failures.append("could not spawn selected CCTV feed actor")
    else:
        feed.set_actor_label("LB_MCR_V021_SELECTED_CCTV_PR004")
        feed.tags = [unreal.Name("LB.ControlRoom.v021"), unreal.Name("LB.CCTV.Selected.PR004"),
                     unreal.Name("LB.Asset.CandidateNotPromoted")]
        feed.set_editor_property("capture_world_location", SOURCE_CAMERA_LOCATION + STAGE_OFFSET)
        feed.set_editor_property("capture_world_rotation", SOURCE_CAMERA_ROTATION)
        feed.set_editor_property("selected_feed", True)

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-pr004-live-cctv-build-v021/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__REAL_STREAMED_PR004_SELECTED_CCTV_BUILT__RUNTIME_VISUAL_AND_PERFORMANCE_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_PR004_LIVE_CCTV_BUILD__NOT_PROMOTED",
    "source_control_map": SOURCE_CONTROL,
    "source_stage_map": SOURCE_STAGE,
    "isolated_stage_map": STAGE,
    "map": MAP,
    "stage_offset_cm": [STAGE_OFFSET.x, STAGE_OFFSET.y, STAGE_OFFSET.z],
    "capture_source_camera": "LB_INT_PR004_V009_CAM_PR004CloseDirty",
    "capture_source_location_cm": [SOURCE_CAMERA_LOCATION.x, SOURCE_CAMERA_LOCATION.y, SOURCE_CAMERA_LOCATION.z],
    "capture_source_rotation_deg": [SOURCE_CAMERA_ROTATION.pitch, SOURCE_CAMERA_ROTATION.yaw, SOURCE_CAMERA_ROTATION.roll],
    "display_panel": "CAMERA OVERVIEW authored wall panel",
    "authority_model": "streamed v026 ALBPR004Station; control-room console retries binding and cannot spawn a duplicate",
    "disabled_stage_global_actors": disabled_global_actors,
    "selected_feed_updates_every_frame": True,
    "inactive_feed_policy": "capture disabled; retained last frame",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
