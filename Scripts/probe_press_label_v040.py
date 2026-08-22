import unreal


ASSET_PATH = "/Game/LineBoss/Candidates/PressTrains/TrainA/ReadableLabels_v328/SM_CA_MW_PressTrainA_UnrealAxisReadableLabels_v040"
mesh = unreal.load_asset(ASSET_PATH)
if not mesh:
    raise RuntimeError("Missing candidate label mesh")

unreal.log("PRESS_LABEL_PROBE mesh={}".format(mesh.get_path_name()))
for index, material in enumerate(mesh.get_editor_property("static_materials")):
    interface = material.get_editor_property("material_interface")
    unreal.log("PRESS_LABEL_PROBE material[{}]={}".format(
        index, interface.get_path_name() if interface else "<none>"))
