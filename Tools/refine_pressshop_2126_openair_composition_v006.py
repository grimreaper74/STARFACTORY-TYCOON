"""Restore a readable open-air composition for the real-Meshy 2126 line.

The v005 live capture correctly proved that a distant coil-to-line hero is too
wide and that the large rear facade reads as an unlit black wall.  This
candidate-only correction removes that visual obstruction, retains the
approved B_stylized numeric calibration, points the approved sun toward the
camera-facing machine elevations, and gives the two supplied coils their own
truthful inbound-stage camera.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_openair_composition_v006.json"
TAG = unreal.Name("LB.PressShop.2126.OpenAirComposition.v006")

CAMERAS = (
    ("CAM | 2126 Steam hero overview", (-11500.0, -9000.0, 850.0), (-300.0, 0.0, 500.0), 50.0),
    ("CAM | 2126 operator line", (-20500.0, -3400.0, 700.0), (-14300.0, 0.0, 800.0), 85.0),
    ("CAM | 2126 draw nexus", (-8500.0, -3200.0, 650.0), (-4200.0, 0.0, 450.0), 70.0),
)

HIDE_LABELS = (
    "2126 | rear production facade warm-white field",
    "2126 | rear production facade foundry plinth",
    "2126 | rear production facade Cairnwell band",
    "2126 | rear production facade pale-green supervision band",
    "2126 | rear production facade safety datum",
    "2126 | rear production facade inbound field",
    "2126 | rear facade optical supervision 1",
    "2126 | rear facade optical supervision 2",
    "2126 | rear facade optical supervision 3",
    "2126 | rear facade optical supervision 4",
    "2126 | rear facade optical supervision 5",
    "2126 | open-bay longitudinal gantry rail -7600",
    "2126 | open-bay longitudinal gantry rail 7600",
)


def sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    flat = math.sqrt(dx * dx + dy * dy)
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, flat)),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


def hide(actor):
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load fresh candidate map")

actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Open-air composition v006 exists; refusing duplicate pass")

hidden = []
for label in HIDE_LABELS:
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError("Expected candidate-only obstruction missing: " + label)
    hide(actor)
    hidden.append(label)

sun = actors.get("2126 | B_stylized sun")
sky = actors.get("2126 | B_stylized sky")
if not isinstance(sun, unreal.DirectionalLight) or not isinstance(sky, unreal.SkyLight):
    raise RuntimeError("Approved B_stylized sun or sky missing")
sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
if not math.isclose(float(sun_component.get_editor_property("intensity")), 0.30, abs_tol=1e-4):
    raise RuntimeError("B_stylized sun intensity changed")
if not math.isclose(float(sky_component.get_editor_property("intensity")), 0.20, abs_tol=1e-4):
    raise RuntimeError("B_stylized sky intensity changed")

# Numeric calibration is unchanged.  A sun direction is composition, not a
# brightness override; +Y lights the operator/camera-facing (-Y) elevations.
sun.set_actor_rotation(unreal.Rotator(pitch=-38.0, yaw=152.0, roll=0.0), False)

camera_rows = []
for label, location_values, target_values, focal_length in CAMERAS:
    camera = actors.get(label)
    if camera is None or not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Missing named review camera: " + label)
    location = unreal.Vector(*location_values)
    target = unreal.Vector(*target_values)
    rotation = aim(location, target)
    camera.set_actor_location(location, False, False)
    camera.set_actor_rotation(rotation, False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    camera_rows.append({"label": label, "location_cm": list(location_values), "target_cm": list(target_values), "focal_length_mm": focal_length})

hero_location = unreal.Vector(*CAMERAS[0][1])
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero_location, aim(hero_location, unreal.Vector(*CAMERAS[0][2])))
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate open-air composition")

protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed during candidate-only composition correction")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__OPEN_AIR_COMPOSITION_RESTORED_WITH_MESHY_HERO_AND_SEPARATE_COIL_STAGE",
    "candidate_map": MAP,
    "hidden_candidate_only_obstructions": hidden,
    "sun_rotation": [-38.0, 152.0, 0.0],
    "b_stylized": {"fixtures": 6, "lumens_each": 1200, "sun_intensity": 0.30, "sky_intensity": 0.20, "exposure_bias": -0.50},
    "cameras": camera_rows,
    "new_meshy_generation_or_edit": False,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_OPENAIR_COMPOSITION_V006_PASS")
