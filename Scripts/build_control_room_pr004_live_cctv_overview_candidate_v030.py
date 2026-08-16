"""Build v030 with an upright, large overview-wall PR-004 live CCTV feed."""

import json
import math
from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_control_room_pr004_live_cctv_upright_candidate_v029.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("CCTVStageCandidate_v007", "CCTVStageCandidate_v008")
code = code.replace("LiveCCTVUprightCandidate_v029", "LiveCCTVOverviewCandidate_v030")
code = code.replace("live_cctv_upright_build_v029", "live_cctv_overview_build_v030")
code = code.replace("live-cctv-upright-build-v029", "live-cctv-overview-build-v030")
code = code.replace("LB.ControlRoom.v029", "LB.ControlRoom.v030")
code = code.replace("LB_MCR_V029", "LB_MCR_V030")

exec_marker = 'exec(compile(code, str(SOURCE) + "::v029", "exec"), globals(), globals())'
if exec_marker not in code:
    raise RuntimeError("v029 execution marker changed; refusing unverified v030 rewrite")

v030_rewrite = '''exec(compile(code, str(SOURCE) + "::v030", "exec"), globals(), globals())

# Apply the v030 composition only after v028/v029 have completed their guarded
# source rewrites. This preserves those predecessor verification markers.
front_location = unreal.Vector(-7800.0, 2200.0, 3150.0)
front_rotation = unreal.Rotator(pitch=-33.568, yaw=-59.25, roll=0.0)
overview_location = unreal.Vector(-203.0, 312.5, 243.0)
feed.set_actor_location(overview_location, False, False)
feed.set_actor_scale3d(unreal.Vector(1.0, 1.0, 2.30))
feed.set_editor_property("capture_world_location", front_location + STAGE_OFFSET)
feed.set_editor_property("capture_world_rotation", front_rotation)
feed.set_actor_label("LB_MCR_V030_SELECTED_CCTV_PR004_OVERVIEW")

player_start = next((a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.PlayerStart)), None)
if player_start is None:
    failures.append("seated PlayerStart missing during v030 overview composition")
else:
    seat = unreal.Vector(0.0, 82.0, 112.0)
    direction = overview_location - seat
    horizontal = math.sqrt(direction.x * direction.x + direction.y * direction.y)
    player_start.set_actor_location(seat, False, False)
    player_start.set_actor_rotation(unreal.Rotator(
        pitch=math.degrees(math.atan2(direction.z, horizontal)),
        yaw=math.degrees(math.atan2(direction.y, direction.x)), roll=0.0), False)
    player_start.set_actor_label("LB_MCR_V030_PlayerStart_FactoryOverviewCCTV")

if not library.save_asset(MAP, only_if_is_dirty=False):
    failures.append("could not resave persistent v030 map after overview composition")

payload = json.loads(OUT.read_text(encoding="utf-8"))
payload["capture_source_camera"] = "LB_INT_PR004_V009_CAM_FrontEndDirty"
payload["capture_source_location_cm"] = [front_location.x, front_location.y, front_location.z]
payload["capture_source_rotation_deg"] = [front_rotation.pitch, front_rotation.yaw, front_rotation.roll]
payload["display_panel"] = "FACTORY OVERVIEW authored wall panel (large, seated-eye-level)"
payload["display_location_cm"] = [overview_location.x, overview_location.y, overview_location.z]
payload["display_actor_scale"] = [1.0, 1.0, 2.30]
payload["capture_exposure_bias"] = 3.2
payload["failures"] = failures
payload["status"] = ("PASS__UPRIGHT_FACTORY_OVERVIEW_PR004_CCTV_BUILT__RUNTIME_VISUAL_AND_PERFORMANCE_GATES_REQUIRED__NOT_PROMOTED"
                     if not failures else "FAIL__CONTROL_ROOM_PR004_OVERVIEW_CCTV_BUILD__NOT_PROMOTED")
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))'''

code = code.replace(exec_marker, v030_rewrite)
exec(compile(code, str(SOURCE) + "::v030-wrapper", "exec"), globals(), globals())
