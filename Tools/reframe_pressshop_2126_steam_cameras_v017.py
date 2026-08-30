"""Reframe the roofless candidate around its real Meshy machine groups.

This pass changes no geometry, materials, or protected maps. It separates the
five-press hero from the feeder-and-coil close-up so each real machine group is
large enough to carry a Steam screenshot.
"""

import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_steam_cameras_v017.json"
TAG = unreal.Name("LB.PressShop.2126.SteamCameras.v017")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))),
        yaw=math.degrees(math.atan2(dy, dx)),
        roll=0.0,
    )


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Camera pass v017 already applied")

shots = {
    # Five-machine production spine: deliberate diagonal rather than a distant aerial.
    "CAM | 2126 Steam hero overview": ((-8500.0, -10800.0, 3000.0), (-250.0, 0.0, 1900.0), 48.0),
    # Infeed is its own feature shot: one stripped Meshy feeder plus approved bare coil.
    "CAM | 2126 operator line": ((-17700.0, -5500.0, 1050.0), (-13200.0, 0.0, 450.0), 52.0),
    # Draw press is a close production detail, still with the automated floor visible.
    "CAM | 2126 draw nexus": ((-8300.0, -4800.0, 2250.0), (-4200.0, 0.0, 1950.0), 50.0),
}
applied = {}
for label, (location_values, target_values, focal_length) in shots.items():
    camera = actors.get(label)
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Missing camera " + label)
    location = unreal.Vector(*location_values)
    camera.set_actor_location(location, False, False)
    camera.set_actor_rotation(aim(location, unreal.Vector(*target_values)), False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    camera.tags = list(camera.tags) + [TAG]
    applied[label] = {"location_cm": list(location_values), "target_cm": list(target_values), "focal_length_mm": focal_length}

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__CAMERAS_REFRAMED_AROUND_REAL_MESHY_MACHINE_GROUPS",
    "geometry_changed": False,
    "shots": applied,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_STEAM_CAMERAS_V017_PASS")
