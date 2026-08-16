"""Bright, review-only derivative of the passing Train A runtime/nav map."""
from pathlib import Path
from datetime import datetime, timezone
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v673"
MAP = "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_VisualReview_v682"
OUT = ROOT / r"Saved\Audits\PressTrains\complete_train_a_visual_review_build_v682.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("Refusing to overwrite v682")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("Could not derive v682")

hidden = 0
for actor in actors.get_all_level_actors():
    if unreal.Name("LB.Collision.Proxy") in actor.tags:
        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)
        hidden += 1

def camera(label, location, target, fov):
    actor = actors.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(
            unreal.Vector(*location), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    actor.tags = [
        unreal.Name("LB.VisualGate.FixedCamera"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    return actor

camera("LB_CAM_TrainA_OperatorOverview_v682", (-7600, 2250, 2300), (0, 2250, 350), 42)
camera("LB_CAM_TrainA_ElevatedProcess_v682", (-6200, -1500, 3400), (0, 2300, 300), 48)
camera("LB_CAM_TrainA_ServiceOverview_v682", (7200, 2250, 2100), (0, 2250, 350), 43)

# A neutral industrial review rig. Point lights are deliberately shadowless so
# the gate judges the meshes and placement instead of an unfinished building shell.
light_labels = []
for side, x in (("OPERATOR", -2300), ("SERVICE", 2300)):
    for index, y in enumerate((-1200, 900, 3000, 5100), 1):
        light = actors.spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(x, y, 1550), unreal.Rotator())
        label = f"LB_TrainA_Review_{side}_{index:02d}_v682"
        light.set_actor_label(label)
        light.get_component_by_class(unreal.PointLightComponent).set_editor_properties({
            "intensity": 220000.0,
            "attenuation_radius": 3900.0,
            "source_radius": 180.0,
            "soft_source_radius": 360.0,
            "cast_shadows": False,
            "light_color": unreal.Color(245, 248, 255, 255),
        })
        light_labels.append(label)

sun = actors.spawn_actor_from_class(
    unreal.DirectionalLight, unreal.Vector(0, 2250, 2500), unreal.Rotator(-42, -35, 0))
sun.set_actor_label("LB_TrainA_ReviewSun_v682")
sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_properties({
    "intensity": 3.5,
    "cast_shadows": True,
})

sky = actors.spawn_actor_from_class(
    unreal.SkyLight, unreal.Vector(0, 2250, 1600), unreal.Rotator())
sky.set_actor_label("LB_TrainA_ReviewSky_v682")
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_properties({
    "intensity": 1.5,
    "cast_shadows": False,
})

post = actors.spawn_actor_from_class(
    unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
post.set_actor_label("LB_TrainA_ReviewExposure_v682")
post.set_editor_properties({"unbound": True, "blend_weight": 1.0})
settings = post.settings
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 0.75,
})
post.settings = settings

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v682")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "revision": "v682",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__BRIGHT_FIXED_CAMERA_REVIEW_MAP__CAPTURE_PENDING",
    "map": MAP,
    "source": BASE,
    "fixed_cameras": 3,
    "industrial_review_lights": len(light_labels),
    "collision_proxies_hidden_visual_only": hidden,
    "gameplay_collision_unchanged": True,
    "protected_map_modified": False,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_TRAIN_A_VISUAL_BUILD_V682_PASS")
