"""Repair the two suite regressions from the blanket mesh refresh.

1. SM_LB_WeldRobot_SharedBase_v001: the DetailUplift alias drop has
   different geometry than the validated runtime art (contract bounds
   90 x 66 x 186); re-import from the true source in
   WeldRobotRuntime_v001/Exports.
2. Robot joints J3-J6: slots the refresh added fell to WorldGrid; the
   slot names name their semantic v002 MICs, so rebind by name.
"""
import unreal

ROOT = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
        "SourceAssets/Candidate/WeldShop/WeldRobotRuntime_v001/Exports/"
        "LB_WeldRobot_SharedBase_LOD0_v001.fbx")
MIC_ROOT = ("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/"
            "Materials_v002/")

registry = unreal.AssetRegistryHelpers.get_asset_registry()
PACKAGES = {}
for data in registry.get_assets_by_class(
        unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh"), True):
    PACKAGES[str(data.asset_name)] = str(data.package_name)

tools = unreal.AssetToolsHelpers.get_asset_tools()

# --- shared base re-import from the validated source ---
package = PACKAGES["SM_LB_WeldRobot_SharedBase_v001"]
mesh = unreal.load_asset(package)
saved_slots = {}
for entry in mesh.get_editor_property("static_materials"):
    slot = str(entry.get_editor_property("material_slot_name"))
    saved_slots[slot] = entry.get_editor_property("material_interface")

options = unreal.FbxImportUI()
options.set_editor_property("import_mesh", True)
options.set_editor_property("import_materials", False)
options.set_editor_property("import_textures", False)
options.set_editor_property("import_as_skeletal", False)
options.static_mesh_import_data.set_editor_property("combine_meshes", True)
task = unreal.AssetImportTask()
task.set_editor_property("filename", ROOT)
task.set_editor_property("destination_path", package.rsplit("/", 1)[0])
task.set_editor_property("destination_name",
                         "SM_LB_WeldRobot_SharedBase_v001")
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", False)
task.set_editor_property("options", options)
tools.import_asset_tasks([task])

mesh = unreal.load_asset(package)
materials = list(mesh.get_editor_property("static_materials"))
for entry in materials:
    slot = str(entry.get_editor_property("material_slot_name"))
    if slot in saved_slots and saved_slots[slot]:
        entry.set_editor_property("material_interface", saved_slots[slot])
mesh.set_editor_property("static_materials", materials)
unreal.EditorAssetLibrary.save_asset(package)
box = mesh.get_bounding_box()
size = box.max - box.min
unreal.log("REPAIR_BASE size={:.1f}x{:.1f}x{:.1f}".format(
    size.x, size.y, size.z))

# --- joint slot rebinding by semantic name ---
fixed = 0
for joint in ("J3", "J4", "J5", "J6"):
    name = "SM_LB_BodyShopRobotNative_{}_v001".format(joint)
    pkg = PACKAGES.get(name)
    if not pkg:
        continue
    jmesh = unreal.load_asset(pkg)
    materials = list(jmesh.get_editor_property("static_materials"))
    changed = False
    for entry in materials:
        mat = entry.get_editor_property("material_interface")
        if mat and mat.get_name() != "WorldGridMaterial":
            continue
        slot = str(entry.get_editor_property("material_slot_name"))
        if not slot.startswith("M_LB_BS_"):
            continue
        semantic = slot[len("M_LB_BS_"):]
        mic_path = "{}MI_LB_BodyShop_{}_v002".format(MIC_ROOT, semantic)
        mic = unreal.EditorAssetLibrary.load_asset(mic_path)
        if mic:
            entry.set_editor_property("material_interface", mic)
            changed = True
            fixed += 1
    if changed:
        jmesh.set_editor_property("static_materials", materials)
        unreal.EditorAssetLibrary.save_asset(pkg)
unreal.log("REPAIR_JOINTS rebound={}".format(fixed))
