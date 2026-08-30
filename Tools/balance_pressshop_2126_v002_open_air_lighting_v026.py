"""Replace the pooly review fixtures with even native Unreal open-air lighting."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_open_air_lighting_v026.json"
TAG = unreal.Name("LB.PressShop.2126.v002.OpenAirLighting.v026")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("v026 lighting pass already applied")

# The B_stylized rectangular fixtures were correct as a calibration reference,
# but in this roofless prototype their 26m sources visibly stamped white pools
# onto the process zones.  Disable, do not delete, them for this candidate-only
# daylight review; the sun and skylight remain the only active illumination.
disabled = []
for index in range(1, 7):
    label = "B_stylized | 1200 lm fixture %02d" % index
    actor = actors.get(label)
    if not isinstance(actor, unreal.RectLight):
        raise RuntimeError("Expected B fixture missing: " + label)
    actor.light_component.set_visibility(False, True)
    actor.light_component.set_editor_property("affects_world", False)
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Lighting.DisabledPoolFixture")]
    disabled.append(label)

sun = actors.get("B_stylized | sun 0.30")
sky = actors.get("B_stylized | sky 0.20")
post = actors.get("B_stylized | fixed exposure -0.50")
if not isinstance(sun, unreal.DirectionalLight) or not isinstance(sky, unreal.SkyLight):
    raise RuntimeError("Expected native B_stylized components missing")
sun.light_component.set_editor_property("intensity", 8.0)
sun.light_component.set_editor_property("temperature", 5600.0)
sky.light_component.set_editor_property("intensity", 5.0)
sky.light_component.set_editor_property("real_time_capture", True)
if post is not None:
    settings = post.get_editor_property("settings")
    settings.override_auto_exposure_bias = True
    settings.auto_exposure_bias = 0.0
    post.set_editor_property("settings", settings)
for actor in (sun, sky):
    actor.tags = list(actor.tags) + [TAG]
if post is not None:
    post.tags = list(post.tags) + [TAG]

active_rects = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if isinstance(actor, unreal.RectLight) and actor.light_component.get_editor_property("affects_world"):
        active_rects.append(actor.get_actor_label())
if active_rects:
    raise RuntimeError("Pool-light gate failed; remaining active RectLights: " + ", ".join(active_rects))

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate map")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__EVEN_ROOFLESS_DAYLIGHT_REVIEW",
    "candidate_map": MAP,
    "disabled_existing_rect_fixtures": disabled,
    "remaining_active_rect_lights": active_rects,
    "new_dynamic_lights": 0,
    "directional_sun_intensity": 8.0,
    "skylight_intensity": 5.0,
    "exposure_bias": 0.0,
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_OPEN_AIR_LIGHTING_V026_PASS")
