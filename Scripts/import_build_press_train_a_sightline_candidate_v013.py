"""Build fresh Train A v013 from validated v007 source and retained v012 runtime."""

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
TARGET_VERSION = os.environ.get("LB_PTA_SIGHTLINE_TARGET_VERSION", "v013")
SOURCE_VERSION = os.environ.get("LB_PTA_SIGHTLINE_SOURCE_VERSION", "v007")
SOURCE_VALIDATION_PREFIX = os.environ.get("LB_PTA_SIGHTLINE_SOURCE_PASS_PREFIX", "PASS__V007_REAL_DIE_SPACE")
STAGING_PASS_PREFIX = os.environ.get("LB_PTA_SIGHTLINE_STAGING_PASS_PREFIX", "PASS__DEDUPLICATED_V007")
SOURCE_MAP = os.environ.get("LB_PTA_SIGHTLINE_SOURCE_MAP", "/Game/LineBoss/Maps/LB_PressTrainAMotionCandidate_v012")
MAP = os.environ.get("LB_PTA_SIGHTLINE_TARGET_MAP", f"/Game/LineBoss/Maps/LB_PressTrainASightlineCandidate_{TARGET_VERSION}")
SOURCE_MAP_FILE_NAME = SOURCE_MAP.rsplit("/", 1)[-1] + ".umap"
TARGET_MAP_FILE_NAME = MAP.rsplit("/", 1)[-1] + ".umap"
SOURCE_PRESENTATION_TAG = os.environ.get("LB_PTA_SIGHTLINE_SOURCE_PRESENTATION_TAG", "LB.PressTrain.TrainA.Motion.v012")
SOURCE_MATERIAL_ROOT = os.environ.get("LB_PTA_SIGHTLINE_SOURCE_MATERIAL_ROOT", "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyMotion_v012/Materials")
SOURCE_MATERIAL_LABEL = os.environ.get("LB_PTA_SIGHTLINE_SOURCE_MATERIAL_LABEL", "Motion_v012")
TARGET_STUDY_LABEL = os.environ.get("LB_PTA_SIGHTLINE_TARGET_STUDY_LABEL", "AssemblyStudySightline")
SOURCE = ROOT / f"SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_{SOURCE_VERSION}"
MANIFEST_PATH = SOURCE / f"PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_{SOURCE_VERSION}.json"
VALIDATION_PATH = SOURCE / f"PRESS_TRAIN_A_ASSEMBLY_STUDY_VALIDATION_{SOURCE_VERSION}.json"
STAGING = ROOT / f"Saved/ImportStaging/PressTrainASightline_{TARGET_VERSION}"
STAGING_RECEIPT = ROOT / f"Saved/Audits/PressTrains/press_train_a_sightline_staging_{TARGET_VERSION}.json"
DEST = f"/Game/LineBoss/Candidates/PressTrains/TrainA/{TARGET_STUDY_LABEL}_{TARGET_VERSION}"
AUTHORED_DEST = DEST + "/Authored"
MATERIAL_DEST = DEST + "/Materials"
OUT = ROOT / f"Saved/Audits/PressTrains/press_train_a_sightline_build_{TARGET_VERSION}.json"
SOURCE_MAP_FILE = ROOT / "Content/LineBoss/Maps" / SOURCE_MAP_FILE_NAME
TARGET_MAP_FILE = ROOT / "Content/LineBoss/Maps" / TARGET_MAP_FILE_NAME

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
staging = json.loads(STAGING_RECEIPT.read_text(encoding="utf-8"))
if not validation["status"].startswith(SOURCE_VALIDATION_PREFIX):
    raise RuntimeError(f"{SOURCE_VERSION} source validation is not the expected PASS")
if not staging["status"].startswith(STAGING_PASS_PREFIX):
    raise RuntimeError(f"{TARGET_VERSION} staging is not the expected PASS")
if library.does_asset_exist(MAP) or library.does_directory_exist(DEST) or OUT.exists():
    raise RuntimeError(f"Refusing to overwrite Train A sightline {TARGET_VERSION}")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


