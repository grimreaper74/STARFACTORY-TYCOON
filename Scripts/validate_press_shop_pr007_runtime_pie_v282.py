from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr007_runtime_pie_v273.py")
code = source.read_text(encoding="utf-8").replace("v273", "v282").replace("V273", "V282")
exec(compile(code, str(source) + "::v282", "exec"), globals(), globals())
