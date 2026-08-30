"""Import the eight processed drone/dock GLBs from DroneBatch_v001 into
Unreal, each as a set of named StaticMesh assets (one per part) under
its own destination folder. Reports every mesh landed with triangle
count and Nanite state, same pattern as import_scout01_v003.py.
"""
import unreal

SRC_ROOT = (r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
            r"\SourceAssets\Spacecraft\DroneBatch_v001")
DEST_ROOT = "/Game/LineBoss/Candidates/Spacecraft/DroneBatch_v001"

ASSETS = [
    "cargolift_v001", "assembly_v001", "spray_v001", "winch_v001",
    "ground_lifter_v001", "ground_sprayer_v001", "ground_assembly_v001",
    "charging_dock_v001",
]

registry = unreal.AssetRegistryHelpers.get_asset_registry()

for stem in ASSETS:
    dest = "%s/%s" % (DEST_ROOT, stem)
    if unreal.EditorAssetLibrary.does_directory_exist(dest):
        unreal.log("DRONEBATCH: clearing previous import at %s" % dest)
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
        found.append(name)
        unreal.log("DRONEBATCH %-24s ASSET %-40s tris=%-7d nanite=%-5s path=%s"
                   % (stem, name, tris, nanite, path))
    if not found:
        unreal.log_error("DRONEBATCH %s: IMPORT PRODUCED NO STATIC MESHES" % stem)
    else:
        unreal.log("DRONEBATCH %s IMPORT OK: %d mesh assets" % (stem, len(found)))

unreal.log("DRONEBATCH IMPORT COMPLETE")
