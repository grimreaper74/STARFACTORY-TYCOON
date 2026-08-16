"""Add the proven operator-distance HMI camera to final crane candidate v035."""

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFinishCandidate_v035"
LABEL = "LB_PR004_V035_CAM_PR004HMIReadable"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label() == LABEL:
        actors.destroy_actor(actor)
camera = actors.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(-4990.0, -1295.0, 175.0), unreal.Rotator())
camera.set_actor_label(LABEL)
camera.tags = [unreal.Name(value) for value in (
    "LB.Camera.Validation", "LB.Camera.Fixed.PR004Crane.v035",
    "LB.Asset.Candidate.v035", "LB.Asset.CandidateNotPromoted")]
camera.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=-4.38, yaw=-146.44), False)
component = camera.camera_component
component.set_editor_properties({"field_of_view": 39.0, "aspect_ratio": 16.0 / 9.0,
                                 "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
settings = component.get_editor_property("post_process_settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 0.10,
})
component.set_editor_property("post_process_settings", settings)
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
unreal.log(f"LINE_BOSS_PR004_HMI_READABLE_CAMERA_V035_PASS camera={LABEL}")
unreal.SystemLibrary.quit_editor()
