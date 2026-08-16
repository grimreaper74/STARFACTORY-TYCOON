import unreal

PATHS = [
    "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_CairnwellGreen_R_v002",
    "/Game/LineBoss/Runtime/PressShop/CoilAGV/UntouchedControlled_v20260810/Materials/M_Cairnwell_CoilAGV_ControlledPaint_v20260810",
    "/Game/LineBoss/Runtime/PressShop/CoilHandlerAGV_v999/Material_0",
]

for path in PATHS:
    material = unreal.EditorAssetLibrary.load_asset(path)
    unreal.log(f"BRAND_AUDIT material={path} loaded={material is not None}")
    if not material:
        continue
    expressions = unreal.MaterialEditingLibrary.get_all_expressions_in_material(material)
    for index, expression in enumerate(expressions):
        detail = ""
        for prop in ("constant", "parameter_name", "default_value"):
            try:
                detail += f" {prop}={expression.get_editor_property(prop)}"
            except Exception:
                pass
        unreal.log(f"BRAND_AUDIT expression[{index}]={expression.get_class().get_name()}{detail}")
