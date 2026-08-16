"""Fresh v004 retry of the v003 identity-plate direction.

v003 correctly stopped when the spawned BasicShape components retained their
default collision profile despite collision being disabled transiently.  This
retry starts again from retained v001 and explicitly applies the NoCollision
profile before the existing exact collision gate.
"""

from pathlib import Path


source = Path(__file__).resolve().parent / "build_press_train_bc_visual_identity_v003.py"
code = source.read_text(encoding="utf-8")
code = code.replace("v003", "v004")
code = code.replace(
    "component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)\n",
    "component.set_collision_profile_name(unreal.Name(\"NoCollision\"))\n"
    "    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)\n")
exec(compile(code, str(source) + "::fresh-v004-no-collision-profile", "exec"), globals(), globals())
