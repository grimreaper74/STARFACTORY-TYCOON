"""Import and install the dimensioned PR-010 four-lane blockout in isolated v097."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/PR010/FourLaneBuffer/Blockout_v001"
MANIFEST = json.loads((SOURCE / "PR010_BLOCKOUT_MANIFEST_v001.json").read_text(encoding="utf-8"))
SOURCE_AUDIT = json.loads((ROOT / "Saved/Audits/PR010_Blockout/pr010_dimensioned_source_v001.json").read_text(encoding="utf-8"))
TARGET = "/Game/LineBoss/Maps/LB_PressShop_PR010BlockoutCandidate_v097"
DEST = "/Game/LineBoss/Candidates/PressShop/PR010/Blockout_v001"
PREFIX = "LB_PR010_V097_"
OUT = ROOT / "Saved/Audits/PR010_Blockout/pr010_unreal_blockout_build_v097.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

if not str(SOURCE_AUDIT.get("status", "")).startswith("PASS"):
    raise RuntimeError("PR-010 source audit has not passed")

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def import_static(path, name):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(path), "destination_path": DEST, "destination_name": name,
        "automated": True, "replace_existing": True, "replace_existing_settings": True, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": False,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "generate_lightmap_u_vs": True, "auto_generate_collision": True, "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])


for row in MANIFEST["assets"]:
    import_static(SOURCE / row["file"], row["asset"])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

if not levels.load_level(TARGET): raise RuntimeError(TARGET)
for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX): actors_api.destroy_actor(actor)

pr009_material_root = "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials"
material_paths = {
    "CairnwellGreen": f"{pr009_material_root}/M_CA_MW_PR009_LayeredCairnwellGreen_v085",
    "FoundryCharcoal": f"{pr009_material_root}/M_CA_MW_PR009_LayeredFoundryCharcoal_v085",
    "SafetyYellow": f"{pr009_material_root}/M_CA_MW_PR009_LayeredSafetyYellow_v085",
    "ServiceGrey": f"{pr009_material_root}/M_CA_MW_PR009_LayeredServiceGrey_v085",
    "WorkedSteel": f"{pr009_material_root}/M_CA_MW_PR009_MachinedSteel_v085",
    "BlankSteel": f"{pr009_material_root}/M_CA_MW_PR009_OiledBlankSteel_v085",
    "StatusGreen": f"{pr009_material_root}/M_CA_MW_PR009_HMIScreenOnline_v085",
    "StatusAmber": f"{pr009_material_root}/M_CA_MW_PR009_AmberSafetyActive_v085",
    "Glass": f"{pr009_material_root}/M_CA_MW_PR009_SensorGlass_v085",
}
materials = {key: library.load_asset(value) for key, value in material_paths.items()}
if any(value is None for value in materials.values()): raise RuntimeError("Missing shared Press Shop materials")


def local_to_world(local_mm):
    x, y, z = local_mm
    return unreal.Vector(1350.0 + y / 10.0, -2000.0 - x / 10.0, z / 10.0)


moving_tags = {"moving_infeed_shuttle", "moving_carrier_roller", "moving_stop_pin", "moving_reservation_gate", "moving_quality_spur"}
spawned = []
world_rows = []
for row in MANIFEST["placements"]:
    mesh = library.load_asset(f"{DEST}/{row['asset']}")
    if not isinstance(mesh, unreal.StaticMesh): raise RuntimeError(f"Missing imported mesh {row['asset']}")
    location = local_to_world(row["location_mm"])
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator(yaw=-90.0))
    actor.set_actor_label(PREFIX + row["object"])
    tags = list(row["tags"]) + ["LB.Station.PR010", "LB.Asset.Candidate.v097", "LB.Asset.CandidateNotPromoted", "LB.Control.ControlRoomOnly"]
    actor.tags = [unreal.Name(value) for value in tags]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    material_key = MANIFEST["asset_specs"][row["asset"]]["material"]
    component.set_material(0, materials[material_key])
    movable = bool(moving_tags.intersection(row["tags"]))
    component.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    spawned.append(actor)
    world_rows.append({"label": actor.get_actor_label(), "location_cm": [location.x, location.y, location.z], "tags": row["tags"]})


def text_actor(label, text, location, yaw, size, colour):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=yaw))
    actor.set_actor_label(PREFIX + "TEXT_" + label)
    actor.tags = [unreal.Name(value) for value in ("LB.Station.PR010", "LB.Identity.Diegetic", "LB.Asset.Candidate.v097", "LB.Asset.CandidateNotPromoted")]
    actor.text_render.set_text(text)
    actor.text_render.set_world_size(size)
    actor.text_render.set_text_render_color(colour)
    actor.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    actor.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.text_render.set_editor_property("can_ever_affect_navigation", False)
    return actor


identity = [
    text_actor("Corporation", "CAIRNWELL AUTOMOTIVE", (1110, -2690, 275), -90.0, 6.0, unreal.Color(45, 160, 120, 255)),
    text_actor("Site", "MOORCROSS WORKS", (1110, -2690, 254), -90.0, 4.8, unreal.Color(220, 225, 220, 255)),
    text_actor("Station", "PR-010  FOUR-LANE BLANK BUFFER", (1110, -2690, 235), -90.0, 3.6, unreal.Color(235, 180, 35, 255)),
]


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name(value) for value in ("LB.Camera.Validation", "LB.Camera.Fixed.PR010.v097", "LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    return actor


cameras = [
    camera("Overview", (2320, -3250, 760), (1370, -2000, 105), 60),
    camera("Infeed", (650, -3300, 500), (1030, -2000, 120), 58),
    camera("LaneHandoff", (2180, -950, 500), (1650, -2000, 110), 56),
    camera("Elevated", (2550, -3300, 1250), (1400, -2000, 90), 62),
]

if not levels.save_current_level(): raise RuntimeError("Could not save PR-010 v097 blockout")

lane_beds = [row for row in world_rows if "lane_bed" in row["tags"]]
carriers = [row for row in world_rows if "carrier_position" in row["tags"]]
shuttle = [row for row in world_rows if "moving_infeed_shuttle" in row["tags"]]
failures = []
if len(spawned) != 142: failures.append(f"expected 142 blockout actors, found {len(spawned)}")
if len(lane_beds) != 4: failures.append(f"expected four lane beds, found {len(lane_beds)}")
if len(carriers) != 8: failures.append(f"expected eight carrier positions, found {len(carriers)}")
if len(shuttle) != 1 or abs(shuttle[0]["location_cm"][0] - 1020.0) > 0.01: failures.append("infeed shuttle world-X handoff mismatch")
if len([actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label().startswith(PREFIX + "Station")]):
    failures.append("unexpected invented native PR-010 station authority")

result = {
    "$schema": "cairnwell/audit/pr010-unreal-blockout-build-v097/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V097_DIMENSIONED_UNREAL_BLOCKOUT__VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V097_BLOCKOUT__NOT_PROMOTED",
    "map": TARGET,
    "parent": "/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v096",
    "actor_count": len(spawned),
    "lane_bed_count": len(lane_beds),
    "carrier_position_count": len(carriers),
    "shuttle_world_x_cm": shuttle[0]["location_cm"][0] if shuttle else None,
    "camera_count": len(cameras),
    "identity_count": len(identity),
    "press_train_datums": "TBC_NOT_INVENTED",
    "collision_navigation_state": "BLOCKOUT_NO_COLLISION_NAVIGATION_NEUTRAL",
    "failures": failures,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR010_V097 {result['status']} {OUT}")
if failures: raise RuntimeError("; ".join(failures))
