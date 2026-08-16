"""Import crown/endpoint v002 and replace the seven v050 presentation actors in place."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/CrownEndpointPresentation_v002"
MANIFEST = json.loads((SOURCE_DIR / "PRESS_TRAIN_CROWN_ENDPOINT_PRESENTATION_MANIFEST_v002.json").read_text(encoding="utf-8"))
AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_crown_endpoint_presentation_source_audit_v002.json").read_text(encoding="utf-8"))
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainACrownEndpointCalibrationCandidate_v050"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainACrownEndpointRefinementCandidate_v051"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/CrownEndpointPresentation_v002"
MAT25 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_crown_endpoint_refinement_v051.json"
if not str(AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("crown/endpoint v002 source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("crown/endpoint v002 source invented world placement")

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
        raise RuntimeError(f"crown/endpoint v002 import missing: {row['asset']}")
    meshes[row["asset"]] = mesh

if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v051 from v050: {TARGET_MAP}")

material_paths = {
    "CA_MW_FoundryCharcoal": f"{MAT25}/M_CA_MW_PT_FoundryCharcoalLayered_v025",
    "CA_MW_CairnwellGreen": f"{MAT25}/M_CA_MW_PT_CairnwellGreenLayered_v025",
    "CA_MW_SafetyYellow": f"{MAT25}/M_CA_MW_PT_SafetyYellowLayered_v025",
    "CA_MW_ServiceGrey": f"{MAT25}/M_CA_MW_PT_ServiceGreyLayered_v025",
    "CA_MW_WorkedSteel": f"{MAT25}/M_CA_MW_PT_WorkedSteelLayered_v025",
    "CA_MW_DarkRubber": f"{MAT25}/M_CA_MW_PT_DarkRubberLayered_v025",
    "CA_MW_TrainAAccent": f"{MAT25}/M_CA_MW_PT_TrainAAccentLayered_v025",
    "CA_MW_InspectionCyan": f"{MAT25}/M_CA_MW_PT_StateBlueRestrained_v025",
}
materials = {name: library.load_asset(path) for name, path in material_paths.items()}
missing_materials = [name for name, material in materials.items() if material is None]
if missing_materials:
    raise RuntimeError(f"missing crown/endpoint v002 material mappings: {missing_materials}")
rows = {row["asset"]: row for row in MANIFEST["assets"]}

replaced = []
scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.Fixed.CrownEndpointPresentation" in tags:
        if any(".HeavyCrown" in tag for tag in tags):
            asset_name = "SM_CA_MW_PT_HeavyCrownMass_v002"
        elif "LB.PressTrain.CrownEndpoint.S01.VisibleBlankFeed" in tags:
            asset_name = "SM_CA_MW_PT_S01VisibleBlankFeed_v002"
        elif "LB.PressTrain.CrownEndpoint.S07.VisiblePanelDischarge" in tags:
            asset_name = "SM_CA_MW_PT_S07VisiblePanelDischarge_v002"
        else:
            raise RuntimeError(f"unrecognized crown/endpoint semantic: {actor.get_actor_label()} {tags}")
        component = actor.static_mesh_component
        component.set_static_mesh(meshes[asset_name])
        for slot_index, slot in enumerate(rows[asset_name]["material_slots"]):
            material = materials[slot]
            if asset_name == "SM_CA_MW_PT_HeavyCrownMass_v002" and slot == "CA_MW_ServiceGrey":
                material = materials["CA_MW_FoundryCharcoal"]
            component.set_material(slot_index, material)
        replaced.append({"actor": actor.get_actor_label(), "asset": asset_name})
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v051" not in tags:
            tags.append("LB.Asset.Candidate.v051")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(replaced) != 7:
    failures.append(f"expected seven in-place replacements, found {len(replaced)}")
if scope_count != 180:
    failures.append(f"expected 180 scoped actors, found {scope_count}")
if not levels.save_current_level():
    failures.append("could not save v051 crown/endpoint refinement candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-crown-endpoint-refinement-v051/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V051_RECESSED_CROWN_DRIVES_AND_PRESERVED_VISIBLE_ENDPOINT_FLOW__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V051_CROWN_ENDPOINT_REFINEMENT__NOT_PROMOTED"
    ),
    "source_map": SOURCE_MAP,
    "map": TARGET_MAP,
    "asset_root": DEST,
    "replaced": replaced,
    "scope_actor_count": scope_count,
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
