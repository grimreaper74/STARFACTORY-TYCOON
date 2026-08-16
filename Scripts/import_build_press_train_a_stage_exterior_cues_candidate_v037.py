"""Import four reusable stage cues and integrate them into isolated Train A v037."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/StageExteriorCues_v001"
MANIFEST = json.loads((SOURCE_DIR / "PRESS_TRAIN_STAGE_EXTERIOR_CUES_MANIFEST_v001.json").read_text(encoding="utf-8"))
AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_stage_exterior_cues_source_audit_v001.json").read_text(encoding="utf-8"))
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAInheritedFrameMaterialCandidate_v036"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainAStageExteriorCuesCandidate_v037"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/StageExteriorCues_v001"
MAT25 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025"
MAT14 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v014"
PR009_MAT = "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_stage_exterior_cues_build_v037.json"
if not str(AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("stage exterior cue source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("stage exterior cue source invented world placement")

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
        "filename": str(SOURCE_DIR / row["file"]), "destination_path": DEST,
        "destination_name": row["asset"], "automated": True,
        "replace_existing": True, "replace_existing_settings": True, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": False,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "generate_lightmap_u_vs": True, "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
for row in MANIFEST["assets"]:
    mesh = library.load_asset(f"{DEST}/{row['asset']}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"stage exterior cue import missing: {row['asset']}")
    meshes[row["asset"]] = mesh

material_paths = {
    "CA_MW_FoundryCharcoal": f"{MAT25}/M_CA_MW_PT_FoundryCharcoalLayered_v025",
    "CA_MW_CairnwellGreen": "/Game/LineBoss/Candidates/PressTrains/Shared/EnclosedFacadeMaterials_v035/M_CA_MW_PT_EnclosureGreenLayered_v035",
    "CA_MW_SafetyYellow": f"{MAT25}/M_CA_MW_PT_SafetyYellowLayered_v025",
    "CA_MW_ServiceGrey": "/Game/LineBoss/Candidates/PressTrains/Shared/EnclosedFacadeMaterials_v035/M_CA_MW_PT_EnclosureGreyLayered_v035",
    "CA_MW_WorkedSteel": f"{MAT25}/M_CA_MW_PT_WorkedSteelLayered_v025",
    "CA_MW_InspectionGlass": f"{MAT14}/M_CA_MW_PT_InspectionGlass_v014",
    "CA_MW_TrainAAccent": f"{MAT25}/M_CA_MW_PT_TrainAAccentLayered_v025",
    "CA_MW_StatusGreen": f"{PR009_MAT}/M_CA_MW_PR009_HMIScreenOnline_v085",
    "CA_MW_StatusAmber": f"{PR009_MAT}/M_CA_MW_PR009_AmberSafetyActive_v085",
}
materials = {name: library.load_asset(path) for name, path in material_paths.items()}
missing_materials = [name for name, material in materials.items() if material is None]
if missing_materials:
    raise RuntimeError(f"missing stage exterior cue materials: {missing_materials}")
rows = {row["asset"]: row for row in MANIFEST["assets"]}

if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v037 from v036: {TARGET_MAP}")


def spawn_cue(stage, asset_name, y_cm):
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(-360.0, y_cm, 0.0), unreal.Rotator(yaw=180.0))
    actor.set_actor_label(f"CA_MW_PTA_{stage}_StageExteriorCue_v037")
    actor.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated", "LB.PressTrain.Fixed.StageExteriorCue",
        f"LB.PressTrain.StageExteriorCue.{stage}", "LB.PressTrain.OperatorSide.ProcessEvidence",
        "LB.Asset.Candidate.v037", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    component = actor.static_mesh_component
    component.set_static_mesh(meshes[asset_name])
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    for index, slot in enumerate(rows[asset_name]["material_slots"]):
        component.set_material(index, materials[slot])
    return actor.get_actor_label()


specs = [
    ("S03", "SM_CA_MW_PT_S03SecondaryFormExteriorCue_v001", 1500.0),
    ("S04", "SM_CA_MW_PT_S04TrimScrapExteriorCue_v001", 2250.0),
    ("S05", "SM_CA_MW_PT_S05PierceSlugExteriorCue_v001", 3000.0),
    ("S06", "SM_CA_MW_PT_S06RestrikeQualityExteriorCue_v001", 3750.0),
]
placed = [spawn_cue(*spec) for spec in specs]

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v037" not in tags:
            tags.append("LB.Asset.Candidate.v037")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(placed) != 4 or scope_count != 173:
    failures.append(f"cardinality mismatch cues={len(placed)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v037 stage-exterior-cue candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-stage-exterior-cues-build-v037/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V037_S03_FORM_S04_TRIM_S05_PIERCE_S06_RESTRIKE_DISTINCT_EXTERIOR_PROCESS_CUES__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V037_STAGE_EXTERIOR_CUE_BUILD__NOT_PROMOTED"),
    "source_map": SOURCE_MAP, "map": TARGET_MAP, "asset_root": DEST,
    "placed_cues": placed, "scope_actor_count": scope_count,
    "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
    "accepted_pr010_map_changed": False, "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
