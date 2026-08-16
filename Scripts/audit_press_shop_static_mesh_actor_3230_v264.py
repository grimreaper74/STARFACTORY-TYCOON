"""Resolve the v264 MR01 route-revision-2 blocker."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_static_mesh_actor_65_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v264").replace("V263", "V264")
code = code.replace("actor_65", "actor_3230").replace("Actor_65", "Actor_3230")
exec(compile(code, str(source) + "::v264-actor-3230", "exec"), globals(), globals())
