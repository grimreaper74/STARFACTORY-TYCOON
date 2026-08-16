from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE = Path(r"C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\Shared\SegmentedTransferRuntime_v746\Cairnwell_InterPressTransfer_Runtime_v746.glb")
DEST = "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260810_v927/CupTransfer"
AUDIT = ROOT / "Saved/Audits/PressTrains/approved_cup_transfer_intake_v927.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"

sha = lambda: hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if sha() != EXPECTED: raise RuntimeError("protected v438 mismatch")
if not SOURCE.is_file(): raise RuntimeError(f"missing {SOURCE}")
lib = unreal.EditorAssetLibrary
if lib.does_directory_exist(DEST) and lib.list_assets(DEST, recursive=True, include_folder=False):
    raise RuntimeError(f"destination is not empty: {DEST}")

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(SOURCE), "destination_path": DEST, "automated": True,
    "replace_existing": False, "replace_existing_settings": False, "save": True,
})
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
assets = lib.list_assets(DEST, recursive=True, include_folder=False)
meshes = [p for p in assets if isinstance(unreal.load_asset(p), unreal.StaticMesh)]
required = ["TIC_FRAME", "CROSSBEAM", "ATOR_PACK", "CUP_ARRAY"]
failures = [f"missing {name}" for name in required if not any(name.lower() in p.lower() for p in meshes)]
if sha() != EXPECTED: failures.append("protected v438 changed")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "revision": "v927", "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__APPROVED_CUP_TRANSFER_INTAKE" if not failures else "FAIL__V927",
    "source": str(SOURCE), "destination": DEST, "static_meshes": meshes,
    "failures": failures, "protected_sha256": sha(), "meshy_credits_used": 0,
}, indent=2), encoding="utf-8")
if failures: raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_APPROVED_CUP_TRANSFER_V927_PASS")
