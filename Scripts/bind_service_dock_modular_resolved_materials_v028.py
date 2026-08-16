"""Bind v026 modular meshes to the retained resolved aggregate material set."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

PROJECT = Path(unreal.Paths.project_dir()).resolve()
OUT = Path(unreal.Paths.project_saved_dir()).resolve() / "Audits/SupportRobots/service_dock_modular_resolved_material_bind_v028.json"
SOURCES = {
    "mr01": "/Game/LineBoss/SupportRobots/ServiceDocks/Resolved_v006/SM_LB_MR01_ServiceDock_ResolvedMaterials_v006",
    "cr01": "/Game/LineBoss/SupportRobots/ServiceDocks/Resolved_v006/SM_LB_CR01_ServiceDock_ResolvedMaterials_v006",
}
TARGET_ROOTS = {
    "mr01": "/Game/LineBoss/SupportRobots/ServiceDocks/Runtime_v026/MR01",
    "cr01": "/Game/LineBoss/SupportRobots/ServiceDocks/Runtime_v026/CR01",
}

def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()

lib = unreal.EditorAssetLibrary
records = []
for mode, source_path in SOURCES.items():
    source = lib.load_asset(source_path)
    if not isinstance(source, unreal.StaticMesh):
        raise RuntimeError(f"resolved source mesh missing: {source_path}")
    resolved = {}
    for slot in source.get_editor_property("static_materials"):
        material = slot.material_interface
        if material:
            resolved[str(slot.material_slot_name)] = material
    if not resolved:
        raise RuntimeError(f"resolved source has no assigned materials: {source_path}")

    target_paths = lib.list_assets(TARGET_ROOTS[mode], recursive=True, include_folder=False)
    # list_assets returns object paths with .Asset suffix; load_asset handles both.
    for target_path in target_paths:
        mesh = lib.load_asset(target_path)
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        package_file = PROJECT / "Content" / Path(mesh.get_path_name().split(".")[0].removeprefix("/Game/") + ".uasset")
        before = sha256(package_file)
        assignments = []
        missing = []
        for index, slot in enumerate(mesh.get_editor_property("static_materials")):
            slot_name = str(slot.material_slot_name)
            material = resolved.get(slot_name)
            if material is None:
                missing.append(slot_name)
                continue
            mesh.set_material(index, material)
            assignments.append({"index": index, "slot": slot_name, "material": material.get_path_name()})
        if missing:
            raise RuntimeError(f"{mesh.get_path_name()} has unresolved material slots: {missing}")
        lib.save_loaded_asset(mesh, only_if_is_dirty=False)
        records.append({
            "mode": mode, "mesh": mesh.get_path_name(), "source": source.get_path_name(),
            "assignments": assignments, "uasset_sha256_before": before,
            "uasset_sha256_after": sha256(package_file),
        })

if len(records) != 5:
    raise RuntimeError(f"expected five modular meshes, bound {len(records)}")
payload = {
    "$schema": "cairnwell/audit/service-dock-modular-resolved-material-bind-v028/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__RETAINED_RESOLVED_MATERIALS_BOUND_TO_FIVE_MODULAR_MESHES__VISUAL_GATE_OPEN__NOT_PROMOTED",
    "records": records,
    "policy": "No new palette; exact named slots reuse retained Resolved_v006 materials",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_SERVICE_DOCK_MODULAR_MATERIAL_BIND_V028_PASS")
