"""Resolve the v267 CR01 route blocker at the utilities divider bend."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_static_mesh_actor_65_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v267").replace("V263", "V267")
code = code.replace("actor_65", "actor_3233").replace("Actor_65", "Actor_3233")
exec(compile(code, str(source) + "::v267-actor-3233", "exec"), globals(), globals())
