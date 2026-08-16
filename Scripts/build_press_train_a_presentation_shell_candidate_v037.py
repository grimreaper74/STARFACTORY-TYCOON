"""Fresh v034 child with corrected centimetre scale and explicit NoCollision profile."""
from pathlib import Path
src=Path(__file__).with_name("build_press_train_a_presentation_shell_candidate_v036.py")
code=src.read_text(encoding="utf-8").replace("v036","v037").replace("V036","V037")
old='c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_editor_property("can_ever_affect_navigation",False); c.set_editor_property("cast_shadow",True)'
new='c.set_collision_profile_name(unreal.Name("NoCollision"), True); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_editor_property("generate_overlap_events", False); c.set_editor_property("can_ever_affect_navigation",False); c.set_editor_property("cast_shadow",True)'
if old not in code: raise RuntimeError("v036 collision source changed")
code=code.replace(old,new,1)
old_check='if c.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION: fail.append(f"shell collision is {c.get_collision_enabled()}")'
new_check='if str(c.get_collision_profile_name()) != "NoCollision": fail.append(f"shell profile is {c.get_collision_profile_name()}")'
if old_check not in code: raise RuntimeError("v036 collision check changed")
code=code.replace(old_check,new_check,1)
exec(compile(code,str(src)+"::collision-profile-v037","exec"),{"__name__":"__main__","__file__":str(src).replace("v036","v037")})
