"""Run the train bounds audit against corrected-rotation v223."""

from pathlib import Path


source = Path(__file__).with_name("audit_press_shop_v222_train_scope_bounds.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v222",
    "/Game/LineBoss/Maps/LB_PressShop_WholeShopAutomationPreviewCandidate_v223")
code = code.replace("press_shop_v222_train_scope_bounds.json", "press_shop_v223_train_scope_bounds.json")
code = code.replace("LB_V222_SCOPE_BOUNDS", "LB_V223_SCOPE_BOUNDS")
exec(compile(code, str(source) + "::v223", "exec"), globals(), globals())

