"""Recompile and resave the two master materials in a RENDERING editor.

The v007 package cooked both masters with NULL SHADER MAPS - every
generated building and station mesh falls back to flat black in a
packaged build. The owner's words on launching it: "its still a mess".

Root-cause hypothesis under test: every material-repair script so far
ran in a -NullRHI editor session, where no shaders compile, so the
assets were saved without compiled shader data. This script must be run
WITHOUT -NullRHI. It recompiles each master, waits for the shader
compiler to drain, saves, and reports - the receipt is only meaningful
if the NEXT cook stops printing the ShaderMap warning.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/master_material_resave_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")

MASTERS = [
    ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes/"
     "BuildingTextures/M_LB_Building_Master"),
    ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/"
     "M_LB_MeshyPBR_v002"),
]

library = unreal.EditorAssetLibrary
mat_lib = unreal.MaterialEditingLibrary
rows = []
failures = []

for path in MASTERS:
    asset = library.load_asset(path)
    if asset is None:
        failures.append("missing master %s" % path)
        continue
    mat_lib.recompile_material(asset)
    rows.append({"master": path, "recompiled": True})

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
    save_map_packages=False, save_content_packages=True)
for path in MASTERS:
    saved = library.save_asset(path, only_if_is_dirty=False)
    for row in rows:
        if row["master"] == path:
            row["saved"] = bool(saved)
            if not saved:
                failures.append("%s did not save" % path)

report = {
    "$schema": "lineboss/audit/master-material-resave-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__MASTERS_RECOMPILED_AND_SAVED" if not failures
               else "FAIL_CLOSED__MASTER_RESAVE"),
    "why": ("v007 cooked both masters with null shader maps; suspected "
            "cause is that all prior repair scripts saved them under "
            "-NullRHI where shaders never compile. This run must be "
            "made WITHOUT -NullRHI."),
    "masters": rows,
    "failures": failures,
    "not_proven": [
        "Only the next cook proves anything: the ShaderMap warning must "
        "be absent from the package log, and a sighted launch of that "
        "package must show textured buildings.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "failures": failures},
                 indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
