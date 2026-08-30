"""Frame the isolated 2126 press candidate with a roofless perimeter elevation.

These are broad architectural panels, not new machine geometry: they give the
open-air candidate a credible, screenshot-friendly horizon while preserving an
entirely open roof and all supplied Meshy/reused production assets.
"""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
MATERIALS = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_open_air_perimeter_v035.json"
TAG = unreal.Name("LB.PressShop.2126.v003.OpenAirPerimeter.v035")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def material(name):
    result = unreal.load_asset(MATERIALS + "/" + name)
    if not isinstance(result, unreal.MaterialInterface):
        raise RuntimeError("Candidate material missing: " + name)
    return result


def cube(label, location, dimensions_cm, value, tags=()):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Could not create open-air architecture: " + label)
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(cube_mesh)
    actor.static_mesh_component.set_world_scale3d(unreal.Vector(*(size / 100.0 for size in dimensions_cm)))
    actor.static_mesh_component.set_material(0, value)
    actor.tags = [TAG] + list(tags)
    return actor


if not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Protected evidence map missing")
protected_before, v002_before = digest(PROTECTED), digest(V002)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load isolated v003 candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Open-air perimeter v035 already applied")
sun = actors.get("2126 v003 | open-air directional sun")
if not isinstance(sun, unreal.DirectionalLight):
    raise RuntimeError("Open-air directional light missing")
cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
if not isinstance(cube_mesh, unreal.StaticMesh):
    raise RuntimeError("Native Unreal cube unavailable")
warm_white = material("M_LB_PS2126v003_WarmWhite")
green = material("M_LB_PS2126v003_CairnwellGreen")
steel = material("M_LB_PS2126v003_SteelGrey")

# Six large panels, 7.4 m high, placed beyond the service side.  Gaps are kept
# intentionally wide: an open-air factory edge rather than a continuous box.
panel_x = (-7500.0, -4500.0, -1500.0, 1500.0, 4500.0, 7500.0)
panels = []
for index, x in enumerate(panel_x, start=1):
    main = warm_white if index % 2 else steel
    panels.append(cube("2126 v003 | open-air perimeter panel %02d" % index, (x, 11800.0, 370.0), (2550.0, 100.0, 740.0), main, (unreal.Name("LB.Architecture.OpenAirPerimeter"),)))
    # One large green identity blade per bay—not a railing or a field of posts.
    cube("2126 v003 | perimeter green identity blade %02d" % index, (x - 950.0, 11720.0, 390.0), (170.0, 125.0, 700.0), green, (unreal.Name("LB.Architecture.OpenAirPerimeter"),))

# A slightly steeper, low-intensity sun produces shorter readable contact
# shadows; there are still no RectLights in the candidate.
sun.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=-62.0, yaw=-28.0), False)
sun.tags = list(sun.tags) + [TAG]

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save isolated v003 candidate")
protected_after, v002_after = digest(PROTECTED), digest(V002)
if protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Protected map changed during v035")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__ROOFLESS_OPEN_AIR_PERIMETER_FRAMED",
    "candidate_map": MAP,
    "native_architecture": {"perimeter_panels": len(panels), "green_identity_blades": len(panels), "new_machine_geometry": 0},
    "lighting": {"sun_pitch_degrees": -62.0, "rect_lights_active": 0},
    "roof_created": False,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_OPEN_AIR_PERIMETER_V035_PASS")
