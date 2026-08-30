"""Author a native Unreal Level Sequence for the 2126 Press Shop flow.

The candidate's fixed-angle sprite actors remain independent gameplay objects.
This pass adds restrained, legible motion only to actors with an explicit mover
role: three inter-press shuttles, the active decoiler coil, and the three-part
outbound hover-pallet convoy.  Protected authority maps are hash-gated.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
SEQUENCE_DIR = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Sequences"
SEQUENCE_NAME = "LS_CA_MW_2126_PressShopAutomationLoop_v001"
SEQUENCE_PATH = SEQUENCE_DIR + "/" + SEQUENCE_NAME
ACTOR_LABEL = "2126 AUTOMATION | press-shop material-flow loop"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "native_automation_loop_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.AutomationLoop.v001")
FPS = 30
END_FRAME = 360
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def make_movable(actor):
    components = list(actor.get_components_by_class(unreal.SceneComponent))
    if not components:
        raise RuntimeError("actor has no SceneComponent: " + actor.get_actor_label())
    for component in components:
        try:
            component.set_mobility(unreal.ComponentMobility.MOVABLE)
        except Exception:
            pass


def base_values(actor):
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    return {
        "Location.X": float(location.x),
        "Location.Y": float(location.y),
        "Location.Z": float(location.z),
        # Transform channels use Euler X/Y/Z = roll/pitch/yaw.
        "Rotation.X": float(rotation.roll),
        "Rotation.Y": float(rotation.pitch),
        "Rotation.Z": float(rotation.yaw),
        "Scale.X": float(scale.x),
        "Scale.Y": float(scale.y),
        "Scale.Z": float(scale.z),
    }


def add_transform_track(sequence, actor, animated_channel, keys):
    make_movable(actor)
    binding = sequence.add_possessable(actor)
    if not binding.is_valid():
        raise RuntimeError("could not bind actor: " + actor.get_actor_label())
    binding.set_display_name(actor.get_actor_label())
    track = binding.add_track(unreal.MovieScene3DTransformTrack)
    if track is None:
        raise RuntimeError("could not add transform track: " + actor.get_actor_label())
    section = track.add_section()
    section.set_range(0, END_FRAME)
    channels = list(section.get_channels_by_type(unreal.MovieSceneScriptingDoubleChannel))
    values = base_values(actor)
    found = set()
    for channel in channels:
        name = str(channel.channel_name)
        if name not in values:
            continue
        channel.set_default(values[name])
        found.add(name)
        if name == animated_channel:
            for frame, value in keys:
                channel.add_key(
                    unreal.FrameNumber(frame), float(value),
                    interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    if animated_channel not in found:
        raise RuntimeError(
            f"transform channel {animated_channel} missing on {actor.get_actor_label()}; found={sorted(found)}")
    return {
        "actor": actor.get_actor_label(),
        "channel": animated_channel,
        "keys": [[int(frame), float(value)] for frame, value in keys],
        "channel_count": len(channels),
    }


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if unreal.EditorAssetLibrary.does_asset_exist(SEQUENCE_PATH):
    raise RuntimeError("automation sequence already exists; refusing overwrite")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
by_label = {actor.get_actor_label(): actor for actor in actors}
if ACTOR_LABEL in by_label:
    raise RuntimeError("automation actor already exists")

sequence = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    SEQUENCE_NAME, SEQUENCE_DIR, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
if not isinstance(sequence, unreal.LevelSequence):
    raise RuntimeError("could not create native Level Sequence")
sequence.set_display_rate(unreal.FrameRate(FPS, 1))
sequence.set_playback_start(0)
sequence.set_playback_end(END_FRAME)

tracks = []

# Each shuttle moves only within its own inter-press pitch.  The phase offsets
# prevent the whole line from looking mechanically synchronized.
for index, phase in ((1, 0), (2, 45), (3, 90)):
    label = f"2126 TRANSFER | magnetic panel shuttle sprite {index}"
    actor = by_label.get(label)
    if actor is None:
        raise RuntimeError("missing shuttle: " + label)
    y0 = float(actor.get_actor_location().y)
    keyed = [
        (0, y0),
        (phase, y0),
        (phase + 60, y0 + 420.0),
        (phase + 120, y0 + 420.0),
        (phase + 180, y0),
        (END_FRAME, y0),
    ]
    tracks.append(add_transform_track(sequence, actor, "Location.Y", keyed))

# The active strip coil spins slowly at the front-end mandrel.  Rotation.X is
# the coil axle for the authored placement.
coil_label = "2126 FRONT END | active feed coil"
coil = by_label.get(coil_label)
if coil is None:
    raise RuntimeError("active feed coil missing")
roll0 = float(coil.get_actor_rotation().roll)
tracks.append(add_transform_track(
    sequence, coil, "Rotation.X", [(0, roll0), (END_FRAME, roll0 + 360.0)]))

# All visible parts of the three outbound carriers move as one wheel-less
# convoy toward dispatch and return, preserving their spacing.
for slot in ("A", "B", "C"):
    group = [
        f"2126 OUTBOUND | hover pallet {slot} collision base",
        f"2126 OUTBOUND | hover pallet {slot} safety rail north",
        f"2126 OUTBOUND | hover pallet {slot} safety rail south",
        f"2126 OUTBOUND | hover pallet {slot} status beacon",
        f"2126 OUTBOUND | finished-panel payload {slot}",
    ]
    for label in group:
        actor = by_label.get(label)
        if actor is None:
            raise RuntimeError("outbound convoy actor missing: " + label)
        x0 = float(actor.get_actor_location().x)
        tracks.append(add_transform_track(sequence, actor, "Location.X", [
            (0, x0),
            (60, x0),
            (150, x0 + 720.0),
            (210, x0 + 720.0),
            (300, x0),
            (END_FRAME, x0),
        ]))

sequence_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.LevelSequenceActor, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())
if not isinstance(sequence_actor, unreal.LevelSequenceActor):
    raise RuntimeError("could not spawn LevelSequenceActor")
sequence_actor.set_actor_label(ACTOR_LABEL)
sequence_actor.tags = [TAG, unreal.Name("LB.PressShop.2126.RuntimeNative")]
sequence_actor.set_sequence(sequence)
settings = unreal.MovieSceneSequencePlaybackSettings(
    auto_play=True,
    loop_count=unreal.MovieSceneSequenceLoopCount(-1),
    play_rate=1.0,
    disable_camera_cuts=True,
)
sequence_actor.set_editor_property("playback_settings", settings)

unreal.EditorAssetLibrary.save_loaded_asset(sequence, only_if_is_dirty=False)
if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("candidate map did not save after automation pass")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during automation pass")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_NATIVE_AUTOMATION_LOOP_AUTHORED",
    "map": MAP,
    "sequence": sequence.get_path_name(),
    "sequence_actor": sequence_actor.get_actor_label(),
    "display_rate_fps": FPS,
    "duration_frames": END_FRAME,
    "duration_seconds": END_FRAME / FPS,
    "autoplay": True,
    "loop_count": -1,
    "animated_actor_count": len(tracks),
    "animated_tracks": tracks,
    "motion_scope": {
        "transfer_shuttles": 3,
        "active_feed_coils": 1,
        "outbound_hover_pallet_actors": 15,
    },
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_NATIVE_AUTOMATION_LOOP_PASS receipt=" + str(RECEIPT))
unreal.SystemLibrary.quit_editor()
