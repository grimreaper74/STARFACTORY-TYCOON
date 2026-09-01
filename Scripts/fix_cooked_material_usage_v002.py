"""v002: undo the engine-install mutation from v001, fix in-project.

v001 set the ISM usage flag on the wall-bay MICs' base material -
which turned out to be the Interchange plugin's M_Default inside the
ENGINE INSTALL, and the save actually landed there. An engine verify
or update would silently revert it and resurrect the packaged-build
default-material bug, and other projects on this machine would see a
modified engine asset. This lane:

1. duplicates M_Default into ShipFactoryInterior_v001 as a
   project-owned base with used_with_instanced_static_meshes set,
2. re-parents the three wall-bay MICs onto it, and
3. restores the engine asset's flag to False.
"""
import unreal

lib = unreal.MaterialEditingLibrary

ENGINE_BASE = "/InterchangeAssets/gltf/M_Default"
PROJECT_BASE = ("/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001/"
    "SM_LB_IN_WallBay/Materials/M_LB_InterchangeDefault_ISM_v001")
MICS = [
    "/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001/SM_LB_IN_WallBay/Materials/machined_pale",
    "/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001/SM_LB_IN_WallBay/Materials/brushed_aluminium",
    "/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001/SM_LB_IN_WallBay/Materials/graphite_metal",
]

if not unreal.EditorAssetLibrary.does_asset_exist(PROJECT_BASE):
    dup = unreal.EditorAssetLibrary.duplicate_asset(ENGINE_BASE, PROJECT_BASE)
    assert dup is not None, "duplicate failed"
base = unreal.load_asset(PROJECT_BASE)
assert base is not None
base.set_editor_property("used_with_instanced_static_meshes", True)
lib.recompile_material(base)
assert unreal.EditorAssetLibrary.save_loaded_asset(base)
unreal.log("USAGEFIX2 project base ready: " + PROJECT_BASE)

for path in MICS:
    mi = unreal.load_asset(path)
    assert mi is not None, path
    lib.set_material_instance_parent(mi, base)
    lib.update_material_instance(mi)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mi), path
    unreal.log("USAGEFIX2 reparented: " + path)

eng = unreal.load_asset(ENGINE_BASE)
assert eng is not None
eng.set_editor_property("used_with_instanced_static_meshes", False)
lib.recompile_material(eng)
assert unreal.EditorAssetLibrary.save_loaded_asset(eng)
unreal.log("USAGEFIX2 engine M_Default flag restored to False")
unreal.log("USAGEFIX2 DONE")
