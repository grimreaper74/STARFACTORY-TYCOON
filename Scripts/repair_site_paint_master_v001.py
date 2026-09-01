"""Re-parent the site paint MIs off the dead car-era FrontEnd master.

Every packaged cook died with "Array index out of bounds: 2 into an
array of size 1" while cooking MI_LB_Site_PaintWhite_v001 /
MI_LB_Site_PaintYellow_v001. Their parent,
M_LB_FrontEndPaintedConcrete_Master, is a car-era material whose five
TextureSample nodes are ALL null - its T_ConcretePillar01_* source
textures were deleted from Content/LineBoss/Vendor. The editor renders
null samplers as defaults, so PIE never noticed; the cooker asserts.

Fix: a minimal spacecraft-era paint master with no texture
dependencies, parameter names identical (ZoneTint, TintStrength,
Roughness) so the MIs' stored overrides keep applying by name. The old
FrontEnd master is left in place as car-era prior art - nothing in the
cook set references it once the MIs move.
"""
import unreal

lib = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

MASTER = "/Game/LineBoss/Site/Materials_v001/M_LB_SitePaint_Master_v001"
if unreal.EditorAssetLibrary.does_asset_exist(MASTER):
    unreal.EditorAssetLibrary.delete_asset(MASTER)
mat = tools.create_asset(
    asset_name="M_LB_SitePaint_Master_v001",
    package_path="/Game/LineBoss/Site/Materials_v001",
    asset_class=unreal.Material,
    factory=unreal.MaterialFactoryNew())
assert mat is not None, "master create failed"

def node(cls, x, y):
    n = lib.create_material_expression(mat, cls, x, y)
    assert n is not None, cls.get_name()
    return n

tint = node(unreal.MaterialExpressionVectorParameter, -600, 0)
tint.set_editor_property("parameter_name", "ZoneTint")
tint.set_editor_property("default_value",
    unreal.LinearColor(0.9, 0.895, 0.86, 1.0))
strength = node(unreal.MaterialExpressionScalarParameter, -600, 220)
strength.set_editor_property("parameter_name", "TintStrength")
strength.set_editor_property("default_value", 1.0)
mul = node(unreal.MaterialExpressionMultiply, -320, 60)
assert lib.connect_material_expressions(tint, "", mul, "A")
assert lib.connect_material_expressions(strength, "", mul, "B")
assert lib.connect_material_property(mul, "",
    unreal.MaterialProperty.MP_BASE_COLOR)
rough = node(unreal.MaterialExpressionScalarParameter, -320, 320)
rough.set_editor_property("parameter_name", "Roughness")
rough.set_editor_property("default_value", 0.8)
assert lib.connect_material_property(rough, "",
    unreal.MaterialProperty.MP_ROUGHNESS)
lib.recompile_material(mat)
assert unreal.EditorAssetLibrary.save_loaded_asset(mat), "master save"

for name in ("MI_LB_Site_PaintWhite_v001", "MI_LB_Site_PaintYellow_v001"):
    path = "/Game/LineBoss/Site/Materials_v001/" + name
    mi = unreal.load_asset(path)
    assert mi is not None, path
    lib.set_material_instance_parent(mi, mat)
    lib.update_material_instance(mi)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mi), name
    unreal.log("SITEPAINT reparented " + name)
unreal.log("SITEPAINT OK")
