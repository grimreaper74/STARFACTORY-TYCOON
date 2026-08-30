"""Replace inherited FullHall lighting with the approved B_stylized rig.

The candidate inherited 133 active lights from many historical production
passes.  They are retained but disabled, then superseded by exactly six 1200 lm
5000 K rect fixtures, a 0.30 sun, a 0.20 sky and fixed -0.50 exposure.  This
script is fail-closed on the audited light count and protected map hashes.
"""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "fullhall_bstylized_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.BStylized.FullHall.v001")
EXPECTED_LEGACY_LIGHTS = 133
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
FIXTURE_POSITIONS = (
    (-4500.0, -2800.0, 5200.0),
    (-3800.0, -800.0, 5200.0),
    (-3500.0, 1200.0, 5200.0),
    (-3500.0, 3200.0, 5200.0),
    (-2500.0, 5200.0, 5200.0),
    (4200.0, 4500.0, 5200.0),
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("FullHall B_stylized pass already exists")

light_classes = (unreal.DirectionalLight, unreal.SkyLight, unreal.RectLight, unreal.PointLight, unreal.SpotLight)
legacy = [actor for actor in actors if isinstance(actor, light_classes)]
if len(legacy) != EXPECTED_LEGACY_LIGHTS:
    raise RuntimeError("expected %d audited legacy lights, found %d" % (EXPECTED_LEGACY_LIGHTS, len(legacy)))

disabled = []
for actor in legacy:
    actor.set_actor_hidden_in_game(True)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.LegacyLighting.Disabled")]
    for component in actor.get_components_by_class(unreal.LightComponent):
        component.set_visibility(False, True)
    disabled.append(actor.get_actor_label())

fixtures = []
for index, position in enumerate(FIXTURE_POSITIONS, start=1):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(*position), unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0))
    if actor is None:
        raise RuntimeError("could not spawn B_stylized fixture %d" % index)
    actor.set_actor_label("2126 LIGHT | B_stylized fixture %02d" % index)
    actor.tags = [TAG, unreal.Name("LB.Visual.B_stylized")]
    component = actor.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_property("intensity", 1200.0)
    component.set_editor_property("use_temperature", True)
    component.set_editor_property("temperature", 5000.0)
    component.set_editor_property("source_width", 3200.0)
    component.set_editor_property("source_height", 1800.0)
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    fixtures.append(actor.get_actor_label())

sun = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 10000.0), unreal.Rotator(pitch=-38.0, yaw=-28.0, roll=0.0))
sun.set_actor_label("2126 LIGHT | B_stylized sun")
sun.tags = [TAG, unreal.Name("LB.Visual.B_stylized")]
sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
sun_component.set_editor_property("intensity", 0.30)
sun_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

sky = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.SkyLight, unreal.Vector(0.0, 0.0, 8000.0), unreal.Rotator())
sky.set_actor_label("2126 LIGHT | B_stylized sky")
sky.tags = [TAG, unreal.Name("LB.Visual.B_stylized")]
sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
sky_component.set_editor_property("intensity", 0.20)
sky_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

volume = next((actor for actor in actors if isinstance(actor, unreal.PostProcessVolume)), None)
if volume is None:
    volume = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
volume.set_actor_label("2126 LIGHT | fixed Steam exposure")
volume.tags = list(volume.tags) + [TAG, unreal.Name("LB.Visual.B_stylized")]
volume.set_editor_property("unbound", True)
volume.set_editor_property("blend_weight", 1.0)
settings = volume.get_editor_property("settings")
settings.override_auto_exposure_method = True
settings.auto_exposure_method = unreal.AutoExposureMethod.AEM_MANUAL
settings.override_auto_exposure_bias = True
settings.auto_exposure_bias = -0.50
settings.override_bloom_intensity = True
settings.bloom_intensity = 0.15
settings.override_vignette_intensity = True
settings.vignette_intensity = 0.10
volume.set_editor_property("settings", settings)

camera = next((actor for actor in actors if actor.get_actor_label() == "CAM | 2126 full hall fixed game view"), None)
if not isinstance(camera, unreal.CameraActor):
    raise RuntimeError("fixed camera missing")
camera_component = camera.get_component_by_class(unreal.CameraComponent)
camera_settings = camera_component.get_editor_property("post_process_settings")
camera_settings.override_auto_exposure_method = True
camera_settings.auto_exposure_method = unreal.AutoExposureMethod.AEM_MANUAL
camera_settings.override_auto_exposure_bias = True
camera_settings.auto_exposure_bias = -0.50
camera_settings.override_bloom_intensity = True
camera_settings.bloom_intensity = 0.15
camera_component.set_editor_property("post_process_settings", camera_settings)
camera_component.set_editor_property("post_process_blend_weight", 1.0)

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("could not save B_stylized FullHall candidate")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during lighting pass")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_FULLHALL_B_STYLIZED_ONLY_ACTIVE_RIG",
    "map": MAP,
    "disabled_legacy_light_count": len(disabled),
    "disabled_legacy_lights": disabled,
    "fixtures": fixtures,
    "fixture_lumens": 1200.0,
    "fixture_kelvin": 5000.0,
    "sun_intensity": 0.30,
    "sky_intensity": 0.20,
    "manual_exposure_bias": -0.50,
    "bloom_intensity": 0.15,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_FULLHALL_B_STYLIZED_PASS receipt=" + str(RECEIPT))
unreal.SystemLibrary.quit_editor()
