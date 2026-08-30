"""Give the real Meshy press run readable station identities and story cameras.

This changes only actor material overrides and cameras in the isolated v003
candidate.  It never alters a source mesh, source material, v002, or v438.
"""
import hashlib
import json
import math
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Materials"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_station_identity_v033.json"
TAG = unreal.Name("LB.PressShop.2126.v003.StationIdentity.v033")
SOURCE_MESHES = {
    "S02": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S02_DrawForm_MeshyClean_v001",
    "S03": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S03_Trim_MeshyClean_v001",
    "S04": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S04_Pierce_MeshyClean_v001",
    "S05": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S05_FlangeHem_MeshyClean_v001",
    "S06": "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/SM_LB_PS_S06_VisionOutfeed_MeshyClean_v001",
}


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def source_uasset(path):
    return PROJECT / "Content" / (path.removeprefix("/Game/").replace("/", "\\") + ".uasset")


def aim(source, target):
    dx, dy, dz = target.x - source.x, target.y - source.y, target.z - source.z
    return unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy))), yaw=math.degrees(math.atan2(dy, dx)))


def material(name):
    result = unreal.load_asset(ROOT + "/" + name)
    if not isinstance(result, unreal.MaterialInterface):
        raise RuntimeError("Candidate material unavailable: " + name)
    return result


def set_paint(actor, order):
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Expected mesh actor: " + actor.get_actor_label())
    for slot, value in enumerate(order):
        actor.static_mesh_component.set_material(slot, value)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.Visual.StationIdentity")]


if not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Protected evidence map missing")
protected_before, v002_before = digest(PROTECTED), digest(V002)
source_before = {path: digest(source_uasset(path)) for path in SOURCE_MESHES.values()}
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load isolated v003 candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Station-identity v033 already applied")

charcoal = material("M_LB_PS2126v003_FoundryCharcoal")
warm_white = material("M_LB_PS2126v003_WarmWhite")
red = material("M_LB_PS2126v003_StatusRed")
yellow = material("M_LB_PS2126v003_SafetyYellow")
steel = material("M_LB_PS2126v003_SteelGrey")
green = material("M_LB_PS2126v003_CairnwellGreen")

# Meshy uses the sixth slot for each machine's dominant shell.  We vary only
# candidate actor overrides: clear, broad colour roles at management distance.
palette = {
    "2126 v003 | 02 | draw / form": (charcoal, green, red, yellow, steel, warm_white),
    "2126 v003 | 03 | trim": (charcoal, warm_white, red, yellow, steel, green),
    "2126 v003 | 04 | pierce": (charcoal, warm_white, red, yellow, green, steel),
    "2126 v003 | 05 | flange / hem": (charcoal, green, red, yellow, steel, warm_white),
    "2126 v003 | 06 | vision / outfeed": (charcoal, warm_white, red, yellow, green, steel),
}
for label, order in palette.items():
    if label not in actors:
        raise RuntimeError("Press actor missing: " + label)
    set_paint(actors[label], order)

def add_camera(label, source, target, focal, beat):
    if label in actors:
        raise RuntimeError("Camera label already exists: " + label)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CineCameraActor, source, aim(source, target))
    if not isinstance(actor, unreal.CineCameraActor):
        raise RuntimeError("Could not create story camera: " + label)
    actor.set_actor_label(label)
    actor.get_cine_camera_component().set_editor_property("current_focal_length", focal)
    actor.tags = [TAG, unreal.Name("LB.ManagementCamera." + beat)]
    return actor


infeed = add_camera(
    "CAM v003 | coil to first press story",
    unreal.Vector(-7000.0, -7800.0, 3100.0),
    unreal.Vector(-3900.0, 100.0, 360.0),
    48.0,
    "Infeed",
)
outfeed = add_camera(
    "CAM v003 | inspection to stillage story",
    unreal.Vector(7600.0, -7600.0, 3050.0),
    unreal.Vector(4650.0, 100.0, 280.0),
    50.0,
    "Outfeed",
)

if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save isolated v003 candidate")
protected_after, v002_after = digest(PROTECTED), digest(V002)
source_after = {path: digest(source_uasset(path)) for path in SOURCE_MESHES.values()}
if protected_before != protected_after or v002_before != v002_after or source_before != source_after:
    raise RuntimeError("Protected map or source mesh changed during v033")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__MESHY_STATION_IDENTITY_AND_STORY_CAMERAS_AUTHORED",
    "candidate_map": MAP,
    "presses_repainted_via_candidate_actor_overrides": list(palette),
    "cameras": {
        "infeed": infeed.get_actor_label(),
        "outfeed": outfeed.get_actor_label(),
    },
    "roof_created": False,
    "source_mesh_hashes_before": source_before,
    "source_mesh_hashes_after": source_after,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_STATION_IDENTITY_V033_PASS")
