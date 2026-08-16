"""Import dimension-corrected release-directed LB-CR01 geometry as Unreal Candidate v004."""

import json
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/SharedSystems/CleaningAMR/Candidate_v002/LB_CR01_CleaningAMR_Candidate_v002.fbx"
DEST = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v004"
MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v004"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v004_unreal_import.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(MAP) or unreal.EditorAssetLibrary.does_directory_exist(DEST):
    raise RuntimeError("Candidate v004 destination must be empty before import")

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(SOURCE),
    "destination_path": DEST,
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
    "import_textures": False,
    "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
})
data = options.get_editor_property("static_mesh_import_data")
data.set_editor_properties({
    "combine_meshes": False,
    "convert_scene": True,
    "convert_scene_unit": True,
    "force_front_x_axis": False,
    "generate_lightmap_u_vs": True,
    "auto_generate_collision": True,
    "remove_degenerates": True,
})
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

mesh_paths = []
for path in unreal.EditorAssetLibrary.list_assets(DEST, recursive=False, include_folder=False):
    asset = unreal.load_asset(path)
    if isinstance(asset, unreal.StaticMesh):
        mesh_paths.append(path)
if len(mesh_paths) < 20:
    raise RuntimeError(f"Expected modular LB-CR01 import; found only {len(mesh_paths)} meshes")

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.new_level(MAP):
    raise RuntimeError(f"Could not create validation map {MAP}")

created = []
for path in mesh_paths:
    mesh = unreal.load_asset(path)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
    label = "LB_CR01_V004_" + mesh.get_name()
    actor.set_actor_label(label)
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(mesh)
    mover = any(token in mesh.get_name().upper() for token in ("WHEEL", "BRUSH", "SCRUB", "SQUEEGEE"))
    component.set_editor_property(
        "mobility",
        unreal.ComponentMobility.MOVABLE if mover else unreal.ComponentMobility.STATIC,
    )
    actor.set_editor_property("tags", [
        unreal.Name("LB.SupportRobot.LB-CR01"),
        unreal.Name("LB.Asset.Candidate.v004"),
        unreal.Name("LB.Motion.Mover" if mover else "LB.Motion.Static"),
    ])
    created.append({"label": label, "mesh": path, "mover": mover})

# Neutral dimension grid: 5 m concrete review pad and a 1.8 m human datum.
cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -3), unreal.Rotator())
floor.set_actor_label("LB_CR01_V004_ValidationFloor")
floor.get_editor_property("static_mesh_component").set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(5.0, 5.0, 0.05))

sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 400), unreal.Rotator(-42, -35, 0))
sun.set_actor_label("LB_CR01_V004_KeyLight")
sun.get_editor_property("directional_light_component").set_editor_property("intensity", 4.0)
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 300), unreal.Rotator())
sky.set_actor_label("LB_CR01_V004_SkyLight")
sky.get_editor_property("light_component").set_editor_property("intensity", 0.55)

camera_specs = (
    ("LB_CR01_V004_CAM_Oblique", unreal.Vector(285, -320, 215), unreal.Vector(0, 0, 45), 46.0),
    ("LB_CR01_V004_CAM_Side", unreal.Vector(0, -360, 105), unreal.Vector(0, 0, 48), 42.0),
    ("LB_CR01_V004_CAM_Top", unreal.Vector(0, 0, 420), unreal.Vector(0, 0, 30), 36.0),
)
for label, location, target, fov in camera_specs:
    camera = actors.spawn_actor_from_class(unreal.CameraActor, location, unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    camera.get_editor_property("camera_component").set_editor_property("field_of_view", fov)

for label, location, intensity, colour in (
    ("LB_CR01_V004_Fill_Front", unreal.Vector(260, -260, 260), 120.0, unreal.Color(255, 225, 205, 255)),
    ("LB_CR01_V004_Fill_Rear", unreal.Vector(-220, 220, 190), 80.0, unreal.Color(190, 215, 255, 255)),
):
    light = actors.spawn_actor_from_class(unreal.PointLight, location, unreal.Rotator())
    light.set_actor_label(label)
    component = light.get_editor_property("point_light_component")
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("attenuation_radius", 650.0)
    component.set_editor_property("light_color", colour)

if not levels.save_current_level():
    raise RuntimeError("Could not save LB-CR01 validation map")

bounds = []
for path in mesh_paths:
    mesh = unreal.load_asset(path)
    box = mesh.get_bounding_box()
    bounds.append((box.min, box.max))
minimum = [min(box[0].to_tuple()[i] for box in bounds) for i in range(3)]
maximum = [max(box[1].to_tuple()[i] for box in bounds) for i in range(3)]
result = {
    "status": "CANDIDATE_NOT_PROMOTED__VISUAL_REVIEW_REQUIRED",
    "source": str(SOURCE),
    "destination": DEST,
    "map": MAP,
    "mesh_count": len(mesh_paths),
    "mover_count": sum(1 for row in created if row["mover"]),
    "aggregate_bounds_cm": {
        "min": minimum,
        "max": maximum,
        "size": [maximum[i] - minimum[i] for i in range(3)],
    },
    "authoritative_envelope_cm": [152.0, 98.0, 112.0],
    "actors": created,
    "fixed_cameras": [row[0] for row in camera_specs],
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_LB_CR01_V004_IMPORT_PASS meshes={len(mesh_paths)} map={MAP}")
