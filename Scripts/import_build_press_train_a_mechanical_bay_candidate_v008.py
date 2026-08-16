"""Import and place the reusable mechanical-bay dress in Train A v008."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/MechanicalBay_v001"
MANIFEST = json.loads((SOURCE_DIR / "PRESS_TRAIN_MECHANICAL_BAY_MANIFEST_v001.json").read_text(encoding="utf-8"))
AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_mechanical_bay_source_audit_v001.json").read_text(encoding="utf-8"))
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainABalancedReadabilityCandidate_v007"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainAMechanicalBayCandidate_v008"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/MechanicalBay_v001"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_mechanical_bay_build_v008.json"
if not str(AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("mechanical-bay source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("mechanical-bay source invented world placement")

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET_MAP):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET_MAP}")

row = MANIFEST["assets"][0]
task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(SOURCE_DIR / row["file"]),
    "destination_path": DEST,
    "destination_name": row["asset"],
    "automated": True,
    "replace_existing": True,
    "replace_existing_settings": True,
    "save": True,
})
options = unreal.FbxImportUI()
options.set_editor_properties({
    "import_mesh": True,
    "import_as_skeletal": False,
    "import_materials": False,
    "import_textures": False,
    "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
})
data = options.get_editor_property("static_mesh_import_data")
data.set_editor_properties({
    "combine_meshes": True,
    "convert_scene": True,
    "convert_scene_unit": True,
    "generate_lightmap_u_vs": True,
    "auto_generate_collision": False,
    "remove_degenerates": True,
})
task.set_editor_property("options", options)
asset_tools.import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh = library.load_asset(f"{DEST}/{row['asset']}")
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("mechanical-bay Unreal import missing")

if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v008 from preserved v007: {TARGET_MAP}")

material_paths = {
    "CA_MW_CairnwellGreen": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v085",
    "CA_MW_SafetyYellow": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v085",
    "CA_MW_FoundryCharcoal": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v085",
    "CA_MW_ServiceGrey": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredServiceGrey_v085",
    "CA_MW_WorkedSteel": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_MachinedSteel_v085",
    "CA_MW_TrainAAccent": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_DriveBlue_v086",
}
materials = {name: library.load_asset(path) for name, path in material_paths.items()}
if any(value is None for value in materials.values()):
    raise RuntimeError("one or more mechanical-bay material mappings are missing")

placed = []
for stage, y_cm in (("S02", 750.0), ("S03", 1500.0), ("S04", 2250.0), ("S05", 3000.0), ("S06", 3750.0)):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0.0, y_cm, 35.0), unreal.Rotator(yaw=180.0))
    actor.set_actor_label(f"CA_MW_PTA_{stage}_MechanicalBayDress")
    actor.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.SharedKit",
        "LB.PressTrain.TrainA.Isolated",
        "LB.PressTrain.Fixed.MechanicalBay",
        f"LB.PressTrain.Fixed.MechanicalBay.{stage}",
        "LB.Asset.Candidate.v008",
        "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    for index, slot in enumerate(row["material_slots"]):
        actor.static_mesh_component.set_material(index, materials[slot])
    placed.append(actor.get_actor_label())

# v007 proved that only restrained internal task lighting is required once the
# visible mechanical geometry exists; avoid lighting the die surfaces to white.
bay_light_count = 0
for actor in actors_api.get_all_level_actors():
    if actor.get_actor_label().startswith("CA_MW_PTA_ProcessBayLight_"):
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 24.0)
        bay_light_count += 1
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags and "LB.Asset.Candidate.v008" not in tags:
        tags.append("LB.Asset.Candidate.v008")
        actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(placed) != 5:
    failures.append(f"expected five mechanical-bay instances, found {len(placed)}")
if bay_light_count != 7:
    failures.append(f"expected seven retained process-bay lights, found {bay_light_count}")
if not levels.save_current_level():
    failures.append("could not save v008 mechanical-bay candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

report = {
    "$schema": "cairnwell/audit/press-train-a-mechanical-bay-build-v008/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V008_FIVE_REUSABLE_MECHANICAL_BAYS_VISIBLE_TIE_RODS_CYLINDERS_DRIVES_UTILITIES__STATIC_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V008_MECHANICAL_BAY_BUILD__NOT_PROMOTED",
    "source_map": SOURCE_MAP,
    "map": TARGET_MAP,
    "asset": f"{DEST}/{row['asset']}",
    "placed_mechanical_bay_count": len(placed),
    "placed_actors": placed,
    "process_bay_light_intensity": 24.0,
    "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False,
    "accepted_pr010_map_changed": False,
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
