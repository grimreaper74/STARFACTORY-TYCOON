"""Non-overwriting Unreal intake of corrected physical sign source v402."""
from pathlib import Path

source=Path(__file__).with_name("import_audit_press_shop_train_identity_signs_v397.py")
code=source.read_text(encoding="utf-8")
code=code.replace("PhysicalSigns_v396","PhysicalSigns_v402")
code=code.replace("PhysicalSigns_v397","PhysicalSigns_v403")
code=code.replace("v396","v402")
code=code.replace("v397","v403")
exec(compile(code,str(source),"exec"),{"__name__":"__main__","__file__":str(source)})
