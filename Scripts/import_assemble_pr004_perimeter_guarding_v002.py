"""Import and assemble the 2.4 m PR-004 perimeter guarding candidate."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/IndustrialKit/SafetyBarrier_v002"
MANIFEST = SOURCE / "safety_barrier_kit_2400_candidate_v002_manifest.json"
DEST = "/Game/LineBoss/IndustrialKit/Safety/Barrier_v002"
MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v004"
AUDIT = ROOT / "Saved/Audits/pr004_perimeter_guarding_candidate_v002.json"
PREFIX = "LB_PR004_PERIMETER_"

ASSETS = {
    100.0: "SM_LB_GuardPanel_1000x2400_v002",
    140.0: "SM_LB_GuardPanel_1400x2400_v002",
    200.0: "SM_LB_GuardPanel_2000x2400_v002",
}
POST = "SM_LB_GuardPost_2500_v002"
PERSON_GATE = "SM_LB_InterlockedGate_1400x2400_v002"
TRANSFER_GATE = "SM_LB_InterlockedSlidingGate_2400x2400_v002"
INTERLOCK = "SM_LB_GuardInterlockBox_v002"


def tags(*values):
    return [
        unreal.Name("LB.PR004.PerimeterGuarding.Candidate_v002"),
        unreal.Name("LB.Asset.Candidate.NotPromoted"),
        *(unreal.Name(value) for value in values),
    ]


if not MANIFEST.exists():
    raise RuntimeError(f"Missing safety-barrier source manifest {MANIFEST}")
source_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
if source_manifest.get("status") != "SOURCE_CANDIDATE_NOT_PROMOTED":
    raise RuntimeError(f"Unexpected source status: {source_manifest.get('status')}")

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
tasks = []
for name in [*ASSETS.values(), POST, PERSON_GATE, TRANSFER_GATE, INTERLOCK]:
    fbx = SOURCE / f"{name}.fbx"
    if not fbx.exists() or fbx.stat().st_size < 1024:
        raise RuntimeError(f"Missing or empty source FBX {fbx}")
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(fbx),
        "destination_path": DEST,
        "destination_name": name,
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
    static_data = options.get_editor_property("static_mesh_import_data")
    static_data.set_editor_properties({
        "combine_meshes": True,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": True,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)

asset_tools.import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

material_paths = {
    "yellow": "/Game/LineBoss/Materials/M_LB_SafetyYellow.M_LB_SafetyYellow",
    "dark": "/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel",
    "steel": (
        "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/"
        "M_HMI04_SS304.M_HMI04_SS304"
    ),
    "red": (
        "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/"
        "M_HMI04_Red.M_HMI04_Red"
    ),
    "green": (
        "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/"
        "M_HMI04_Green.M_HMI04_Green"
    ),
}
materials = {key: unreal.load_asset(path) for key, path in material_paths.items()}
if any(value is None for value in materials.values()):
    raise RuntimeError(f"Missing controlled guarding materials: {materials}")

meshes = {}
import_records = []
for name in [*ASSETS.values(), POST, PERSON_GATE, TRANSFER_GATE, INTERLOCK]:
    mesh = unreal.load_asset(f"{DEST}/{name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Unreal import missing {name}")
    assignments = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(
            slot.get_editor_property("imported_material_slot_name")
            or slot.get_editor_property("material_slot_name")
        )
        lower = slot_name.lower()
        selected = materials["yellow"]
        if "dark" in lower or "wire" in lower or "plate" in lower:
            selected = materials["dark"]
        elif "galvanized" in lower or "fastener" in lower or "steel" in lower:
            selected = materials["steel"]
        elif "red" in lower:
            selected = materials["red"]
        elif "green" in lower:
            selected = materials["green"]
        mesh.set_material(index, selected)
        assignments.append({"slot": slot_name, "material": selected.get_path_name()})
    body_setup = mesh.get_editor_property("body_setup")
    body_setup.set_editor_property(
        "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    )
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    bounds = mesh.get_bounding_box()
    size = [
        bounds.max.x - bounds.min.x,
        bounds.max.y - bounds.min.y,
        bounds.max.z - bounds.min.z,
    ]
    meshes[name] = mesh
    import_records.append({
        "asset": mesh.get_path_name(),
        "bounds_cm": [round(value, 3) for value in size],
        "materials": assignments,
        "collision": "COMPLEX_AS_SIMPLE_CANDIDATE__RELEASE_SIMPLE_COLLISION_REQUIRED",
    })

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load candidate map {MAP}")

for actor in actor_subsystem.get_all_level_actors():
    if actor.get_actor_label().startswith(PREFIX):
        actor_subsystem.destroy_actor(actor)

spawned = []


def spawn(name, mesh_name, location, yaw, role, movable=False):
    actor = actor_subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(*location),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw),
    )
    actor.set_actor_label(PREFIX + name)
    actor.static_mesh_component.set_static_mesh(meshes[mesh_name])
    actor.static_mesh_component.set_editor_property(
        "mobility", unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC
    )
    actor.set_editor_property("tags", tags(role))
    spawned.append({
        "actor": actor.get_actor_label(),
        "asset": meshes[mesh_name].get_path_name(),
        "location_cm": list(actor.get_actor_location().to_tuple()),
        "rotation_deg": list(actor.get_actor_rotation().to_tuple()),
        "role": role,
        "mobility": "MOVABLE" if movable else "STATIC",
    })
    return actor


panel_index = 0
post_points = set()


def tile_horizontal(start_x, end_x, y, lengths, side):
    global panel_index
    cursor = start_x
    post_points.add((round(start_x, 3), round(y, 3)))
    for length in lengths:
        panel_index += 1
        centre = cursor + length / 2.0
        spawn(
            f"Panel_{side}_{panel_index:02d}",
            ASSETS[length],
            (centre, y, 0.0),
            0.0,
            "LB.Safety.Perimeter.Panel",
        )
        cursor += length
        post_points.add((round(cursor, 3), round(y, 3)))
    if abs(cursor - end_x) > 0.01:
        raise RuntimeError(f"Horizontal tiling mismatch {side}: {cursor} != {end_x}")


def tile_vertical(x, start_y, end_y, lengths, side):
    global panel_index
    cursor = start_y
    post_points.add((round(x, 3), round(start_y, 3)))
    for length in lengths:
        panel_index += 1
        centre = cursor + length / 2.0
        spawn(
            f"Panel_{side}_{panel_index:02d}",
            ASSETS[length],
            (x, centre, 0.0),
            90.0,
            "LB.Safety.Perimeter.Panel",
        )
        cursor += length
        post_points.add((round(x, 3), round(cursor, 3)))
    if abs(cursor - end_y) > 0.01:
        raise RuntimeError(f"Vertical tiling mismatch {side}: {cursor} != {end_y}")


# Fence sits inside the fixed 1240 x 1440 cm validation envelope.  Openings
# correspond to the drawing's west crane drop, east PR-005 transfer and south
# operator access.  Every panel end receives a real bolted post.
tile_horizontal(-570.0, 570.0, -620.0, [200.0] * 5 + [140.0], "N")
tile_horizontal(-570.0, -70.0, 620.0, [200.0, 200.0, 100.0], "S_W")
tile_horizontal(70.0, 570.0, 620.0, [100.0, 200.0, 200.0], "S_E")
tile_vertical(-570.0, -620.0, -120.0, [200.0, 200.0, 100.0], "W_N")
tile_vertical(-570.0, 120.0, 620.0, [100.0, 200.0, 200.0], "W_S")
tile_vertical(570.0, -620.0, -120.0, [200.0, 200.0, 100.0], "E_N")
tile_vertical(570.0, 120.0, 620.0, [100.0, 200.0, 200.0], "E_S")

post_points.update({
    (-70.0, 620.0), (70.0, 620.0),
    (-570.0, -120.0), (-570.0, 120.0),
    (570.0, -120.0), (570.0, 120.0),
})
for index, (x, y) in enumerate(sorted(post_points), 1):
    spawn(
        f"Post_{index:02d}", POST, (x, y, 0.0), 0.0,
        "LB.Safety.Perimeter.Post",
    )

spawn(
    "Gate_Operator", PERSON_GATE, (-70.0, 620.0, 0.0), 0.0,
    "LB.Safety.Gate.Operator.Interlocked", movable=True,
)
spawn(
    "Gate_CraneDrop", TRANSFER_GATE, (-570.0, -120.0, 0.0), 90.0,
    "LB.Safety.Gate.CraneDrop.Interlocked", movable=True,
)
spawn(
    "Gate_PR005Transfer", TRANSFER_GATE, (570.0, -120.0, 0.0), 90.0,
    "LB.Safety.Gate.PR005Transfer.Interlocked", movable=True,
)

spawn("Interlock_Operator", INTERLOCK, (70.0, 620.0, 0.0), 0.0, "LB.Safety.Interlock.Operator")
spawn("Interlock_CraneDrop", INTERLOCK, (-570.0, 120.0, 0.0), 90.0, "LB.Safety.Interlock.CraneDrop")
spawn("Interlock_PR005Transfer", INTERLOCK, (570.0, 120.0, 0.0), -90.0, "LB.Safety.Interlock.PR005Transfer")

if not levels.save_current_level():
    raise RuntimeError("Could not save PR-004 candidate map after guarding assembly")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/pr004-perimeter-guarding-candidate-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CANDIDATE_ASSEMBLY_PASS__VISUAL_COLLISION_AND_INTERLOCK_GATES_REQUIRED",
    "map": MAP,
    "drawing_requirement": {
        "cell_envelope_cm": [1240.0, 1440.0, 450.0],
        "fence_height_cm": 240.0,
        "operator_gate_clear_width_cm": 140.0,
        "transfer_gate_clear_width_cm": 240.0,
    },
    "fence_rectangle_cm": {"x": [-570.0, 570.0], "y": [-620.0, 620.0]},
    "imported_modules": import_records,
    "spawned_actor_count": len(spawned),
    "panel_count": sum(item["role"] == "LB.Safety.Perimeter.Panel" for item in spawned),
    "post_count": sum(item["role"] == "LB.Safety.Perimeter.Post" for item in spawned),
    "gate_count": sum("LB.Safety.Gate" in item["role"] for item in spawned),
    "actors": spawned,
    "remaining_gates": [
        "simple release collision per post/panel/gate",
        "operator and transfer gate motion",
        "coded interlock state binding",
        "navigation obstacle rebuild",
        "swept robot/crane/transfer collision",
        "fresh fixed-camera comparison against the PR-004 Pro drawings",
    ],
    "promotion_supported": False,
}, indent=2), encoding="utf-8")
unreal.log(
    "LINE_BOSS_PR004_PERIMETER_GUARDING_V002_PASS "
    f"actors={len(spawned)} panels={panel_index} posts={len(post_points)} audit={AUDIT}"
)
