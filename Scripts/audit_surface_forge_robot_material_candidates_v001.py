"""Mount the completed Surface Forge Fab vault content read-only and audit robot-suitable materials.

The script runs from the canonical Line Boss project.  It does not save or modify
the Vault content; the caller exposes it through a temporary read-only directory
junction at ``Content/Surface_Forge`` for this audit, then removes that junction.
The script only scans assets, resolves dependencies, and writes an audit JSON
file in the canonical project.
"""

import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
VAULT_CONTENT = Path(
    r"C:\ProgramData\Epic\EpicGamesLauncher\VaultCache\SurfaceFf4bcebbd3c7eV10"
    r"\data\Content\Surface_Forge"
)
MOUNT = "/Game/Surface_Forge/"
AUDIT = ROOT / "Saved/Audits/surface_forge_robot_material_candidates_v001.json"
CANDIDATES = [
    "/Game/Surface_Forge/Materials/Material_Instances/MI_SF_Metal",
    "/Game/Surface_Forge/Materials/Main_Shaders/M_Surface_Forge_Inst",
]


def package_to_file(package_name):
    prefix = "/Game/Surface_Forge/"
    if not package_name.startswith(prefix):
        return None
    relative = package_name[len(prefix) :].replace("/", "\\") + ".uasset"
    return VAULT_CONTENT / relative


if not VAULT_CONTENT.is_dir():
    raise RuntimeError(f"Surface Forge vault content is missing: {VAULT_CONTENT}")

registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous([MOUNT], force_rescan=True, ignore_deny_list_scan_filters=True)

dependency_options = unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=True,
    include_hard_package_references=True,
    include_searchable_names=False,
    include_soft_management_references=True,
    include_hard_management_references=True,
)


def dependency_closure(root_package):
    visited = set()
    queue = deque([root_package])
    while queue:
        package = queue.popleft()
        if package in visited:
            continue
        visited.add(package)
        for dependency in registry.get_dependencies(package, dependency_options):
            dependency = str(dependency)
            if dependency.startswith("/Game/Surface_Forge/") and dependency not in visited:
                queue.append(dependency)
    return sorted(visited)


records = []
all_candidate_packages = set()
for object_path in CANDIDATES:
    asset = unreal.EditorAssetLibrary.load_asset(object_path)
    package = object_path.rsplit(".", 1)[0]
    if asset is None:
        records.append({"asset": object_path, "loaded": False})
        continue
    closure = dependency_closure(package)
    all_candidate_packages.update(closure)
    record = {
        "asset": object_path,
        "loaded": True,
        "class": asset.get_class().get_name(),
        "dependency_package_count": len(closure),
        "dependency_packages": closure,
    }
    try:
        record["scalar_parameters"] = [str(x) for x in unreal.MaterialEditingLibrary.get_scalar_parameter_names(asset)]
        record["vector_parameters"] = [str(x) for x in unreal.MaterialEditingLibrary.get_vector_parameter_names(asset)]
        record["texture_parameters"] = [str(x) for x in unreal.MaterialEditingLibrary.get_texture_parameter_names(asset)]
    except Exception as exc:
        record["parameter_introspection_error"] = str(exc)
    records.append(record)

files = []
total_bytes = 0
missing_files = []
for package in sorted(all_candidate_packages):
    source_file = package_to_file(package)
    if source_file is None:
        continue
    if not source_file.is_file():
        missing_files.append(str(source_file))
        continue
    size = source_file.stat().st_size
    total_bytes += size
    files.append(
        {
            "package": package,
            "source_file": str(source_file),
            "bytes": size,
        }
    )

payload = {
    "$schema": "line-boss/audit/surface-forge-robot-material-candidates-v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_VAULT_AUDIT__NO_ASSETS_IMPORTED__NOT_PROMOTED",
    "vault_content": str(VAULT_CONTENT),
    "temporary_mount": MOUNT,
    "candidate_materials": records,
    "candidate_dependency_packages": sorted(all_candidate_packages),
    "candidate_dependency_file_count": len(files),
    "candidate_dependency_bytes": total_bytes,
    "candidate_dependency_files": files,
    "missing_dependency_files": missing_files,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    "LINE_BOSS_SURFACE_FORGE_ROBOT_MATERIAL_AUDIT_PASS "
    f"materials={len(records)} packages={len(all_candidate_packages)} bytes={total_bytes} audit={AUDIT}"
)
unreal.SystemLibrary.quit_editor()
