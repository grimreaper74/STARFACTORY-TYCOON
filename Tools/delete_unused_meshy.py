"""Delete unused Meshy content: the 7 Meshy dev/validation maps and the
PR009/PR010 UserMeshy folder, each only after proving no external asset
references it. Kept deliberately (and reported): the two MeshyMaster_v632
meshes bound by the press-train authorities in both maps, the PR005 dHMI
mesh hard-referenced from LBFactoryBuildMachine.cpp, and the MeshyPBR
materials bound to the approved inbound lorry and coil stand.

Run with -ExecutePythonScript.
"""
import io
import json

import unreal

OUT = "C:/Temp/lb_meshy_cleanup.json"
REPORT = {"deleted": [], "kept": [], "blocked": []}

MAPS = [
    "/Game/LineBoss/Maps/LB_PressShop_CleanMeshyBuild_v720",
    "/Game/LineBoss/Maps/LB_PressShop_CleanMeshyTrains_v722",
    "/Game/LineBoss/Maps/LB_PressShop_PR009_PR010_UserMeshy_Isolated_v864",
    "/Game/LineBoss/Developer/Validation/PressShop/"
    "LB_PressShop_CleanMeshyTrainsReview_v723",
    "/Game/LineBoss/Developer/Validation/PressShop/"
    "LB_PressShop_MeshyPressVisuals_v714",
    "/Game/LineBoss/Developer/Validation/PressShop/"
    "LB_PressShop_MeshyPressVisuals_v716",
    "/Game/LineBoss/Developer/Validation/PressShop/"
    "LB_PressShop_MeshyPressVisuals_v717",
]
FOLDER = "/Game/LineBoss/Candidates/PressShop/PR009_PR010_UserMeshy_v864"

registry = unreal.AssetRegistryHelpers.get_asset_registry()
lib = unreal.EditorAssetLibrary


def external_referencers(package_name, internal_prefixes):
    options = unreal.AssetRegistryDependencyOptions()
    refs = registry.get_referencers(package_name, options) or []
    outside = []
    for ref in refs:
        text = str(ref)
        if any(text.startswith(p) for p in internal_prefixes):
            continue
        outside.append(text)
    return outside


# Maps first: nothing should reference a dev map; deleting them releases
# their Meshy contents.
for map_path in MAPS:
    if not lib.does_asset_exist(map_path):
        REPORT["blocked"].append({"asset": map_path, "why": "not found"})
        continue
    refs = external_referencers(map_path, [map_path])
    if refs:
        REPORT["blocked"].append({"asset": map_path, "why": refs[:4]})
        continue
    if lib.delete_asset(map_path):
        REPORT["deleted"].append(map_path)
    else:
        REPORT["blocked"].append({"asset": map_path, "why": "delete failed"})

# The UserMeshy folder: every asset inside must have no referencer outside
# the folder itself (the isolated map that referenced it is deleted above).
folder_assets = lib.list_assets(FOLDER, recursive=True) or []
blockers = []
for asset in folder_assets:
    package = asset.split(".")[0]
    refs = external_referencers(package, [FOLDER])
    if refs:
        blockers.append({"asset": package, "why": refs[:4]})
if folder_assets and not blockers:
    if lib.delete_directory(FOLDER):
        REPORT["deleted"].append(FOLDER + " ({} assets)".format(
            len(folder_assets)))
    else:
        REPORT["blocked"].append({"asset": FOLDER, "why": "delete failed"})
else:
    REPORT["blocked"].extend(blockers)

# Anything else Meshy-pathed under /Game: classify but do not touch.
for asset in lib.list_assets("/Game", recursive=True):
    if "meshy" in asset.lower():
        REPORT["kept"].append(asset.split(".")[0])

with io.open(OUT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(REPORT, indent=1, sort_keys=True))
unreal.log("LINE_BOSS_MESHY_CLEANUP {}".format(
    json.dumps({k: len(v) for k, v in REPORT.items()})))