protected_source_map_hash = sha(SOURCE_MAP_FILE)


def import_mesh(path, destination, name):
    task = unreal.AssetImportTask()
    task.set_editor_properties({"filename": str(path), "destination_path": destination,
                                "destination_name": name, "automated": True,
                                "replace_existing": False, "save": True})
    options = unreal.FbxImportUI()
    options.set_editor_properties({"import_mesh": True, "import_as_skeletal": False,
                                   "import_materials": False, "import_textures": False,
                                   "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH})
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({"combine_meshes": True, "convert_scene": True,
                                "convert_scene_unit": True, "transform_vertex_to_absolute": False,
                                "bake_pivot_in_vertex": False, "generate_lightmap_u_vs": True,
                                "auto_generate_collision": False, "remove_degenerates": True})
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])
    asset = library.load_asset(f"{destination}/{name}")
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Import failed: {path}")
    return asset


authored_assets = {row["asset"]: import_mesh(STAGING / row["file"], AUTHORED_DEST, row["asset"])
                   for row in staging["assets"]}
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

material_roles = ("Charcoal", "Foundation", "WorkedSteel", "Green", "SafetyYellow", "TrainABlue",
                  "DarkRubber", "LabelIvory", "HydraulicRed", "PneumaticBlue", "ElectricalOrange",
                  "InspectionWhite", "PanelSteel", "BlankSteel")
materials = {}
for role in material_roles:
    source_material = f"{SOURCE_MATERIAL_ROOT}/M_CA_MW_PTA_{role}_{SOURCE_MATERIAL_LABEL}"
    target_material = f"{MATERIAL_DEST}/M_CA_MW_PTA_{role}_{TARGET_STUDY_LABEL}_{TARGET_VERSION}"
    if not library.duplicate_asset(source_material, target_material):
        raise RuntimeError(f"Could not duplicate retained source material: {role}")
    materials[role] = library.load_asset(target_material)

if TARGET_VERSION != "v013":
    robot_paint_source = "/Game/LineBoss/Candidates/PressShop/PR005/ReleaseArt_v205/Materials/M_CA_MW_PR005_ServiceOrange_v205"
    robot_paint_target = f"{MATERIAL_DEST}/M_CA_MW_PTA_RobotSafetyYellow_{TARGET_STUDY_LABEL}_{TARGET_VERSION}"
    if not library.duplicate_asset(robot_paint_source, robot_paint_target):
        raise RuntimeError("Could not duplicate retained PR005 service-orange robot paint")
    materials["RobotSafetyYellow"] = library.load_asset(robot_paint_target)

glass_source = "/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v003/Materials/M_CA_MW_PR005_LaminatedInspectionGlass_v003"
glass_target = f"{MATERIAL_DEST}/M_CA_MW_PTA_InspectionGlass_{TARGET_STUDY_LABEL}_{TARGET_VERSION}"
if not library.duplicate_asset(glass_source, glass_target):
    raise RuntimeError("Could not duplicate retained translucent inspection glass")
materials["InspectionGlass"] = library.load_asset(glass_target)


def slot_names(mesh):
    return [str(row.get_editor_property("material_slot_name"))
            for row in mesh.get_editor_property("static_materials")]


def role_for(slot):
    key = slot.lower()
    tests = (("robotsafetyyellow", "RobotSafetyYellow"),
             ("robotjointorange", "RobotSafetyYellow"),
             ("inspectionglass", "InspectionGlass"), ("foundation", "Foundation"),
             ("inspectionwhite", "InspectionWhite"), ("blanksteel", "BlankSteel"),
             ("panelsteel", "PanelSteel"), ("yellow", "SafetyYellow"),
             ("traina", "TrainABlue"), ("hydraulic", "HydraulicRed"),
             ("pneumatic", "PneumaticBlue"), ("electrical", "ElectricalOrange"),
             ("rubber", "DarkRubber"), ("ivory", "LabelIvory"), ("green", "Green"))
    for token, role in tests:
        if token in key:
            return role
    if "worked" in key or "steel" in key or "metal" in key:
        return "WorkedSteel"
    return "Charcoal"


