"""Build v031 with the upright overview feed inside the seated viewing envelope."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_control_room_pr004_live_cctv_overview_candidate_v030.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("CCTVStageCandidate_v008", "CCTVStageCandidate_v009")
code = code.replace("LiveCCTVOverviewCandidate_v030", "LiveCCTVSeatedCandidate_v031")
code = code.replace("live_cctv_overview_build_v030", "live_cctv_seated_build_v031")
code = code.replace("live-cctv-overview-build-v030", "live-cctv-seated-build-v031")
code = code.replace("LB.ControlRoom.v030", "LB.ControlRoom.v031")
code = code.replace("LB_MCR_V030", "LB_MCR_V031")
code = code.replace("unreal.Vector(-203.0, 312.5, 243.0)", "unreal.Vector(-203.0, 312.5, 210.0)")
code = code.replace(
    '"display_panel": "FACTORY OVERVIEW authored wall panel (large, seated-eye-level)"',
    '"display_panel": "FACTORY OVERVIEW authored wall panel (upright, seated viewing envelope)"')
code = code.replace(
    'payload["capture_exposure_bias"] = 3.2',
    'payload["capture_exposure_bias"] = 3.2\npayload["seated_view_pitch_degrees"] = math.degrees(math.atan2(210.0 - 112.0, math.sqrt(203.0 * 203.0 + 230.5 * 230.5)))')
code = code.replace(
    "PASS__UPRIGHT_FACTORY_OVERVIEW_PR004_CCTV_BUILT__RUNTIME_VISUAL_AND_PERFORMANCE_GATES_REQUIRED__NOT_PROMOTED",
    "PASS__UPRIGHT_SEATED_ENVELOPE_PR004_CCTV_BUILT__RUNTIME_VISUAL_AND_PERFORMANCE_GATES_REQUIRED__NOT_PROMOTED")
exec(compile(code, str(SOURCE) + "::v031", "exec"), globals(), globals())
