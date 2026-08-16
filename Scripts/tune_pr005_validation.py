"""Tune candidate-only PR-005 validation lighting and auxiliary placement."""

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}

# The HPU is authored as a reusable local-origin module and is deliberately
# positioned at station assembly time, outside the guarded process envelope.
hpu = by_label.get("LB_PR005_HydraulicPowerUnit_Static")
if hpu:
    hpu.set_actor_location(unreal.Vector(-565.0, 425.0, 0.0), False, False)

for label, intensity in (("LB_PR005_Key", 425.0), ("LB_PR005_Fill", 225.0)):
    light = by_label.get(label)
    if light:
        light.get_editor_property("rect_light_component").set_editor_property("intensity", intensity)

exposure = by_label.get("LB_PR005_FixedExposure")
if exposure:
    settings = exposure.get_editor_property("settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -2.25,
    })
    exposure.set_editor_property("settings", settings)

directional = by_label.get("LB_PR005_DirectionalFill")
if directional is None:
    directional = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 700), unreal.Rotator(-48, -32, 0))
    directional.set_actor_label("LB_PR005_DirectionalFill")
directional.get_editor_property("directional_light_component").set_editor_properties({
    "intensity": 1.0,
    "light_color": unreal.Color(225, 235, 255, 255),
})

if not levels.save_current_level():
    raise RuntimeError("Failed saving tuned PR-005 validation map")
unreal.log("LINE_BOSS_PR005_VALIDATION_TUNE_PASS")
