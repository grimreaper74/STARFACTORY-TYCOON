"""Non-overwriting Unreal intake of normal-corrected sign source v410."""
from pathlib import Path
source=Path(__file__).with_name("import_audit_press_shop_train_identity_signs_v397.py")
code=source.read_text(encoding="utf-8").replace("PhysicalSigns_v396","PhysicalSigns_v410").replace("PhysicalSigns_v397","PhysicalSigns_v411").replace("v396","v410").replace("v397","v411")
exec(compile(code,str(source),"exec"),{"__name__":"__main__","__file__":str(source)})
