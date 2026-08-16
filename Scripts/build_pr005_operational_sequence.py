"""Build the first modular PR-005 operational animation proof in Unreal.

This is a candidate visualization sequence, not the eventual gameplay state
machine.  Its purpose is to prove that the exported semantic movers have usable
pivots and can be driven independently inside Unreal.
"""

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation"
SEQUENCE_PATH = "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Sequences"
SEQUENCE_NAME = "LS_PR005_OperationalCycle_v001"
SEQUENCE_ASSET = f"{SEQUENCE_PATH}/{SEQUENCE_NAME}"
FPS = 30
END = 240


def actor_transform_values(actor):
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    return [loc.x, loc.y, loc.z, rot.roll, rot.pitch, rot.yaw, scale.x, scale.y, scale.z]


def add_transform_animation(sequence, actor, changes):
    binding = sequence.add_possessable(actor)
    track = binding.add_track(unreal.MovieScene3DTransformTrack)
    section = track.add_section()
    section.set_range(0, END)
    channels = section.get_all_channels()
    if len(channels) < 9:
        raise RuntimeError(f"Expected 9 transform channels for {actor.get_actor_label()}, got {len(channels)}")
    base = actor_transform_values(actor)
    for channel_index, channel in enumerate(channels[:9]):
        key_values = changes.get(channel_index, ((0, base[channel_index]), (END, base[channel_index])))
        for frame, value in key_values:
            channel.add_key(
                unreal.FrameNumber(frame), float(value),
                interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    return binding


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
actors = {actor.get_actor_label(): actor for actor in actor_system.get_all_level_actors()}

old_sequence_actor = actors.get("LB_PR005_OperationalCycle")
if old_sequence_actor:
    actor_system.destroy_actor(old_sequence_actor)
if unreal.EditorAssetLibrary.does_asset_exist(SEQUENCE_ASSET):
    unreal.EditorAssetLibrary.delete_asset(SEQUENCE_ASSET)

sequence = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    SEQUENCE_NAME, SEQUENCE_PATH, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
sequence.set_display_rate(unreal.FrameRate(FPS, 1))
sequence.set_playback_start(0)
sequence.set_playback_end(END)

animated = []
for label, actor in actors.items():
    changes = None
    if "MandrelRotationMover" in label or "PayoffCoilTransferMover" in label:
        base = actor_transform_values(actor)
        changes = {3: ((0, base[3]), (END, base[3] + 1080.0))}
    elif "PinchLowerRotationMover" in label or "PinchUpperRotationMover" in label or "RollerBedMover" in label or "TableRollMover" in label:
        base = actor_transform_values(actor)
        changes = {3: ((0, base[3]), (END, base[3] + 1440.0))}
    elif "StripTravelWitnessMover" in label:
        base = actor_transform_values(actor)
        changes = {1: ((0, base[1]), (END, base[1] + 21.8))}
    elif "CropShearMover" in label:
        base = actor_transform_values(actor)
        changes = {2: ((0, base[2]), (175, base[2]), (185, base[2] - 24.0), (195, base[2]), (END, base[2]))}
    elif "CropClampMover" in label:
        base = actor_transform_values(actor)
        changes = {2: ((0, base[2]), (165, base[2]), (175, base[2] - 12.0), (205, base[2] - 12.0), (215, base[2]), (END, base[2]))}
    elif "KeeperArmMover" in label:
        base = actor_transform_values(actor)
        changes = {3: ((0, base[3] - 22.0), (45, base[3] - 22.0), (75, base[3]), (END, base[3]))}
    elif "SnubberMover" in label:
        base = actor_transform_values(actor)
        changes = {4: ((0, base[4] - 16.0), (60, base[4] - 16.0), (90, base[4]), (END, base[4]))}
    elif "PeelerBladeMover" in label:
        base = actor_transform_values(actor)
        changes = {4: ((0, base[4] - 18.0), (75, base[4] - 18.0), (110, base[4]), (END, base[4]))}
    elif "PinchUpperLiftMover" in label:
        base = actor_transform_values(actor)
        changes = {2: ((0, base[2] + 18.0), (100, base[2] + 18.0), (130, base[2]), (END, base[2]))}
    if changes:
        add_transform_animation(sequence, actor, changes)
        animated.append(label)

unreal.EditorAssetLibrary.save_loaded_asset(sequence, only_if_is_dirty=False)
sequence_actor = actor_system.spawn_actor_from_class(unreal.LevelSequenceActor, unreal.Vector(), unreal.Rotator())
sequence_actor.set_actor_label("LB_PR005_OperationalCycle")
sequence_actor.set_sequence(sequence)
sequence_actor.set_editor_property("playback_settings", unreal.MovieSceneSequencePlaybackSettings(
    auto_play=True,
    loop_count=unreal.MovieSceneSequenceLoopCount(-1),
    play_rate=1.0,
))
if not levels.save_current_level():
    raise RuntimeError("Failed saving PR-005 operational sequence actor")
unreal.log(f"LINE_BOSS_PR005_SEQUENCE_PASS animated={len(animated)} asset={SEQUENCE_ASSET}")
