"""Import release-detail v001 into an isolated v023 child of retained Train A v022."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_DIR = ROOT / "SourceAssets/PressTrains/Shared/ReleaseDetail_v001"
MANIFEST = json.loads((SOURCE_DIR / "PRESS_TRAIN_RELEASE_DETAIL_MANIFEST_v001.json").read_text(encoding="utf-8"))
AUDIT = json.loads((ROOT / "Saved/Audits/PressTrains/press_train_release_detail_source_audit_v001.json").read_text(encoding="utf-8"))
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainADieChangeEvidenceCandidate_v022"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainAReleaseDetailCandidate_v023"
DEST = "/Game/LineBoss/Candidates/PressTrains/Shared/ReleaseDetail_v001"
MAT_ROOT = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v023"
BASE_MAT_ROOT = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v014"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_release_detail_build_v023.json"
if not str(AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("release-detail source audit has not passed")
if MANIFEST.get("world_placement") != "TBC_NOT_INVENTED":
    raise RuntimeError("release-detail source invented world placement")

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
        raise RuntimeError(f"release-detail import missing: {row['asset']}")
    meshes[row["asset"]] = mesh

if not levels.new_level_from_template(TARGET_MAP, SOURCE_MAP):
    raise RuntimeError(f"Could not create v023 from retained v022: {TARGET_MAP}")


def simple_surface(name, colour, metallic, roughness, emissive=None):
    path = f"{MAT_ROOT}/{name}"
    material = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(path)
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -340, -100)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -340, 30)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -340, 120)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if emissive is not None:
        emit = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -340, 220)
        emit.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        mel.connect_material_property(emit, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


material_paths = {
    "CA_MW_FoundryCharcoal": f"{BASE_MAT_ROOT}/M_CA_MW_PT_FoundryCharcoal_v014",
    "CA_MW_CairnwellGreen": f"{BASE_MAT_ROOT}/M_CA_MW_PT_CairnwellGreen_v014",
    "CA_MW_SafetyYellow": f"{BASE_MAT_ROOT}/M_CA_MW_PT_SafetyYellow_v014",
    "CA_MW_WorkedSteel": f"{BASE_MAT_ROOT}/M_CA_MW_PT_WorkedSteel_v014",
    "CA_MW_ServiceGrey": f"{BASE_MAT_ROOT}/M_CA_MW_PT_ServiceGrey_v014",
    "CA_MW_TrainAAccent": f"{BASE_MAT_ROOT}/M_CA_MW_PT_TrainAAccent_v014",
    "CA_MW_StateGreen": f"{BASE_MAT_ROOT}/M_CA_MW_PT_StateGreen_v014",
}
materials = {name: library.load_asset(path) for name, path in material_paths.items()}
materials.update({
    "CA_MW_DarkRubber": simple_surface("M_CA_MW_PT_DarkRubber_v023", (0.006, 0.008, 0.009), 0.02, 0.84),
    "CA_MW_StateAmber": simple_surface("M_CA_MW_PT_StateAmber_v023", (0.48, 0.095, 0.002), 0.03, 0.30, (1.8, 0.28, 0.01)),
    "CA_MW_StateRed": simple_surface("M_CA_MW_PT_StateRed_v023", (0.42, 0.005, 0.002), 0.03, 0.32, (1.4, 0.008, 0.002)),
    "CA_MW_StateBlue": simple_surface("M_CA_MW_PT_StateBlue_v023", (0.008, 0.10, 0.38), 0.05, 0.30, (0.02, 0.22, 1.1)),
    "CA_MW_LabelWhite": simple_surface("M_CA_MW_PT_LabelWhite_v023", (0.42, 0.50, 0.48), 0.12, 0.44),
})
missing_materials = [name for name, material in materials.items() if material is None]
if missing_materials:
    raise RuntimeError(f"missing release-detail materials: {missing_materials}")
rows = {row["asset"]: row for row in MANIFEST["assets"]}


def apply_mesh(actor, asset_name):
    component = actor.static_mesh_component
    component.set_static_mesh(meshes[asset_name])
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    for slot_index, slot in enumerate(rows[asset_name]["material_slots"]):
        component.set_material(slot_index, materials[slot])


def add_tags(actor, *values):
    actor_tags = [str(tag) for tag in actor.tags]
    for value in values:
        if value not in actor_tags:
            actor_tags.append(value)
    actor.set_editor_property("tags", [unreal.Name(value) for value in actor_tags])


def one(label):
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {label}, found {len(matches)}")
    return matches[0]


def spawn_mesh(asset_name, label, location, rotation, semantic):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.SharedKit", "LB.PressTrain.TrainA.Isolated",
        "LB.PressTrain.Fixed.ReleaseDetail", semantic,
        "LB.Asset.Candidate.v023", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    apply_mesh(actor, asset_name)
    return actor


def spawn_text(label, text, location, rotation, semantic, size=16.0):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, location, rotation)
    actor.set_actor_label(label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated", "LB.PressTrain.ReleaseDetail.Text", semantic,
        "LB.Brand.CairnwellAutomotive", "LB.Site.MoorcrossWorks",
        "LB.Asset.Candidate.v023", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    actor.text_render.set_text(text)
    actor.text_render.set_world_size(size)
    actor.text_render.set_text_render_color(unreal.Color(218, 228, 224, 255))
    actor.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    actor.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return actor


press_stages = [(f"S{index:02d}", (index - 1) * 750.0) for index in range(2, 7)]
cart_swaps = []
dock_swaps = []
tooling_loads = []
release_detail = []
release_text = []
for stage, y_cm in press_stages:
    cart = one(f"CA_MW_PTA_{stage}_DieCart")
    apply_mesh(cart, "SM_CA_MW_PT_DieCartRelease_v001")
    add_tags(cart, "LB.PressTrain.ReleaseDetail.DieCart", f"LB.PressTrain.ReleaseDetail.{stage}.DieCart")
    cart_swaps.append(cart.get_actor_label())
    tooling = spawn_mesh(
        "SM_CA_MW_PT_DieCartToolingLoad_v001", f"CA_MW_PTA_{stage}_DieCartToolingLoad",
        cart.get_actor_location(), cart.get_actor_rotation(),
        f"LB.PressTrain.ReleaseDetail.{stage}.DieCartToolingLoad")
    tooling.set_actor_scale3d(cart.get_actor_scale3d())
    tooling_loads.append(tooling.get_actor_label())
    cart_location = cart.get_actor_location()
    release_text.append(spawn_text(
        f"CA_MW_PTA_TEXT_{stage}_DieCart",
        f"CAIRNWELL AUTOMOTIVE  |  TRAIN A  {stage} DIE CART",
        unreal.Vector(cart_location.x + 238.0, cart_location.y, cart_location.z + 8.0),
        unreal.Rotator(yaw=-90.0), f"LB.PressTrain.ReleaseDetail.{stage}.DieCartIdentity", 14.0).get_actor_label())

    dock = one(f"CA_MW_PTA_{stage}_DieChangeDock")
    apply_mesh(dock, "SM_CA_MW_PT_DieChangeDockRelease_v001")
    add_tags(dock, "LB.PressTrain.ReleaseDetail.DieChangeDock", f"LB.PressTrain.ReleaseDetail.{stage}.DieChangeDock")
    dock_swaps.append(dock.get_actor_label())

    release_detail.append(spawn_mesh(
        "SM_CA_MW_PT_FrameSeamFastenerPack_v001", f"CA_MW_PTA_{stage}_FrameReleaseDetail",
        unreal.Vector(0.0, y_cm, 35.0), unreal.Rotator(yaw=180.0),
        f"LB.PressTrain.ReleaseDetail.{stage}.FrameSeamsFasteners").get_actor_label())
    release_detail.append(spawn_mesh(
        "SM_CA_MW_PT_HoseCableDress_v001", f"CA_MW_PTA_{stage}_SupportedUtilityDress",
        unreal.Vector(0.0, y_cm, 35.0), unreal.Rotator(yaw=180.0),
        f"LB.PressTrain.ReleaseDetail.{stage}.SupportedUtilities").get_actor_label())

state_assignments = {
    "S01": ("SM_CA_MW_PT_ServiceStateRunning_v001", "RUNNING"),
    "S02": ("SM_CA_MW_PT_ServiceStateRunning_v001", "RUNNING"),
    "S03": ("SM_CA_MW_PT_ServiceStateRunning_v001", "RUNNING"),
    "S04": ("SM_CA_MW_PT_ServiceStateMaintenance_v001", "MAINTENANCE HOLD"),
    "S05": ("SM_CA_MW_PT_ServiceStateStandby_v001", "STANDBY"),
    "S06": ("SM_CA_MW_PT_ServiceStateRunning_v001", "RUNNING"),
    "S07": ("SM_CA_MW_PT_ServiceStateRunning_v001", "RUNNING"),
}
state_modules = []
for index in range(1, 8):
    stage = f"S{index:02d}"
    y_cm = (index - 1) * 750.0
    asset_name, state = state_assignments[stage]
    state_modules.append(spawn_mesh(
        asset_name, f"CA_MW_PTA_{stage}_ServiceState_{state.replace(' ', '_')}",
        unreal.Vector(0.0, y_cm, 35.0), unreal.Rotator(yaw=180.0),
        f"LB.PressTrain.ReleaseDetail.{stage}.ServiceState.{state.replace(' ', '')}").get_actor_label())
    release_text.append(spawn_text(
        f"CA_MW_PTA_TEXT_{stage}_ServiceState", f"{stage}  {state}",
        unreal.Vector(-340.0, y_cm - 185.0, 328.0), unreal.Rotator(yaw=90.0),
        f"LB.PressTrain.ReleaseDetail.{stage}.StateLabel", 15.0).get_actor_label())

scope_count = 0
for actor in actors_api.get_all_level_actors():
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        scope_count += 1
        if "LB.Asset.Candidate.v023" not in actor_tags:
            actor_tags.append("LB.Asset.Candidate.v023")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])

failures = []
checks = {
    "cart_swaps": (len(cart_swaps), 5), "dock_swaps": (len(dock_swaps), 5),
    "tooling_loads": (len(tooling_loads), 5), "release_detail": (len(release_detail), 10),
    "state_modules": (len(state_modules), 7), "release_text": (len(release_text), 12),
    "scope": (scope_count, 145),
}
for name, (actual, wanted) in checks.items():
    if actual != wanted:
        failures.append(f"expected {wanted} {name}, found {actual}")
visible_text = [str(actor.text_render.get_editor_property("text")) for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.TextRenderActor)]
if any("LINE BOSS" in value.upper() or "LINEBOSS" in value.upper() for value in visible_text):
    failures.append("working-title branding found in visible v023 text")
if not levels.save_current_level():
    failures.append("could not save v023 release-detail candidate")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
library.save_directory(MAT_ROOT, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/press-train-a-release-detail-build-v023/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V023_RELEASE_CARTS_DOCKS_FRAME_DETAIL_SUPPORTED_UTILITIES_DISTINCT_STATES_AND_IDENTITY__STATIC_AND_FRESH_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V023_RELEASE_DETAIL_BUILD__NOT_PROMOTED"),
    "source_map": SOURCE_MAP, "map": TARGET_MAP, "asset_root": DEST,
    "counts": {name: actual for name, (actual, _wanted) in checks.items()},
    "cart_swaps": cart_swaps, "dock_swaps": dock_swaps,
    "state_assignments": {stage: state for stage, (_asset, state) in state_assignments.items()},
    "mixed_states_are_visual_validation_only_until_native_binding": True,
    "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
    "accepted_pr010_map_changed": False, "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
