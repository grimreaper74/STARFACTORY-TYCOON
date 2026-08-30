"""Tighten live review cameras around the real Meshy press line.

Candidate-only art-direction pass.  It suppresses the repeated local transfer
rail stubs that cross the camera sightlines, while retaining the actual press,
conveyor and coil assets.  No roof, no primitive replacement machinery and no
protected-map mutation are permitted.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_camera_clarity_v008.json"
TAG = unreal.Name("LB.PressShop.2126.CameraClarity.v008")

CAMERAS = (
    # S02-S04 fill the card: the actual Meshy silhouettes now carry the hero.
    ("CAM | 2126 Steam hero overview", (-8500.0, -5500.0, 700.0), (-2100.0, 0.0, 480.0), 65.0),
    # Preserve the two project coils as a dedicated inbound material-story shot.
    ("CAM | 2126 operator line", (-19500.0, -3000.0, 320.0), (-14300.0, 0.0, 400.0), 70.0),
    # One undistracted close proof of the S02 Meshy press.
    ("CAM | 2126 draw nexus", (-7700.0, -2800.0, 550.0), (-4200.0, 0.0, 380.0), 80.0),
)
RAIL_LABELS = tuple("FLOW | reused transfer rail %d %s" % (index, side) for index in range(1, 5) for side in ("L", "R"))


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
    raise RuntimeError("Camera-clarity v008 already exists")

hidden = []
for label in RAIL_LABELS:
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError("Expected repeated transfer stub missing: " + label)
    hide(actor)
    actor.tags = list(actor.tags) + [TAG]
    hidden.append(label)

camera_rows = []
for label, location_values, target_values, focal_length in CAMERAS:
    camera = actors.get(label)
    if camera is None or not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Missing review camera: " + label)
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
    raise RuntimeError("Could not save candidate camera clarity pass")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed during candidate-only camera refinement")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__REAL_MESHY_CAMERA_SUBJECTS_CLEAR_REPEATED_RAIL_CLUTTER_HIDDEN",
    "candidate_map": MAP,
    "hidden_repeated_rail_stubs": hidden,
    "cameras": camera_rows,
    "no_new_machine_geometry": True,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_CAMERA_CLARITY_V008_PASS")
