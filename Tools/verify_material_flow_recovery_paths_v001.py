"""Read-only Unreal AssetRegistry check after recoverable MaterialFlow cleanup."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT_ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
OUT = (PROJECT_ROOT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v001/"
       "native_recovery_registry_check_v001.json")
ROOTS = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v001",
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowTransformProbe_v001",
)


rows = {}
for root in ROOTS:
    assets = sorted(unreal.EditorAssetLibrary.list_assets(
        root, recursive=True, include_folder=False))
    rows[root] = {
        "virtual_directory_exists": bool(unreal.EditorAssetLibrary.does_directory_exist(root)),
        "assets": assets,
    }

failures = {root: row["assets"] for root, row in rows.items() if row["assets"]}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "lineboss/onefactory/press/material-flow-recovery-registry-check/v1",
    "status": ("PASS__RECOVERED_MATERIAL_FLOW_AND_PROBE_ASSETS_ABSENT"
               if not failures else "FAIL__RECOVERED_ASSETS_STILL_REGISTERED"),
    "roots": rows,
    "failures": failures,
    "map_opened_by_script": False,
    "map_saved_by_script": False,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
if failures:
    raise RuntimeError("Recovered AssetRegistry paths still contain assets: {}".format(failures))
unreal.log("LINE_BOSS_MATERIAL_FLOW_RECOVERY_REGISTRY_PASS")
unreal.SystemLibrary.quit_editor()
