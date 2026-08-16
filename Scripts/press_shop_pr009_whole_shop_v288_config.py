"""Use the retained PR009 whole-shop route contract against v288."""
from pathlib import Path
source = Path(__file__).with_name("press_shop_pr009_whole_shop_v287_config.py")
code = source.read_text(encoding="utf-8").replace("v287", "v288").replace("V287", "V288")
exec(compile(code, str(source) + "::v288", "exec"), globals(), globals())
