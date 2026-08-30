"""Read-only inventory of the protected v438 Press Shop presentation map."""

import hashlib
import json
from pathlib import Path
import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
DISK = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_v438_readonly_inventory_v001.json"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


before = digest(DISK)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load protected v438 read-only")
rows = []
cameras = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    location = actor.get_actor_location()
    row = {"label": actor.get_actor_label(), "class": actor.get_class().get_name(), "location_cm": [round(location.x, 1), round(location.y, 1), round(location.z, 1)]}
    if isinstance(actor, unreal.StaticMeshActor):
        mesh = actor.static_mesh_component.static_mesh
        row["mesh"] = mesh.get_path_name() if mesh else None
    rows.append(row)
    if isinstance(actor, (unreal.CameraActor, unreal.CineCameraActor)):
        cameras.append(row)
after = digest(DISK)
if before != after:
    raise RuntimeError("Read-only v438 audit changed protected map")
payload = {
    "status": "PASS__PROTECTED_V438_READ_ONLY_INVENTORY",
    "map": MAP,
    "actor_count": len(rows),
    "cameras": cameras,
    "actor_label_sample": sorted(row["label"] for row in rows)[:400],
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_V438_READONLY_AUDIT_PASS=" + json.dumps({"actor_count": len(rows), "cameras": cameras}))
