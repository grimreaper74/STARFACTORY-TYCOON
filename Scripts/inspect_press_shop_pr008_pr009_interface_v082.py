from pathlib import Path
base = Path(__file__).with_name("inspect_press_shop_pr008_pr009_interface_v074.py")
code = base.read_text(encoding="utf-8").replace(
    "NativeRuntimeCandidate_v074", "ExternalAnchorTabsCandidate_v082")
code = code.replace("v074", "v082").replace("V074", "V082")
exec(compile(code, str(base) + "::v082-adapter", "exec"), globals(), globals())
