"""Author sun, sky and yard lighting for the Moorcross Works site.

The map shipped with no directional light, sky light, sky atmosphere or fog: the
whole scene was lit by one 800,000 lumen RectLight aimed straight down, which was
sufficient while nothing existed outside the shop buildings. Once the site was
built the yards, roads, fence and car park sat in darkness, so this adds a real
sun and sky.

Two constraints from Tools/Diagnostics/probe_map_lighting.py, which must be
respected rather than rediscovered:

1. `LB_OF_ENV_FixedExposureAuthority_v001` is an unbound post-process volume that
   pins auto-exposure min AND max brightness to 1.0. Exposure is deliberately
   fixed so the tuned interiors and the capture set stay comparable. This script
   MUST NOT touch that volume: the sun is calibrated to sit correctly at the
   existing fixed exposure instead.
2. `LB_OF_ENV_LightingAuthority_5000K_v001` is the existing overhead RectLight at
   5000 K. The sun is warmed slightly against it rather than matched, so exterior
   daylight and interior working light read as different sources.

Everything placed here is tagged `LB.Site.Lighting` and cleared on re-run, so the
sun intensity can be re-calibrated without disturbing the 5,049 site actors
placed by build_site_authored.py.

Run headless (an editor world is required - a commandlet has none):
  UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=Tools/build_site_lighting.py
Tune without editing the file:
  LB_SUN_INTENSITY=6.0 LB_SUN_PITCH=-42 LB_SUN_YAW=-35
"""
import io
import json
import os

import unreal

LEVEL = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
LIGHT_TAG = "LB.Site.Lighting"
OUT = os.environ.get("LB_LIGHTING_OUT", "C:/Temp/lb_lighting.json")


def env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# Calibrated against the fixed exposure above, not against physical daylight.
# Calibrated by capture against the pinned exposure: 6.0 blew the ground out to
# near-white, 1.0 read as dusk with a black sky. 3.0 holds both.
SUN_INTENSITY = env_float("LB_SUN_INTENSITY", 3.0)
SUN_PITCH = env_float("LB_SUN_PITCH", -42.0)
SUN_YAW = env_float("LB_SUN_YAW", -35.0)
SUN_TEMPERATURE = env_float("LB_SUN_TEMPERATURE", 5800.0)
SKYLIGHT_INTENSITY = env_float("LB_SKYLIGHT_INTENSITY", 1.0)
FOG_DENSITY = env_float("LB_FOG_DENSITY", 0.006)
# Off by default. The masts are real geometry and want real lights at dusk, but
# with the sun up a lit ring around the yard reads as an airport runway rather
# than as a working site. Set LB_MAST_INTENSITY to enable them.
MAST_INTENSITY = env_float("LB_MAST_INTENSITY", 0.0)

# The site is just over a kilometre across, so the sun's dynamic shadow cascade
# has to reach far enough to shadow the far fence rather than fading out mid-yard.
SHADOW_DISTANCE_CM = env_float("LB_SHADOW_DISTANCE", 90000.0)

REPORT = {"placed": {}, "cleared": 0, "settings": {
    "sun_intensity": SUN_INTENSITY, "sun_pitch": SUN_PITCH, "sun_yaw": SUN_YAW,
    "sun_temperature": SUN_TEMPERATURE, "skylight": SKYLIGHT_INTENSITY,
    "fog_density": FOG_DENSITY, "mast_intensity": MAST_INTENSITY,
    "shadow_distance_cm": SHADOW_DISTANCE_CM}}

ACTOR_SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LEVEL_SUB = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

if not LEVEL_SUB.load_level(LEVEL):
    raise RuntimeError("could not load {}".format(LEVEL))
WORLD = unreal.EditorLevelLibrary.get_editor_world()
if WORLD is None or LEVEL.rsplit("/", 1)[-1] != WORLD.get_name():
    raise RuntimeError(
        "expected world '{}' but got '{}'. Use -ExecutePythonScript, not "
        "-run=pythonscript.".format(LEVEL.rsplit("/", 1)[-1],
                                    "<none>" if WORLD is None else WORLD.get_name()))

# Clear only our own lighting, so re-calibrating the sun never touches the site
# geometry or the map's own lighting and exposure authorities.
for actor in ACTOR_SUB.get_all_level_actors():
    if actor and unreal.Name(LIGHT_TAG) in actor.tags:
        ACTOR_SUB.destroy_actor(actor)
        REPORT["cleared"] += 1


def count(kind):
    REPORT["placed"][kind] = REPORT["placed"].get(kind, 0) + 1


def spawn(actor_class, location, rotation=(0.0, 0.0, 0.0), label=None,
          kind="actor"):
    actor = ACTOR_SUB.spawn_actor_from_class(
        actor_class, unreal.Vector(*location), unreal.Rotator(*rotation))
    if actor is None:
        raise RuntimeError("could not spawn {}".format(actor_class))
    actor.tags = [unreal.Name(LIGHT_TAG), unreal.Name("LB.Environment.VisualOnly"),
                  unreal.Name("LB.NotProcessWIP")]
    if label:
        actor.set_actor_label(label)
    count(kind)
    return actor


def set_props(component, **properties):
    """Set what this engine version actually exposes and report the rest."""
    missing = []
    for name, value in properties.items():
        try:
            component.set_editor_property(name, value)
        except Exception:  # noqa: BLE001 - property set varies across versions
            missing.append(name)
    if missing:
        REPORT.setdefault("unsupported_properties", []).extend(missing)


