"""Import the shared press-train kit and assemble isolated Train A at local origin."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/Blockout_v001"
MANIFEST = json.loads((SOURCE / "PRESS_TRAIN_SHARED_KIT_MANIFEST_v001.json").read_text(encoding="utf-8"))
SOURCE_AUDIT_PATH = ROOT / "Saved/Audits/PressTrains/press_train_shared_source_audit_v001.json"
SOURCE_AUDIT = json.loads(SOURCE_AUDIT_PATH.read_text(encoding="utf-8"))
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/Blockout_v001"
MAP = "/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_isolated_build_v001.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
if not str(SOURCE_AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("shared press-train source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("source manifest no longer preserves TBC world placement")

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
existing_receipt = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else None
failed_receipt = bool(existing_receipt and str(existing_receipt.get("status", "")).startswith("FAIL"))
resume_partial = library.does_asset_exist(MAP) and (not OUT.exists() or failed_receipt)
if library.does_asset_exist(MAP) and OUT.exists() and not failed_receipt:
    raise RuntimeError(f"Completed candidate and receipt already exist; refusing to overwrite: {MAP}")


def import_static(row):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / row["file"]),
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


for row in MANIFEST["assets"]:
    import_static(row)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if resume_partial:
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not resume partial isolated Train A map: {MAP}")
    # Remove only this builder's own partial actors before deterministic reconstruction.
    for actor in list(actors_api.get_all_level_actors()):
        actor_tags = {str(tag) for tag in actor.tags}
        if "LB.PressTrain.TrainA.Isolated" in actor_tags or actor.get_actor_label().startswith("CA_MW_PTA_"):
            actors_api.destroy_actor(actor)
else:
    if not levels.new_level(MAP):
        raise RuntimeError(f"Could not create isolated Train A map: {MAP}")

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
rows = {row["asset"]: row for row in MANIFEST["assets"]}


def mesh(name):
    value = library.load_asset(f"{DEST}/{name}")
    if not isinstance(value, unreal.StaticMesh):
        raise RuntimeError(f"missing imported static mesh: {name}")
    return value


def apply_materials(component, name):
    for index, slot in enumerate(rows[name]["material_slots"]):
        material = materials.get(slot)
        if material is None:
            raise RuntimeError(f"no Unreal material mapping for {slot} on {name}")
        component.set_material(index, material)


COMMON_TAGS = (
    "LB.PressTrain.SharedKit",
    "LB.PressTrain.TrainA.Isolated",
    "LB.Asset.Candidate.v001",
    "LB.Asset.CandidateNotPromoted",
    "LB.Authority.WorldPlacement.TBCNotInvented",
)


def spawn_mesh(label, asset_name, loc_mm, semantic, collision=False):
    location = unreal.Vector(*(value / 10.0 for value in loc_mm))
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator())
    actor.set_actor_label(label)
    actor.tags = [unreal.Name(value) for value in (*COMMON_TAGS, semantic)]
    actor.static_mesh_component.set_static_mesh(mesh(asset_name))
    actor.static_mesh_component.set_collision_enabled(
        unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll" if collision else "NoCollision"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", collision)
    apply_materials(actor.static_mesh_component, asset_name)
    return actor


placed = []
placed.append(spawn_mesh("CA_MW_PTA_CommonPlatform", "SM_CA_MW_PT_CommonPlatform_v001", (0, 0, 0), "LB.PressTrain.Fixed.Platform"))
placed.append(spawn_mesh("CA_MW_PTA_UtilitySpine", "SM_CA_MW_PT_CommonUtilitySpine_v001", (6200, 0, 0), "LB.PressTrain.Fixed.UtilitySpine"))
placed.append(spawn_mesh("CA_MW_PTA_TransferRail", "SM_CA_MW_PT_TransferRail_v001", (0, 0, 0), "LB.PressTrain.Fixed.TransferRail"))

stage_assets = [
    ("S01", 0, "SM_CA_MW_PT_DestackLoadCell_v001", "DESTACK / LOAD"),
    ("S02", 7500, "SM_CA_MW_PT_PressFrame_Draw_v001", "DRAW PRESS"),
    ("S03", 15000, "SM_CA_MW_PT_PressFrame_Form_v001", "SECONDARY FORM"),
    ("S04", 22500, "SM_CA_MW_PT_PressFrame_Trim_v001", "TRIM PRESS"),
    ("S05", 30000, "SM_CA_MW_PT_PressFrame_Pierce_v001", "PIERCE PRESS"),
    ("S06", 37500, "SM_CA_MW_PT_PressFrame_Flange_v001", "FINAL RESTRIKE"),
    ("S07", 45000, "SM_CA_MW_PT_UnloadInspectCell_v001", "UNLOAD / INSPECT"),
]
stage_actor_labels = []
for stage, y, asset_name, title in stage_assets:
    actor = spawn_mesh(f"CA_MW_PTA_{stage}_{title.replace(' ', '_').replace('/', '')}", asset_name, (0, y, 350), f"LB.PressTrain.Stage.{stage}")
    placed.append(actor)
    stage_actor_labels.append(actor.get_actor_label())
    text = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(-365, y / 10.0 - 260, 470), unreal.Rotator(yaw=90))
    text.set_actor_label(f"CA_MW_PTA_TEXT_{stage}")
    text.tags = [unreal.Name(value) for value in (*COMMON_TAGS, f"LB.PressTrain.StageIdentity.{stage}")]
    text.text_render.set_text(f"{stage}  {title}")
    text.text_render.set_world_size(38.0)
    text.text_render.set_text_render_color(unreal.Color(215, 225, 220, 255))
    text.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    text.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

# Moving/tooling presentation actors are separate and pivot-correct; they remain NoCollision in this first visual candidate.
press_stages = (("S02", 7500, 11000), ("S03", 15000, 9500), ("S04", 22500, 9000), ("S05", 30000, 8500), ("S06", 37500, 9000))
for stage, y, height in press_stages:
    placed.append(spawn_mesh(f"CA_MW_PTA_{stage}_PressSlide", "SM_CA_MW_PT_PressSlide_v001", (0, y, height * 0.56), f"LB.PressTrain.Mover.{stage}.PressSlide"))
    placed.append(spawn_mesh(f"CA_MW_PTA_{stage}_MovingBolster", "SM_CA_MW_PT_MovingBolster_v001", (0, y, 900), f"LB.PressTrain.Mover.{stage}.Bolster"))
    placed.append(spawn_mesh(f"CA_MW_PTA_{stage}_DieSet", "SM_CA_MW_PT_StageDieSet_v001", (0, y, 1550), f"LB.PressTrain.Tooling.{stage}.Die"))
    placed.append(spawn_mesh(f"CA_MW_PTA_{stage}_DieCart", "SM_CA_MW_PT_DieCart_v001", (6200, y, 900), f"LB.PressTrain.Mover.{stage}.DieCart"))
placed.append(spawn_mesh("CA_MW_PTA_S01_DestackLift", "SM_CA_MW_PT_DestackLift_v001", (0, 0, 1200), "LB.PressTrain.Mover.S01.DestackLift"))
for index, y in enumerate((3750, 11250, 18750, 26250, 33750, 41250), start=1):
    placed.append(spawn_mesh(f"CA_MW_PTA_TransferCrossbar_{index:02d}", "SM_CA_MW_PT_TransferCrossbar_v001", (0, y, 4700), f"LB.PressTrain.Mover.Transfer.{index:02d}"))

# Diegetic Train A identity; Line Boss is deliberately absent from visible wording.
identity = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(-500, -300, 880), unreal.Rotator(yaw=90))
identity.set_actor_label("CA_MW_PTA_TEXT_TrainIdentity")
identity.tags = [unreal.Name(value) for value in (*COMMON_TAGS, "LB.Brand.CairnwellAutomotive", "LB.Site.MoorcrossWorks")]
identity.text_render.set_text("CAIRNWELL AUTOMOTIVE\nMOORCROSS WORKS\nTRAIN A  LARGE OUTER PANELS")
identity.text_render.set_world_size(48.0)
identity.text_render.set_text_render_color(unreal.Color(220, 230, 225, 255))
identity.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
identity.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

# Neutral isolated evidence environment. This is not a production-map placement.
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
floor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 2250, -25), unreal.Rotator())
floor.set_actor_label("CA_MW_PTA_IsolatedEvidenceFloor")
floor.tags = [unreal.Name(value) for value in (*COMMON_TAGS, "LB.Validation.Environment")]
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(18, 65, 0.5))
floor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
floor.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"))

sky = actors_api.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.set_actor_label("CA_MW_PTA_IsolatedSky")
sky.get_editor_property("light_component").set_editor_property("intensity", 0.35)
directional = actors_api.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(), unreal.Rotator(pitch=-42, yaw=-28))
directional.set_actor_label("CA_MW_PTA_IsolatedKey")
directional.get_editor_property("directional_light_component").set_editor_property("intensity", 2.2)
for index, y in enumerate((0, 750, 1500, 2250, 3000, 3750, 4500)):
    light = actors_api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(-800, y, 1200), unreal.Rotator(pitch=-25, yaw=0))
    light.set_actor_label(f"CA_MW_PTA_IsolatedFill_{index + 1:02d}")
    component = light.get_editor_property("rect_light_component")
    component.set_editor_property("intensity", 1800.0)
    component.set_editor_property("source_width", 650.0)
    component.set_editor_property("source_height", 160.0)
    component.set_light_color(unreal.LinearColor(0.72, 0.82, 0.80, 1.0))


def camera(label, location, target, semantic):
    rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, location, rotation)
    actor.set_actor_label(label)
    actor.tags = [unreal.Name(value) for value in (*COMMON_TAGS, "LB.Camera.Fixed", semantic)]
    actor.camera_component.set_editor_property("field_of_view", 58.0)
    return actor


cameras = [
    camera("CA_MW_PTA_CAM_Hero", unreal.Vector(-2500, -2500, 1700), unreal.Vector(0, 2250, 480), "LB.Camera.PressTrainA.Hero"),
    camera("CA_MW_PTA_CAM_Overview", unreal.Vector(-4700, 2250, 5200), unreal.Vector(0, 2250, 350), "LB.Camera.PressTrainA.Overview"),
    camera("CA_MW_PTA_CAM_DrawStage", unreal.Vector(-1500, 300, 1150), unreal.Vector(0, 750, 480), "LB.Camera.PressTrainA.DrawStage"),
]

failures = []
if len(placed) != 37:
    failures.append(f"expected 37 mesh presentation actors, found {len(placed)}")
if len(stage_actor_labels) != 7:
    failures.append(f"expected seven stage shells, found {len(stage_actor_labels)}")
if len(cameras) != 3:
    failures.append(f"expected three fixed cameras, found {len(cameras)}")
visible_text = [str(actor.text_render.get_editor_property("text")) for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.TextRenderActor)]
if any("LINE BOSS" in value.upper() or "LINEBOSS" in value.upper() for value in visible_text):
    failures.append("working-title branding found in isolated Train A text")
if not levels.save_current_level():
    failures.append("could not save isolated Train A map")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-isolated-build-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V001_ISOLATED_LOCAL_ORIGIN_SEVEN_STAGES_SEPARATE_MOVERS_BRANDING_CAMERAS__STATIC_VISUAL_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_ISOLATED_BUILD_V001__NOT_PROMOTED",
    "map": MAP,
    "asset_destination": DEST,
    "imported_asset_count": len(MANIFEST["assets"]),
    "placed_mesh_actor_count": len(placed),
    "stage_shell_count": len(stage_actor_labels),
    "fixed_camera_count": len(cameras),
    "resumed_partial_candidate": resume_partial,
    "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False,
    "accepted_pr010_map_changed": False,
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
