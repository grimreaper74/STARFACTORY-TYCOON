"""Import the fourteen ship-derived pallet-load GLBs directly (no Blender
pass needed - the design tool's own reported dimensions were verified
against an independent Blender measurement of pallet-wing.glb and matched
exactly, so these are already correctly scaled).
"""
import unreal

SRC_ROOT = r"C:\Users\greg_\Downloads"
DEST_ROOT = "/Game/LineBoss/Candidates/Spacecraft/PalletLoads_v001"

PALLETS = [
    "pallet-hull_nose", "pallet-hull_fwd", "pallet-hull_mid",
    "pallet-hull_aft", "pallet-wing", "pallet-wing_port",
    "pallet-canopy", "pallet-booster", "pallet-booster_port",
    "pallet-mainengine", "pallet-cellbank", "pallet-avionics",
    "pallet-sensor", "pallet-interior",
]

registry = unreal.AssetRegistryHelpers.get_asset_registry()

for stem in PALLETS:
    safe_stem = stem.replace("-", "_")
    dest = "%s/%s" % (DEST_ROOT, safe_stem)
    if unreal.EditorAssetLibrary.does_directory_exist(dest):
        unreal.log("PALLETBATCH: clearing previous import at %s" % dest)
        unreal.EditorAssetLibrary.delete_directory(dest)

    task = unreal.AssetImportTask()
    task.filename = "%s\\%s.glb" % (SRC_ROOT, stem)
    task.destination_path = dest
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    found = []
    for data in registry.get_assets_by_path(dest, recursive=True):
        asset = data.get_asset()
        if not isinstance(asset, unreal.StaticMesh):
            continue
        name = asset.get_name()
        path = asset.get_path_name()
        tris = asset.get_num_triangles(0)
        nanite = asset.get_editor_property("nanite_settings").enabled
        bounds = asset.get_bounds()
        extent = bounds.box_extent
        found.append(name)
        unreal.log("PALLETBATCH %-20s ASSET %-30s tris=%-7d nanite=%-5s "
                   "extentCm=(%.1f,%.1f,%.1f) path=%s"
                   % (stem, name, tris, nanite, extent.x, extent.y,
                      extent.z, path))
    if not found:
        unreal.log_error("PALLETBATCH %s: IMPORT PRODUCED NO STATIC MESHES"
                          % stem)
    elif len(found) > 1:
        unreal.log_warning("PALLETBATCH %s: %d mesh assets (expected 1 - "
            "not pre-joined?)" % (stem, len(found)))
    else:
        unreal.log("PALLETBATCH %s IMPORT OK: 1 mesh asset" % stem)

unreal.log("PALLETBATCH IMPORT COMPLETE")
