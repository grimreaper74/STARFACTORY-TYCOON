"""Bring the roofless v003 perimeter into the actual screenshot horizon."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_open_air_perimeter_v036.json"
TAG = unreal.Name("LB.PressShop.2126.v003.OpenAirPerimeter.v036")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Protected evidence map missing")
protected_before, v002_before = digest(PROTECTED), digest(V002)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load isolated v003 candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Open-air perimeter v036 already applied")
labels = []
for index in range(1, 7):
    for name in ("2126 v003 | open-air perimeter panel %02d" % index, "2126 v003 | perimeter green identity blade %02d" % index):
        actor = actors.get(name)
        if not isinstance(actor, unreal.StaticMeshActor):
            raise RuntimeError("Open-air perimeter actor missing: " + name)
        location = actor.get_actor_location()
        location.y = 6700.0
        actor.set_actor_location(location, False, False)
        actor.tags = list(actor.tags) + [TAG]
        labels.append(name)
if any("roof" in actor.get_actor_label().lower() for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("Roof actor found in roofless candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save isolated v003 candidate")
protected_after, v002_after = digest(PROTECTED), digest(V002)
if protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Protected map changed during v036")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__ROOFLESS_PERIMETER_REPOSITIONED_FOR_MANAGEMENT_CAMERAS",
    "candidate_map": MAP,
    "relocated_actor_count": len(labels),
    "perimeter_y_cm_after": 6700.0,
    "roof_created": False,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_OPEN_AIR_PERIMETER_V036_PASS")