for mesh in authored_assets.values():
    for index, slot in enumerate(slot_names(mesh)):
        mesh.set_material(index, materials[role_for(slot)])
    library.save_loaded_asset(mesh, only_if_is_dirty=False)

if not levels.new_level_from_template(MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create {TARGET_VERSION} from retained source map")


def tags(actor):
    return {str(value) for value in actor.tags}


def add_tags(actor, *values):
    current = [str(value) for value in actor.tags]
    for value in values:
        if value not in current:
            current.append(value)
    actor.set_editor_property("tags", [unreal.Name(value) for value in current])


old_presentation = [actor for actor in actors_api.get_all_level_actors()
                    if isinstance(actor, unreal.StaticMeshActor)
                    and SOURCE_PRESENTATION_TAG in tags(actor)
                    and any(value.startswith("LB.PressTrain.Role.") for value in tags(actor))]
if len(old_presentation) != manifest["instance_count"]:
    raise RuntimeError(f"Expected {manifest['instance_count']} inherited presentation actors, found {len(old_presentation)}")
actors_api.destroy_actors(old_presentation)

for actor in actors_api.get_all_level_actors():
    add_tags(actor, f"LB.PressTrain.TrainA.Sightline.{TARGET_VERSION}", f"LB.Asset.Candidate.{TARGET_VERSION}",
             "LB.Asset.CandidateNotPromoted", "LB.Authority.WorldPlacement.TBCNotInvented")

authored_map = {row["object"]: row["asset"] for row in staging["instances"]}
placed = {}
role_counts = Counter()
for record in manifest["instances"]:
    mesh = authored_assets[authored_map[record["name"]]]
    loc = record["location_mm"]
    rot = record["rotation_deg"]
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor,
        unreal.Vector(*(value / 10 for value in loc)),
        unreal.Rotator(pitch=rot[1], yaw=rot[2], roll=rot[0]))
    actor.set_actor_label(record["name"] + f"_UE{TARGET_VERSION}")
    add_tags(actor, f"LB.PressTrain.TrainA.Sightline.{TARGET_VERSION}", f"LB.Asset.Candidate.{TARGET_VERSION}",
             "LB.Asset.CandidateNotPromoted", "LB.Authority.WorldPlacement.TBCNotInvented",
             "LB.Scope.IsolatedLocalOrigin", f"LB.PressTrain.Stage.{record['stage']}",
             f"LB.PressTrain.Role.{record['role']}", "LB.PressTrain.ProcessDirection.PositiveY")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(*record["scale"]))
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    for index, slot in enumerate(slot_names(mesh)):
        actor.static_mesh_component.set_material(index, materials[role_for(slot)])
    placed[record["name"]] = actor
    role_counts[record["role"]] += 1

