"""Create clean dock-mesh successors with retained v005 materials at asset level."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
INVENTORY = ROOT / "Saved/Audits/SupportRobots/service_dock_actor_assets_v024.json"
OUT = ROOT / "Saved/Audits/SupportRobots/service_dock_resolved_meshes_build_v006.json"
DEST = "/Game/LineBoss/SupportRobots/ServiceDocks/Resolved_v006"
V253 = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253.umap"
V255 = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v255.umap"
LIB = unreal.EditorAssetLibrary


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if not INVENTORY.exists():
    raise RuntimeError(INVENTORY)
v253_before = sha256(V253)
v255_before = sha256(V255)
inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
outputs = {}

for row in inventory["actors"]:
    family = "MR01" if "MR01" in row["label"] else "CR01"
    source_path = row["mesh"].split(".")[0]
    asset_name = f"SM_LB_{family}_ServiceDock_ResolvedMaterials_v006"
    destination = f"{DEST}/{asset_name}"
    if LIB.does_asset_exist(destination):
        raise RuntimeError(f"Refusing to overwrite {destination}")
    mesh = LIB.duplicate_asset(source_path, destination)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Could not duplicate {source_path}")
    static_materials = list(mesh.get_editor_property("static_materials"))
    if len(static_materials) != len(row["materials"]):
        raise RuntimeError(f"{family} slot mismatch {len(static_materials)} != {len(row['materials'])}")
    bindings = []
    for index, material_path in enumerate(row["materials"]):
        material = LIB.load_asset(material_path)
        if not isinstance(material, unreal.MaterialInterface):
            raise RuntimeError(f"Missing retained material {material_path}")
        slot = static_materials[index]
        slot.set_editor_property("material_interface", material)
        bindings.append({
            "index": index,
            "slot_name": str(slot.get_editor_property("material_slot_name")),
            "material": material.get_path_name(),
        })
    mesh.set_editor_property("static_materials", static_materials)
    if not LIB.save_loaded_asset(mesh, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save {destination}")
    package_file = ROOT / "Content" / Path(destination.removeprefix("/Game/") + ".uasset")
    outputs[family] = {
        "source": source_path,
        "resolved": destination,
        "slot_count": len(bindings),
        "bindings": bindings,
        "sha256": sha256(package_file),
    }

v253_after = sha256(V253)
v255_after = sha256(V255)
if v253_before != v253_after or v255_before != v255_after:
    raise RuntimeError("Protected map changed while resolving dock meshes")

payload = {
    "$schema": "cairnwell/audit/service-dock-resolved-meshes-build-v006/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_DOCK_MESH_SUCCESSORS_REFERENCE_ONLY_RETAINED_V005_MATERIALS__LOAD_REAUDIT_REQUIRED__NOT_PROMOTED",
    "assets": outputs,
    "protected_v253_sha256_before": v253_before,
    "protected_v253_sha256_after": v253_after,
    "protected_v255_sha256_before": v255_before,
    "protected_v255_sha256_after": v255_after,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_SERVICE_DOCK_RESOLVED_MESHES_V006_PASS")
unreal.SystemLibrary.quit_editor()
