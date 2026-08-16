from pathlib import Path
code = Path(__file__).with_name("prepare_press_shop_inbound_functional_candidate_v575.py").read_text(encoding="utf-8")
code = code.replace("v575", "v576").replace("V575", "V576")
exec(compile(code, __file__ + "::v576", "exec"), globals(), globals())
