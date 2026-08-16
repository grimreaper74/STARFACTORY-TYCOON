"""Import installed-service v001 into an isolated child of retained Train A v015."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/InstalledService_v001"
MANIFEST = json.loads((SOURCE_DIR / "PRESS_TRAIN_INSTALLED_SERVICE_MANIFEST_v001.json").read_text(encoding="utf-8"))
AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_installed_service_source_audit_v001.json").read_text(encoding="utf-8"))
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAInstalledReadabilityCandidate_v015"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainAInstalledServiceCandidate_v017"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/InstalledService_v001"
MAT_ROOT = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v017"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_installed_service_build_v017.json"
if not str(AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("installed-service source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("installed-service source invented world placement")

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
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
        raise RuntimeError(f"installed-service import missing: {row['asset']}")
    meshes[row["asset"]] = mesh

if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v017 from retained v015: {TARGET_MAP}")


def simple_surface(name, colour, metallic, roughness, emissive=None):
    path = f"{MAT_ROOT}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(path)
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -330, -100)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -330, 25)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -330, 115)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if emissive is not None:
        emit = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -330, 215)
        emit.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        mel.connect_material_property(emit, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


base_material_root = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v014"
material_paths = {
    "CA_MW_FoundryCharcoal": f"{base_material_root}/M_CA_MW_PT_FoundryCharcoal_v014",
    "CA_MW_CairnwellGreen": f"{base_material_root}/M_CA_MW_PT_CairnwellGreen_v014",
    "CA_MW_SafetyYellow": f"{base_material_root}/M_CA_MW_PT_SafetyYellow_v014",
    "CA_MW_WorkedSteel": f"{base_material_root}/M_CA_MW_PT_WorkedSteel_v014",
    "CA_MW_ServiceGrey": f"{base_material_root}/M_CA_MW_PT_ServiceGrey_v014",
    "CA_MW_TrainAAccent": f"{base_material_root}/M_CA_MW_PT_TrainAAccent_v014",
}
materials = {name: library.load_asset(path) for name, path in material_paths.items()}
materials["CA_MW_TaskWhite"] = simple_surface(
    "M_CA_MW_PT_TaskLens_v017", (0.18, 0.23, 0.21), 0.05, 0.32, (0.24, 0.38, 0.32))
materials["CA_MW_OilAmber"] = simple_surface(
    "M_CA_MW_PT_OilAmber_v017", (0.16, 0.038, 0.001), 0.08, 0.42, (0.12, 0.022, 0.0))
missing_materials = [name for name, value in materials.items() if value is None]
if missing_materials:
    raise RuntimeError(f"missing installed-service material mappings: {missing_materials}")
rows = {row["asset"]: row for row in MANIFEST["assets"]}


def place(asset, label, y_cm, semantic):
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0.0, y_cm, 35.0), unreal.Rotator(yaw=180.0))
    actor.set_actor_label(label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.SharedKit", "LB.PressTrain.TrainA.Isolated",
        "LB.PressTrain.Fixed.InstalledService", semantic,
        "LB.Asset.Candidate.v017", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    component = actor.static_mesh_component
    component.set_static_mesh(meshes[asset])
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    for slot_index, slot in enumerate(rows[asset]["material_slots"]):
        component.set_material(slot_index, materials[slot])
    return actor.get_actor_label()


stage_centres = [(f"S{index:02d}", (index - 1) * 750.0) for index in range(1, 8)]
placed = []
for stage, y_cm in stage_centres:
    placed.append(place(
        "SM_CA_MW_PT_InstalledServiceBank_v001", f"CA_MW_PTA_{stage}_InstalledServiceBank",
        y_cm, f"LB.PressTrain.InstalledService.{stage}.OperatorSide"))
    placed.append(place(
        "SM_CA_MW_PT_LocalTaskFixture_v001", f"CA_MW_PTA_{stage}_LocalTaskFixture",
        y_cm, f"LB.PressTrain.InstalledService.{stage}.TaskFixture"))
for stage, y_cm in stage_centres[1:6]:
    placed.append(place(
        "SM_CA_MW_PT_DieChangeDock_v001", f"CA_MW_PTA_{stage}_DieChangeDock",
        y_cm, f"LB.PressTrain.InstalledService.{stage}.DieChangeDock"))
placed.append(place(
    "SM_CA_MW_PT_S04TrimScrapService_v001", "CA_MW_PTA_S04_TrimScrapService",
    2250.0, "LB.PressTrain.InstalledService.S04.TrimScrap"))
placed.append(place(
    "SM_CA_MW_PT_S05PierceSlugService_v001", "CA_MW_PTA_S05_PierceSlugService",
    3000.0, "LB.PressTrain.InstalledService.S05.PierceSlug"))

# Each authored fixture gets a close, directional Unreal light. These are local
# validation lights, not a change to global exposure or production hall authority.
lights = []
for stage, y_cm in stage_centres:
    location = unreal.Vector(-310.0, y_cm, 415.0)
    target = unreal.Vector(0.0, y_cm, 250.0)
    light = actors_api.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target))
    light.set_actor_label(f"CA_MW_PTA_{stage}_InstalledTaskLight")
    light.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated", "LB.Validation.Environment",
        "LB.Validation.LocalTaskLighting", f"LB.Validation.LocalTaskLighting.{stage}",
        "LB.Asset.Candidate.v017", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    component = light.get_editor_property("rect_light_component")
    component.set_editor_property("intensity", 420.0)
    component.set_editor_property("source_width", 150.0)
    component.set_editor_property("source_height", 24.0)
    component.set_editor_property("attenuation_radius", 480.0)
    component.set_light_color(unreal.LinearColor(0.62, 0.72, 0.68, 1.0))
    lights.append(light.get_actor_label())

scope_count = 0
for actor in actors_api.get_all_level_actors():
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        scope_count += 1
        if "LB.Asset.Candidate.v017" not in actor_tags:
            actor_tags.append("LB.Asset.Candidate.v017")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])

failures = []
if len(placed) != 21:
    failures.append(f"expected 21 installed-service actors, found {len(placed)}")
if len(lights) != 7:
    failures.append(f"expected seven local task lights, found {len(lights)}")
if not levels.save_current_level():
    failures.append("could not save v017 installed-service candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
library.save_directory(MAT_ROOT, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-installed-service-build-v017/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V017_INSTALLED_SERVICE_DIE_CHANGE_S04_S05_AND_LOCAL_FIXTURES__EARLY_DRAW_CAMERA_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V017_INSTALLED_SERVICE_BUILD__NOT_PROMOTED",
    "source_map": SOURCE_MAP, "map": TARGET_MAP, "asset_root": DEST,
    "placed_actor_count": len(placed), "placed_actors": placed,
    "local_task_light_count": len(lights), "local_task_light_intensity": 420.0,
    "scope_actor_count_after_build": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
