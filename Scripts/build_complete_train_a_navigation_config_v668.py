"""Use the loadable NavigationSystemModuleConfig class in UE 5.8 Python."""
from pathlib import Path
import unreal
project=Path(unreal.Paths.project_dir());source=(project/r"Scripts\build_complete_train_a_navigation_config_v665.py").read_text(encoding="utf-8")
source=source.replace('config=settings.get_editor_property("navigation_system_config")','config=None')
source=source.replace('unreal.NavigationSystemModuleConfig','unreal.load_class(None,"/Script/NavigationSystem.NavigationSystemModuleConfig")')
source=source.replace("v665","v668").replace("V665","V668")
exec(compile(source,str(project/r"Scripts\build_complete_train_a_navigation_config_v665.py"),"exec"),globals(),globals())
