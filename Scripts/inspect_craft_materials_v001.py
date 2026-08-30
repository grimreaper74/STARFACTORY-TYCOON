"""What material does the HERO ASSET wear?

The craft is the star of the game's signature moment and it renders
dark in the first launch capture ever taken - the same look the
buildings had before their master material was found to be failing
compilation. Read-only: find out before touching anything.
"""
import unreal

ROOT = "/Game/LineBoss/Candidates/Spacecraft"
NAMES = [
    "SpacecraftFactory_v001/Meshes/SM_LB_SC_Scout01_v001",
    "StationMeshes_v001/Meshes/SM_LB_SC_Scout01_Canopy_v001",
    "SpacecraftFactory_v001/Meshes/SM_LB_SC_Cargo01_v001",
]
library = unreal.EditorAssetLibrary
# Find every mesh whose name looks like a craft, wherever it lives.
found = []
for asset in library.list_assets(ROOT, recursive=True):
    name = asset.split("/")[-1].split(".")[0]
    if "Scout01" in name or "Cargo01" in name:
        found.append(asset)
print("CRAFTPROBE candidates %d" % len(found))
for path in sorted(set(found))[:14]:
    mesh = library.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        continue
    mats = mesh.get_editor_property("static_materials")
    for index, slot in enumerate(mats):
        mat = slot.get_editor_property("material_interface")
        print("CRAFTPROBE %s slot %d -> %s"
              % (path.split("/")[-1], index,
                 mat.get_path_name() if mat else "NONE"))