# ---- the sun -------------------------------------------------------------
sun = spawn(unreal.DirectionalLight, (0.0, 0.0, 20000.0),
            (0.0, SUN_YAW, SUN_PITCH), "Site_Sun_DirectionalLight", "sun")
set_props(
    sun.light_component,
    intensity=SUN_INTENSITY,
    use_temperature=True,
    temperature=SUN_TEMPERATURE,
    cast_shadows=True,
    dynamic_shadow_distance_movable_light=SHADOW_DISTANCE_CM,
    dynamic_shadow_cascades=4,
    cascade_distribution_exponent=2.5,
    atmosphere_sun_light=True,
    light_source_angle=0.5357,
)
# UE puts a DirectionalLight's pitch in roll when spawned from a Rotator, so set
# the rotation explicitly afterwards to get an unambiguous sun angle.
sun.set_actor_rotation(unreal.Rotator(0.0, SUN_PITCH, SUN_YAW), False)

# ---- sky -----------------------------------------------------------------
spawn(unreal.SkyAtmosphere, (0.0, 0.0, 0.0), label="Site_SkyAtmosphere",
      kind="sky_atmosphere")

sky_light = spawn(unreal.SkyLight, (0.0, 0.0, 25000.0), label="Site_SkyLight",
                  kind="sky_light")
set_props(
    sky_light.light_component,
    intensity=SKYLIGHT_INTENSITY,
    source_type=unreal.SkyLightSourceType.SLS_CAPTURED_SCENE,
    real_time_capture=True,
    cast_shadows=True,
    sky_distance_threshold=200000.0,
)

fog = spawn(unreal.ExponentialHeightFog, (0.0, 0.0, 0.0), label="Site_HeightFog",
            kind="height_fog")
set_props(
    fog.get_editor_property("component"),
    fog_density=FOG_DENSITY,
    fog_height_falloff=0.08,
    start_distance=8000.0,
)

# ---- yard light masts ----------------------------------------------------
# Matches the 28 SM_CrashAreaSpotlight_01 masts placed by build_site_authored.py
# along the north and south ring edges. Non-shadow-casting on purpose: 28
# shadow-casting spots over a square kilometre costs a great deal and buys
# nothing while the sun is up, but the pools keep the yard reading as lit
# infrastructure rather than bare ground.
SHOPS = {"min_x": -30900.0, "min_y": -13900.0, "max_x": 30900.0, "max_y": 14900.0}
APRON = {"min_x": SHOPS["min_x"] - 12000.0, "min_y": SHOPS["min_y"] - 15000.0,
         "max_x": SHOPS["max_x"] + 11000.0, "max_y": SHOPS["max_y"] + 13000.0}
RING = {"min_x": APRON["min_x"] - 4200.0, "min_y": APRON["min_y"] - 4200.0,
        "max_x": APRON["max_x"] + 4200.0, "max_y": APRON["max_y"] + 4200.0}
ring_width = RING["max_x"] - RING["min_x"]

for index in range(14 if MAST_INTENSITY > 0.0 else 0):
    fraction = (index + 0.5) / 14.0
    x = RING["min_x"] + ring_width * fraction
    for edge, y, yaw in (("N", RING["max_y"] + 900.0, 180.0),
                         ("S", RING["min_y"] - 900.0, 0.0)):
        mast = spawn(unreal.SpotLight, (x, y, 1050.0), (0.0, yaw, -62.0),
                     "Site_YardMast_{}_{:02d}".format(edge, index), "yard_mast")
        set_props(
            mast.light_component,
            intensity=MAST_INTENSITY,
            intensity_units=unreal.LightUnits.LUMENS,
            attenuation_radius=9000.0,
            outer_cone_angle=62.0,
            inner_cone_angle=26.0,
            use_temperature=True,
            temperature=4200.0,
            cast_shadows=False,
        )
        mast.set_actor_rotation(unreal.Rotator(0.0, -62.0, yaw), False)

# --------------------------------------------------------------------------
# Guard the two authorities the probe found. If a future edit ever moves the
# exposure pin or removes the map's own light, the tuned interiors change
# silently, so assert they are still present and untouched by this script.
authorities = {"exposure": False, "rect_light": False}
for actor in ACTOR_SUB.get_all_level_actors():
    if not actor:
        continue
    label = actor.get_actor_label()
    if label == "LB_OF_ENV_FixedExposureAuthority_v001":
        settings = actor.get_editor_property("settings")
        authorities["exposure"] = (
            float(settings.get_editor_property("auto_exposure_min_brightness")) == 1.0
            and float(settings.get_editor_property("auto_exposure_max_brightness")) == 1.0)
    elif label == "LB_OF_ENV_LightingAuthority_5000K_v001":
        authorities["rect_light"] = True
REPORT["authorities_intact"] = authorities
if not all(authorities.values()):
    raise RuntimeError(
        "refusing to save: the map's exposure or lighting authority is missing "
        "or altered ({})".format(authorities))

LEVEL_SUB.save_current_level()

REPORT["total"] = sum(REPORT["placed"].values())
with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_SITE_LIGHTING placed {} (cleared {}) sun={} lux pitch={} "
           "authorities={} -> {}".format(
               REPORT["total"], REPORT["cleared"], SUN_INTENSITY, SUN_PITCH,
               authorities, OUT))
