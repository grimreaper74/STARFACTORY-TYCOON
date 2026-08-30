"""Create a readable roofless production backdrop and human-scale review cameras.

The v003 live-D3D review confirmed that the actual Meshy machines are present
and clean, while also rejecting the purely open-sky treatment: the old cameras
looked down from 24–56 m and placed 8 m machines against an empty blue void.
This candidate-only pass keeps the deck roofless, adds a large rear production
facade on the service side, and resets the three Steam review cameras to
machine-scale compositions.  It does not modify any reused mesh or protected
map.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_backdrop_cameras_v003.json"
MATERIAL_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Materials"
TAG = unreal.Name("LB.PressShop.2126.SteamBackdrop.v003")
CUBE_PATH = "/Engine/BasicShapes/Cube"

CAMERAS = (
    # Full line: the five real Meshy press assets span roughly 77 m, so the
    # 50 mm lens at this distance makes the line fill the width rather than
    # read as floor decoration.
    ("CAM | 2126 Steam hero overview", (-11500.0, -9000.0, 850.0), (-300.0, 0.0, 500.0), 50.0),
    # Operator-side medium shot: three different press silhouettes, transfer
    # hardware and robotic cue all remain legible at Steam-card scale.
    ("CAM | 2126 operator line", (-8500.0, -5500.0, 700.0), (-2700.0, 0.0, 500.0), 55.0),
    # Draw-cell proof shot: one repaired Meshy machine holds the frame.
    ("CAM | 2126 draw nexus", (-8500.0, -3200.0, 650.0), (-4200.0, 0.0, 450.0), 70.0),
)


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


def require_material(name):
    material = unreal.load_asset(MATERIAL_ROOT + "/" + name)
    if not isinstance(material, unreal.Material):
        raise RuntimeError("Candidate material unavailable: " + name)
    return material


def box(label, location, dimensions, material):
    cube = unreal.load_asset(CUBE_PATH)
    if not isinstance(cube, unreal.StaticMesh):
        raise RuntimeError("Native Unreal cube unavailable")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        raise RuntimeError("Could not create backdrop actor: " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, unreal.Name("LB.Visual.2126"), unreal.Name("LB.PressShop.Candidate")]
    component = actor.static_mesh_component
    component.set_static_mesh(cube)
    component.set_world_scale3d(unreal.Vector(
        dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component.set_material(0, material)
    return actor


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load fresh candidate map")

all_actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in all_actors):
    raise RuntimeError("Steam backdrop v003 tag already exists; refusing duplicate pass")
by_label = {actor.get_actor_label(): actor for actor in all_actors}

warm_white = require_material("M_LB_PS2126_WarmWhite")
green = require_material("M_LB_PS2126_CairnwellGreen")
charcoal = require_material("M_LB_PS2126_FoundryCharcoal")
yellow = require_material("M_LB_PS2126_SafetyYellow")
cyan = require_material("M_LB_PS2126_OpticalCyan")

# A single service-side facade makes an outdoor/roofless production campus
# legible in a frame.  It has no roof or enclosure: only the rear elevation
# behind the process train.
created = []
for label, location, dimensions, material in (
    ("2126 | rear production facade warm-white field", (-250.0, 8050.0, 6000.0), (17400.0, 340.0, 12000.0), warm_white),
    ("2126 | rear production facade foundry plinth", (-250.0, 7800.0, 1100.0), (17800.0, 820.0, 2200.0), charcoal),
    ("2126 | rear production facade Cairnwell band", (-250.0, 7770.0, 4600.0), (17800.0, 880.0, 2500.0), green),
    ("2126 | rear production facade safety datum", (-250.0, 7580.0, 6200.0), (17800.0, 380.0, 240.0), yellow),
):
    created.append(box(label, location, dimensions, material).get_actor_label())

# Five strong, widely spaced optical pucks make the facade read as a future
# supervised line. They are not a repeated micro-prop field.
for index, x in enumerate((-6500.0, -3500.0, -500.0, 2500.0, 5500.0), start=1):
    created.append(box("2126 | rear facade optical supervision %d" % index,
                       (x, 7470.0, 8050.0), (1000.0, 220.0, 540.0), cyan).get_actor_label())

camera_rows = []
for label, location_values, target_values, focal_length in CAMERAS:
    camera_actor = by_label.get(label)
    if camera_actor is None or not isinstance(camera_actor, unreal.CineCameraActor):
        raise RuntimeError("Missing review camera: " + label)
    location = unreal.Vector(*location_values)
    target = unreal.Vector(*target_values)
    rotation = aim(location, target)
    camera_actor.set_actor_location(location, False, False)
    camera_actor.set_actor_rotation(rotation, False)
    camera_actor.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    forward = camera_actor.get_actor_forward_vector()
    camera_rows.append({
        "label": label,
        "location_cm": list(location_values),
        "target_cm": list(target_values),
        "rotation": [rotation.pitch, rotation.yaw, rotation.roll],
        "forward": [forward.x, forward.y, forward.z],
        "focal_length_mm": focal_length,
    })

hero_location = unreal.Vector(*CAMERAS[0][1])
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero_location, aim(hero_location, unreal.Vector(*CAMERAS[0][2])))
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save the refined fresh candidate")

protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed during candidate-only backdrop pass")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__CANDIDATE_V003_MACHINE_SCALE_CAMERAS_AND_ROOFLESS_REAR_FACADE_AUTHORED",
    "candidate_map": MAP,
    "created_candidate_only_actors": created,
    "camera_rows": camera_rows,
    "roof_created": False,
    "new_meshy_generation_or_edit": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
    "reason": "Live-D3D v003 capture rejected blue-void, aerial framing although the real Meshy press actors were present.",
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_BACKDROP_CAMERAS_V003_PASS: created=%d cameras=%d" % (len(created), len(camera_rows)))
