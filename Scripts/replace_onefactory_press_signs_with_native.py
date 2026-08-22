import unreal


MAP_PATH = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
BROKEN_ROOT = "/Game/LineBoss/Candidates/PressShop/TrainIdentity/PhysicalSigns_v411"
TRAIN_NAMES = {"A": "PRESS TRAIN A", "B": "PRESS TRAIN B", "C": "PRESS TRAIN C", "D": "PRESS TRAIN D"}


if not unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH):
    raise RuntimeError("Unable to load authoritative OneFactory map")

targets = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh and mesh.get_path_name().startswith(BROKEN_ROOT):
            targets.append((actor, mesh.get_path_name()))

if len(targets) != 4:
    raise RuntimeError("Expected exactly four broken v411 signs, found {}".format(len(targets)))

for old_actor, old_path in targets:
    letter = next((key for key in TRAIN_NAMES if "Identity_{}_".format(key) in old_path), None)
    if not letter:
        raise RuntimeError("Could not identify press train for {}".format(old_path))
    replacement = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.LBPressTrainSignageActor,
        old_actor.get_actor_location(),
        old_actor.get_actor_rotation())
    if not replacement:
        raise RuntimeError("Failed to spawn native sign for {}".format(letter))
    replacement.set_actor_label("LB_PressTrain{}_NativeSign".format(letter))
    label = replacement.get_editor_property("label")
    label.set_text(unreal.TextLibrary.conv_string_to_text(TRAIN_NAMES[letter]))
    if not unreal.EditorLevelLibrary.destroy_actor(old_actor):
        raise RuntimeError("Failed to remove broken sign for {}".format(letter))
    unreal.log("PRESS_SIGN_NATIVE_REPLACED train={} old={} new={}".format(
        letter, old_path, replacement.get_path_name()))

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Failed to save OneFactory map after native sign replacement")
unreal.log("PRESS_SIGN_NATIVE_REPLACEMENT_COMPLETE count=4")
