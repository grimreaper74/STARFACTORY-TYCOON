"""Build v032 with upright live CCTV and the authored forward seated camera."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_control_room_pr004_live_cctv_overview_candidate_v030.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("CCTVStageCandidate_v008", "CCTVStageCandidate_v010")
code = code.replace("LiveCCTVOverviewCandidate_v030", "LiveCCTVAuthoredSeatCandidate_v032")
code = code.replace("live_cctv_overview_build_v030", "live_cctv_authored_seat_build_v032")
code = code.replace("live-cctv-overview-build-v030", "live-cctv-authored-seat-build-v032")
code = code.replace("LB.ControlRoom.v030", "LB.ControlRoom.v032")
code = code.replace("LB_MCR_V030", "LB_MCR_V032")

exec_marker = 'exec(compile(code, str(SOURCE) + "::v030-wrapper", "exec"), globals(), globals())'
if exec_marker not in code:
    raise RuntimeError("v030 execution marker changed; refusing unverified v032 rewrite")

post = '''exec(compile(code, str(SOURCE) + "::v032", "exec"), globals(), globals())

evidence_camera = next((a for a in actors_api.get_all_level_actors()
                        if "CAM_SeatedPlayer" in a.get_actor_label()), None)
player_start = next((a for a in actors_api.get_all_level_actors()
                     if isinstance(a, unreal.PlayerStart)), None)
if evidence_camera is None or player_start is None:
    failures.append("authored seated evidence camera or PlayerStart missing")
else:
    player_start.set_actor_location(evidence_camera.get_actor_location(), False, False)
    player_start.set_actor_rotation(evidence_camera.get_actor_rotation(), False)
    player_start.set_actor_label("LB_MCR_V032_PlayerStart_AuthoredForwardSeat")

if not library.save_asset(MAP, only_if_is_dirty=False):
    failures.append("could not resave v032 authored-seat map")

payload = json.loads(OUT.read_text(encoding="utf-8"))
payload["player_view_basis"] = "authored fixed CAM_SeatedPlayer transform; no screen-target camera override"
payload["console_monitor_pitch_degrees"] = 12.0
payload["console_monitor_face_direction"] = "down/front toward seated operator"
payload["failures"] = failures
payload["status"] = ("PASS__UPRIGHT_CCTV_AND_AUTHORED_SEATED_VIEW_BUILT__RUNTIME_VISUAL_AND_PERFORMANCE_GATES_REQUIRED__NOT_PROMOTED"
                     if not failures else "FAIL__CONTROL_ROOM_PR004_AUTHORED_SEAT_BUILD__NOT_PROMOTED")
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))'''

code = code.replace(exec_marker, post)
exec(compile(code, str(SOURCE) + "::v032-wrapper", "exec"), globals(), globals())
