"""Create a non-destructive v326 review map with broadside cameras for Train A."""
import unreal

SOURCE = "/Game/LineBoss/Maps/LB_PressTrainA_AxisBakedReviewCandidate_v325"
DEST = "/Game/LineBoss/Maps/LB_PressTrainA_AxisBakedBroadsideReviewCandidate_v326"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assets = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

if assets.does_asset_exist(DEST):
    raise RuntimeError("Refusing to overwrite existing v326 map")
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST):
    raise RuntimeError("Could not duplicate v325 as v326")
if not levels.load_level(DEST):
    raise RuntimeError("Could not load v326 review map")

candidate = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "CA_MW_PTA_AxisBaked_v039_STUDIO_VISUAL_ONLY_v325")
origin, extent = candidate.get_actor_bounds(False)
target = unreal.Vector(origin.x, origin.y, origin.z)

for label, x in (("LB_V326_CAM_BROADSIDE_A", origin.x - 2200.0), ("LB_V326_CAM_BROADSIDE_B", origin.x + 2200.0)):
    cam = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(x, origin.y, origin.z), unreal.Rotator())
    cam.set_actor_label(label)
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(), target), False)
    cam.camera_component.set_editor_properties({
        "projection_mode": unreal.CameraProjectionMode.ORTHOGRAPHIC,
        "ortho_width": extent.y * 2.15,
        "aspect_ratio": 16 / 9,
        "constrain_aspect_ratio": True,
    })
    pp = cam.camera_component.get_editor_property("post_process_settings")
    pp.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": 3.5,
    })
    cam.camera_component.set_editor_property("post_process_settings", pp)
    cam.camera_component.set_editor_property("post_process_blend_weight", 1.0)

unreal.EditorAssetLibrary.save_asset(DEST, only_if_is_dirty=False)
unreal.log("LB_V326_BROADSIDE_CAMERA_BUILD_PASS")
