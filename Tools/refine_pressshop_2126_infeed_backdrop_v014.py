"""Prune obsolete cyan infeed pucks and restore roofless factory back walls."""

import hashlib
import json
import math
from pathlib import Path
import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_infeed_backdrop_v014.json"
TAG = unreal.Name("LB.PressShop.2126.InfeedBackdrop.v014")
PADS = (
    "S00 | field pad left 0", "S00 | field pad left 1",
    "S00 | field pad right 0", "S00 | field pad right 1",
)
WALLS = (
    "2126 | rear production facade pale-green supervision band",
    "2126 | rear production facade inbound field",
)
CAMERA = "CAM | 2126 operator line"


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)), roll=0.0)


def show(actor):
    actor.set_actor_hidden_in_game(False)
    actor.set_is_temporarily_hidden_in_editor(False)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(True, True)


def hide(actor):
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        component.set_visibility(False, True)


before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("infeed backdrop v014 already applied")
for label in PADS:
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError("Missing obsolete infeed puck: " + label)
    hide(actor)
    actor.tags = list(actor.tags) + [TAG]
for label in WALLS:
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError("Missing candidate back wall: " + label)
    show(actor)
    actor.tags = list(actor.tags) + [TAG]

camera = actors.get(CAMERA)
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Missing infeed camera")
location = unreal.Vector(-19000.0, -6000.0, 950.0)
camera.set_actor_location(location, False, False)
camera.set_actor_rotation(aim(location, unreal.Vector(-13200.0, 0.0, 280.0)), False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 52.0)
camera.tags = list(camera.tags) + [TAG]

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
after = sha256(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__CYAN_PLACEHOLDERS_HIDDEN_AND_ROOFLESS_BACKDROPS_RESTORED",
    "hidden_cyan_placeholder_pucks": list(PADS),
    "visible_roofless_back_walls": list(WALLS),
    "camera": {"label": CAMERA, "location_cm": [-19000, -6000, 950], "target_cm": [-13200, 0, 280], "focal_length_mm": 52.0},
    "roof_created": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_INFEED_BACKDROP_V014_PASS")
