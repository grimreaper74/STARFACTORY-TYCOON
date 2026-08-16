from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
DEST = "/Game/LineBoss/Developer/Validation/PressTrains/SegmentedTransferRuntime_v747"
SOURCE = Path(r"C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\Shared\SegmentedTransferRuntime_v746\Cairnwell_InterPressTransfer_Runtime_v746.glb")
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/segmented_transfer_runtime_intake_v747.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"

def protected_hash():
    return hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()

if protected_hash() != EXPECTED:
    raise RuntimeError("Protected v438 hash mismatch before import")
if not SOURCE.is_file():
    raise RuntimeError(f"Missing source: {SOURCE}")
if AUDIT.exists():
    raise RuntimeError("Refusing to overwrite v747 audit")

lib = unreal.EditorAssetLibrary
if lib.does_directory_exist(DEST) and lib.list_assets(DEST, recursive=True, include_folder=False):
    raise RuntimeError(f"Refusing non-empty destination: {DEST}")

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(SOURCE),
    "destination_path": DEST,
    "automated": True,
    "replace_existing": False,
    "replace_existing_settings": False,
    "save": True,
})
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

assets = lib.list_assets(DEST, recursive=True, include_folder=False)
rows = []
for path in assets:
    asset = unreal.load_asset(path)
    rows.append({"path": path, "class": asset.get_class().get_name() if asset else None})

required = ["STATIC_FRAME", "CARRIAGE_CROSSBEAM", "ACTUATOR_PACK", "CUP_ARRAY"]
failures = [f"missing {name}" for name in required if not any(name.lower() in row["path"].lower() for row in rows)]
if protected_hash() != EXPECTED:
    failures.append("protected v438 changed")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "revision": "v747",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__SEGMENTED_TRANSFER_RUNTIME_INTAKE" if not failures else "FAIL__V747",
    "destination": DEST,
    "source": str(SOURCE),
    "asset_count": len(rows),
    "assets": rows,
    "failures": failures,
    "protected_sha256": protected_hash(),
    "meshy_credits_used": 0,
}, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_SEGMENTED_TRANSFER_RUNTIME_V747_PASS")
