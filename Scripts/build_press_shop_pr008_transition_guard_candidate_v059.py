"""Import the measured strip transition and guard it in an isolated PR-008 v059 map."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/PR008/StripTransition/Candidate_v001"
RECORDS = json.loads(
    (SOURCE / "pr008_strip_transition_module_manifest_v001.json").read_text(encoding="utf-8")
)
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008ServoBlankingCandidate_v058"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008TransitionGuardCandidate_v059"
DEST = "/Game/LineBoss/Stations/Press/PR008/StripTransition/Candidate_v001"
PREFIX = "LB_PR008_V059_"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_transition_guard_candidate_v059.json"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

tasks = []
for record in RECORDS:
    task = unreal.AssetImportTask()
    task.set_editor_properties(
        {
            "filename": str(SOURCE / record["fbx"]),
            "destination_path": DEST,
            "destination_name": "SM_" + record["name"],
            "automated": True,
            "replace_existing": True,
            "replace_existing_settings": True,
            "save": True,
        }
    )
    options = unreal.FbxImportUI()
    options.set_editor_properties(
        {
            "import_mesh": True,
            "import_as_skeletal": False,
            "import_materials": False,
            "import_textures": False,
            "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        }
    )
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties(
        {
            "combine_meshes": True,
            "convert_scene": True,
            "convert_scene_unit": True,
            "generate_lightmap_u_vs": True,
            "auto_generate_collision": True,
            "remove_degenerates": True,
        }
    )
    task.set_editor_property("options", options)
    tasks.append(task)
tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008TransitionGuardCandidate_v059.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate v058 to v059")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v059 map")
    unreal.log("LINE_BOSS_PR008_V059_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for existing in list(actors.get_all_level_actors()):
    if existing.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(existing)

strip = library.load_asset(
    "/Game/LineBoss/Stations/Press/PR008/Candidate_v001/Materials/M_PR008_StripSteel_v001"
)
worked = library.load_asset(
    "/Game/LineBoss/Stations/Press/PR008/Candidate_v001/Materials/M_PR008_WorkedSteel_v001"
)
dark = library.load_asset(
    "/Game/LineBoss/Stations/Press/PR008/Candidate_v001/Materials/M_PR008_FoundryCharcoal_v001"
)
yellow = library.load_asset(
    "/Game/LineBoss/Stations/Press/PR008/Candidate_v001/Materials/M_PR008_SafetyYellow_v001"
)
if not all((strip, worked, dark, yellow)):
    raise RuntimeError("Missing controlled PR-008 materials")

created = []
for record in RECORDS:
    mesh = library.load_asset(f"{DEST}/SM_{record['name']}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing transition mesh {record['name']}")
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*record["location_cm"]), unreal.Rotator()
    )
    actor.set_actor_label(PREFIX + record["name"])
    actor.tags = [
        unreal.Name("LB.Asset.Candidate.v059"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Station.PR008"),
        unreal.Name("LB.Process.StripContinuity"),
    ]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_mobility(
        unreal.ComponentMobility.MOVABLE
        if record["role"] == "support_roll"
        else unreal.ComponentMobility.STATIC
    )
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(
            slot.get_editor_property("imported_material_slot_name")
            or slot.get_editor_property("material_slot_name")
        ).lower()
        chosen = (
            yellow
            if "yellow" in slot_name
            else dark
            if "charcoal" in slot_name
            else worked
            if "roller" in slot_name
            else strip
        )
        component.set_material(index, chosen)
    no_collision = record["role"] == "strip_transition"
    component.set_collision_enabled(
        unreal.CollisionEnabled.NO_COLLISION
        if no_collision
        else unreal.CollisionEnabled.QUERY_AND_PHYSICS
    )
    component.set_collision_profile_name(unreal.Name("NoCollision" if no_collision else "BlockAll"))
    component.set_editor_property("can_ever_affect_navigation", False)
    created.append(actor)

guard_root = "/Game/LineBoss/IndustrialKit/Safety/Barrier_v002"
panel = library.load_asset(guard_root + "/SM_LB_GuardPanel_2000x2400_v002")
post = library.load_asset(guard_root + "/SM_LB_GuardPost_2500_v002")
if not panel or not post:
    raise RuntimeError("Approved open-mesh safety-barrier kit is missing")

guards = []


def guard(label, mesh, location):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = [
        unreal.Name("LB.Asset.Candidate.v059"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Station.PR008"),
        unreal.Name("LB.Safety.OpenMeshGuard"),
    ]
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name(unreal.Name("BlockAll"))
    component.set_editor_property("can_ever_affect_navigation", True)
    guards.append(actor)


for side, y in (("Operator", -2215.0), ("Drive", -1785.0)):
    for x in (-1245.0, -1045.0):
        guard(f"TransitionGuard_{side}_{int(x)}", panel, (x, y, 0.0))
    for x in (-1345.0, -1145.0, -945.0):
        guard(f"TransitionPost_{side}_{int(x)}", post, (x, y, 0.0))


def camera(label, location, target, fov):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [
        unreal.Name("LB.Camera.Validation"),
        unreal.Name("LB.Camera.Fixed.PR008.v059"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False
    )
    actor.camera_component.set_editor_properties(
        {"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True}
    )
    return actor


cameras = [
    camera("TransitionOperator", (-1750, -3150, 390), (-1170, -2000, 118), 50),
    camera("TransitionElevated", (-1950, -3400, 780), (-1000, -2000, 125), 57),
    camera("ConnectedLine", (-3400, -4400, 1120), (-1150, -2000, 135), 62),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-transition-guard-candidate-v059/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "DIMENSIONED_STRIP_TRANSITION_AND_LOCAL_OPEN_MESH_GUARD_ASSEMBLY_PASS__RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "source": str(SOURCE),
    "transition_module_count": len(created),
    "strip_width_cm": 150.0,
    "longitudinal_gap_closed_cm": 305.0,
    "vertical_fall_cm": 2.5,
    "support_count": 3,
    "open_mesh_panel_count": 4,
    "guard_post_count": 6,
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "hmi_included": False,
    "native_runtime_controller_included": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_PR008_V059_BUILD_PASS transition_modules={len(created)} guards={len(guards)}"
)
unreal.SystemLibrary.quit_editor()
