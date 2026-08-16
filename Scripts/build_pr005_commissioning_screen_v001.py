"""Mount the first PR-005 commissioning overview screen candidate."""

from pathlib import Path
import json
import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_CairnwellBranding_v001"
ROOT = "/Game/LineBoss/Brand/Cairnwell/Candidate_v001/PR005_HMI"
MESH_ROOT = ROOT + "/DisplaySurface_v001"
MESH = MESH_ROOT + "/SM_LB_PR005_HMIDisplaySurface_Candidate_v001"
TEXTURE = ROOT + "/T_PR005_COMMISSIONING_OVERVIEW_v001"
MATERIAL = ROOT + "/M_PR005_COMMISSIONING_OVERVIEW_v001"
SOURCE = str(Path(unreal.Paths.project_dir()) / "SourceAssets/Brand/Candidate_v001/PR005_HMI/T_PR005_COMMISSIONING_OVERVIEW_v001.png")
FBX = str(Path(unreal.Paths.project_dir()) / "SourceAssets/Brand/Candidate_v001/PR005_HMI/DisplaySurface_v001/SM_LB_PR005_HMIDisplaySurface_Candidate_v001.fbx")
MANIFEST = str(Path(unreal.Paths.project_dir()) / "SourceAssets/Brand/Candidate_v001/PR005_HMI/DisplaySurface_v001/manifest.json")
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/pr005_commissioning_screen_v001.json"

asset_lib = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
mel = unreal.MaterialEditingLibrary

current_map = unreal.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0]
if current_map != MAP:
    raise RuntimeError(f"Launch with {MAP}; current map is {current_map}")

for actor in actors.get_all_level_actors():
    if actor.get_actor_label().startswith("LB_HMI_SCREEN_"):
        actors.destroy_actor(actor)

texture = unreal.load_asset(TEXTURE)
if texture is None:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": SOURCE, "destination_path": ROOT,
        "destination_name": "T_PR005_COMMISSIONING_OVERVIEW_v001",
        "automated": True, "replace_existing": True, "save": True,
    })
    asset_tools.import_asset_tasks([task])
    texture = unreal.load_asset(TEXTURE)
if texture is None:
    raise RuntimeError("PR-005 commissioning texture import failed")

material = unreal.load_asset(MATERIAL)
if material is None:
    material = asset_tools.create_asset(
        "M_PR005_COMMISSIONING_OVERVIEW_v001", ROOT,
        unreal.Material, unreal.MaterialFactoryNew())
if material is None:
    raise RuntimeError("PR-005 commissioning material creation failed")
mel.delete_all_material_expressions(material)
texcoord = mel.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -700, 80)
minus_one = mel.create_material_expression(material, unreal.MaterialExpressionConstant2Vector, -700, 190)
minus_one.set_editor_properties({"r": -1.0, "g": -1.0})
invert = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -520, 90)
one = mel.create_material_expression(material, unreal.MaterialExpressionConstant2Vector, -520, 220)
one.set_editor_properties({"r": 1.0, "g": 1.0})
rotate_uv = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -340, 100)
sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -300, 0)
sample.set_editor_property("texture", texture)
mel.connect_material_expressions(texcoord, "", invert, "A")
mel.connect_material_expressions(minus_one, "", invert, "B")
mel.connect_material_expressions(invert, "", rotate_uv, "A")
mel.connect_material_expressions(one, "", rotate_uv, "B")
mel.connect_material_expressions(rotate_uv, "", sample, "UVs")
mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
material.set_editor_property("two_sided", True)
material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mel.recompile_material(material)
asset_lib.save_loaded_asset(material, only_if_is_dirty=False)

mesh = unreal.load_asset(MESH)
if mesh is None:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": FBX, "destination_path": MESH_ROOT,
        "destination_name": "SM_LB_PR005_HMIDisplaySurface_Candidate_v001",
        "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "generate_lightmap_u_vs": True,
        "auto_generate_collision": False, "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = unreal.load_asset(MESH)
if mesh is None:
    raise RuntimeError("Exact authored PR-005 HMI display-surface import failed")

# The FBX has the original display's world-space coordinates baked into its
# vertices, including an 8 mm offset along the authored face normal.  Keeping
# this actor at identity avoids fragile Euler reconstruction in Unreal.
screen = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector())
screen.set_actor_label("LB_HMI_SCREEN_PR005_CommissioningOverview")
screen.set_actor_rotation(unreal.Rotator(), False)
screen.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
component = screen.get_component_by_class(unreal.StaticMeshComponent)
component.set_static_mesh(mesh)
component.set_material(0, material)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_editor_property("cast_shadow", False)

target = unreal.Vector(-296.7, 280.0, 110.5)
operator_camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-430.0, 540.0, 145.0))
operator_camera.set_actor_label("LB_HMI_SCREEN_CAM_Operator")
operator_camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(operator_camera.get_actor_location(), target), False)
operator_camera.get_editor_property("camera_component").set_editor_property("field_of_view", 42.0)

close_camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-414.0, 305.0, 152.0))
close_camera.set_actor_label("LB_HMI_SCREEN_CAM_Close")
close_camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(close_camera.get_actor_location(), target), False)
close_camera.get_editor_property("camera_component").set_editor_property("field_of_view", 30.0)

levels.save_current_level()
asset_lib.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "status": "CANDIDATE_NOT_PROMOTED",
    "map": MAP,
    "source_png": SOURCE,
    "screen_size_mm": [340, 255],
    "screen_pitch_down_deg": 20,
    "display_surface_mesh": MESH,
    "display_surface_fbx": FBX,
    "display_surface_manifest": MANIFEST,
    "actor_transform": "identity; authored world-space coordinates baked into FBX vertices",
    "printed_surface_standoff_mm": 8,
    "uv_correction": "180 degrees in material (UV = 1 - UV)",
    "presentation": "static deterministic commissioning overview; live UMG binding pending native build gate",
    "promotion": False
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_COMMISSIONING_SCREEN_V001_PASS audit={AUDIT}")
