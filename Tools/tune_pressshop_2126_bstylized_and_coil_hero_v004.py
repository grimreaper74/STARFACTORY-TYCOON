"""Tune the approved B_stylized fixtures for the compact real-Meshy line.

The B_stylized contract remains exact (six 1200 lm fixtures, 5000 K; sun 0.30;
sky 0.20; camera exposure -0.50).  Its original fixture positions came from a
much larger, superseded blockout bay, leaving the compact real-Meshy assets
underlit.  This candidate-only pass moves—not duplicates—the six approved
fixtures to practical 2126 drone-light positions, replaces the visually black
rear band with the approved pale-green floor colour, and changes the hero
camera to show the user's separate coils progressing into the first press.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_bstylized_coilhero_v004.json"
MATERIAL_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Materials"
TAG = unreal.Name("LB.PressShop.2126.BStylizedTune.v004")

FIXTURES = (
    ("2126 | B_stylized 5000K fixture 1", (-14500.0, -500.0, 1500.0)),
    ("2126 | B_stylized 5000K fixture 2", (-4300.0, -400.0, 1400.0)),
    ("2126 | B_stylized 5000K fixture 3", (-2200.0, -400.0, 1400.0)),
    ("2126 | B_stylized 5000K fixture 4", (-200.0, -400.0, 1400.0)),
    ("2126 | B_stylized 5000K fixture 5", (1800.0, -400.0, 1400.0)),
    ("2126 | B_stylized 5000K fixture 6", (3600.0, -400.0, 1400.0)),
)
HERO = ("CAM | 2126 Steam hero overview", (-24000.0, -10000.0, 900.0), (-9000.0, 0.0, 600.0), 55.0)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def create_box(label, location, dimensions, material):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    if not isinstance(cube, unreal.StaticMesh):
        raise RuntimeError("Native cube unavailable")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        raise RuntimeError("Could not create " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, unreal.Name("LB.Visual.2126"), unreal.Name("LB.PressShop.Candidate")]
    component = actor.static_mesh_component
    component.set_static_mesh(cube)
    component.set_world_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component.set_material(0, material)
    return actor


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load fresh candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("B_stylized tune v004 already exists; refusing duplicate pass")

fixture_rows = []
for label, position in FIXTURES:
    light_actor = actors.get(label)
    if light_actor is None or not isinstance(light_actor, unreal.RectLight):
        raise RuntimeError("Missing B_stylized fixture: " + label)
    component = light_actor.get_component_by_class(unreal.RectLightComponent)
    if component is None:
        raise RuntimeError("B_stylized fixture lacks RectLightComponent: " + label)
    # Fail closed on the approved calibration; we only change placement.
    if not math.isclose(float(component.get_editor_property("intensity")), 1200.0, abs_tol=0.01):
        raise RuntimeError("B_stylized fixture intensity changed: " + label)
    if not component.get_editor_property("use_temperature") or not math.isclose(float(component.get_editor_property("temperature")), 5000.0, abs_tol=0.01):
        raise RuntimeError("B_stylized fixture temperature changed: " + label)
    light_actor.set_actor_location(unreal.Vector(*position), False, False)
    light_actor.set_actor_rotation(unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0), False)
    fixture_rows.append({"label": label, "location_cm": list(position), "lumens": 1200, "kelvin": 5000})

sun = actors.get("2126 | B_stylized sun")
sky = actors.get("2126 | B_stylized sky")
if not isinstance(sun, unreal.DirectionalLight) or not isinstance(sky, unreal.SkyLight):
    raise RuntimeError("Approved B_stylized sun or sky missing")
if not math.isclose(float(sun.get_component_by_class(unreal.DirectionalLightComponent).get_editor_property("intensity")), 0.30, abs_tol=1e-4):
    raise RuntimeError("B_stylized sun intensity changed")
if not math.isclose(float(sky.get_component_by_class(unreal.SkyLightComponent).get_editor_property("intensity")), 0.20, abs_tol=1e-4):
    raise RuntimeError("B_stylized sky intensity changed")

dark_band = actors.get("2126 | rear production facade Cairnwell band")
if dark_band is None:
    raise RuntimeError("Rear facade band missing")
hide(dark_band)
pale_green = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_PaintedPaleGreen")
if not isinstance(pale_green, unreal.Material):
    raise RuntimeError("Pale-green material missing")
facade = create_box("2126 | rear production facade pale-green supervision band",
                     (-250.0, 7580.0, 4600.0), (17800.0, 380.0, 2500.0), pale_green)

# Extend the facade only around the inbound stage, so the hero can include the
# two project coils without reverting to the blue horizon that failed v003.
warm_white = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_WarmWhite")
if not isinstance(warm_white, unreal.Material):
    raise RuntimeError("Warm-white material missing")
inbound_facade = create_box("2126 | rear production facade inbound field",
                            (-13400.0, 8050.0, 6000.0), (7500.0, 340.0, 12000.0), warm_white)

camera_label, location_values, target_values, focal_length = HERO
camera = actors.get(camera_label)
if camera is None or not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Missing hero camera")
location = unreal.Vector(*location_values)
target = unreal.Vector(*target_values)
rotation = aim(location, target)
camera.set_actor_location(location, False, False)
camera.set_actor_rotation(rotation, False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(location, rotation)

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate B_stylized tuning")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed during candidate-only lighting tune")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__B_STYLIZED_CALIBRATION_REPOSITIONED_FOR_COMPACT_REAL_MESHY_LINE",
    "candidate_map": MAP,
    "fixtures": fixture_rows,
    "sun_intensity": 0.30,
    "sky_intensity": 0.20,
    "camera_exposure_bias_unchanged": -0.50,
    "hero_camera": {"location_cm": list(location_values), "target_cm": list(target_values), "focal_length_mm": focal_length},
    "candidate_only_created": [facade.get_actor_label(), inbound_facade.get_actor_label()],
    "candidate_only_hidden": [dark_band.get_actor_label()],
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
    "roof_created": False,
    "new_meshy_generation_or_edit": False,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_B_STYLIZED_COIL_HERO_V004_PASS")
