"""Import the Blender-validated repaired wrapped coil as the player-storage load visual."""
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
source = root / "SourceAssets/Candidate/PressShop/InboundCoilDelivery/WrappedCoil_v20260809_v003/SM_CA_MW_WrappedCoil_Repaired_v003.fbx"
destination = "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound"
asset_name = "SM_CA_MW_WrappedCoil_Repaired_v003"
asset_path = f"{destination}/{asset_name}"
if not source.is_file():
    raise RuntimeError(f"Missing Blender FBX export: {source}")

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(source),
    "destination_path": destination,
    "destination_name": asset_name,
    "automated": True,
    "replace_existing": True,
    "replace_existing_settings": True,
    "save": True,
})
options = unreal.FbxImportUI()
options.set_editor_properties({
    "import_mesh": True,
    "import_as_skeletal": False,
    "import_materials": True,
    "import_textures": True,
    "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    "automated_import_should_detect_type": False,
})
options.static_mesh_import_data.set_editor_properties({
    "combine_meshes": True,
    "generate_lightmap_u_vs": True,
    "auto_generate_collision": True,
    "import_uniform_scale": 100.0,
})
task.options = options
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Wrapped coil static mesh import failed")
d = mesh.get_bounds().box_extent * 2.0
if not (175.0 < d.x < 185.0 and 145.0 < d.y < 155.0 and 173.0 < d.z < 185.0):
    raise RuntimeError(f"Wrapped coil bounds changed unexpectedly: {d}")

texture_dir = source.parent / "Textures"
texture_sources = {
    "T_CA_MW_WrappedCoil_BaseColor_v003": texture_dir / "T_CA_MW_WrappedCoil_BaseColor_v003.png",
    "T_CA_MW_WrappedCoil_ORM_v003": texture_dir / "T_CA_MW_WrappedCoil_ORM_v003.png",
    "T_CA_MW_WrappedCoil_Normal_v003": texture_dir / "T_CA_MW_WrappedCoil_Normal_v003.png",
}
texture_tasks = []
for name, filename in texture_sources.items():
    if not filename.is_file():
        raise RuntimeError(f"Missing Blender-extracted texture: {filename}")
    texture_task = unreal.AssetImportTask()
    texture_task.set_editor_properties({
        "filename": str(filename), "destination_path": destination,
        "destination_name": name, "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": True,
    })
    texture_tasks.append(texture_task)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(texture_tasks)
textures = {name: unreal.EditorAssetLibrary.load_asset(f"{destination}/{name}") for name in texture_sources}
if not all(isinstance(texture, unreal.Texture2D) for texture in textures.values()):
    raise RuntimeError("Wrapped coil textures failed to import")
textures["T_CA_MW_WrappedCoil_ORM_v003"].set_editor_property("srgb", False)
textures["T_CA_MW_WrappedCoil_Normal_v003"].set_editor_properties({
    "srgb": False, "compression_settings": unreal.TextureCompressionSettings.TC_NORMALMAP,
})

tools = unreal.AssetToolsHelpers.get_asset_tools()
body_path = f"{destination}/Material_0"
core_path = f"{destination}/MI_CA_MW_WrappedCoil_StructuralCore"
for path in (body_path, core_path):
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        created = tools.create_asset(path.rsplit("/", 1)[1], destination, unreal.Material, unreal.MaterialFactoryNew())
        if not isinstance(created, unreal.Material):
            raise RuntimeError(f"Could not create {path}")
body = unreal.EditorAssetLibrary.load_asset(body_path)
core = unreal.EditorAssetLibrary.load_asset(core_path)
unreal.MaterialEditingLibrary.delete_all_material_expressions(body)
base = unreal.MaterialEditingLibrary.create_material_expression(body, unreal.MaterialExpressionTextureSample, -500, -100)
base.texture = textures["T_CA_MW_WrappedCoil_BaseColor_v003"]
orm = unreal.MaterialEditingLibrary.create_material_expression(body, unreal.MaterialExpressionTextureSample, -500, 100)
orm.texture = textures["T_CA_MW_WrappedCoil_ORM_v003"]
normal = unreal.MaterialEditingLibrary.create_material_expression(body, unreal.MaterialExpressionTextureSample, -500, 300)
normal.texture = textures["T_CA_MW_WrappedCoil_Normal_v003"]
normal.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
unreal.MaterialEditingLibrary.connect_material_property(base, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
unreal.MaterialEditingLibrary.connect_material_property(orm, "G", unreal.MaterialProperty.MP_ROUGHNESS)
unreal.MaterialEditingLibrary.connect_material_property(orm, "B", unreal.MaterialProperty.MP_METALLIC)
unreal.MaterialEditingLibrary.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
unreal.MaterialEditingLibrary.recompile_material(body)
unreal.MaterialEditingLibrary.delete_all_material_expressions(core)
core_colour = unreal.MaterialEditingLibrary.create_material_expression(core, unreal.MaterialExpressionConstant3Vector, -250, 0)
core_colour.constant = unreal.LinearColor(0.11, 0.12, 0.13, 1.0)
unreal.MaterialEditingLibrary.connect_material_property(core_colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
unreal.MaterialEditingLibrary.recompile_material(core)
slots = mesh.get_editor_property("static_materials")
if len(slots) != 2:
    raise RuntimeError(f"Expected body and structural-core material slots, got {len(slots)}")
slots[0].set_editor_property("material_interface", body)
slots[1].set_editor_property("material_interface", core)
mesh.set_editor_property("static_materials", slots)
mesh.set_material(0, body)
mesh.set_material(1, core)
for path in (body_path, core_path, asset_path):
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
if not unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False):
    raise RuntimeError("Wrapped coil asset save failed")
unreal.log(f"LB_APPROVED_WRAPPED_COIL_V914_PASS bounds_cm=({d.x:.3f},{d.y:.3f},{d.z:.3f})")
