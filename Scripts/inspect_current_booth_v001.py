"""What is CURRENTLY at the booth's asset path, right now, in the
project - not what the source code says should be there, and not what
a downloaded file measures as. The owner pushed back that it already
looked like the new booth in a live run, so this checks the actual
asset content rather than re-argue from source.
"""
import unreal

PATH = ("/Game/LineBoss/Candidates/Spacecraft/PaintBooth_v001/"
        "LB_Booth_paint_booth/StaticMeshes/LB_Booth_paint_booth"
        ".LB_Booth_paint_booth")
registry = unreal.AssetRegistryHelpers.get_asset_registry()
mesh = unreal.EditorAssetLibrary.load_asset(PATH)
if mesh is None:
    unreal.log_error("BOOTHCHECK: nothing at %s" % PATH)
else:
    tris = mesh.get_num_triangles(0)
    b = mesh.get_bounds().box_extent
    unreal.log("BOOTHCHECK found at exact path: tris=%d extent=%.2fx%.2fx%.2fm"
               % (tris, b.x*0.02, b.y*0.02, b.z*0.02))

# Also list EVERYTHING under PaintBooth_v001, in case a re-import
# landed somewhere slightly different.
root = "/Game/LineBoss/Candidates/Spacecraft/PaintBooth_v001"
unreal.log("BOOTHCHECK listing everything under %s:" % root)
for data in registry.get_assets_by_path(root, recursive=True):
    asset = data.get_asset()
    if isinstance(asset, unreal.StaticMesh):
        tris = asset.get_num_triangles(0)
        unreal.log("BOOTHCHECK ASSET %s tris=%d path=%s"
                   % (asset.get_name(), tris, asset.get_path_name()))
