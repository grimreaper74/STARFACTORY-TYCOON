"""Resolve the v266 CR01-01 berth-egress blocker."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_static_mesh_actor_65_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v266").replace("V263", "V266")
code = code.replace("actor_65", "actor_3181").replace("Actor_65", "Actor_3181")
exec(compile(code, str(source) + "::v266-actor-3181", "exec"), globals(), globals())
