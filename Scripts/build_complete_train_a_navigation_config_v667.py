"""Correct v665's generic config type by always authoring a module config."""
from pathlib import Path
import unreal
project=Path(unreal.Paths.project_dir());source=(project/r"Scripts\build_complete_train_a_navigation_config_v665.py").read_text(encoding="utf-8")
source=source.replace('config=settings.get_editor_property("navigation_system_config")\nif config is None:config=unreal.new_object(unreal.NavigationSystemModuleConfig,outer=settings,name="LB_TrainA_NavigationSystemConfig_v665")',
 'config=unreal.new_object(unreal.NavigationSystemModuleConfig,outer=settings,name="LB_TrainA_NavigationSystemConfig_v667")')
source=source.replace("v665","v667").replace("V665","V667")
exec(compile(source,str(project/r"Scripts\build_complete_train_a_navigation_config_v665.py"),"exec"),globals(),globals())
