"""Second Meshy cleanup pass: delete the PR009/PR010 UserMeshy folder.

The first pass deleted the isolated dev map that referenced it, but the
in-session asset registry still returned the dead map as a referencer.
This pass runs in a fresh editor session, so the check is trustworthy.
Run with -ExecutePythonScript.
"""
import io
import json

import unreal

OUT = "C:/Temp/lb_meshy_cleanup2.json"
FOLDER = "/Game/LineBoss/Candidates/PressShop/PR009_PR010_UserMeshy_v864"

registry = unreal.AssetRegistryHelpers.get_asset_registry()
lib = unreal.EditorAssetLibrary
report = {"deleted": [], "blocked": []}

assets = lib.list_assets(FOLDER, recursive=True) or []
blockers = []
for asset in assets:
    package = asset.split(".")[0]
    refs = registry.get_referencers(
        package, unreal.AssetRegistryDependencyOptions()) or []
    outside = [str(r) for r in refs if not str(r).startswith(FOLDER)]
    if outside:
        blockers.append({"asset": package, "why": outside[:4]})
if assets and not blockers:
    if lib.delete_directory(FOLDER):
        report["deleted"].append("{} ({} assets)".format(FOLDER, len(assets)))
    else:
        report["blocked"].append({"asset": FOLDER, "why": "delete failed"})
else:
    report["blocked"] = blockers

with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(report, indent=1))
unreal.log("LINE_BOSS_MESHY_CLEANUP2 {}".format(json.dumps(report)))
