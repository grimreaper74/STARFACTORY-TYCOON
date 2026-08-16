"""Fresh v034 child correcting scale, collision profile and FBX forward sign."""
from pathlib import Path
src=Path(__file__).with_name("build_press_train_a_presentation_shell_candidate_v036.py")
code=src.read_text(encoding="utf-8").replace("v036","v038").replace("V036","V038")
old='a.set_actor_scale3d(unreal.Vector(100,100,100));'
new='a.set_actor_scale3d(unreal.Vector(100,-100,100));'
if old not in code: raise RuntimeError("v036 scale source changed")
code=code.replace(old,new,1).replace('"actor_scale":[100,100,100]','"actor_scale":[100,-100,100]')
old='c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_editor_property("can_ever_affect_navigation",False); c.set_editor_property("cast_shadow",True)'
new='c.set_collision_profile_name(unreal.Name("NoCollision"), True); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_editor_property("generate_overlap_events", False); c.set_editor_property("can_ever_affect_navigation",False); c.set_editor_property("cast_shadow",True)'
if old not in code: raise RuntimeError("v036 collision source changed")
code=code.replace(old,new,1)
old='if c.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION: fail.append(f"shell collision is {c.get_collision_enabled()}")'
new='if str(c.get_collision_profile_name()) != "NoCollision": fail.append(f"shell profile is {c.get_collision_profile_name()}")'
if old not in code: raise RuntimeError("v036 collision check changed")
code=code.replace(old,new,1)
exec(compile(code,str(src)+"::scale-profile-forward-sign-v038","exec"),{"__name__":"__main__","__file__":str(src).replace("v036","v038")})
