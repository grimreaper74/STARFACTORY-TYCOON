from pathlib import Path
code = Path(__file__).with_name("build_press_shop_inbound_functional_candidate_v575.py").read_text(encoding="utf-8")
code = code.replace("v575", "v576").replace("V575", "V576")
code = code.replace('    root = actor.get_root_component()\n    if root and hasattr(root, "set_visibility"):\n        root.set_visibility(False, True)\n', '')
exec(compile(code, __file__ + "::v576", "exec"), globals(), globals())
