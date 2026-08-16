from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr008_native_runtime_pie_v273.py")
code = source.read_text(encoding="utf-8").replace("v273", "v283").replace("V273", "V283")
exec(compile(code, str(source) + "::v283", "exec"), globals(), globals())
