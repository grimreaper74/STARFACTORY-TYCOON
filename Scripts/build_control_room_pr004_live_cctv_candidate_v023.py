"""Build v023 with a retained persistent-level handle before streaming."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_control_room_pr004_live_cctv_candidate_v022.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("CCTVStageCandidate_v002", "CCTVStageCandidate_v003")
code = code.replace("LiveCCTVCandidate_v022", "LiveCCTVCandidate_v023")
code = code.replace("live_cctv_build_v022", "live_cctv_build_v023")
code = code.replace("live-cctv-build-v022", "live-cctv-build-v023")
code = code.replace("LB.ControlRoom.v022", "LB.ControlRoom.v023")
code = code.replace("LB_MCR_V022", "LB_MCR_V023")
code = code.replace(
    'persistent_level = world.get_editor_property("persistent_level")',
    'persistent_level = unreal.EditorLevelUtils.get_levels(world)[0]',
)
exec(compile(code, str(SOURCE) + "::v023", "exec"), globals(), globals())
