"""Import enclosed facades and create an isolated v033 child of retained v032."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/EnclosedFacade_v001"
MANIFEST = json.loads((SOURCE_DIR / "PRESS_TRAIN_ENCLOSED_FACADE_MANIFEST_v001.json").read_text(encoding="utf-8"))
AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_enclosed_facade_source_audit_v001.json").read_text(encoding="utf-8"))
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainACartPlateClearanceCandidate_v032"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainAEnclosedFacadeCandidate_v033"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/EnclosedFacade_v001"
MAT25 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025"
MAT14 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v014"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_enclosed_facade_build_v033.json"
if not str(AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("enclosed-facade source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("enclosed-facade source invented world placement")

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
        raise RuntimeError(f"enclosed-facade import missing: {row['asset']}")
    meshes[row["asset"]] = mesh

if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v033 from v032: {TARGET_MAP}")

material_paths = {
    "CA_MW_FoundryCharcoal": f"{MAT25}/M_CA_MW_PT_FoundryCharcoalLayered_v025",
    "CA_MW_CairnwellGreen": f"{MAT25}/M_CA_MW_PT_CairnwellGreenLayered_v025",
    "CA_MW_SafetyYellow": f"{MAT25}/M_CA_MW_PT_SafetyYellowLayered_v025",
    "CA_MW_ServiceGrey": f"{MAT25}/M_CA_MW_PT_ServiceGreyLayered_v025",
    "CA_MW_WorkedSteel": f"{MAT25}/M_CA_MW_PT_WorkedSteelLayered_v025",
    "CA_MW_DarkRubber": f"{MAT25}/M_CA_MW_PT_DarkRubberLayered_v025",
    "CA_MW_TrainAAccent": f"{MAT25}/M_CA_MW_PT_TrainAAccentLayered_v025",
    "CA_MW_LabelWhite": f"{MAT25}/M_CA_MW_PT_LabelWhiteLayered_v025",
    "CA_MW_InspectionGlass": f"{MAT14}/M_CA_MW_PT_InspectionGlass_v014",
}
materials = {name: library.load_asset(path) for name, path in material_paths.items()}
missing_materials = [name for name, material in materials.items() if material is None]
if missing_materials:
    raise RuntimeError(f"missing enclosed-facade materials: {missing_materials}")
rows = {row["asset"]: row for row in MANIFEST["assets"]}


def spawn_mesh(asset_name, label, y_cm, stage):
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0.0, y_cm, 35.0), unreal.Rotator(yaw=180.0))
    actor.set_actor_label(label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.SharedKit", "LB.PressTrain.TrainA.Isolated",
        "LB.PressTrain.Fixed.EnclosedFacade", f"LB.PressTrain.EnclosedFacade.{stage}",
        "LB.Asset.Candidate.v033", "LB.Asset.CandidateNotPromoted",
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


def spawn_plate(stage, title, location, size):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, location, unreal.Rotator(yaw=90.0))
    actor.set_actor_label(f"CA_MW_PTA_{stage}_IntegratedIdentity_v033")
    actor.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated", "LB.PressTrain.EnclosedFacade.IntegratedIdentity",
        f"LB.PressTrain.EnclosedFacade.{stage}.IntegratedIdentity",
        "LB.Brand.CairnwellAutomotive", "LB.Site.MoorcrossWorks",
        "LB.Asset.Candidate.v033", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    actor.text_render.set_text(f"{stage}  {title}")
    actor.text_render.set_world_size(size)
    actor.text_render.set_text_render_color(unreal.Color(24, 36, 34, 255))
    actor.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    actor.text_render.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    actor.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.text_render.set_editor_property("cast_shadow", False)
    return actor.get_actor_label()


# Remove the validation-era floating identifiers; replace them with flush text
# on physical label plates authored into the new facades.
removed_labels = []
for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label() in {f"CA_MW_PTA_TEXT_S{index:02d}" for index in range(1, 8)}:
        removed_labels.append(actor.get_actor_label())
        actors_api.destroy_actor(actor)

placed = []
placed.append(spawn_mesh("SM_CA_MW_PT_S01DestackEnclosedFacade_v001", "CA_MW_PTA_S01_EnclosedFacade", 0.0, "S01"))
placed.append(spawn_mesh("SM_CA_MW_PT_DrawPressEnclosedFacade_v001", "CA_MW_PTA_S02_EnclosedFacade", 750.0, "S02"))
for index in range(3, 7):
    stage = f"S{index:02d}"
    placed.append(spawn_mesh(
        "SM_CA_MW_PT_MidPressEnclosedFacade_v001", f"CA_MW_PTA_{stage}_EnclosedFacade",
        (index - 1) * 750.0, stage))
placed.append(spawn_mesh("SM_CA_MW_PT_S07UnloadInspectEnclosedFacade_v001", "CA_MW_PTA_S07_EnclosedFacade", 4500.0, "S07"))

identity_specs = [
    ("S01", "DESTACK / LOAD", unreal.Vector(-358.0, 90.0, 520.0), 14.0),
    ("S02", "DRAW PRESS", unreal.Vector(-389.0, 845.0, 825.0), 15.0),
    ("S03", "SECONDARY FORM", unreal.Vector(-370.0, 1585.0, 665.0), 13.0),
    ("S04", "TRIM PRESS", unreal.Vector(-370.0, 2335.0, 665.0), 14.0),
    ("S05", "PIERCE PRESS", unreal.Vector(-370.0, 3085.0, 665.0), 14.0),
    ("S06", "FINAL RESTRIKE", unreal.Vector(-370.0, 3835.0, 665.0), 13.0),
    ("S07", "UNLOAD / INSPECT", unreal.Vector(-475.0, 4600.0, 565.0), 14.0),
]
integrated_labels = [spawn_plate(stage, title, location, size) for stage, title, location, size in identity_specs]


def set_exposure(camera, bias):
    settings = camera.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True, "auto_exposure_bias": bias,
    })
    camera.camera_component.set_editor_property("post_process_settings", settings)
    camera.camera_component.set_editor_property("post_process_blend_weight", 1.0)


camera_bias = {
    "CA_MW_PTA_CAM_Hero": 1.30, "CA_MW_PTA_CAM_Overview": 1.22,
    "CA_MW_PTA_CAM_DrawStage": 1.05, "CA_MW_PTA_CAM_DieChangeService": 0.95,
    "CA_MW_PTA_CAM_DieCartDetail": 0.82,
}
for actor in actors_api.get_all_level_actors():
    if actor.get_actor_label() in camera_bias:
        set_exposure(actor, camera_bias[actor.get_actor_label()])
    if "LB.Validation.ReleaseOverheadLighting" in {str(tag) for tag in actor.tags}:
        component = actor.get_editor_property("rect_light_component")
        component.set_editor_property("intensity", 285.0)

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v033" not in tags:
            tags.append("LB.Asset.Candidate.v033")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(removed_labels) != 7 or len(placed) != 7 or len(integrated_labels) != 7 or scope_count != 164:
    failures.append(
        f"cardinality mismatch removed={len(removed_labels)} facades={len(placed)} labels={len(integrated_labels)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v033 enclosed-facade candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-enclosed-facade-build-v033/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V033_SEVEN_ENCLOSED_FACADES_INTEGRATED_PHYSICAL_IDENTITIES_AND_CCTV_EXPOSURE_CALIBRATION__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V033_ENCLOSED_FACADE_BUILD__NOT_PROMOTED"),
    "source_map": SOURCE_MAP, "map": TARGET_MAP, "asset_root": DEST,
    "placed_facades": placed, "removed_floating_labels": removed_labels,
    "integrated_labels": integrated_labels, "camera_exposure_bias": camera_bias,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
