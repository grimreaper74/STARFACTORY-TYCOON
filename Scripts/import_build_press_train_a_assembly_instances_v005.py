"""Reconstruct retained 163-object Train A manifest at exact local coordinates in isolated UE map."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v001"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v001.json"
SOURCE_VALIDATION = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_VALIDATION_v001.json"
MODULE_STAGING = ROOT / "Saved/ImportStaging/PressTrainAAssemblyIntegration_v004"
AUTHORED_STAGING = ROOT / "Saved/ImportStaging/PressTrainAAssemblyInstances_v005"
AUTHORED_RECEIPT = ROOT / "Saved/Audits/PressTrains/press_train_a_assembly_instance_staging_v005.json"
DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v005"
MODULE_DEST = DEST + "/Modules"
AUTHORED_DEST = DEST + "/Authored"
MATERIAL_DEST = DEST + "/Materials"
MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v005"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_assembly_integration_build_v005.json"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
source_validation = json.loads(SOURCE_VALIDATION.read_text(encoding="utf-8"))
authored_receipt = json.loads(AUTHORED_RECEIPT.read_text(encoding="utf-8"))
if source_validation.get("status") != "PASS" or authored_receipt.get("status", "").startswith("PASS") is False:
    raise RuntimeError("Retained source or authored staging validation is not PASS")
if library.does_asset_exist(MAP) or library.does_directory_exist(DEST) or OUT.exists():
    raise RuntimeError("Refusing to overwrite AssemblyStudyIntegration v005")


def import_mesh(path, dest, name):
    task = unreal.AssetImportTask()
    task.set_editor_properties({"filename": str(path), "destination_path": dest, "destination_name": name,
                                "automated": True, "replace_existing": False, "save": True})
    options = unreal.FbxImportUI()
    options.set_editor_properties({"import_mesh": True, "import_as_skeletal": False,
                                   "import_materials": False, "import_textures": False,
                                   "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH})
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({"combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
                                "transform_vertex_to_absolute": False, "bake_pivot_in_vertex": False,
                                "generate_lightmap_u_vs": True, "auto_generate_collision": False,
                                "remove_degenerates": True})
    task.set_editor_property("options", options)
    tools.import_asset_tasks([task])
    asset = library.load_asset(f"{dest}/{name}")
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Import failed: {path}")
    return asset


module_assets = {}
for source_record in manifest["source_files"]:
    name = Path(source_record["path"]).stem
    module_assets[name] = import_mesh(MODULE_STAGING / f"{name}.fbx", MODULE_DEST, name)
authored_assets = {}
for row in authored_receipt["assets"]:
    authored_assets[row["asset"]] = import_mesh(AUTHORED_STAGING / row["file"], AUTHORED_DEST, row["asset"])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

roles = ("Charcoal", "Foundation", "WorkedSteel", "Green", "SafetyYellow", "TrainABlue", "DarkRubber",
         "LabelIvory", "HydraulicRed", "PneumaticBlue", "ElectricalOrange", "InspectionWhite", "PanelSteel", "BlankSteel")
materials = {}
for role in roles:
    src = f"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v004/Materials/M_CA_MW_PTA_{role}_Integration_v004"
    dst = f"{MATERIAL_DEST}/M_CA_MW_PTA_{role}_Integration_v005"
    if not library.duplicate_asset(src, dst):
        raise RuntimeError(f"Could not duplicate calibrated candidate material: {role}")
    materials[role] = library.load_asset(dst)


def slot_names(mesh):
    return [str(row.get_editor_property("material_slot_name")) for row in mesh.get_editor_property("static_materials")]


def role_for(slot):
    key = slot.lower()
    tests = (("foundation", "Foundation"), ("inspectionwhite", "InspectionWhite"), ("blanksteel", "BlankSteel"),
             ("panelsteel", "PanelSteel"), ("yellow", "SafetyYellow"), ("traina", "TrainABlue"),
             ("hydraulic", "HydraulicRed"), ("pneumatic", "PneumaticBlue"), ("electrical", "ElectricalOrange"),
             ("rubber", "DarkRubber"), ("ivory", "LabelIvory"), ("green", "Green"))
    for token, role in tests:
        if token in key:
            return role
    if "worked" in key or "steel" in key or "metal" in key:
        return "WorkedSteel"
    return "Charcoal"


all_assets = {**module_assets, **authored_assets}
material_rows = []
for name, mesh in all_assets.items():
    for index, slot in enumerate(slot_names(mesh)):
        role = role_for(slot)
        mesh.set_material(index, materials[role])
        material_rows.append({"asset": name, "slot": slot, "role": role})

nanite_assets = []
nanite_failures = []
for name, mesh in module_assets.items():
    if any(token in name for token in ("HeavyCrownFrame", "EnclosureExterior", "YellowAccessGuard", "Identity", "StagePlate", "Badge")):
        try:
            settings = mesh.get_editor_property("nanite_settings")
            settings.set_editor_property("enabled", True)
            mesh.set_editor_property("nanite_settings", settings)
            nanite_assets.append(name)
        except Exception as exc:
            nanite_failures.append({"asset": name, "error": str(exc)})
for mesh in all_assets.values():
    library.save_loaded_asset(mesh, only_if_is_dirty=False)

if not levels.new_level(MAP):
    raise RuntimeError(MAP)

COMMON = ("LB.PressTrain.TrainA.AssemblyIntegration.v005", "LB.Asset.Candidate.v005",
          "LB.Asset.CandidateNotPromoted", "LB.Authority.WorldPlacement.TBCNotInvented",
          "LB.Scope.IsolatedLocalOrigin", "LB.Runtime.Authority.NotImplemented")


def tag(actor, *extra):
    actor.tags = [unreal.Name(value) for value in (*COMMON, *extra)]


authored_map = {row["object"]: row["asset"] for row in authored_receipt["instances"]}
placed = []
for record in manifest["instances"]:
    if record["source_fbx"] == "ASSEMBLY_STUDY_AUTHORED":
        mesh = authored_assets[authored_map[record["name"]]]
    else:
        mesh = module_assets[Path(record["source_fbx"]).stem]
    loc = record["location_mm"]
    rot = record["rotation_deg"]
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*(value / 10.0 for value in loc)),
        unreal.Rotator(pitch=rot[1], yaw=rot[2], roll=rot[0]))
    actor.set_actor_label(record["name"] + "_UEv005")
    tag(actor, f"LB.PressTrain.Stage.{record['stage']}", f"LB.PressTrain.Role.{record['role']}",
        "LB.PressTrain.ProcessDirection.PositiveY")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(*record["scale"]))
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    for index, slot in enumerate(slot_names(mesh)):
        actor.static_mesh_component.set_material(index, materials[role_for(slot)])
    placed.append(actor)

cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")


def cube_actor(label, location, dimensions, collision, hidden, *extra):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    tag(actor, *extra)
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(*(value / 100.0 for value in dimensions)))
    actor.static_mesh_component.set_material(0, materials["Foundation"])
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll" if collision else "NoCollision"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", collision)
    actor.set_actor_hidden_in_game(hidden)
    return actor


floor = cube_actor("CA_MW_PTA_IsolationFloor_v005", (0, 2250, -20), (1800, 6500, 40), True, False,
                   "LB.Validation.Environment", "LB.Collision.WalkableFloor")
stage_specs = [("S01", 0, 650, 700, 650), ("S02", 750, 700, 700, 1100), ("S03", 1500, 650, 700, 950),
               ("S04", 2250, 650, 700, 900), ("S05", 3000, 650, 700, 850), ("S06", 3750, 650, 700, 900),
               ("S07", 4500, 900, 700, 700)]
proxies = [cube_actor(f"CA_MW_PTA_{stage}_SimpleCollision_v005", (0, y, h / 2), (w, length, h), True, True,
                      "LB.Collision.SimpleProxy", f"LB.PressTrain.Stage.{stage}")
           for stage, y, w, length, h in stage_specs]
nav = actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume, unreal.Vector(0, 2250, 350), unreal.Rotator())
nav.set_actor_label("CA_MW_PTA_IsolationNavBounds_v005")
tag(nav, "LB.Navigation.IsolationEvidenceOnly")
nav.set_actor_scale3d(unreal.Vector(18, 65, 7))

sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.set_actor_label("CA_MW_PTA_IsolationSky_v005"); tag(sky, "LB.Validation.Lighting")
sky.get_editor_property("light_component").set_editor_property("intensity", 0.55)
key = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(), unreal.Rotator(pitch=-48, yaw=-32))
key.set_actor_label("CA_MW_PTA_IsolationKey_v005"); tag(key, "LB.Validation.Lighting")
key.get_editor_property("directional_light_component").set_editor_property("intensity", 4.0)
for index, y in enumerate((-250, 750, 1750, 2750, 3750, 4750), 1):
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(900, y, 1450), unreal.Rotator(pitch=-42, yaw=180))
    light.set_actor_label(f"CA_MW_PTA_IsolationFill_{index:02d}_v005"); tag(light, "LB.Validation.Lighting")
    comp = light.get_editor_property("rect_light_component")
    comp.set_editor_properties({"intensity": 3200.0, "source_width": 900.0, "source_height": 220.0})
    comp.set_light_color(unreal.LinearColor(0.72, 0.82, 0.78, 1.0))
post = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
post.set_actor_label("CA_MW_PTA_IsolationExposure_v005"); tag(post, "LB.Validation.Lighting")
post.set_editor_property("unbound", True)
pps = post.get_editor_property("settings")
pps.set_editor_properties({"override_auto_exposure_method": True, "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
                           "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
                           "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
                           "override_auto_exposure_bias": True, "auto_exposure_bias": 0.15})
post.set_editor_property("settings", pps)


def camera(label, location, target, fov, semantic, roll=0):
    rotation = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*location), unreal.Vector(*target)); rotation.roll = roll
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), rotation)
    actor.set_actor_label(label); tag(actor, "LB.Camera.Fixed", semantic)
    actor.camera_component.set_editor_property("field_of_view", fov)
    return actor


cameras = [camera("CA_MW_PTA_CAM_Hero_v005", (-2900, -2500, 1900), (0, 2250, 390), 48, "LB.Camera.PressTrainA.Hero"),
           camera("CA_MW_PTA_CAM_OperatorSide_v005", (2350, 2250, 820), (0, 2250, 380), 50, "LB.Camera.PressTrainA.OperatorSide"),
           camera("CA_MW_PTA_CAM_Overhead_v005", (0, 2250, 6600), (0, 2250, 0), 46, "LB.Camera.PressTrainA.Overhead", 90),
           camera("CA_MW_PTA_CAM_S01_v005", (1450, -1150, 720), (0, -180, 250), 46, "LB.Camera.PressTrainA.S01"),
           camera("CA_MW_PTA_CAM_S07_v005", (1450, 5750, 720), (0, 4660, 250), 46, "LB.Camera.PressTrainA.S07"),
           camera("CA_MW_PTA_CAM_LoadedCart_v005", (-1650, 1700, 600), (-360, 2200, 155), 48, "LB.Camera.PressTrainA.LoadedCart"),
           camera("CA_MW_PTA_CAM_Mechanics_v005", (1650, 2550, 900), (330, 2550, 260), 50, "LB.Camera.PressTrainA.Mechanics")]

identity = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(-780, -480, 120), unreal.Rotator(yaw=90))
identity.set_actor_label("CA_MW_PTA_IsolationAuthorityText_v005"); tag(identity, "LB.Validation.NonProductionLabel")
identity.text_render.set_text("CAIRNWELL AUTOMOTIVE | MOORCROSS WORKS\nPRESS TRAIN A | ISOLATED STUDY | TBC_NOT_INVENTED")
identity.text_render.set_world_size(30); identity.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

if not levels.save_current_level():
    raise RuntimeError("Map save failed")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

minimum = unreal.Vector(1e12, 1e12, 1e12); maximum = unreal.Vector(-1e12, -1e12, -1e12)
for actor in placed:
    origin, extent = actor.get_actor_bounds(False, False)
    minimum.x = min(minimum.x, origin.x - extent.x); minimum.y = min(minimum.y, origin.y - extent.y); minimum.z = min(minimum.z, origin.z - extent.z)
    maximum.x = max(maximum.x, origin.x + extent.x); maximum.y = max(maximum.y, origin.y + extent.y); maximum.z = max(maximum.z, origin.z + extent.z)
bounds_mm = [round((maximum.x-minimum.x)*10,3), round((maximum.y-minimum.y)*10,3), round((maximum.z-minimum.z)*10,3)]
report = {"generated_utc": datetime.now(timezone.utc).isoformat(),
          "status": "PASS__EXACT_MANIFEST_RECONSTRUCTION_V005__STATIC_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
          "map": MAP, "asset_destination": DEST, "world_placement": "TBC_NOT_INVENTED",
          "placed_manifest_actor_count": len(placed), "aggregate_actor_bounds_mm": bounds_mm,
          "module_asset_count": len(module_assets), "deduplicated_authored_asset_count": len(authored_assets),
          "material_asset_count": len(materials), "material_assignment_count": len(material_rows),
          "nanite_enabled_fixed_assets": nanite_assets, "nanite_failures": nanite_failures,
          "lod_policy": "LOD0 only in first study; Nanite enabled only on large fixed presentation families; moving-candidate families remain non-Nanite",
          "collision": {"strategy": "visual meshes NoCollision; seven hidden simple stage blockers plus walkable isolation floor",
                        "proxy_count": len(proxies)},
          "navigation": {"bounds_actor": nav.get_actor_label(), "runtime_path_authority": False,
                         "reason": "No production/gameplay placement or authoritative route exists"},
          "fixed_camera_count": len(cameras), "runtime_machine_authority": False, "animation_implemented": False,
          "protected_assets_modified": [], "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
