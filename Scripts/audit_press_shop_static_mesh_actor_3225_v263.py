"""Resolve the exact v263 route blocker at the MR01 divider bend."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_static_mesh_actor_65_v263.py")
code = source.read_text(encoding="utf-8").replace("actor_65", "actor_3225").replace("Actor_65", "Actor_3225")
exec(compile(code, str(source) + "::actor-3225", "exec"), globals(), globals())
