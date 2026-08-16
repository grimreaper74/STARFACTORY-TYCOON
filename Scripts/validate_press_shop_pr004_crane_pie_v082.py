from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_crane_pie_v074.py")
code = base.read_text(encoding="utf-8").replace("v074", "v082").replace("NativeRuntime", "ExternalAnchorTabs")
exec(compile(code, str(base) + "::v082-adapter", "exec"), globals(), globals())
