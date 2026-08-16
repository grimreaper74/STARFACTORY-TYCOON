"""Build v022 with a nav-free CCTV stage and persistent-level display actor."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_control_room_pr004_live_cctv_candidate_v021.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("CCTVStageCandidate_v001", "CCTVStageCandidate_v002")
code = code.replace("LiveCCTVCandidate_v021", "LiveCCTVCandidate_v022")
code = code.replace("live_cctv_build_v021", "live_cctv_build_v022")
code = code.replace("live-cctv-build-v021", "live-cctv-build-v022")
code = code.replace("LB.ControlRoom.v021", "LB.ControlRoom.v022")
code = code.replace("LB_MCR_V021", "LB_MCR_V022")

loop = '''for actor in actors_api.get_all_level_actors():
    if isinstance(actor, (unreal.DirectionalLight, unreal.SkyLight)):'''
loop_replacement = '''for actor in actors_api.get_all_level_actors():
    if isinstance(actor, unreal.NavMeshBoundsVolume) or actor.get_class().get_name() == "LBPressShopNavigationBootstrap":
        actors_api.destroy_actor(actor)
        disabled_global_actors.append(actor.get_actor_label())
        continue
    if isinstance(actor, (unreal.DirectionalLight, unreal.SkyLight)):'''
if loop not in code:
    raise RuntimeError("v021 stage loop changed; refusing unverified v022 rewrite")
code = code.replace(loop, loop_replacement)

marker = '''console = next((a for a in actors_api.get_all_level_actors()
                if a.get_class().get_name() == "LBControlRoomPR004Console"), None)'''
replacement = '''persistent_level = world.get_editor_property("persistent_level")
if not unreal.EditorLevelUtils.make_level_current(persistent_level):
    failures.append("could not restore persistent control-room level before actor spawn")

console = next((a for a in actors_api.get_all_level_actors()
                if a.get_class().get_name() == "LBControlRoomPR004Console"), None)'''
if marker not in code:
    raise RuntimeError("v021 persistent-level marker changed; refusing unverified v022 rewrite")
code = code.replace(marker, replacement)
exec(compile(code, str(SOURCE) + "::v022", "exec"), globals(), globals())
