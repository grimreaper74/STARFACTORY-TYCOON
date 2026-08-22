import unreal


MAP_PATH = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
OLD_ROOT = "/Game/LineBoss/Candidates/PressShop/TrainIdentity/PhysicalSigns_v397"
NEW_ROOT = "/Game/LineBoss/Candidates/PressShop/TrainIdentity/PhysicalSigns_v411"
OLD_SUFFIX = "_v396"
NEW_SUFFIX = "_v410"


def replacement_path(old_path):
    if not old_path.startswith(OLD_ROOT):
        return None
    return old_path.replace(OLD_ROOT, NEW_ROOT).replace(OLD_SUFFIX, NEW_SUFFIX)


if not unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH):
    raise RuntimeError("Unable to load authoritative OneFactory map: {}".format(MAP_PATH))

replaced = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if not mesh:
            continue
        old_path = mesh.get_path_name()
        new_path = replacement_path(old_path)
        if not new_path:
            continue
        new_mesh = unreal.load_asset(new_path)
        if not new_mesh:
            raise RuntimeError("Replacement sign asset missing: {}".format(new_path))
        component.set_editor_property("static_mesh", new_mesh)
        replaced.append((actor.get_name(), component.get_name(), old_path, new_path))

if not replaced:
    raise RuntimeError("No obsolete v397 press-sign references found; map was not saved.")

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Failed to save authoritative OneFactory map after sign migration.")

for row in replaced:
    unreal.log("PRESS_SIGN_V411_MIGRATED actor={} component={} old={} new={}".format(*row))
unreal.log("PRESS_SIGN_V411_MIGRATION_COMPLETE count={}".format(len(replaced)))
