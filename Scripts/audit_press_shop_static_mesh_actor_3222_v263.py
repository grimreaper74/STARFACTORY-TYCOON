"""Resolve the second exact v263 MR01 sweep blocker."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_static_mesh_actor_65_v263.py")
code = source.read_text(encoding="utf-8").replace("actor_65", "actor_3222").replace("Actor_65", "Actor_3222")
exec(compile(code, str(source) + "::actor-3222", "exec"), globals(), globals())
