"""Apply the approved B_stylized lighting calibration to the 2126 candidate.

This is a candidate-map-only adjustment.  It makes the review composition use
the project-wide exposure and colour language rather than a one-off preview
rig: six 5000 K fixtures at 1200 lm, sun 0.30, sky 0.20, exposure -0.50.
"""

import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_bstylized_lighting_v001.json"
TAG = unreal.Name("LB.PressShop.2126.BStylizedLighting.v001")
FIXTURE_LABEL = "2126 | B_stylized 5000K fixture "
CAMERA_LABELS = {
    "CAM | 2126 Steam hero overview",
    "CAM | 2126 operator line",
    "CAM | 2126 draw nexus",
}
POSITIONS = (
    (-14500.0, -1700.0, 8600.0),
    (-11200.0, -1700.0, 8600.0),
    (-7800.0, -1700.0, 8600.0),
    (-4400.0, -1700.0, 8600.0),
    (-1000.0, -1700.0, 8600.0),
    (2600.0, -1700.0, 8600.0),
)


def fail(message):
    raise RuntimeError("PRESSSHOP_2126_B_STYLIZED_FAIL: " + message)


def get_component(actor, component_class):
    component = actor.get_component_by_class(component_class)
    if component is None:
        fail("missing %s on %s" % (component_class.get_name(), actor.get_actor_label()))
    return component


def hide_preview_lights(actor):
    actor.set_actor_hidden_in_game(True)
    actor.tags = list(actor.tags) + [unreal.Name("LB.PressShop.2126.PreviewLight.Hidden")]
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    fail("fresh candidate map missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load fresh candidate map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    fail("B_stylized tag already present; refusing duplicate lighting pass")

# Supersede the deliberately provisional build-v001 lights, retaining them as
# reversible candidate history instead of silently deleting them.
hidden = []
for actor in actors:
    label = actor.get_actor_label()
    if label in {"2126 | native skylight", "2126 | warm directional sun"} or label.startswith("2126 | native softbox "):
        hide_preview_lights(actor)
        hidden.append(label)

if len(hidden) != 7:
    fail("expected 7 provisional build-v001 lights, found %d" % len(hidden))

fixtures = []
for index, position in enumerate(POSITIONS, start=1):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(*position), unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0))
    if actor is None:
        fail("could not create fixture %d" % index)
    actor.set_actor_label(FIXTURE_LABEL + str(index))
    actor.tags = [TAG, unreal.Name("LB.Visual.B_stylized"), unreal.Name("LB.PressShop.2126.Candidate")]
    component = get_component(actor, unreal.RectLightComponent)
    component.set_editor_property("intensity", 1200.0)
    component.set_editor_property("use_temperature", True)
    component.set_editor_property("temperature", 5000.0)
    component.set_editor_property("source_width", 3400.0)
    component.set_editor_property("source_height", 1800.0)
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    fixtures.append({"label": actor.get_actor_label(), "location_cm": list(position), "lumens": 1200, "kelvin": 5000})

sun = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 12000.0), unreal.Rotator(pitch=-38.0, yaw=-28.0, roll=0.0))
if sun is None:
    fail("could not create B_stylized sun")
sun.set_actor_label("2126 | B_stylized sun")
sun.tags = [TAG, unreal.Name("LB.Visual.B_stylized")]
sun_component = get_component(sun, unreal.DirectionalLightComponent)
sun_component.set_editor_property("intensity", 0.30)
sun_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 9000.0), unreal.Rotator())
if sky is None:
    fail("could not create B_stylized skylight")
sky.set_actor_label("2126 | B_stylized sky")
sky.tags = [TAG, unreal.Name("LB.Visual.B_stylized")]
sky_component = get_component(sky, unreal.SkyLightComponent)
sky_component.set_editor_property("intensity", 0.20)
sky_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

# The approved standard fixes exposure on the review camera lens.  Applying it
# to all three named cameras makes viewport and screenshot review reproducible.
camera_results = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if actor.get_actor_label() not in CAMERA_LABELS:
        continue
    camera = get_component(actor, unreal.CineCameraComponent)
    settings = camera.get_editor_property("post_process_settings")
    settings.set_editor_property("override_auto_exposure_bias", True)
    settings.set_editor_property("auto_exposure_bias", -0.50)
    camera.set_editor_property("post_process_settings", settings)
    camera.set_editor_property("post_process_blend_weight", 1.0)
    camera_results.append(actor.get_actor_label())

if set(camera_results) != CAMERA_LABELS:
    fail("not every named review camera received the fixed exposure")

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save B_stylized candidate lighting")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__B_STYLIZED_CALIBRATION_APPLIED_TO_FRESH_2126_CANDIDATE",
    "map": MAP,
    "candidate_only": True,
    "hidden_not_deleted_provisional_lights": hidden,
    "fixtures": fixtures,
    "sun_intensity": 0.30,
    "sky_intensity": 0.20,
    "fixed_camera_exposure_bias": -0.50,
    "no_roof_or_wall_mesh_created": True,
    "honest_status": "calibration property validation only; player-view screenshot proof remains required",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_B_STYLIZED_PASS: fixtures=%d cameras=%d" % (len(fixtures), len(camera_results)))