hierarchy_edges = []
for record in manifest["instances"]:
    parent_name = record.get("runtime_parent")
    if not parent_name:
        continue
    child = placed[record["name"]]
    parent = placed.get(parent_name)
    if parent is None:
        raise RuntimeError(f"Missing runtime parent {parent_name}")
    child.attach_to_actor(parent, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    hierarchy_edges.append({"child": record["name"], "parent": parent_name})

authority_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBPressTrainAStation")
authorities = [actor for actor in actors_api.get_all_level_actors()
               if authority_class and actor.get_class() == authority_class]
if len(authorities) != 1:
    raise RuntimeError(f"Expected one native authority, found {len(authorities)}")
add_tags(authorities[0], f"LB.PressTrain.TrainA.Sightline.{TARGET_VERSION}")

live_hmis = [actor for actor in actors_api.get_all_level_actors()
             if "LB.HMI.PressTrainA.LiveState" in tags(actor)]
if len(live_hmis) != 1:
    raise RuntimeError(f"Expected one live HMI, found {len(live_hmis)}")
hmi_screen = next((record for record in manifest["instances"] if record["role"] == "runtime_hmi_screen"), None)
if hmi_screen is None:
    raise RuntimeError("Authored runtime HMI screen missing")
hmi_loc = hmi_screen["location_mm"]
hmi_rot = hmi_screen["rotation_deg"]
live_hmis[0].set_actor_location(unreal.Vector(hmi_loc[0] / 10 + 8, hmi_loc[1] / 10, hmi_loc[2] / 10), False, False)
live_hmis[0].set_actor_rotation(unreal.Rotator(pitch=hmi_rot[1], yaw=hmi_rot[2], roll=hmi_rot[0]), False)
live_hmis[0].set_actor_label(f"CA_MW_PTA_HMI_LiveState_OnAuthoredScreen_{TARGET_VERSION}")
add_tags(live_hmis[0], f"LB.HMI.PressTrainA.BoundToAuthoredScreen.{TARGET_VERSION}")

if not levels.save_current_level():
    raise RuntimeError(f"Could not save Train A {TARGET_VERSION}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
if not TARGET_MAP_FILE.exists():
    raise RuntimeError(f"{TARGET_VERSION} map missing after save")
if sha(SOURCE_MAP_FILE) != protected_source_map_hash:
    raise RuntimeError("Protected source map changed")

minimum = unreal.Vector(1e12, 1e12, 1e12)
maximum = unreal.Vector(-1e12, -1e12, -1e12)
for actor in placed.values():
    origin, extent = actor.get_actor_bounds(False, False)
    minimum.x = min(minimum.x, origin.x - extent.x); minimum.y = min(minimum.y, origin.y - extent.y); minimum.z = min(minimum.z, origin.z - extent.z)
    maximum.x = max(maximum.x, origin.x + extent.x); maximum.y = max(maximum.y, origin.y + extent.y); maximum.z = max(maximum.z, origin.z + extent.z)
bounds_mm = [round((maximum.x - minimum.x) * 10, 3),
             round((maximum.y - minimum.y) * 10, 3), round((maximum.z - minimum.z) * 10, 3)]

report = {"$schema": f"cairnwell/audit/press-train-a-sightline-build-{TARGET_VERSION}/v1",
          "generated_utc": datetime.now(timezone.utc).isoformat(),
          "status": "PASS__EXACT_V007_TRUE_THROATS_IN_V012_NATIVE_RUNTIME__TRANSLUCENT_GLAZING__AUTHORED_HMI_BINDING__RUNTIME_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
          "source_map": SOURCE_MAP, "source_map_sha256": protected_source_map_hash,
          "map": MAP, "map_sha256": sha(TARGET_MAP_FILE),
          "source_manifest_sha256": sha(MANIFEST_PATH),
          "source_validation_sha256": sha(VALIDATION_PATH),
          "removed_source_presentation_actor_count": len(old_presentation),
          "placed_manifest_actor_count": len(placed),
          "deduplicated_authored_asset_count": len(authored_assets),
          "material_asset_count": len(materials), "translucent_glass_material_count": 1,
          "aggregate_actor_bounds_mm": bounds_mm, "native_authority_count": len(authorities),
          "live_hmi_count": len(live_hmis), "hmi_bound_to_authored_screen": True,
          "runtime_hierarchy_edge_count": len(hierarchy_edges), "runtime_hierarchy_edges": hierarchy_edges,
          "motion_role_counts": {role: role_counts[role] for role in
              ("moving_press_slide", "moving_upper_die", "carried_workpiece_state",
               "unload_robot_shoulder_runtime", "state_beacon_red", "state_beacon_amber", "state_beacon_green")},
          "die_space_throat_actor_count": sum(1 for row in manifest["instances"]
                                               if row["source_fbx"] == "ASSEMBLY_STUDY_V007_DIE_SPACE_THROAT_WITH_RETAINED_UPRIGHTS"),
          "true_window_frame_actor_count": sum(1 for row in manifest["instances"]
                                                if row["source_fbx"] == "ASSEMBLY_STUDY_V006_TRUE_OPEN_BOLTED_WINDOW_FRAME"),
          "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
          "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
