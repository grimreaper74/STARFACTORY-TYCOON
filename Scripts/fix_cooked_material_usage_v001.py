"""Usage flags the cooked game needs (found in the first packaged run).

The packaged journey log (Builds/Overnight_2026_09_01) showed two
classes of material fallback that never appear in the editor, which
sets usage flags on demand:

1. The three wall-bay materials render as DEFAULT MATERIAL in game -
   "missing usage flag InstancedStaticMeshes". Set the flag on the
   assets.
2. The track belt MIDs derive from the engine BasicShapeMaterial,
   which lacks bUsedWithSplineMeshes ("Had to pass SMU back to game
   thread" - a runtime fixup in Development, a default-material break
   in Shipping). Engine content is not editable, so this creates a
   project-owned equivalent - VectorParameter "Color" into BaseColor,
   flags set - for the presenter to parent belt MIDs from. It lives in
   StationMeshes_v001/Materials, which is in DirectoriesToAlwaysCook.
"""
import unreal

lib = unreal.MaterialEditingLibrary

WALL_MATS = [
    "/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001/SM_LB_IN_WallBay/Materials/machined_pale",
    "/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001/SM_LB_IN_WallBay/Materials/brushed_aluminium",
    "/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001/SM_LB_IN_WallBay/Materials/graphite_metal",
]
# The wall-bay assets are MaterialInstanceConstants; usage flags live
# on the base Material, so set it there (dedupe shared bases).
seen_bases = set()
for path in WALL_MATS:
    m = unreal.load_asset(path)
    assert m is not None, path
    base = m.get_base_material() if isinstance(
        m, unreal.MaterialInterface) else m
    assert base is not None, path
    bpath = base.get_path_name()
    if bpath in seen_bases:
        unreal.log("USAGEFIX base already flagged: " + bpath)
        continue
    seen_bases.add(bpath)
    base.set_editor_property("used_with_instanced_static_meshes", True)
    lib.recompile_material(base)
    assert unreal.EditorAssetLibrary.save_loaded_asset(base), bpath
    unreal.log("USAGEFIX ISM flag set on base: " + bpath)

SPLINE_MAT = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/"
    "Materials/M_LB_ShapeSpline_v001")
if unreal.EditorAssetLibrary.does_asset_exist(SPLINE_MAT):
    unreal.EditorAssetLibrary.delete_asset(SPLINE_MAT)
tools = unreal.AssetToolsHelpers.get_asset_tools()
mat = tools.create_asset(
    asset_name="M_LB_ShapeSpline_v001",
    package_path="/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials",
    asset_class=unreal.Material,
    factory=unreal.MaterialFactoryNew())
assert mat is not None
col = lib.create_material_expression(mat,
    unreal.MaterialExpressionVectorParameter, -400, 0)
col.set_editor_property("parameter_name", "Color")
col.set_editor_property("default_value",
    unreal.LinearColor(0.5, 0.5, 0.5, 1.0))
assert lib.connect_material_property(col, "",
    unreal.MaterialProperty.MP_BASE_COLOR)
rough = lib.create_material_expression(mat,
    unreal.MaterialExpressionScalarParameter, -400, 240)
rough.set_editor_property("parameter_name", "Roughness")
rough.set_editor_property("default_value", 0.5)
assert lib.connect_material_property(rough, "",
    unreal.MaterialProperty.MP_ROUGHNESS)
mat.set_editor_property("used_with_spline_meshes", True)
mat.set_editor_property("used_with_instanced_static_meshes", True)
lib.recompile_material(mat)
assert unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("USAGEFIX spline shape material created: " + SPLINE_MAT)
unreal.log("USAGEFIX DONE")
