"""Create isolated PR-010 v103 installed-service, calibrated-light and readable-ID candidate."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v102"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v103"
SOURCE = ROOT / "SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v103"
MANIFEST = json.loads((SOURCE / "PR010_RELEASE_ART_MANIFEST_v103.json").read_text(encoding="utf-8"))
SOURCE_AUDIT = json.loads((ROOT / "Saved/Audits/PR010_ReleaseArt_v103/pr010_release_art_source_audit_v103.json").read_text(encoding="utf-8"))
DEST = "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v103"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v103/pr010_release_art_build_v103.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
if not str(SOURCE_AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("v103 source audit has not passed")

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET_MAP):
    raise RuntimeError(f"Refusing to overwrite {TARGET_MAP}")
if not library.duplicate_asset(SOURCE_MAP, TARGET_MAP):
    raise RuntimeError("v103 map duplication failed")
if not library.save_asset(TARGET_MAP, only_if_is_dirty=False):
    raise RuntimeError("v103 duplicated map save failed")


def import_static(row):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE / row["file"]), "destination_path": DEST,
        "destination_name": row["asset"], "automated": True,
        "replace_existing": True, "replace_existing_settings": True, "save": True})
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": False,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH})
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "generate_lightmap_u_vs": True, "auto_generate_collision": False, "remove_degenerates": True})
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])


for row in MANIFEST["assets"]:
    import_static(row)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(TARGET_MAP)

material_root = "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials"
paths = {
    "CA_MW_CairnwellGreen": f"{material_root}/M_CA_MW_PR009_LayeredCairnwellGreen_v085",
    "CA_MW_SafetyYellow": f"{material_root}/M_CA_MW_PR009_LayeredSafetyYellow_v085",
    "CA_MW_FoundryCharcoal": f"{material_root}/M_CA_MW_PR009_LayeredFoundryCharcoal_v085",
    "CA_MW_ServiceGrey": f"{material_root}/M_CA_MW_PR009_LayeredServiceGrey_v085",
    "CA_MW_WorkedSteel": f"{material_root}/M_CA_MW_PR009_MachinedSteel_v085",
    "CA_MW_IdentityFace": f"{material_root}/M_CA_MW_PR009_LayeredServiceGrey_v085",
}
materials = {name: library.load_asset(path) for name, path in paths.items()}
if any(value is None for value in materials.values()):
    raise RuntimeError("missing shared Press Shop material")
rows = {row["asset"]: row for row in MANIFEST["assets"]}


def mesh(name):
    value = library.load_asset(f"{DEST}/{name}")
    if not isinstance(value, unreal.StaticMesh):
        raise RuntimeError(f"missing imported mesh {name}")
    return value


def apply_materials(component, name):
    for index, slot in enumerate(rows[name]["material_slots"]):
        component.set_material(index, materials[slot])


def local_to_world(local_mm):
    x, y, z = local_mm
    return unreal.Vector(1350.0 + y / 10.0, -2000.0 - x / 10.0, z / 10.0)


def actor_tags(actor):
    return {str(tag) for tag in actor.tags}


def hide_visual(actor):
    component = actor.get_component_by_class(unreal.PrimitiveComponent)
    if component:
        component.set_visibility(False, True)
    actor.set_actor_hidden_in_game(True)


def visual_actor(label, asset_name, local_mm, semantic):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, local_to_world(local_mm), unreal.Rotator(yaw=-90))
    actor.set_actor_label("LB_PR010_V103_" + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Station.PR010", "LB.Asset.Candidate.v103", "LB.Asset.CandidateNotPromoted",
        semantic, "LB.PR010.ReleaseArt.Visual")]
    actor.static_mesh_component.set_static_mesh(mesh(asset_name))
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    apply_materials(actor.static_mesh_component, asset_name)
    return actor


actors = list(actors_api.get_all_level_actors())
failures = []
service_visuals = []
for index, local_x in enumerate((-4800, -1600, 1600, 4800), start=1):
    service_visuals.append(visual_actor(
        f"ServiceAccessHatches_{index}", "SM_CA_MW_PR010_ServiceAccessHatchSection_v103",
        (local_x, -2915, 2220), "LB.PR010.ServiceDeck.AccessDetail"))
    service_visuals.append(visual_actor(
        f"InstalledServiceBank_{index}", "SM_CA_MW_PR010_InstalledServiceBank_v103",
        (local_x, -2820, 2140), "LB.PR010.ServiceDeck.InstalledRouting"))

# Replace only v102 stack-ID presentation; stack geometry and saveable identities remain unchanged.
old_stack_text = [actor for actor in actors if "LB.PR010.StackPositionID" in actor_tags(actor)]
new_plates = []
new_text = []
for old in old_stack_text:
    value = str(old.text_render.get_editor_property("text"))
    old_location = old.get_actor_location()
    hide_visual(old)
    old.tags = [unreal.Name(value) for value in list(actor_tags(old)) + ["LB.PR010.LegacyStackID.Hidden.v103"]]
    plate_location = unreal.Vector(old_location.x + 5.0, old_location.y, 5.0)
    plate = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, plate_location, unreal.Rotator(yaw=-90))
    plate.set_actor_label("LB_PR010_V103_StackIDPlate_" + value.replace(" ", "_"))
    plate.tags = [unreal.Name(tag) for tag in (
        "LB.Station.PR010", "LB.Asset.Candidate.v103", "LB.Asset.CandidateNotPromoted",
        "LB.Identity.Traceability", "LB.PR010.StackIdentityPlate")]
    plate.static_mesh_component.set_static_mesh(mesh("SM_CA_MW_PR010_StackIdentityPlate_v103"))
    plate.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    plate.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    plate.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    apply_materials(plate.static_mesh_component, "SM_CA_MW_PR010_StackIdentityPlate_v103")
    text = actors_api.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(old_location.x - 3.5, old_location.y, 21.0), unreal.Rotator(yaw=180))
    text.set_actor_label("LB_PR010_V103_TEXT_StackID_" + value.replace(" ", "_"))
    text.tags = [unreal.Name(tag) for tag in (
        "LB.Station.PR010", "LB.Asset.Candidate.v103", "LB.Asset.CandidateNotPromoted",
        "LB.Identity.Traceability", "LB.PR010.StackPositionID.v103")]
    text.text_render.set_text(value)
    text.text_render.set_world_size(4.8)
    text.text_render.set_text_render_color(unreal.Color(12, 35, 28, 255))
    text.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    text.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    text.text_render.set_editor_property("can_ever_affect_navigation", False)
    new_plates.append(plate)
    new_text.append(text)

# Calibrate local station lights for fixed CCTV readability; do not alter shared hall lighting.
calibrated_lights = []
light_levels = {"Infeed": 95.0, "Centre": 105.0, "Handoff": 95.0, "Service": 65.0}
for actor in actors_api.get_all_level_actors():
    if not isinstance(actor, unreal.PointLight):
        continue
    for label, intensity in light_levels.items():
        if label in actor.get_actor_label() and "PR010" in actor.get_actor_label():
            actor.point_light_component.set_editor_property("intensity", intensity)
            actor.tags = [unreal.Name(value) for value in list(actor_tags(actor)) + ["LB.PR010.Lighting.Calibrated.v103"]]
            calibrated_lights.append({"label": actor.get_actor_label(), "intensity": intensity})
            break

if len(service_visuals) != 8:
    failures.append(f"expected eight v103 service visuals, found {len(service_visuals)}")
if len(old_stack_text) != 9 or len(new_plates) != 9 or len(new_text) != 9:
    failures.append(f"stack identity cardinality mismatch old={len(old_stack_text)} plates={len(new_plates)} text={len(new_text)}")
if len(calibrated_lights) != 4:
    failures.append(f"expected four calibrated PR010 lights, found {len(calibrated_lights)}")
if not levels.save_current_level():
    failures.append("could not save v103")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
report = {
    "$schema": "cairnwell/audit/pr010-release-art-build-v103/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V103_ISOLATED_INSTALLED_SERVICE_STACK_ID_LIGHT_CALIBRATION_INSTALLED__GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V103_BUILD__NOT_PROMOTED",
    "source_map": SOURCE_MAP, "map": TARGET_MAP, "asset_destination": DEST,
    "installed_service_visual_count": len(service_visuals),
    "stack_identity_plate_count": len(new_plates), "stack_identity_text_count": len(new_text),
    "calibrated_lights": calibrated_lights,
    "technical_geometry_changed": False, "new_collision_proxies": 0,
    "press_train_datums": "TBC_NOT_INVENTED", "failures": failures,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
