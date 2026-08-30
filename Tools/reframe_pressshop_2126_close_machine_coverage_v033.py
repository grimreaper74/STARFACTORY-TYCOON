"""Replace weak horizon-heavy review angles with equipment-scale compositions.

The v032 wide line now proves the real assets are present, but it is not a
Steam composition.  The camera series therefore has one contextual overview
and three machine-close stories: coil into feeder, draw-cell face and robotic
transfer.  No world geometry or source asset is modified.
"""

import hashlib
import json
import math
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_close_machine_coverage_v033.json"
TAG = unreal.Name("LB.PressShop.2126.CloseMachineCoverage.v033")
CAMERAS = (
    ("CAM | 2126 Steam hero overview", (-9000.0, -7000.0, 700.0), (-1000.0, 0.0, -300.0), 35.0, "context: full five-station machine train"),
    ("CAM | 2126 operator line", (-15500.0, -2300.0, 350.0), (-13000.0, -200.0, 220.0), 65.0, "material story: separate bare coil and actual coil-free feeder"),
    ("CAM | 2126 draw nexus", (-6600.0, -3000.0, 350.0), (-4200.0, -200.0, 250.0), 65.0, "featured Meshy draw press, open die face and tending arm"),
    ("CAM | 2126 outbound autonomy", (-2600.0, -3000.0, 400.0), (-200.0, -1000.0, 250.0), 65.0, "real S04 press and reused robot hand-off"),
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def unreal_camera_aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    elevation = math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy)))
    return unreal.Rotator(pitch=-elevation, yaw=math.degrees(math.atan2(dy, dx)), roll=0.0)


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Close-machine camera pass v033 already applied")
rows = []
for label, source_values, target_values, focal_length, purpose in CAMERAS:
    camera = actors.get(label)
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Missing named review camera: " + label)
    source = unreal.Vector(*source_values)
    target = unreal.Vector(*target_values)
    rotation = unreal_camera_aim(source, target)
    camera.set_actor_location(source, False, False)
    camera.set_actor_rotation(rotation, False)
    camera.get_cine_camera_component().set_editor_property("current_focal_length", focal_length)
    camera.tags = list(camera.tags) + [TAG]
    rows.append({"label": label, "source_cm": list(source_values), "target_cm": list(target_values), "focal_length_mm": focal_length, "story": purpose})

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__CAMERAS_COMPOSED_AT_REAL_MACHINE_SCALE",
    "camera_rows": rows,
    "change_scope": "candidate camera transforms and lenses only",
    "no_machine_mesh_material_light_or_actor_transform_changed": True,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_CLOSE_MACHINE_COVERAGE_V033_PASS")
