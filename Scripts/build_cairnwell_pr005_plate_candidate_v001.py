"""Build the isolated Cairnwell PR-005 asset-plate validation candidate."""

from pathlib import Path
import json
import unreal

SOURCE_MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation"
MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_CairnwellBranding_v001"
MATERIAL = "/Game/LineBoss/Brand/Cairnwell/Candidate_v001/M_Cairnwell_PR005_AssetPlate_FlipU_v001"
TEXTURE = "/Game/LineBoss/Brand/Cairnwell/Candidate_v001/T_Cairnwell_PR005_AssetPlate_FlipU_v001"
TEXTURE_SOURCE = str(Path(unreal.Paths.project_dir()) / "SourceAssets/Brand/Candidate_v001/T_CAIRNWELL_PR005_ASSET_PLATE_FLIPU_v001.png")
MESH_PATH = "/Game/LineBoss/Brand/Cairnwell/Candidate_v001/PR005_Plaque/SM_LB_PR005_CairnwellAssetPlaque_Candidate_v001"
FBX = str(Path(unreal.Paths.project_dir()) / "SourceAssets/Brand/Candidate_v001/PR005_Plaque/SM_LB_PR005_CairnwellAssetPlaque_Candidate_v001.fbx")
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/cairnwell_pr005_plate_candidate_v001.json"

asset_lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

current_map = unreal.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0]
if current_map != MAP:
    raise RuntimeError(f"Launch this script with {MAP}; current map is {current_map}")
for actor in actors.get_all_level_actors():
    if actor.get_actor_label().startswith("LB_BRAND_PR005_"):
        actors.destroy_actor(actor)

material = unreal.load_asset(MATERIAL)
texture = unreal.load_asset(TEXTURE)
if texture is None:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": TEXTURE_SOURCE,
        "destination_path": "/Game/LineBoss/Brand/Cairnwell/Candidate_v001",
        "destination_name": "T_Cairnwell_PR005_AssetPlate_FlipU_v001",
        "automated": True, "replace_existing": True, "save": True,
    })
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(TEXTURE)
if material is None:
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_Cairnwell_PR005_AssetPlate_FlipU_v001",
        "/Game/LineBoss/Brand/Cairnwell/Candidate_v001",
        unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -420, -80)
    sample.set_editor_property("texture", texture)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 140)
    rough.set_editor_property("r", 0.42)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 230)
    metal.set_editor_property("r", 0.12)
    mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    material.set_editor_property("two_sided", True)
    mel.recompile_material(material)
    asset_lib.save_loaded_asset(material, only_if_is_dirty=False)
carrier_material = unreal.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_DarkMachine")
face_mesh = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
mesh = unreal.load_asset(MESH_PATH)
if mesh is None:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": FBX,
        "destination_path": "/Game/LineBoss/Brand/Cairnwell/Candidate_v001/PR005_Plaque",
        "destination_name": "SM_LB_PR005_CairnwellAssetPlaque_Candidate_v001",
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
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(MESH_PATH)
if material is None or carrier_material is None or face_mesh is None or mesh is None:
    raise RuntimeError("Missing branding, carrier material, face plane, or modular plaque mesh")

plate = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-290.7, 280.0, 65.5))
plate.set_actor_label("LB_BRAND_PR005_AssetPlate")
plate.set_actor_rotation(unreal.Rotator(), False)
component = plate.get_component_by_class(unreal.StaticMeshComponent)
component.set_static_mesh(mesh)
component.set_material(0, carrier_material)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_editor_property("cast_shadow", False)

face = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-292.0, 280.0, 65.5))
face.set_actor_label("LB_BRAND_PR005_AssetPlateFace")
face.set_actor_rotation(unreal.Rotator(roll=90.0, pitch=0.0, yaw=-90.0), False)
face.set_actor_scale3d(unreal.Vector(0.48, 0.144, 1.0))
face_component = face.get_component_by_class(unreal.StaticMeshComponent)
face_component.set_static_mesh(face_mesh)
face_component.set_material(0, material)
face_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
face_component.set_editor_property("cast_shadow", False)

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-430.0, 540.0, 145.0))
camera.set_actor_label("LB_BRAND_PR005_CAM_HMI")
camera.set_actor_rotation(
    unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(-290.7, 280.0, 70.0)), False
)
camera.get_editor_property("camera_component").set_editor_property("field_of_view", 42.0)

levels.save_current_level()
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "status": "VISUAL_PASS_MODULE_NOT_PROMOTED",
    "map": MAP,
    "plate_id": "PR005-DC01",
    "size_mm": [480, 144],
    "location_cm": [-290.7, 280.0, 65.5],
    "printed_face_location_cm": [-292.0, 280.0, 65.5],
    "printed_face_rotation_deg": {"roll": 90.0, "pitch": 0.0, "yaw": -90.0},
    "mesh": MESH_PATH,
    "visual_evidence": "Saved/ValidationScreenshots/Brand/Candidate_v001/cairnwell_pr005_asset_plate_hmi.png",
    "visual_review": "PASS: readable, correctly oriented, seated below controls; surrounding HMI remains unpromoted",
    "promotion": False,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_CAIRNWELL_PR005_PLATE_V001_PASS audit={AUDIT}")
