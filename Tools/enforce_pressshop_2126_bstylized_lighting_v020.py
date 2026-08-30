"""Make the documented B_stylized lighting the only active candidate rig.

The read-only audit found a second legacy sky, sun and four high-output
softboxes still active alongside the approved six-fixture B_stylized rig.  They
are hidden in this candidate only; the approved rig keeps its exact numerical
contract and the post-process volume becomes an unbound fixed-exposure volume.
"""

import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_bstylized_enforced_v020.json"
TAG = unreal.Name("LB.PressShop.2126.BStylizedEnforced.v020")
LEGACY_LIGHTS = (
    "2126 | native skylight",
    "2126 | warm directional sun",
    "2126 | native softbox 1",
    "2126 | native softbox 2",
    "2126 | native softbox 3",
    "2126 | native softbox 4",
    "2126 | native softbox 5",
)
FIXTURES = tuple("2126 | B_stylized 5000K fixture " + str(index) for index in range(1, 7))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hide(actor):
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("B_stylized enforcement v020 already applied")

hidden = []
for label in LEGACY_LIGHTS:
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError("Expected legacy light missing: " + label)
    hide(actor)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.LegacyLighting.Disabled")]
    hidden.append(label)

# Fail closed on the six documented fixtures and their direct-light conditions.
for label in FIXTURES:
    actor = actors.get(label)
    if not isinstance(actor, unreal.RectLight):
        raise RuntimeError("Approved B_stylized fixture missing: " + label)
    component = actor.get_component_by_class(unreal.RectLightComponent)
    if component is None:
        raise RuntimeError("Approved B_stylized component missing: " + label)
    if not math.isclose(float(component.get_editor_property("intensity")), 1200.0, abs_tol=0.01):
        raise RuntimeError("Fixture calibration changed: " + label)
    if not component.get_editor_property("use_temperature") or not math.isclose(float(component.get_editor_property("temperature")), 5000.0, abs_tol=0.01):
        raise RuntimeError("Fixture temperature changed: " + label)
    actor.set_actor_hidden_in_game(False)
    actor.set_is_temporarily_hidden_in_editor(False)
    component.set_visibility(True, True)
    actor.tags = list(actor.tags) + [TAG]

sun = actors.get("2126 | B_stylized sun")
sky = actors.get("2126 | B_stylized sky")
if not isinstance(sun, unreal.DirectionalLight) or not isinstance(sky, unreal.SkyLight):
    raise RuntimeError("Approved B_stylized sun or sky missing")
if not math.isclose(float(sun.get_component_by_class(unreal.DirectionalLightComponent).get_editor_property("intensity")), 0.30, abs_tol=1e-4):
    raise RuntimeError("B_stylized sun intensity changed")
if not math.isclose(float(sky.get_component_by_class(unreal.SkyLightComponent).get_editor_property("intensity")), 0.20, abs_tol=1e-4):
    raise RuntimeError("B_stylized sky intensity changed")

volume = actors.get("2126 | fixed Steam exposure")
if not isinstance(volume, unreal.PostProcessVolume):
    raise RuntimeError("Fixed-exposure post process volume missing")
volume.set_editor_property("unbound", True)
settings = volume.get_editor_property("settings")
settings.override_auto_exposure_method = True
settings.auto_exposure_method = unreal.AutoExposureMethod.AEM_MANUAL
settings.override_auto_exposure_bias = True
settings.auto_exposure_bias = -0.50
settings.override_bloom_intensity = True
settings.bloom_intensity = 0.15
settings.override_vignette_intensity = True
settings.vignette_intensity = 0.15
volume.set_editor_property("settings", settings)
volume.tags = list(volume.tags) + [TAG]

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__APPROVED_B_STYLIZED_IS_ONLY_ACTIVE_CANDIDATE_LIGHTING_RIG",
    "disabled_legacy_candidate_lights": hidden,
    "approved_b_stylized": {"fixture_count": 6, "fixture_lumens": 1200, "fixture_kelvin": 5000, "sun_intensity": 0.30, "sky_intensity": 0.20},
    "fixed_post_process": {"unbound": True, "manual_exposure_bias": -0.50, "bloom_intensity": 0.15, "vignette_intensity": 0.15},
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_B_STYLIZED_ENFORCED_V020_PASS")
