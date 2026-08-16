"""Import shared presentation source v002 and create isolated Train A v004.

v004 keeps the verified v002/v003 seven-stage transforms and substitutes only the
dimensioned open-bay shared meshes, recalibrated evidence lighting and trace tags.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/Presentation_v002"
MANIFEST_PATH = SOURCE_DIR / "PRESS_TRAIN_SHARED_KIT_MANIFEST_v002.json"
SOURCE_AUDIT_PATH = ROOT / "Saved/Audits/PressTrains/press_train_shared_source_audit_v002.json"
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAVisualCandidate_v003"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainAOpenBayCandidate_v004"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/Presentation_v002"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_open_bay_build_v004.json"

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
source_audit = json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))
if not str(source_audit.get("status", "")).startswith("PASS"):
    raise RuntimeError("shared presentation source v002 has not passed its source gate")
if manifest.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("shared presentation source invented a world placement")

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(TARGET_MAP):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET_MAP}")


def import_static(row):
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
    if not task.get_editor_property("imported_object_paths"):
        raise RuntimeError(f"FBX import produced no asset: {row['asset']}")


for row in manifest["assets"]:
    import_static(row)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v004 from preserved v003: {TARGET_MAP}")

material_paths = {
    "CA_MW_CairnwellGreen": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v085",
    "CA_MW_SafetyYellow": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v085",
    "CA_MW_FoundryCharcoal": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v085",
    "CA_MW_ServiceGrey": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredServiceGrey_v085",
    "CA_MW_WorkedSteel": "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_MachinedSteel_v085",
    "CA_MW_DarkRubber": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_Rubber_v086",
    "CA_MW_InspectionGlass": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_SensorGlass_v086",
    "CA_MW_TrainAAccent": "/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_DriveBlue_v086",
}
materials = {name: library.load_asset(path) for name, path in material_paths.items()}
missing_materials = [name for name, value in materials.items() if value is None]
if missing_materials:
    raise RuntimeError(f"missing shared Press Shop materials: {missing_materials}")
rows = {row["asset"]: row for row in manifest["assets"]}


def add_tag(actor, value):
    values = [str(tag) for tag in actor.tags]
    if value not in values:
        values.append(value)
        actor.set_editor_property("tags", [unreal.Name(tag) for tag in values])


presentation = []
replaced = []
transform_drift = []
for actor in actors_api.get_all_level_actors():
    actor_tags = {str(tag) for tag in actor.tags}
    if not isinstance(actor, unreal.StaticMeshActor) or "LB.PressTrain.TrainA.Isolated" not in actor_tags or "LB.Validation.Environment" in actor_tags:
        continue
    presentation.append(actor)
    before = actor.get_actor_transform()
    old_mesh = actor.static_mesh_component.get_editor_property("static_mesh")
    if old_mesh is None:
        raise RuntimeError(f"presentation actor has no mesh: {actor.get_actor_label()}")
    new_name = old_mesh.get_name().replace("_v001", "_v002")
    if new_name not in rows:
        raise RuntimeError(f"no v002 source mapping for {old_mesh.get_name()} on {actor.get_actor_label()}")
    new_mesh = library.load_asset(f"{DEST}/{new_name}")
    if not isinstance(new_mesh, unreal.StaticMesh):
        raise RuntimeError(f"missing imported v002 mesh: {new_name}")
    actor.static_mesh_component.set_static_mesh(new_mesh)
    for index, slot in enumerate(rows[new_name]["material_slots"]):
        actor.static_mesh_component.set_material(index, materials[slot])
    add_tag(actor, "LB.Asset.Candidate.v004")
    after = actor.get_actor_transform()
    if before.translation != after.translation or before.rotation != after.rotation or before.scale3d != after.scale3d:
        transform_drift.append(actor.get_actor_label())
    replaced.append({"actor": actor.get_actor_label(), "from": old_mesh.get_name(), "to": new_name})

# v003 was intentionally conservative and too dark.  This balanced evidence rig is
# still far below v002's clipped 1800-unit fills but exposes the new process bays.
sky = next(actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == "CA_MW_PTA_IsolatedSky")
sky.get_editor_property("light_component").set_editor_property("intensity", 0.30)
directional = next(actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == "CA_MW_PTA_IsolatedKey")
directional.get_editor_property("directional_light_component").set_editor_property("intensity", 0.78)
rect_count = 0
for actor in actors_api.get_all_level_actors():
    if actor.get_actor_label().startswith("CA_MW_PTA_IsolatedFill_"):
        actor.get_editor_property("rect_light_component").set_editor_property("intensity", 520.0)
        rect_count += 1

for actor in actors_api.get_all_level_actors():
    actor_tags = {str(tag) for tag in actor.tags}
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        add_tag(actor, "LB.Asset.Candidate.v004")

failures = []
if len(manifest["assets"]) != 16:
    failures.append(f"expected 16 imported modules, found {len(manifest['assets'])}")
if len(presentation) != 37 or len(replaced) != 37:
    failures.append(f"expected 37 presentation replacements, found actors={len(presentation)} replacements={len(replaced)}")
if transform_drift:
    failures.append(f"verified presentation transforms drifted: {transform_drift}")
if rect_count != 7:
    failures.append(f"expected seven recalibrated RectLights, found {rect_count}")
if not levels.save_current_level():
    failures.append("could not save v004 open-bay candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

report = {
    "$schema": "cairnwell/audit/press-train-a-open-bay-build-v004/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V004_SIXTEEN_SOURCE_MODULES_THIRTY_SEVEN_OPEN_BAY_REPLACEMENTS_TRANSFORMS_PRESERVED__STATIC_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V004_OPEN_BAY_BUILD__NOT_PROMOTED",
    "source_map": SOURCE_MAP,
    "map": TARGET_MAP,
    "asset_destination": DEST,
    "imported_asset_count": len(manifest["assets"]),
    "presentation_replacement_count": len(replaced),
    "presentation_transform_drift": transform_drift,
    "replacements": replaced,
    "sky_intensity": 0.30,
    "directional_intensity": 0.78,
    "rect_light_intensity": 520.0,
    "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False,
    "accepted_pr010_map_changed": False,
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({key: report[key] for key in ("status", "imported_asset_count", "presentation_replacement_count", "presentation_transform_drift", "world_placement", "failures")}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
