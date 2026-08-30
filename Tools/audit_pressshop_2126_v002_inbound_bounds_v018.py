"""Read-only bounds audit for the separate inbound coil story."""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_inbound_bounds_v018.json"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def row(actor):
    origin, extent = actor.get_actor_bounds(False, True)
    location = actor.get_actor_location()
    return {
        "label": actor.get_actor_label(),
        "actor_location_cm": [round(location.x, 2), round(location.y, 2), round(location.z, 2)],
        "bounds_origin_cm": [round(origin.x, 2), round(origin.y, 2), round(origin.z, 2)],
        "bounds_extent_cm": [round(extent.x, 2), round(extent.y, 2), round(extent.z, 2)],
        "bounds_min_cm": [round(origin.x - extent.x, 2), round(origin.y - extent.y, 2), round(origin.z - extent.z, 2)],
        "bounds_max_cm": [round(origin.x + extent.x, 2), round(origin.y + extent.y, 2), round(origin.z + extent.z, 2)],
    }


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map missing")
before = digest(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate v002")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
labels = (
    "S00 | wrapped master coil | project reuse",
    "S00 | wrapped coil changeover saddle | kit reuse",
    "S00 | bare master coil | project reuse",
    "S00 | Meshy coil-free autonomous feeder",
    "MESHY v002 | S02 Draw / form",
)
rows = []
for label in labels:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Missing inbound actor " + label)
    rows.append(row(actor))
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Read-only inbound audit changed protected v438")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__READ_ONLY_INBOUND_BOUNDS_MEASURED",
    "candidate_map": MAP,
    "actors": rows,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_INBOUND_BOUNDS_AUDIT_V018_PASS")
