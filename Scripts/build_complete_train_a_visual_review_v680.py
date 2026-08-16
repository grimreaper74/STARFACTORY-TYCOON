from pathlib import Path
import unreal
project=Path(unreal.Paths.project_dir());source=(project/r"Scripts\build_complete_train_a_visual_review_v678.py").read_text(encoding="utf-8")
source=source.replace('sun.directional_light_component.set_editor_property("intensity",7.0)','sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity",7.0)')
source=source.replace("v678","v680").replace("V678","V680")
exec(compile(source,str(project/r"Scripts\build_complete_train_a_visual_review_v678.py"),"exec"),globals(),globals())
