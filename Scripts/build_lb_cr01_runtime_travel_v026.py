"""Create an honest runtime travel proof for CR01 v026.

The imported FBX currently bakes per-component placement, so this sequence moves
the entire 497-part assembly together. It deliberately does not claim mechanism
pivot validation.
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v026"
SEQ_DIR = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v026/Sequences"
SEQ_NAME = "LS_LB_CR01_RuntimeTravel_v026"
SEQ_PATH = f"{SEQ_DIR}/{SEQ_NAME}"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v026_runtime_travel.json"
FPS = 30
END = 180

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
actors = actors_api.get_all_level_actors()
robot = [actor for actor in actors if "LB.Asset.Candidate.v026" in {str(tag) for tag in actor.tags}]
if len(robot) != 497:
    raise RuntimeError(f"Expected 497 tagged robot actors, found {len(robot)}")

for actor in actors:
    if actor.get_actor_label() == "LB_CR01_V026_RuntimeTravel":
        actors_api.destroy_actor(actor)
if unreal.EditorAssetLibrary.does_asset_exist(SEQ_PATH):
    unreal.EditorAssetLibrary.delete_asset(SEQ_PATH)

sequence = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    SEQ_NAME, SEQ_DIR, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
sequence.set_display_rate(unreal.FrameRate(FPS, 1))
sequence.set_playback_start(0)
sequence.set_playback_end(END)

for actor in robot:
    base = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    binding = sequence.add_possessable(actor)
    track = binding.add_track(unreal.MovieScene3DTransformTrack)
    section = track.add_section()
    section.set_range(0, END)
    channels = section.get_all_channels()
    values = [base.x, base.y, base.z, rotation.roll, rotation.pitch, rotation.yaw, scale.x, scale.y, scale.z]
    for index, channel in enumerate(channels[:9]):
        if index == 0:
            keys = ((0, base.x - 125.0), (90, base.x), (END, base.x + 125.0))
        else:
            keys = ((0, values[index]), (END, values[index]))
        for frame, value in keys:
            channel.add_key(unreal.FrameNumber(frame), float(value), interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)

camera = next((actor for actor in actors if actor.get_actor_label() == "LB_CR01_V026_CAM_Oblique"), None)
if not camera:
    raise RuntimeError("Missing fixed runtime camera")
camera.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)

unreal.EditorAssetLibrary.save_loaded_asset(sequence, only_if_is_dirty=False)
sequence_actor = actors_api.spawn_actor_from_class(unreal.LevelSequenceActor, unreal.Vector(), unreal.Rotator())
sequence_actor.set_actor_label("LB_CR01_V026_RuntimeTravel")
sequence_actor.set_sequence(sequence)
sequence_actor.set_editor_property("playback_settings", unreal.MovieSceneSequencePlaybackSettings(
    auto_play=True, loop_count=unreal.MovieSceneSequenceLoopCount(-1), play_rate=1.0,
))
if not levels.save_current_level():
    raise RuntimeError("Failed saving runtime travel proof")

result = {
    "status": "RUNTIME_TRAVEL_PROOF_ONLY__MECHANISM_PIVOT_GATE_OPEN",
    "map": MAP, "sequence": SEQ_PATH, "fps": FPS, "frames": END,
    "duration_seconds": END / FPS, "animated_robot_actors": len(robot),
    "travel_cm": 250.0, "camera": camera.get_actor_label(), "auto_play": True,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_LB_CR01_RUNTIME_TRAVEL_PASS actors={len(robot)} sequence={SEQ_PATH}")
