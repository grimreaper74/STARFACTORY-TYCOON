"""Build v024 and explicitly return actor spawning to the persistent level."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_control_room_pr004_live_cctv_candidate_v023.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("CCTVStageCandidate_v003", "CCTVStageCandidate_v004")
code = code.replace("LiveCCTVCandidate_v023", "LiveCCTVCandidate_v024")
code = code.replace("live_cctv_build_v023", "live_cctv_build_v024")
code = code.replace("live-cctv-build-v023", "live-cctv-build-v024")
code = code.replace("LB.ControlRoom.v023", "LB.ControlRoom.v024")
code = code.replace("LB_MCR_V023", "LB_MCR_V024")
code = code.replace(
    'persistent_level = unreal.EditorLevelUtils.get_levels(world)[0]',
    'persistent_level = None',
)
exec(compile(code, str(SOURCE) + "::v024", "exec"), globals(), globals())
