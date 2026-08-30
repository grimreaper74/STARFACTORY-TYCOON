"""Read-only scene audit for the isolated Press Shop v003 candidate."""
import hashlib
import json
from pathlib import Path

import unreal

# Unreal exposes this as an engine-relative string in some editor launch modes;
# use the known project root so the immutable-map guard always hashes the file
# the user has asked us to protect.
PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_scene_audit_v039.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
EXPECTED = {
    PROTECTED: "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    V002: "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path, expected in EXPECTED.items():
    actual = digest(path).lower()
    if actual != expected:
        raise RuntimeError("Protected baseline changed before audit: " + str(path) + " expected=" + expected + " actual=" + actual)

rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if not (label.startswith("2126 v003") or label.startswith("CAM v003")):
        continue
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    bounds = actor.get_actor_bounds(False)
    center, extent = bounds
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
        "rotation": [round(rot.roll, 1), round(rot.pitch, 1), round(rot.yaw, 1)],
        "bounds_center_cm": [round(center.x, 1), round(center.y, 1), round(center.z, 1)],
        "bounds_extent_cm": [round(extent.x, 1), round(extent.y, 1), round(extent.z, 1)],
        "tags": [str(tag) for tag in actor.tags],
    })

for path, expected in EXPECTED.items():
    if digest(path).lower() != expected:
        raise RuntimeError("Protected baseline changed during audit: " + str(path))

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__READ_ONLY_V003_SCENE_AUDIT",
    "candidate": "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003",
    "protected_hashes": {str(path): digest(path) for path in EXPECTED},
    "actors": sorted(rows, key=lambda row: row["label"]),
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_SCENE_AUDIT_V039_PASS")
