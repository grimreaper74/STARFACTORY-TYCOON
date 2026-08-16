"""Resolve the v265 MR01 route blocker south of maintenance."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_static_mesh_actor_65_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v265").replace("V263", "V265")
code = code.replace("actor_65", "actor_1185").replace("Actor_65", "Actor_1185")
exec(compile(code, str(source) + "::v265-actor-1185", "exec"), globals(), globals())
