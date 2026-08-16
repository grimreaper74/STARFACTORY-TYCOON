from pathlib import Path
code = Path(__file__).with_name("build_press_shop_inbound_functional_candidate_v575.py").read_text(encoding="utf-8")
code = code.replace("v575", "v577").replace("V575", "V577")
code = code.replace('    root = actor.get_root_component()\n    if root and hasattr(root, "set_visibility"):\n        root.set_visibility(False, True)\n', '')
code = code.replace('unreal.Vector(650.0, 350.0, 160.0)', 'unreal.Vector(660.0, 600.0, 160.0)')
exec(compile(code, __file__ + "::v577", "exec"), globals(), globals())
