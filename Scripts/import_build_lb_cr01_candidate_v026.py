"""Import CR01 datum-corrected export into an isolated +X-forward v026 Unreal candidate.

Candidate v023 is intentionally preserved as failed orientation evidence.
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v026/LB_CR01_FullRobot_LOD0_XForward_v026.fbx"
DEST = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v026/LOD0"
MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v026"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v026_unreal_import.json"
EXPECTED = [152.0, 98.0, 112.0]

if not SOURCE.exists():
    raise RuntimeError(f"Missing source {SOURCE}")
if unreal.EditorAssetLibrary.does_asset_exist(MAP) or unreal.EditorAssetLibrary.does_directory_exist(DEST):
    raise RuntimeError("v026 destination already exists; preserve candidate evidence")

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(SOURCE), "destination_path": DEST,
    "automated": True, "replace_existing": False, "save": True,
})
opts = unreal.FbxImportUI()
opts.set_editor_properties({
    "import_mesh": True, "import_as_skeletal": False,
    "import_materials": True, "import_textures": False,
    "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
})
data = opts.get_editor_property("static_mesh_import_data")
data.set_editor_properties({
    "combine_meshes": False, "convert_scene": True, "convert_scene_unit": True,
    "force_front_x_axis": True, "generate_lightmap_u_vs": True,
    "auto_generate_collision": False, "remove_degenerates": True,
})
task.set_editor_property("options", opts)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

mesh_paths = []
for path in unreal.EditorAssetLibrary.list_assets(DEST, recursive=False, include_folder=False):
    asset = unreal.load_asset(path)
    if isinstance(asset, unreal.StaticMesh):
        mesh_paths.append(path)
if len(mesh_paths) < 450:
    raise RuntimeError(f"Modular import incomplete: {len(mesh_paths)} meshes")

bounds = [unreal.load_asset(path).get_bounding_box() for path in mesh_paths]
minimum = [min(box.min.to_tuple()[axis] for box in bounds) for axis in range(3)]
maximum = [max(box.max.to_tuple()[axis] for box in bounds) for axis in range(3)]
size = [maximum[axis] - minimum[axis] for axis in range(3)]
bounds_pass = all(abs(actual - expected) <= 0.2 for actual, expected in zip(size, EXPECTED))
if not bounds_pass:
    raise RuntimeError(f"Corrected +X-forward bounds failed: actual={size}, expected={EXPECTED}")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.new_level(MAP):
    raise RuntimeError(f"Could not create {MAP}")

moving_tokens = ("WHEEL", "CASTER", "BRUSH", "SCRUB", "SQUEEGEE", "HOPPER", "DOOR", "LATCH", "LID", "LIFT", "PIVOT")
created = []
for path in mesh_paths:
    mesh = unreal.load_asset(path)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
    name = mesh.get_name()
    actor.set_actor_label("LB_CR01_V026_" + name)
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(mesh)
    mover = any(token in name.upper() for token in moving_tokens)
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE if mover else unreal.ComponentMobility.STATIC)
    actor.set_editor_property("tags", [
        unreal.Name("LB.SupportRobot.LB-CR01"), unreal.Name("LB.Asset.Candidate.v026"),
        unreal.Name("LB.Motion.Mover" if mover else "LB.Motion.Static"),
    ])
    created.append({"mesh": path, "mover": mover})

cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -3), unreal.Rotator())
floor.set_actor_label("LB_CR01_V026_ValidationFloor")
floor.get_editor_property("static_mesh_component").set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(5, 5, 0.05))

sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 400), unreal.Rotator(-42, -35, 0))
sun.set_actor_label("LB_CR01_V026_KeyLight")
sun.get_editor_property("directional_light_component").set_editor_property("intensity", 3.2)
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 300), unreal.Rotator())
sky.set_actor_label("LB_CR01_V026_SkyLight")
sky.get_editor_property("light_component").set_editor_property("intensity", 0.45)
for label, location, intensity, colour in (
    ("FillFront", unreal.Vector(260, -260, 260), 900, unreal.Color(255, 225, 205, 255)),
    ("FillRear", unreal.Vector(-220, 220, 190), 550, unreal.Color(190, 215, 255, 255)),
):
    light = actors.spawn_actor_from_class(unreal.PointLight, location, unreal.Rotator())
    light.set_actor_label("LB_CR01_V026_" + label)
    light.get_editor_property("point_light_component").set_editor_properties({
        "intensity": intensity, "attenuation_radius": 650, "light_color": colour,
    })

cameras = (
    ("Oblique", unreal.Vector(300, -320, 210), unreal.Vector(0, 0, 48), 46.0),
    ("Side", unreal.Vector(0, -360, 105), unreal.Vector(0, 0, 48), 42.0),
    ("Top", unreal.Vector(0, 0, 420), unreal.Vector(0, 0, 30), 36.0),
)
for label, location, target, fov in cameras:
    camera = actors.spawn_actor_from_class(unreal.CameraActor, location, unreal.Rotator())
    camera.set_actor_label("LB_CR01_V026_CAM_" + label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    camera.get_editor_property("camera_component").set_editor_property("field_of_view", fov)

if not levels.save_current_level():
    raise RuntimeError("Could not save v024 evidence map")

result = {
    "status": "CANDIDATE_NOT_PROMOTED__RUNTIME_VISUAL_REVIEW_REQUIRED",
    "source": str(SOURCE), "destination": DEST, "map": MAP,
    "mesh_count": len(mesh_paths), "mover_count": sum(item["mover"] for item in created),
    "aggregate_bounds_cm": {"min": minimum, "max": maximum, "size": size},
    "authoritative_envelope_cm": EXPECTED, "bounds_tolerance_cm": 0.2,
    "bounds_pass": bounds_pass, "forward_axis": "+X",
    "fixed_cameras": ["LB_CR01_V026_CAM_" + item[0] for item in cameras],
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_LB_CR01_V026_IMPORT_PASS meshes={len(mesh_paths)} movers={result['mover_count']} bounds={size}")
