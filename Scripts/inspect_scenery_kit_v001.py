"""Measure the site-scenery candidates in the project's own kit.

The owner asked whether anything already downloaded suits a full site
map. Judgement needs SIZES, not names: a fence panel that is 4 m long
and one that is 40 m dress a perimeter very differently. Read-only.
"""
import unreal

NAMES = [
    "SM_Fence04", "SM_Fence05", "SM_Fence06", "SM_Fence07",
    "SM_FencePart_01", "SM_FencePart_02",
    "SM_Container01_01", "SM_Container01_02", "SM_ContainerP4_01",
    "SM_Lamp01", "SM_Lamp02", "SM_LampArch01", "SM_LampSet_01",
    "SM_Background1_Tower01", "SM_Background1_Tower02",
    "SM_Background1_AntennaTower", "SM_Background2_Hangar",
    "SM_Background2_BoxBuilding", "SM_Background2_Bridge",
    "SM_Background2_Pipe01", "SM_ConcreteFloor_01", "SM_ConcreteWall",
    "SM_ConcretePillar01",
]
library = unreal.EditorAssetLibrary
for name in NAMES:
    path = "/Game/Meshes/%s" % name
    mesh = library.load_asset(path)
    if mesh is None:
        print("SCENERY MISSING %s" % name)
        continue
    extent = mesh.get_bounds().box_extent
    try:
        tris = int(unreal.EditorStaticMeshLibrary.get_number_triangles(mesh, 0))
    except Exception:
        tris = -1
    mats = len(mesh.get_editor_property("static_materials"))
    print("SCENERY %-28s size_cm %6.0f x %6.0f x %6.0f  tris %6d  mats %d"
          % (name, extent.x * 2, extent.y * 2, extent.z * 2, tris, mats))
