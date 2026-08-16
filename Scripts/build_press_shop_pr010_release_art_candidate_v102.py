"""Create isolated PR-010 v102 service-deck, identity and live-HMI candidate."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v101"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v102"
SOURCE = ROOT / "SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v102"
MANIFEST = json.loads((SOURCE / "PR010_RELEASE_ART_MANIFEST_v102.json").read_text(encoding="utf-8"))
SOURCE_AUDIT = json.loads((ROOT / "Saved/Audits/PR010_ReleaseArt_v102/pr010_release_art_source_audit_v102.json").read_text(encoding="utf-8"))
DEST = "/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v102"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v102/pr010_release_art_build_v102.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
if not str(SOURCE_AUDIT.get("status", "")).startswith("PASS"): raise RuntimeError("v102 source audit has not passed")

library = unreal.EditorAssetLibrary; asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET_MAP): raise RuntimeError(f"Refusing to overwrite {TARGET_MAP}")
if not library.duplicate_asset(SOURCE_MAP, TARGET_MAP): raise RuntimeError("v102 map duplication failed")
if not library.save_asset(TARGET_MAP, only_if_is_dirty=False): raise RuntimeError("v102 duplicated map save failed")


def import_static(row):
    task = unreal.AssetImportTask(); task.set_editor_properties({"filename": str(SOURCE / row["file"]), "destination_path": DEST,
        "destination_name": row["asset"], "automated": True, "replace_existing": True, "replace_existing_settings": True, "save": True})
    options = unreal.FbxImportUI(); options.set_editor_properties({"import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH})
    data = options.get_editor_property("static_mesh_import_data"); data.set_editor_properties({"combine_meshes": True,
        "convert_scene": True, "convert_scene_unit": True, "generate_lightmap_u_vs": True, "auto_generate_collision": False, "remove_degenerates": True})
    task.set_editor_property("options", options); asset_tools.import_asset_tasks([task])


for row in MANIFEST["assets"]: import_static(row)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.load_level(TARGET_MAP): raise RuntimeError(TARGET_MAP)

material_root = "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials"
paths = {"CA_MW_CairnwellGreen": f"{material_root}/M_CA_MW_PR009_LayeredCairnwellGreen_v085",
    "CA_MW_SafetyYellow": f"{material_root}/M_CA_MW_PR009_LayeredSafetyYellow_v085",
    "CA_MW_FoundryCharcoal": f"{material_root}/M_CA_MW_PR009_LayeredFoundryCharcoal_v085",
    "CA_MW_ServiceGrey": f"{material_root}/M_CA_MW_PR009_LayeredServiceGrey_v085",
    "CA_MW_WorkedSteel": f"{material_root}/M_CA_MW_PR009_MachinedSteel_v085",
    "CA_MW_ScreenOnline": f"{material_root}/M_CA_MW_PR009_HMIScreenOnline_v085",
    "CA_MW_SensorGlass": f"{material_root}/M_CA_MW_PR009_SensorGlass_v085"}
materials = {name: library.load_asset(path) for name, path in paths.items()}
if any(value is None for value in materials.values()): raise RuntimeError("missing shared Press Shop material")
rows = {row["asset"]: row for row in MANIFEST["assets"]}; cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")


def mesh(name):
    value = library.load_asset(f"{DEST}/{name}")
    if not isinstance(value, unreal.StaticMesh): raise RuntimeError(f"missing imported mesh {name}")
    return value
def apply_materials(component, name):
    for index, slot in enumerate(rows[name]["material_slots"]): component.set_material(index, materials[slot])
def local_to_world(local_mm):
    x, y, z = local_mm; return unreal.Vector(1350.0 + y/10.0, -2000.0 - x/10.0, z/10.0)
def actor_tags(actor): return {str(tag) for tag in actor.tags}
def add_tags(actor, *values):
    current = [str(tag) for tag in actor.tags]; actor.tags = [unreal.Name(value) for value in dict.fromkeys(current + list(values))]
def hide_visual(actor):
    component = actor.get_component_by_class(unreal.PrimitiveComponent)
    if component: component.set_visibility(False, True)
    actor.set_actor_hidden_in_game(True)


def visual_actor(label, asset_name, local_mm, semantic):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, local_to_world(local_mm), unreal.Rotator(yaw=-90))
    actor.set_actor_label("LB_PR010_V102_" + label)
    actor.tags = [unreal.Name(value) for value in ("LB.Station.PR010", "LB.Asset.Candidate.v102", "LB.Asset.CandidateNotPromoted", semantic, "LB.PR010.ReleaseArt.Visual")]
    actor.static_mesh_component.set_static_mesh(mesh(asset_name)); actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision")); actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    apply_materials(actor.static_mesh_component, asset_name); return actor


def collision_proxy(label, local_centre_mm, dims_mm, semantic):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, local_to_world(local_centre_mm), unreal.Rotator(yaw=-90))
    actor.set_actor_label("LB_PR010_V102_COLLISION_" + label)
    actor.tags = [unreal.Name(value) for value in ("LB.Station.PR010", "LB.Asset.Candidate.v102", "LB.Asset.CandidateNotPromoted", "LB.PR010.CollisionProxy", semantic)]
    actor.static_mesh_component.set_static_mesh(cube); actor.static_mesh_component.set_world_scale3d(unreal.Vector(dims_mm[0]/1000, dims_mm[1]/1000, dims_mm[2]/1000))
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS); actor.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"))
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False); actor.static_mesh_component.set_visibility(False, True); actor.set_actor_hidden_in_game(True)
    return actor


actors = list(actors_api.get_all_level_actors()); failures = []
for actor in actors:
    if "LB.PR010.ReleaseArt.OpenFascia" in actor_tags(actor):
        hide_visual(actor); add_tags(actor, "LB.PR010.LegacyFascia.Hidden.v102")

sections, proxies = [], []
for index, local_x in enumerate((-4800, -1600, 1600, 4800), start=1):
    sections.extend([
        visual_actor(f"UpperServiceHousing_{index}", "SM_CA_MW_PR010_UpperServiceHousingSection_v102", (local_x, -3580, 2200), "LB.PR010.ServiceDeck.Housing"),
        visual_actor(f"ServiceWalkway_{index}", "SM_CA_MW_PR010_ServiceWalkwayRailSection_v102", (local_x, -2500, 1950), "LB.PR010.ServiceDeck.Walkway"),
        visual_actor(f"RoofDrive_{index}", "SM_CA_MW_PR010_RoofDrivePod_v102", (local_x, -3800, 3100), "LB.PR010.ServiceDeck.Drive"),
        visual_actor(f"RoofRoute_{index}", "SM_CA_MW_PR010_RoofUtilityRoute_v102", (local_x, -3200, 3100), "LB.PR010.ServiceDeck.Routing"),
    ])
    proxies.extend([
        collision_proxy(f"Housing_{index}", (local_x, -3580, 2650), (2900, 1240, 900), "service_side"),
        collision_proxy(f"WalkwayDeck_{index}", (local_x, -2500, 2000), (2900, 900, 100), "service_side"),
        collision_proxy(f"WalkwayRail_{index}", (local_x, -2922, 2600), (2900, 55, 1100), "service_side"),
        collision_proxy(f"RoofDrive_{index}", (local_x, -3800, 3300), (1200, 800, 400), "service_side"),
        collision_proxy(f"RoofRoute_{index}", (local_x, -3200, 3225), (2900, 500, 250), "service_side"),
    ])

# Preserve the accepted pylon blockers; replace only their visible blockout presentation.
pylon_visuals, pylon_text = [], []
lane_rows = (("A", -4500), ("B", -1500), ("C", 1500), ("D", 4500))
for lane, local_x in lane_rows:
    old = next((actor for actor in actors if "lane_identity" in actor_tags(actor) and f"lane_{lane}" in actor_tags(actor)), None)
    if old is None: failures.append(f"missing lane {lane} identity proxy"); continue
    hide_visual(old); add_tags(old, "LB.PR010.CollisionProxy", "LB.PR010.LegacyPylon.Hidden.v102")
    pylon_visuals.append(visual_actor(f"Lane{lane}_IdentityPylon", "SM_CA_MW_PR010_IDPylonDetailed_v102", (local_x, 0, 0), "LB.PR010.LaneIdentity.Detailed"))
    world_y = -2000.0 - local_x/10.0
    for suffix, value, x, z, size, colour in (
        ("Lane", f"LANE {lane}", 1314.0, 118.0, 5.2, unreal.Color(20, 35, 32, 255)),
        ("Feed", f"TRAIN {lane} FEED", 1313.0, 165.0, 3.5, unreal.Color(235, 240, 235, 255))):
        text = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(x, world_y, z), unreal.Rotator(yaw=180))
        text.set_actor_label(f"LB_PR010_V102_TEXT_Pylon_{lane}_{suffix}"); text.tags = [unreal.Name(v) for v in ("LB.Station.PR010", "LB.Asset.Candidate.v102", "LB.Asset.CandidateNotPromoted", "LB.Identity.Diegetic", "LB.PR010.LaneIdentity.Text")]
        text.text_render.set_text(value); text.text_render.set_world_size(size); text.text_render.set_text_render_color(colour)
        text.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER); text.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); text.text_render.set_editor_property("can_ever_affect_navigation", False)
        pylon_text.append(text)

# Unique fixed-position traceability plates; gameplay stack identity remains native/saveable.
stack_text = []
lane_counts = {lane: 0 for lane, _ in lane_rows}
for actor in actors:
    tags = actor_tags(actor)
    if "identified_blank_stack" not in tags and "quality_hold_stack" not in tags: continue
    if "quality_hold_stack" in tags:
        value = "QH  HOLD-01"
    else:
        lane = next((name for name, _ in lane_rows if f"lane_{name}" in tags), "X")
        lane_counts[lane] += 1; value = f"{lane}{lane_counts[lane]}  MW-010-{lane}{lane_counts[lane]:02d}"
    origin, extent = actor.get_actor_bounds(False, False); location = actor.get_actor_location()
    text = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(location.x-86.0, location.y, origin.z-extent.z+27.5), unreal.Rotator(yaw=180))
    text.set_actor_label("LB_PR010_V102_TEXT_StackID_" + value.replace(" ", "_")); text.tags = [unreal.Name(v) for v in ("LB.Station.PR010", "LB.Asset.Candidate.v102", "LB.Asset.CandidateNotPromoted", "LB.Identity.Traceability", "LB.PR010.StackPositionID")]
    text.text_render.set_text(value); text.text_render.set_world_size(3.0); text.text_render.set_text_render_color(unreal.Color(20, 35, 32, 255))
    text.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER); text.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); text.text_render.set_editor_property("can_ever_affect_navigation", False)
    stack_text.append(text)

station_list = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR010Station)]
if len(station_list) != 1: failures.append(f"expected one native station, found {len(station_list)}")
live_bindings = []
if len(station_list) == 1:
    for field, label in (("State", "LB_PR010_V101_TEXT_State"), ("Capacity", "LB_PR010_V101_TEXT_Capacity")):
        text = next((actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label), None)
        if text and station_list[0].bind_hmi_text_actor(unreal.Name(field), text): live_bindings.append({"field": field, "actor": label})
        else: failures.append(f"could not bind live HMI field {field}")

if len(sections) != 16 or len(proxies) != 20: failures.append(f"service deck count mismatch visuals={len(sections)} proxies={len(proxies)}")
if len(pylon_visuals) != 4 or len(pylon_text) != 8: failures.append("pylon presentation count mismatch")
if len(stack_text) != 9: failures.append(f"expected nine stack labels, found {len(stack_text)}")
if len(live_bindings) != 2: failures.append(f"expected two live HMI bindings, found {len(live_bindings)}")
if not levels.save_current_level(): failures.append("could not save v102")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
report = {"$schema": "cairnwell/audit/pr010-release-art-build-v102/v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V102_ISOLATED_SERVICE_DECK_PYLON_TRACEABILITY_LIVE_HMI_INSTALLED__GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V102_BUILD__NOT_PROMOTED",
    "source_map": SOURCE_MAP, "map": TARGET_MAP, "asset_destination": DEST, "service_deck_visual_count": len(sections),
    "new_collision_proxy_count": len(proxies), "detailed_pylon_count": len(pylon_visuals), "pylon_text_count": len(pylon_text),
    "stack_position_id_count": len(stack_text), "live_hmi_bindings": live_bindings,
    "station_envelope_mm": [14000, 8400, 3600], "press_train_datums": "TBC_NOT_INVENTED",
    "failures": failures, "promotion_authorized": False}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8"); print(json.dumps(report, indent=2))
if failures: raise RuntimeError("; ".join(failures))
