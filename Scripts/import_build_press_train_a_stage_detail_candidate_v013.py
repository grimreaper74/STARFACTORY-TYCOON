"""Import the audited stage-detail kit and build isolated Train A v013."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/StageDetail_v001"
MANIFEST = json.loads((SOURCE_DIR / "PRESS_TRAIN_STAGE_DETAIL_MANIFEST_v001.json").read_text(encoding="utf-8"))
AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_stage_detail_source_audit_v001.json").read_text(encoding="utf-8"))
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAManagementCameraCandidate_v012"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainAStageDetailCandidate_v013"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/StageDetail_v001"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_stage_detail_build_v013.json"
if not str(AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("stage-detail source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("stage-detail source invented world placement")

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET_MAP):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET_MAP}")

meshes = {}
for row in MANIFEST["assets"]:
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
for row in MANIFEST["assets"]:
    mesh = library.load_asset(f"{DEST}/{row['asset']}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"stage-detail Unreal import missing: {row['asset']}")
    meshes[row["asset"]] = mesh

if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v013 from preserved v012: {TARGET_MAP}")

material_root = "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials"
material_paths = {
    "CA_MW_CairnwellGreen": f"{material_root}/M_CA_MW_PR009_LayeredCairnwellGreen_v085",
    "CA_MW_SafetyYellow": f"{material_root}/M_CA_MW_PR009_LayeredSafetyYellow_v085",
    "CA_MW_FoundryCharcoal": f"{material_root}/M_CA_MW_PR009_LayeredFoundryCharcoal_v085",
    "CA_MW_ServiceGrey": f"{material_root}/M_CA_MW_PR009_LayeredServiceGrey_v085",
    "CA_MW_WorkedSteel": f"{material_root}/M_CA_MW_PR009_MachinedSteel_v085",
    "CA_MW_TrainAAccent": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_DriveBlue_v086",
    "CA_MW_HMIScreen": f"{material_root}/M_CA_MW_PR009_HMIScreenOnline_v085",
    "CA_MW_StateGreen": f"{material_root}/M_CA_MW_PR009_HMIScreenOnline_v085",
    "CA_MW_EStopRed": f"{material_root}/M_CA_MW_PR009_EStopRed_v085",
}
materials = {name: library.load_asset(path) for name, path in material_paths.items()}
missing_materials = [name for name, value in materials.items() if value is None]
if missing_materials:
    raise RuntimeError(f"missing material mappings: {missing_materials}")
rows = {row["asset"]: row for row in MANIFEST["assets"]}


def place(asset, label, location_cm, detail_tag):
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location_cm), unreal.Rotator(yaw=180.0))
    actor.set_actor_label(label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.SharedKit",
        "LB.PressTrain.TrainA.Isolated",
        "LB.PressTrain.Fixed.StageDetail",
        detail_tag,
        "LB.Asset.Candidate.v013",
        "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    component = actor.static_mesh_component
    component.set_static_mesh(meshes[asset])
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    for index, slot in enumerate(rows[asset]["material_slots"]):
        component.set_material(index, materials[slot])
    return actor.get_actor_label()


placed = []
stage_centres = [(f"S{index:02d}", (index - 1) * 750.0) for index in range(1, 8)]
for stage, y_cm in stage_centres:
    placed.append(place(
        "SM_CA_MW_PT_StageServicePack_v001",
        f"CA_MW_PTA_{stage}_StageServicePack",
        (0.0, y_cm, 35.0),
        f"LB.PressTrain.Detail.{stage}.RemoteService",
    ))
placed.append(place(
    "SM_CA_MW_PT_S01DestackDetail_v001", "CA_MW_PTA_S01_DestackDetail",
    (0.0, 0.0, 35.0), "LB.PressTrain.Detail.S01.Destack",
))
placed.append(place(
    "SM_CA_MW_PT_S07UnloadInspectDetail_v001", "CA_MW_PTA_S07_UnloadInspectDetail",
    (0.0, 4500.0, 35.0), "LB.PressTrain.Detail.S07.UnloadInspect",
))
for stage, y_cm in (("S04", 2250.0), ("S05", 3000.0)):
    placed.append(place(
        "SM_CA_MW_PT_MidTrainProcessService_v001",
        f"CA_MW_PTA_{stage}_ProcessServiceDetail",
        (0.0, y_cm, 35.0),
        f"LB.PressTrain.Detail.{stage}.ProcessService",
    ))

# Mark every inherited scoped actor as part of the isolated v013 candidate while
# retaining the complete history of earlier candidate tags.
scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v013" not in tags:
            tags.append("LB.Asset.Candidate.v013")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(placed) != 11:
    failures.append(f"expected 11 stage-detail actors, found {len(placed)}")
if not levels.save_current_level():
    failures.append("could not save v013 stage-detail candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-stage-detail-build-v013/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V013_SEVEN_REMOTE_SERVICE_PACKS_DISTINCT_S01_S07_AND_MID_TRAIN_PROCESS_DETAIL__STATIC_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V013_STAGE_DETAIL_BUILD__NOT_PROMOTED",
    "source_map": SOURCE_MAP,
    "map": TARGET_MAP,
    "asset_root": DEST,
    "placed_actor_count": len(placed),
    "placed_actors": placed,
    "scoped_actor_count_after_build": scope_count,
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
