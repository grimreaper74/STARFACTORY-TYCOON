"""Clean non-overwriting successor to v041's Blender-5.2 FBX-option failure."""
from pathlib import Path

base = Path(__file__).with_name("build_press_train_a_pro_detail_source_v041.py")
code = base.read_text(encoding="utf-8")
code = code.replace("ProDetailModular_v041", "ProDetailModular_v042")
code = code.replace("ProDetailModular_v041.blend", "ProDetailModular_v042.blend")
code = code.replace("ProDetailModular_v041.fbx", "ProDetailModular_v042.fbx")
code = code.replace("PRO_DETAIL_MODULAR_v041", "PRO_DETAIL_MODULAR_v042")
code = code.replace("pro-detail-modular-v041", "pro-detail-modular-v042")
code = code.replace("PTA_ProDetail_v041", "PTA_ProDetail_v042")
code = code.replace("_v041", "_v042")
exec(compile(code, str(base) + "::v042", "exec"), globals(), globals())
