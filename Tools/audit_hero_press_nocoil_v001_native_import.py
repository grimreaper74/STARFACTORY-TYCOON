"""Audit the native Unreal import after its separate import task completed."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
FBX = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "HeroPressCell_MeshyNoCoil_v001" / "Runtime" / "SM_LB_PS_HeroPressCell_MeshyNoCoil_v001.fbx"
DESTINATION = "/Game/LineBoss/Candidates/PressShop/HeroPressCellNoCoil_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "hero_press_cell_nocoil_v001_native_import_audit.json"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if not FBX.is_file() or not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Required source or protected evidence file missing")
fbx_before, protected_before, v002_before = digest(FBX), digest(PROTECTED), digest(V002)
assets = unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=True, include_folder=False)
meshes = []
for path in assets:
    asset = unreal.load_asset(path)
    if isinstance(asset, unreal.StaticMesh):
        rows = asset.get_editor_property("static_materials")
        meshes.append({"path": path, "material_slot_count": len(rows), "material_slots": [str(row.get_editor_property("material_interface")) for row in rows]})
if len(meshes) != 2:
    raise RuntimeError("Native import does not contain exactly body + rollers meshes: %r" % meshes)
fbx_after, protected_after, v002_after = digest(FBX), digest(PROTECTED), digest(V002)
if fbx_before != fbx_after or protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Source asset or protected map changed during native import audit")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__NATIVE_UNREAL_MESH_IMPORT_AUDITED",
    "fbx": str(FBX),
    "fbx_sha256_before": fbx_before,
    "fbx_sha256_after": fbx_after,
    "destination": DESTINATION,
    "asset_count": len(assets),
    "static_meshes": meshes,
    "note": "FBX texture payload warnings occurred during import. The candidate map will use its own material overrides; no source texture repair or production-map change is claimed.",
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_HERO_NOCOIL_V001_NATIVE_IMPORT_AUDIT_PASS")
