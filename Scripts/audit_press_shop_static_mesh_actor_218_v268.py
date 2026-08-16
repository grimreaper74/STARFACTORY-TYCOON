"""Resolve the v268 CR01 route blocker south-west of utilities."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_static_mesh_actor_65_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v268").replace("V263", "V268")
code = code.replace("actor_65", "actor_218").replace("Actor_65", "Actor_218")
exec(compile(code, str(source) + "::v268-actor-218", "exec"), globals(), globals())
