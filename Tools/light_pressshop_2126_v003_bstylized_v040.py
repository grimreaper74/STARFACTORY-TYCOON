"""Apply the approved B_stylized lighting calibration to the isolated v003 candidate.

This changes only the candidate map.  Six native light fixtures are deliberately
non-architectural (they render light but add no roof, walls, cables, or props).
"""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
OUT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_bstylized_lighting_v040.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
EXPECTED = {
    PROTECTED: "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    V002: "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
TAG = unreal.Name("LB.PressShop.2126.v003.BStylizedLighting.v040")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().lower()


def light_component(actor):
    component = actor.get_component_by_class(
        unreal.SkyLightComponent if isinstance(actor, unreal.SkyLight) else unreal.LightComponent
    )
    if component is None:
        raise RuntimeError("Light actor lacks light component: " + actor.get_actor_label())
    return component


for path, expected in EXPECTED.items():
    if digest(path) != expected:
        raise RuntimeError("Protected map changed before lighting: " + str(path))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load v003 candidate map")

actors = unreal.EditorLevelLibrary.get_all_level_actors()
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("B_stylized v040 was already applied")
sun = next((actor for actor in actors if actor.get_actor_label() == "2126 v003 | open-air directional sun"), None)
if not isinstance(sun, unreal.DirectionalLight):
    raise RuntimeError("Candidate directional sun unavailable")

# Authority: B_stylized = sun 0.30, sky 0.20, six 1200 lm fixtures,
# fixed exposure bias -0.50.  Warm-white lights preserve readable colour
# separation at the management camera without resorting to blue/cyan fill.
sun_component = light_component(sun)
sun_component.set_intensity(0.30)
sun.tags = list(sun.tags) + [TAG]

sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 9000.0), unreal.Rotator())
if not isinstance(sky, unreal.SkyLight):
    raise RuntimeError("Could not create native skylight")
sky.set_actor_label("2126 v003 | B_stylized skylight")
sky_component = light_component(sky)
sky_component.set_intensity(0.20)
sky_component.set_mobility(unreal.ComponentMobility.MOVABLE)
sky.tags = [TAG]

fixtures = [
    (-5600.0, -1900.0, 800.0),
    (-3800.0, 1900.0, 800.0),
    (-1500.0, -1900.0, 800.0),
    (900.0, 1900.0, 800.0),
    (3300.0, -1900.0, 800.0),
    (5500.0, 1900.0, 800.0),
]
fixture_labels = []
for index, location in enumerate(fixtures, start=1):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    if not isinstance(actor, unreal.PointLight):
        raise RuntimeError("Could not create B_stylized fixture")
    actor.set_actor_label("2126 v003 | B_stylized area fixture {:02d}".format(index))
    component = light_component(actor)
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_intensity(1200.0)
    component.set_light_color(unreal.LinearColor(1.0, 0.94, 0.82, 1.0))
    component.set_editor_property("attenuation_radius", 2400.0)
    actor.tags = [TAG]
    fixture_labels.append(actor.get_actor_label())

volume = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())
if not isinstance(volume, unreal.PostProcessVolume):
    raise RuntimeError("Could not create candidate post process volume")
volume.set_actor_label("2126 v003 | B_stylized fixed exposure")
volume.set_editor_property("unbound", True)
settings = volume.settings
settings.override_auto_exposure_method = True
settings.auto_exposure_method = unreal.AutoExposureMethod.AEM_MANUAL
settings.override_auto_exposure_bias = True
settings.auto_exposure_bias = -0.50
volume.settings = settings
volume.tags = [TAG]

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v040 candidate lighting")
for path, expected in EXPECTED.items():
    if digest(path) != expected:
        raise RuntimeError("Protected map changed during lighting: " + str(path))

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS__V003_B_STYLIZED_LIGHTING_V040",
    "candidate_map": MAP,
    "sun_intensity": 0.30,
    "sky_intensity": 0.20,
    "fixtures": fixture_labels,
    "fixture_count": len(fixture_labels),
    "fixture_lumens": 1200,
    "fixed_exposure_bias": -0.50,
    "roof_created": False,
    "new_geometry": False,
    "protected_hashes": {str(path): digest(path) for path in EXPECTED},
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_B_STYLIZED_LIGHTING_V040_PASS")
