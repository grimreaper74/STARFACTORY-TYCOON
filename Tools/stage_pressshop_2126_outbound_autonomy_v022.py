"""Extend the roofless 2126 candidate around existing real outbound assets.

This adds only the large floor/backdrop architecture needed to frame the
already-present vision gate, inspected-panel stillage and S06 handling robot.
No synthetic machines, wheels or micro-props are introduced.
"""

import hashlib
import json
import math
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
MATERIAL_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Materials"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_outbound_autonomy_v022.json"
TAG = unreal.Name("LB.PressShop.2126.OutboundAutonomy.v022")
CUBE = "/Engine/BasicShapes/Cube"
REQUIRED_EQUIPMENT = (
    "MESHY | S06 Vision / outfeed | reused press asset",
    "ROBOT | S06 | vision stack robot",
    "OUTBOUND | real vision inspection gate",
    "OUTBOUND | inspected panel stillage",
)


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


def create_architecture(label, location, dimensions, material, semantic):
    mesh = unreal.load_asset(CUBE)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("Native architectural cube is unavailable")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        raise RuntimeError("Could not create " + label)
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_world_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    actor.static_mesh_component.set_material(0, material)
    actor.tags = [TAG, unreal.Name("LB.Architecture.OpenAir"), unreal.Name(semantic)]
    return actor


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Outbound autonomy v022 already staged")
for label in REQUIRED_EQUIPMENT:
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError("Required existing automation asset missing: " + label)
    components = actor.get_components_by_class(unreal.PrimitiveComponent)
    if not components or not all(component.is_visible() for component in components):
        raise RuntimeError("Required existing automation asset is hidden: " + label)

pale_green = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_PaintedPaleGreen")
cream = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_CreamLane")
warm_white = unreal.load_asset(MATERIAL_ROOT + "/M_LB_PS2126_WarmWhite")
if not all(isinstance(value, unreal.Material) for value in (pale_green, cream, warm_white)):
    raise RuntimeError("Candidate architectural materials missing")

floor = create_architecture(
    "2126 | pale-green outbound automation field | open-air",
    (11500.0, 0.0, -20.0), (10500.0, 9600.0, 20.0), pale_green, "LB.Architecture.Paint"
)
lane = create_architecture(
    "2126 | cream outbound operator avenue | open-air",
    (11500.0, -3450.0, 2.0), (10500.0, 1200.0, 26.0), cream, "LB.Architecture.Paint"
)
wall = create_architecture(
    "2126 | warm-white outbound back wall | open-air",
    (11500.0, 4700.0, 3400.0), (10500.0, 200.0, 6800.0), warm_white, "LB.Architecture.Backdrop"
)
band = create_architecture(
    "2126 | Cairnwell-green outbound supervision band",
    (11500.0, 4580.0, 1650.0), (10300.0, 60.0, 1100.0), pale_green, "LB.Architecture.Backdrop"
)

camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.CineCameraActor, unreal.Vector(16500.0, -6800.0, 1900.0), unreal.Rotator()
)
if not isinstance(camera, unreal.CineCameraActor):
    raise RuntimeError("Could not create outbound review camera")
camera.set_actor_label("CAM | 2126 outbound autonomy")
camera_location = unreal.Vector(16500.0, -6800.0, 1900.0)
camera.set_actor_rotation(aim(camera_location, unreal.Vector(9000.0, 0.0, 1100.0)), False)
camera.get_cine_camera_component().set_editor_property("current_focal_length", 48.0)
camera.tags = [TAG, unreal.Name("LB.PressShop.Candidate.Camera")]

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__OUTBOUND_AUTONOMY_FRAMED_WITH_EXISTING_REAL_EQUIPMENT",
    "existing_equipment_reused": list(REQUIRED_EQUIPMENT),
    "new_architecture": [floor.get_actor_label(), lane.get_actor_label(), wall.get_actor_label(), band.get_actor_label()],
    "new_machine_geometry": False,
    "roof_created": False,
    "camera": {"label": camera.get_actor_label(), "location_cm": [16500, -6800, 1900], "target_cm": [9000, 0, 1100], "focal_length_mm": 48.0},
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_OUTBOUND_AUTONOMY_V022_PASS")
