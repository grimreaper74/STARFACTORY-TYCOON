"""Build v029 with a fresh front-faced, upright CCTV display actor."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_control_room_pr004_live_cctv_lit_candidate_v028.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("CCTVStageCandidate_v006", "CCTVStageCandidate_v007")
code = code.replace("LiveCCTVLitCandidate_v028", "LiveCCTVUprightCandidate_v029")
code = code.replace("live_cctv_lit_build_v028", "live_cctv_upright_build_v029")
code = code.replace("live-cctv-lit-build-v028", "live-cctv-upright-build-v029")
code = code.replace("LB.ControlRoom.v028", "LB.ControlRoom.v029")
code = code.replace("LB_MCR_V028", "LB_MCR_V029")
code = code.replace('        feed.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0), False)\n', '')
exec(compile(code, str(SOURCE) + "::v029", "exec"), globals(), globals())
