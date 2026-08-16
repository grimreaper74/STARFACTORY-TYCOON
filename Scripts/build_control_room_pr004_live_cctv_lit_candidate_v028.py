"""Build v028 with local PR-004 CCTV illumination and correct wall placement."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_control_room_pr004_live_cctv_candidate_v025.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("import json\n", "import json\nimport math\n")
code = code.replace("CCTVStageCandidate_v005", "CCTVStageCandidate_v006")
code = code.replace("LiveCCTVCandidate_v025", "LiveCCTVLitCandidate_v028")
code = code.replace("live_cctv_build_v025", "live_cctv_lit_build_v028")
code = code.replace("live-cctv-build-v025", "live-cctv-lit-build-v028")
code = code.replace("LB.ControlRoom.v025", "LB.ControlRoom.v028")
code = code.replace("LB_MCR_V025", "LB_MCR_V028")
code = code.replace("unreal.Vector(68.0, -312.5, 170.0)", "unreal.Vector(68.0, 312.5, 170.0)")

stage_marker = '''stage_station = next((a for a in actors_api.get_all_level_actors()
                      if a.get_class().get_name() == "LBPR004Station"), None)'''
stage_replacement = '''inspection_light = actors_api.spawn_actor_from_class(
    unreal.PointLight, unreal.Vector(-5050.0, -2000.0, 900.0), unreal.Rotator())
if inspection_light is None:
    failures.append("could not create range-limited PR-004 CCTV inspection light")
else:
    inspection_light.set_actor_label("LB_PR004_CCTV_LocalInspectionLight_v006")
    inspection_light.tags = [unreal.Name("LB.CCTV.LocalStageLight"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    component = inspection_light.point_light_component
    component.set_editor_property("intensity", 32000.0)
    component.set_editor_property("attenuation_radius", 2600.0)
    component.set_editor_property("source_radius", 220.0)
    component.set_editor_property("soft_source_radius", 480.0)
    component.set_editor_property("use_temperature", True)
    component.set_editor_property("temperature", 5100.0)
    component.set_editor_property("cast_shadows", True)

stage_station = next((a for a in actors_api.get_all_level_actors()
                      if a.get_class().get_name() == "LBPR004Station"), None)'''
if stage_marker not in code:
    raise RuntimeError("v025 stage marker changed; refusing unverified v028 rewrite")
code = code.replace(stage_marker, stage_replacement)

feed_marker = '''        feed.set_editor_property("selected_feed", True)

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()'''
feed_replacement = '''        feed.set_editor_property("selected_feed", True)
        feed.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0), False)

player_start = next((a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.PlayerStart)), None)
seat = unreal.Vector(0.0, 82.0, 112.0)
target = unreal.Vector(68.0, 312.5, 170.0)
if player_start is None:
    failures.append("seated PlayerStart missing")
else:
    direction = target - seat
    horizontal = math.sqrt(direction.x * direction.x + direction.y * direction.y)
    player_start.set_actor_location(seat, False, False)
    player_start.set_actor_rotation(unreal.Rotator(
        pitch=math.degrees(math.atan2(direction.z, horizontal)),
        yaw=math.degrees(math.atan2(direction.y, direction.x)), roll=0.0), False)
    player_start.set_actor_label("LB_MCR_V028_PlayerStart_SelectedCCTVWall")

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()'''
if feed_marker not in code:
    raise RuntimeError("v025 feed marker changed; refusing unverified v028 rewrite")
code = code.replace(feed_marker, feed_replacement)
exec(compile(code, str(SOURCE) + "::v028", "exec"), globals(), globals())
