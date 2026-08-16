"""Import heavy crown and visible endpoint-flow assets into isolated Train A v048."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/CrownEndpointPresentation_v001"
MANIFEST = json.loads((SOURCE_DIR / "PRESS_TRAIN_CROWN_ENDPOINT_PRESENTATION_MANIFEST_v001.json").read_text(encoding="utf-8"))
AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_crown_endpoint_presentation_source_audit_v001.json").read_text(encoding="utf-8"))
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAS07IdentityClearanceCandidate_v047"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainACrownEndpointCandidate_v048"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/CrownEndpointPresentation_v001"
MAT25 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_crown_endpoint_build_v048.json"
if not str(AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("crown/endpoint source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("crown/endpoint source invented world placement")

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
        raise RuntimeError(f"crown/endpoint import missing: {row['asset']}")
    meshes[row["asset"]] = mesh

if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v048 from v047: {TARGET_MAP}")

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
    raise RuntimeError(f"missing crown/endpoint material mappings: {missing_materials}")
rows = {row["asset"]: row for row in MANIFEST["assets"]}


def spawn(asset_name, label, location, semantic):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator(yaw=180.0))
    actor.set_actor_label(label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.SharedKit",
        "LB.PressTrain.TrainA.Isolated",
        "LB.PressTrain.Fixed.CrownEndpointPresentation",
        semantic,
        "LB.Asset.Candidate.v048",
        "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    component = actor.static_mesh_component
    component.set_static_mesh(meshes[asset_name])
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    for slot_index, slot in enumerate(rows[asset_name]["material_slots"]):
        component.set_material(slot_index, materials[slot])
    return actor.get_actor_label()


heights_mm = {"S02": 11000, "S03": 9500, "S04": 9000, "S05": 8500, "S06": 9000}
placed = []
for index in range(2, 7):
    stage = f"S{index:02d}"
    y_cm = (index - 1) * 750.0
    crown_z_cm = 35.0 + (heights_mm[stage] - 1800.0) / 10.0
    placed.append(spawn(
        "SM_CA_MW_PT_HeavyCrownMass_v001",
        f"CA_MW_PTA_{stage}_HeavyCrownMass_v048",
        unreal.Vector(0.0, y_cm, crown_z_cm),
        f"LB.PressTrain.CrownEndpoint.{stage}.HeavyCrown",
    ))
placed.append(spawn(
    "SM_CA_MW_PT_S01VisibleBlankFeed_v001",
    "CA_MW_PTA_S01_VisibleBlankFeed_v048",
    unreal.Vector(0.0, 0.0, 35.0),
    "LB.PressTrain.CrownEndpoint.S01.VisibleBlankFeed",
))
placed.append(spawn(
    "SM_CA_MW_PT_S07VisiblePanelDischarge_v001",
    "CA_MW_PTA_S07_VisiblePanelDischarge_v048",
    unreal.Vector(0.0, 4500.0, 35.0),
    "LB.PressTrain.CrownEndpoint.S07.VisiblePanelDischarge",
))

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v048" not in tags:
            tags.append("LB.Asset.Candidate.v048")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(placed) != 7:
    failures.append(f"expected seven crown/endpoint actors, found {len(placed)}")
if scope_count != 180:
    failures.append(f"expected 180 scoped actors, found {scope_count}")
if not levels.save_current_level():
    failures.append("could not save v048 crown/endpoint candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-crown-endpoint-build-v048/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V048_HEAVY_CROWNS_AND_VISIBLE_S01_S07_MATERIAL_FLOW__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V048_CROWN_ENDPOINT_BUILD__NOT_PROMOTED"
    ),
    "source_map": SOURCE_MAP,
    "map": TARGET_MAP,
    "asset_root": DEST,
    "placed_actor_count": len(placed),
    "placed_actors": placed,
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
