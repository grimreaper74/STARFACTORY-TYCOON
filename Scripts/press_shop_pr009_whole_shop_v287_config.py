"""Use the retained PR009 whole-shop route contract against v287."""
from pathlib import Path
source = Path(__file__).with_name("press_shop_pr009_whole_shop_v285_config.py")
code = source.read_text(encoding="utf-8").replace("v285", "v287").replace("V285", "V287")
exec(compile(code, str(source) + "::v287", "exec"), globals(), globals())
