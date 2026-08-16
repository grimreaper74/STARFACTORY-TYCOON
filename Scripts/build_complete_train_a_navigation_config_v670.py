"""Author the UE 5.8 module config using its exposed class property only."""
from pathlib import Path
import unreal
project=Path(unreal.Paths.project_dir());source=(project/r"Scripts\build_complete_train_a_navigation_config_v665.py").read_text(encoding="utf-8")
source=source.replace('config=settings.get_editor_property("navigation_system_config")','config=None')
source=source.replace('unreal.NavigationSystemModuleConfig','unreal.load_class(None,"/Script/NavigationSystem.NavigationSystemModuleConfig")')
source=source.replace('config.set_editor_property("strictly_static",False);config.set_editor_property("auto_spawn_missing_nav_data",True);config.set_editor_property("spawn_nav_data_in_nav_bounds_level",True);','')
source=source.replace("v665","v670").replace("V665","V670")
exec(compile(source,str(project/r"Scripts\build_complete_train_a_navigation_config_v665.py"),"exec"),globals(),globals())
