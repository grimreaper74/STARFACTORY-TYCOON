"""Stage one sparse, roofless 2126 press hall around the real imported machines.

The only native primitives in this pass are architectural: painted floor field,
operator lane, back wall, and a single automated overhead-handling silhouette.
No machine blockouts or new props are created here.
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
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_openair_hall_v016.json"
TAG = unreal.Name("LB.PressShop.2126.OpenAirHall.v016")
CUBE = "/Engine/BasicShapes/Cube"


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
    cube = unreal.load_asset(CUBE)
    if not isinstance(cube, unreal.StaticMesh):
        raise RuntimeError("Native architectural cube is unavailable")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator()
    )
    if actor is None:
        raise RuntimeError("Could not create " + label)
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(cube)
    actor.static_mesh_component.set_world_scale3d(
        unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0)
    )
    actor.static_mesh_component.set_material(0, material)
    actor.tags = [TAG, unreal.Name("LB.Architecture.OpenAir"), unreal.Name(semantic)]
    return actor


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Open-air hall v016 is already staged")

materials = {}
for name in ("M_LB_PS2126_PaintedPaleGreen", "M_LB_PS2126_CreamLane", "M_LB_PS2126_WarmWhite", "M_LB_PS2126_SteelGrey", "M_LB_PS2126_SafetyYellow"):
    value = unreal.load_asset(MATERIAL_ROOT + "/" + name)
    if not isinstance(value, unreal.Material):
        raise RuntimeError("Missing candidate material " + name)
    materials[name] = value

# The floor is a legible production field, not a second machine or a roofed box.
floor = create_architecture(
    "2126 | pale-green press production field | open-air",
    (-6500.0, 0.0, -20.0), (28000.0, 9600.0, 20.0),
    materials["M_LB_PS2126_PaintedPaleGreen"], "LB.Architecture.Paint"
)
lane = create_architecture(
    "2126 | cream operator avenue | open-air",
    (-6500.0, -3450.0, 2.0), (28000.0, 1200.0, 26.0),
    materials["M_LB_PS2126_CreamLane"], "LB.Architecture.Paint"
)
wall = create_architecture(
    "2126 | warm-white press hall back wall | open-air",
    (-6500.0, 4700.0, 3400.0), (28000.0, 200.0, 6800.0),
    materials["M_LB_PS2126_WarmWhite"], "LB.Architecture.Backdrop"
)
supervision_band = create_architecture(
    "2126 | Cairnwell-green press hall supervision band",
    (-6500.0, 4580.0, 1650.0), (27800.0, 60.0, 1100.0),
    materials["M_LB_PS2126_PaintedPaleGreen"], "LB.Architecture.Backdrop"
)

# One strong autonomous rail crane: two endpoints, one beam, one parked carriage.
# It is intentionally a silhouette only; there are no roof trusses or cable clutter.
crane_left = create_architecture(
    "2126 | autonomous overhead rail left endpoint",
    (-20000.0, 2500.0, 3150.0), (300.0, 500.0, 6300.0),
    materials["M_LB_PS2126_SteelGrey"], "LB.Architecture.OverheadHandling"
)
crane_right = create_architecture(
    "2126 | autonomous overhead rail right endpoint",
    (7000.0, 2500.0, 3150.0), (300.0, 500.0, 6300.0),
    materials["M_LB_PS2126_SteelGrey"], "LB.Architecture.OverheadHandling"
)
crane_beam = create_architecture(
    "2126 | autonomous overhead handling rail | open-air",
    (-6500.0, 2500.0, 6300.0), (27300.0, 320.0, 260.0),
    materials["M_LB_PS2126_SteelGrey"], "LB.Architecture.OverheadHandling"
)
crane_carriage = create_architecture(
    "2126 | autonomous overhead rail carriage | parked",
    (-5200.0, 2500.0, 6020.0), (720.0, 620.0, 430.0),
    materials["M_LB_PS2126_SafetyYellow"],
    "LB.Architecture.OverheadHandling"
)

hero = actors.get("CAM | 2126 Steam hero overview")
if not isinstance(hero, unreal.CineCameraActor):
    raise RuntimeError("Hero camera missing")
hero_location = unreal.Vector(-24500.0, -16600.0, 6100.0)
hero.set_actor_location(hero_location, False, False)
hero.set_actor_rotation(aim(hero_location, unreal.Vector(-6500.0, 300.0, 2550.0)), False)
hero.get_cine_camera_component().set_editor_property("current_focal_length", 46.0)
hero.tags = list(hero.tags) + [TAG]

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate level")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 map changed")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__ROOFLESS_2126_HALL_STAGED_AROUND_EXISTING_REAL_MESHY_MACHINE_LINE",
    "machine_policy": "No machine blockouts or prop clutter introduced; five imported Meshy press assets, feeder, and two approved coils remain the production equipment.",
    "new_architecture": [actor.get_actor_label() for actor in (floor, lane, wall, supervision_band, crane_left, crane_right, crane_beam, crane_carriage)],
    "roof_created": False,
    "hero_camera": {"location_cm": [-24500, -16600, 6100], "target_cm": [-6500, 300, 2550], "focal_length_mm": 46.0},
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_OPENAIR_HALL_V016_PASS")
