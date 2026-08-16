"""Create isolated PR-010 v101 and correct the remaining v100 visual holds."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v100"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v101"
SOURCE = ROOT / "SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v101"
MANIFEST = json.loads((SOURCE / "PR010_RELEASE_ART_MANIFEST_v101.json").read_text(encoding="utf-8"))
SOURCE_AUDIT = json.loads((ROOT / "Saved/Audits/PR010_ReleaseArt_v101/pr010_release_art_source_audit_v101.json").read_text(encoding="utf-8"))
DEST = "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v101"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v101/pr010_release_art_build_v101.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
if not str(SOURCE_AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("v101 source audit has not passed")

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET_MAP): raise RuntimeError(f"Refusing to overwrite {TARGET_MAP}")
if not library.duplicate_asset(SOURCE_MAP, TARGET_MAP): raise RuntimeError("v101 map duplication failed")
if not library.save_asset(TARGET_MAP, only_if_is_dirty=False): raise RuntimeError("v101 duplicated map save failed")


def import_static(row):
    task = unreal.AssetImportTask()
    task.set_editor_properties({"filename": str(SOURCE / row["file"]), "destination_path": DEST,
        "destination_name": row["asset"], "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": True})
    options = unreal.FbxImportUI()
    options.set_editor_properties({"import_mesh": True, "import_as_skeletal": False, "import_materials": False,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH})
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({"combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "generate_lightmap_u_vs": True, "auto_generate_collision": False, "remove_degenerates": True})
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])


for row in MANIFEST["assets"]: import_static(row)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.load_level(TARGET_MAP): raise RuntimeError(TARGET_MAP)

material_root = "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials"
paths = {
    "CA_MW_CairnwellGreen": f"{material_root}/M_CA_MW_PR009_LayeredCairnwellGreen_v085",
    "CA_MW_SafetyYellow": f"{material_root}/M_CA_MW_PR009_LayeredSafetyYellow_v085",
    "CA_MW_FoundryCharcoal": f"{material_root}/M_CA_MW_PR009_LayeredFoundryCharcoal_v085",
    "CA_MW_WorkedSteel": f"{material_root}/M_CA_MW_PR009_MachinedSteel_v085",
    "CA_MW_BlankSteel": f"{material_root}/M_CA_MW_PR009_OiledBlankSteel_v085",
    "CA_MW_White": f"{material_root}/M_CA_MW_PR009_LayeredServiceGrey_v085",
}
materials = {name: library.load_asset(path) for name, path in paths.items()}
if any(value is None for value in materials.values()): raise RuntimeError("missing shared Press Shop material")
manifest = {row["asset"]: row for row in MANIFEST["assets"]}


def load_mesh(name):
    value = library.load_asset(f"{DEST}/{name}")
    if not isinstance(value, unreal.StaticMesh): raise RuntimeError(f"missing imported mesh {name}")
    return value


def apply_materials(component, name):
    for index, slot in enumerate(manifest[name]["material_slots"]): component.set_material(index, materials[slot])


def tags(actor): return {str(tag) for tag in actor.tags}
def add_tags(actor, *values):
    current = [str(tag) for tag in actor.tags]
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(current + list(values))]
def floor_z(actor):
    origin, extent = actor.get_actor_bounds(False, False)
    return origin.z - extent.z
def hide_visual(actor):
    component = actor.get_component_by_class(unreal.PrimitiveComponent)
    if component: component.set_visibility(False, True)
    actor.set_actor_hidden_in_game(True)


actors = list(actors_api.get_all_level_actors())
carriers, stacks, fascia_visuals, failures = [], [], [], []
for actor in actors:
    actor_tags = tags(actor)
    if "carrier_position" in actor_tags:
        z = floor_z(actor)
        actor.static_mesh_component.set_static_mesh(load_mesh("SM_CA_MW_PR010_CarrierPallet_v101"))
        actor.set_actor_scale3d(unreal.Vector(1, 1, 1))
        location = actor.get_actor_location(); actor.set_actor_location(unreal.Vector(location.x, location.y, z), False, False)
        apply_materials(actor.static_mesh_component, "SM_CA_MW_PR010_CarrierPallet_v101")
        add_tags(actor, "LB.Asset.Candidate.v101", "LB.PR010.ReleaseArt.CarrierPallet")
        carriers.append(actor)
    elif "identified_blank_stack" in actor_tags or "quality_hold_stack" in actor_tags:
        z = floor_z(actor)
        actor.static_mesh_component.set_static_mesh(load_mesh("SM_CA_MW_PR010_BlankStack_Layered_v101"))
        actor.set_actor_scale3d(unreal.Vector(1, 1, 1))
        location = actor.get_actor_location(); actor.set_actor_location(unreal.Vector(location.x, location.y, z), False, False)
        apply_materials(actor.static_mesh_component, "SM_CA_MW_PR010_BlankStack_Layered_v101")
        if "quality_hold_stack" in actor_tags: actor.static_mesh_component.set_material(1, materials["CA_MW_SafetyYellow"])
        add_tags(actor, "LB.Asset.Candidate.v101", "LB.PR010.ReleaseArt.LayeredStack")
        stacks.append(actor)

# Keep exact v100/v099 fascia collision envelopes invisibly and add open visual modules.
for actor in actors:
    if "upper_fascia" not in tags(actor): continue
    z = floor_z(actor)
    hide_visual(actor)
    add_tags(actor, "LB.PR010.CollisionProxy", "LB.PR010.LegacyFascia.Hidden.v101")
    location = actor.get_actor_location()
    visual = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(location.x, location.y, z), actor.get_actor_rotation())
    visual.set_actor_label(actor.get_actor_label().replace("LB_PR010_V097_", "LB_PR010_V101_FasciaVisual_"))
    visual.tags = [unreal.Name(value) for value in ("LB.Station.PR010", "LB.Asset.Candidate.v101", "LB.Asset.CandidateNotPromoted", "LB.PR010.ReleaseArt.OpenFascia", "LB.PR010.ReleaseArt.VisualOnly")]
    visual.static_mesh_component.set_static_mesh(load_mesh("SM_CA_MW_PR010_FasciaLouvered_v101"))
    visual.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    visual.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    visual.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    apply_materials(visual.static_mesh_component, "SM_CA_MW_PR010_FasciaLouvered_v101")
    fascia_visuals.append(visual)

# Replace the cramped v100 HMI copy with a CCTV-legible information hierarchy.
for actor in actors:
    if actor.get_actor_label().startswith("LB_PR010_V100_TEXT_"):
        hide_visual(actor)
        add_tags(actor, "LB.PR010.LegacyPresentation.Hidden.v101")


def text_actor(label, value, z, size, colour):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(996, -2645, z), unreal.Rotator(yaw=-90))
    actor.set_actor_label("LB_PR010_V101_TEXT_" + label)
    actor.tags = [unreal.Name(tag) for tag in ("LB.Station.PR010", "LB.Asset.Candidate.v101", "LB.Asset.CandidateNotPromoted", "LB.Identity.Diegetic", "LB.HMI.LiveText")]
    actor.text_render.set_text(value); actor.text_render.set_world_size(size)
    actor.text_render.set_text_render_color(colour)
    actor.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    actor.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.text_render.set_editor_property("can_ever_affect_navigation", False)
    return actor


hmi_text = [
    text_actor("Corporation", "CAIRNWELL AUTOMOTIVE", 143, 4.2, unreal.Color(65, 220, 165, 255)),
    text_actor("Site", "MOORCROSS WORKS", 135, 3.2, unreal.Color(235, 240, 235, 255)),
    text_actor("Station", "PR-010  FOUR-LANE BUFFER", 123, 3.8, unreal.Color(245, 190, 45, 255)),
    text_actor("State", "REMOTE READY", 113, 3.2, unreal.Color(80, 230, 180, 255)),
    text_actor("Capacity", "8 / 8 STACK POSITIONS", 103, 2.7, unreal.Color(235, 240, 235, 255)),
]

camera = next((actor for actor in actors if actor.get_actor_label() == "LB_PR010_V098_CAM_ServiceHMI"), None)
if camera:
    camera.set_actor_location(unreal.Vector(700, -2645, 175), False, False)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(1025, -2645, 105)), False)
    camera.camera_component.set_editor_properties({"field_of_view": 38.0, "aspect_ratio": 16.0/9.0, "constrain_aspect_ratio": True})
    add_tags(camera, "LB.Camera.Fixed.PR010.v101", "LB.Asset.Candidate.v101")
else: failures.append("missing ServiceHMI camera")

light_levels = {"Infeed": 210.0, "Centre": 230.0, "Handoff": 210.0, "Service": 135.0}
adjusted_lights = []
for actor in actors:
    for label, intensity in light_levels.items():
        if actor.get_actor_label() == f"LB_PR010_V098_LIGHT_{label}":
            actor.point_light_component.set_editor_property("intensity", intensity)
            add_tags(actor, "LB.PR010.Lighting.v101")
            adjusted_lights.append({"label": label, "intensity": intensity})

if len(carriers) != 8: failures.append(f"expected 8 carriers, found {len(carriers)}")
if len(stacks) != 9: failures.append(f"expected 9 stacks, found {len(stacks)}")
if len(fascia_visuals) != 4: failures.append(f"expected 4 open fascia visuals, found {len(fascia_visuals)}")
if len(adjusted_lights) != 4: failures.append(f"expected 4 adjusted lights, found {len(adjusted_lights)}")
if len([actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR010Station)]) != 1: failures.append("native authority count changed")
if not levels.save_current_level(): failures.append("could not save v101")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

report = {"$schema": "cairnwell/audit/pr010-release-art-build-v101/v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V101_ISOLATED_CARRIER_STACK_FASCIA_LIGHTING_HMI_CORRECTION_INSTALLED__GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V101_BUILD__NOT_PROMOTED",
    "source_map": SOURCE_MAP, "map": TARGET_MAP, "asset_destination": DEST,
    "carrier_count": len(carriers), "layered_stack_count": len(stacks), "open_fascia_visual_count": len(fascia_visuals),
    "adjusted_lights": adjusted_lights, "hmi_text_count": len(hmi_text), "hmi_camera_location_cm": [700, -2645, 175],
    "retained_v100_and_v099_technical_contracts": True, "failures": failures, "promotion_authorized": False}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures: raise RuntimeError("; ".join(failures))
