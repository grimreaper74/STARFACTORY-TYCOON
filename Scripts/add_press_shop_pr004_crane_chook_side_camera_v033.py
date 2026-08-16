"""Add a side-oblique fixed proof camera for the purpose-built v033 C-hook."""

import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneCHookCandidate_v033"
LABEL = "LB_PR004_V033_CAM_CHookSideProfile"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label() == LABEL:
        actors.destroy_actor(actor)
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-3950.0, -1850.0, 1050.0), unreal.Rotator())
camera.set_actor_label(LABEL)
camera.tags = [unreal.Name(value) for value in ("LB.Camera.Validation", "LB.Camera.Fixed.PR004Crane.v033",
                                                "LB.Asset.Candidate.v033", "LB.Asset.CandidateNotPromoted")]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(-5050.0, -1850.0, 770.0)), False)
component = camera.camera_component
component.set_editor_properties({"field_of_view": 40.0, "aspect_ratio": 16.0/9.0,
                                 "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
settings = component.get_editor_property("post_process_settings")
settings.set_editor_properties({"override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True, "auto_exposure_bias": -0.05})
component.set_editor_property("post_process_settings", settings)
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
unreal.log(f"LINE_BOSS_PR004_CRANE_V033_SIDE_CAMERA_PASS camera={LABEL}")
unreal.SystemLibrary.quit_editor()
