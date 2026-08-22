import unreal

MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load OneFactory map")

for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if isinstance(actor, unreal.CameraActor):
        unreal.log("ONE_FACTORY_CAMERA label={} location={} rotation={}".format(
            actor.get_actor_label(), actor.get_actor_location(), actor.get_actor_rotation()))
