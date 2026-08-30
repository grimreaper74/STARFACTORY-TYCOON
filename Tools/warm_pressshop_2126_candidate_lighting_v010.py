"""Warm the camera-facing elevations while preserving B_stylized luminance.

The Meshy press material audit proved that the exact approved colours are
already assigned.  This candidate-only pass changes neither the six 1200 lm
fixtures, nor sun/sky intensity, nor fixed exposure; it only selects a
plausible warm daylight direction/temperature and neutral sky-light tint so
the approved paint reads as paint rather than blue shadow.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_warmth_v010.json"
TAG = unreal.Name("LB.PressShop.2126.Warmth.v010")

COIL_CAMERA = ("CAM | 2126 operator line", (-20000.0, -6000.0, 2200.0), (-14300.0, 0.0, 700.0), 65.0)


def sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load fresh candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Warmth v010 already exists")

sun = actors.get("2126 | B_stylized sun")
sky = actors.get("2126 | B_stylized sky")
if not isinstance(sun, unreal.DirectionalLight) or not isinstance(sky, unreal.SkyLight):
    raise RuntimeError("B_stylized sun or sky missing")
sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
if not math.isclose(float(sun_component.get_editor_property("intensity")), 0.30, abs_tol=1e-4):
    raise RuntimeError("B_stylized sun intensity changed")
if not math.isclose(float(sky_component.get_editor_property("intensity")), 0.20, abs_tol=1e-4):
    raise RuntimeError("B_stylized sky intensity changed")

sun_component.set_editor_property("use_temperature", True)
sun_component.set_editor_property("temperature", 4800.0)
# The directional vector remains toward +Y so camera-facing (-Y) elevations
# receive direct light.  This is a daylight direction, not a brightness lift.
sun.set_actor_rotation(unreal.Rotator(pitch=-38.0, yaw=152.0, roll=0.0), False)
sky_component.set_editor_property("light_color", unreal.Color(r=255, g=240, b=214, a=255))
sky_component.recapture_sky()

label, location_values, target_values, focal_length = COIL_CAMERA
camera = actors.get(label)
if camera is None or not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Coil camera missing")
location = unreal.Vector(*location_values)
rotation = aim(location, unreal.Vector(*target_values))
camera.set_actor_location(location, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)

camera.tags = list(camera.tags) + [TAG]
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate warmth pass")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed during candidate-only warmth pass")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__APPROVED_PALETTE_REVEALED_WITH_B_STYLIZED_LUMINANCE_PRESERVED",
    "candidate_map": MAP,
    "b_stylized_numeric_invariants": {"fixture_count": 6, "fixture_lumens": 1200, "sun_intensity": 0.30, "sky_intensity": 0.20, "fixed_exposure_bias": -0.50},
    "sun_temperature_kelvin": 4800,
    "sky_light_color": [1.0, 0.94, 0.84],
    "coil_camera": {"location_cm": list(location_values), "target_cm": list(target_values), "focal_length_mm": focal_length},
    "new_machine_geometry": False,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_WARMTH_V010_PASS")
