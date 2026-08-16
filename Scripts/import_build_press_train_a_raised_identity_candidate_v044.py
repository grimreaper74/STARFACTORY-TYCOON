"""Import raised mesh stage plates into an isolated v044 child of retained v038."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/RaisedIdentityPlates_v001"
MANIFEST = json.loads((SOURCE_DIR / "PRESS_TRAIN_RAISED_IDENTITY_PLATES_MANIFEST_v001.json").read_text(encoding="utf-8"))
AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_raised_identity_plates_source_audit_v001.json").read_text(encoding="utf-8"))
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAStageCueFacingCandidate_v038"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainARaisedIdentityCandidate_v044"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/RaisedIdentityPlates_v001"
MAT25 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_raised_identity_build_v044.json"
if not str(AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("raised identity source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("raised identity source invented world placement")
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
        raise RuntimeError(f"raised identity import missing: {row['asset']}")
    meshes[row["stage_code"]] = mesh

material_paths = {
    "CA_MW_TrainAccent": f"{MAT25}/M_CA_MW_PT_TrainAAccentLayered_v025",
    "CA_MW_LabelWhite": f"{MAT25}/M_CA_MW_PT_LabelWhiteLayered_v025",
    "CA_MW_WorkedSteel": f"{MAT25}/M_CA_MW_PT_WorkedSteelLayered_v025",
}
materials = {name: library.load_asset(path) for name, path in material_paths.items()}
missing_materials = [name for name, material in materials.items() if material is None]
if missing_materials:
    raise RuntimeError(f"raised identity materials missing: {missing_materials}")
rows = {row["stage_code"]: row for row in MANIFEST["assets"]}
if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v044 from v038: {TARGET_MAP}")

removed = []
for actor in list(actors_api.get_all_level_actors()):
    if "LB.PressTrain.EnclosedFacade.IntegratedIdentity" in {str(tag) for tag in actor.tags}:
        removed.append(actor.get_actor_label())
        actors_api.destroy_actor(actor)

specs = [
    ("S01", 0.0, 520.0), ("S02", 750.0, 825.0), ("S03", 1500.0, 665.0),
    ("S04", 2250.0, 665.0), ("S05", 3000.0, 665.0),
    ("S06", 3750.0, 665.0), ("S07", 4500.0, 565.0),
]
placed = []
for stage, y_cm, z_cm in specs:
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(-435.0, y_cm, z_cm), unreal.Rotator())
    actor.set_actor_label(f"CA_MW_PTA_{stage}_RaisedIdentityPlate_v044")
    actor.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated", "LB.PressTrain.Fixed.RaisedIdentityPlate",
        f"LB.PressTrain.RaisedIdentityPlate.{stage}",
        "LB.Brand.CairnwellAutomotive", "LB.Site.MoorcrossWorks",
        "LB.Asset.Candidate.v044", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    component = actor.static_mesh_component
    component.set_static_mesh(meshes[stage])
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    for index, slot in enumerate(rows[stage]["material_slots"]):
        component.set_material(index, materials[slot])
    placed.append(actor.get_actor_label())

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v044" not in tags:
            tags.append("LB.Asset.Candidate.v044")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(removed) != 7 or len(placed) != 7 or scope_count != 173:
    failures.append(f"cardinality mismatch removed={len(removed)} placed={len(placed)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v044 raised-identity candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-raised-identity-build-v044/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V044_SEVEN_REAL_GEOMETRY_STAGE_IDENTITY_PLATES_INTEGRATED__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V044_RAISED_IDENTITY_BUILD__NOT_PROMOTED"),
    "source_map": SOURCE_MAP, "map": TARGET_MAP, "asset_root": DEST,
    "removed_text_render_identities": removed, "placed_raised_plates": placed,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
