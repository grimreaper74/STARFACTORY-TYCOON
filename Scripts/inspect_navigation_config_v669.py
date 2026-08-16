import unreal
cls=unreal.load_class(None,"/Script/NavigationSystem.NavigationSystemModuleConfig")
obj=unreal.new_object(cls,name="LB_InspectNavConfig_v669")
unreal.log("LB_NAV_CONFIG_CLASS="+obj.get_class().get_name())
unreal.log("LB_NAV_CONFIG_DIR="+"|".join(sorted(n for n in dir(obj) if not n.startswith("__"))))
