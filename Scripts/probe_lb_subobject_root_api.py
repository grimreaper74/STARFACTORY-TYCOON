"""Read-only UE 5.8 root-subobject API signature probe."""

import unreal

for name in ("make_new_scene_root", "reparent_subobject", "attach_subobject"):
    value = getattr(unreal.SubobjectDataSubsystem, name)
    unreal.log(f"LINE_BOSS_SUBOBJECT_API {name}: {value.__doc__}")
