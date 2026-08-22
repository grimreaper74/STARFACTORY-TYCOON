import unreal


PANEL_ROOT = "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040PanelModules_v001/Meshes"
PANEL_NAMES = (
    "DOOR_FRONT_LEFT", "DOOR_FRONT_RIGHT", "DOOR_REAR_LEFT", "DOOR_REAR_RIGHT",
    "FENDER_FRONT_LEFT", "FENDER_FRONT_RIGHT", "HOOD_PANEL", "QUARTER_PANEL_LEFT",
    "QUARTER_PANEL_RIGHT", "ROOF_PANEL", "TAILGATE_PANEL",
)
MATERIAL_PATH = "/Game/LineBoss/Materials/M_LB_StructureSteel"
LEGACY_RUNTIME_TOKEN = "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"


def fail(message):
    raise RuntimeError("Cairnwell panel rebind failed: " + message)


library = unreal.EditorAssetLibrary
material = library.load_asset(MATERIAL_PATH)
if not isinstance(material, unreal.MaterialInterface):
    fail("required cookable factory material is unavailable: " + MATERIAL_PATH)

changed = []
for name in PANEL_NAMES:
    path = PANEL_ROOT + "/SM_LB_C2040_" + name + "_v001"
    mesh = library.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        fail("panel mesh is unavailable: " + path)
    slots = mesh.get_editor_property("static_materials")
    if len(slots) != 1:
        fail("expected exactly one material slot for " + path + ", got " + str(len(slots)))
    current = slots[0].get_editor_property("material_interface")
    current_path = current.get_path_name() if current else ""
    if LEGACY_RUNTIME_TOKEN not in current_path and current_path != MATERIAL_PATH:
        fail("unexpected existing panel material for " + path + ": " + current_path)
    mesh.set_material(0, material)
    if not library.save_loaded_asset(mesh, only_if_is_dirty=False):
        fail("could not save " + path)
    changed.append(path)

unreal.log("Cairnwell panel rebind complete: " + str(len(changed)) + " meshes now use " + MATERIAL_PATH)
