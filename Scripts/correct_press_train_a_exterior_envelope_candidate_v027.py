"""Create v027 after correcting the S07 exterior-detail source envelope."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/ExteriorDetail_v002"
MANIFEST = json.loads((SOURCE_DIR / "PRESS_TRAIN_EXTERIOR_DETAIL_MANIFEST_v002.json").read_text(encoding="utf-8"))
AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_exterior_detail_source_audit_v002.json").read_text(encoding="utf-8"))
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAExteriorDetailCandidate_v026"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainAExteriorEnvelopeCandidate_v027"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/ExteriorDetail_v002"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_exterior_envelope_v027.json"
if not str(AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("corrected exterior-detail source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("exterior-detail source invented world placement")

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET_MAP):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET_MAP}")

reimported = []
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
    reimported.append(row["asset"])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v027 from v026: {TARGET_MAP}")

scope_count = 0
exterior_count = 0
for actor in actors_api.get_all_level_actors():
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        scope_count += 1
        if "LB.PressTrain.Fixed.ExteriorDetail" in actor_tags:
            exterior_count += 1
        if "LB.Asset.Candidate.v027" not in actor_tags:
            actor_tags.append("LB.Asset.Candidate.v027")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])

failures = []
if len(reimported) != 5:
    failures.append(f"expected five corrected reimports, found {len(reimported)}")
if scope_count != 147 or exterior_count != 14:
    failures.append(f"candidate cardinality mismatch scope={scope_count} exterior={exterior_count}")
if not levels.save_current_level():
    failures.append("could not save v027 corrected exterior-envelope candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-exterior-envelope-v027/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V027_CORRECTED_S07_STILLAGE_WITHIN_SOURCE_AND_TRAIN_ENVELOPE__EXACT_STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V027_EXTERIOR_ENVELOPE__NOT_PROMOTED"),
    "source_map": SOURCE_MAP, "map": TARGET_MAP, "reimported_assets": reimported,
    "scope_actor_count": scope_count, "exterior_actor_count": exterior_count,
    "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
    "accepted_pr010_map_changed": False, "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
