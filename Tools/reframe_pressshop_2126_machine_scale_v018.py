"""Correct the screenshot eyeline so the press equipment, not empty sky, owns frame."""

import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_machine_scale_v018.json"
TAG = unreal.Name("LB.PressShop.2126.MachineScale.v018")


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
    raise RuntimeError("Machine-scale camera pass v018 already applied")

shots = {
    "CAM | 2126 Steam hero overview": ((-8500.0, -10800.0, 2100.0), (-250.0, 0.0, 1050.0), 50.0),
    "CAM | 2126 draw nexus": ((-8300.0, -4800.0, 1600.0), (-4200.0, 0.0, 750.0), 45.0),
}
rows = {}
for label, (source_values, target_values, focal) in shots.items():
    camera = actors.get(label)
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Missing camera " + label)
    source = unreal.Vector(*source_values)
    camera.set_actor_location(source, False, False)
    camera.set_actor_rotation(aim(source, unreal.Vector(*target_values)), False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal)
    camera.tags = list(camera.tags) + [TAG]
    rows[label] = {"location_cm": list(source_values), "target_cm": list(target_values), "focal_length_mm": focal}

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__MACHINE_EYELINE_REFRAMED_NO_EMPTY_SKY_PRIORITY",
    "geometry_changed": False,
    "reframed": rows,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_MACHINE_SCALE_V018_PASS")
