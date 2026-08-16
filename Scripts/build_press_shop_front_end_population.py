"""Populate the Press Shop front end with candidate coils, cranes and floor paint.

This is an idempotent visual-integration layer on the existing candidate map.
Nothing created here is promoted to the production asset library by this script.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v002"
PREFIX = "LB_INT_FRONT_"
ROOT = Path(unreal.Paths.project_dir())
AUDIT = ROOT / "Saved/Audits/press_shop_front_end_population_v002.json"
MASTER_ANCHORS_PATH = ROOT / "Content/LineBoss/Data/press_shop_master_plan_anchors_v001.json"
MASTER_LAYOUT = json.loads(MASTER_ANCHORS_PATH.read_text(encoding="utf-8"))
STATION_ANCHORS = {
    item["id"]: tuple(float(value) for value in item["world_cm"])
    for item in MASTER_LAYOUT["stations"]
}


def station_pos(station_id, dx=0.0, dy=0.0, z=0.0):
    """Return a proposal-aligned Unreal position from a station-local offset."""
    anchor = STATION_ANCHORS[station_id]
    return (anchor[0] + dx, anchor[1] + dy, anchor[2] + z)


COIL_ASSET = (
    "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/"
    "SM_LB_MasterCoil_Candidate_v002.SM_LB_MasterCoil_Candidate_v002"
)
SADDLE_ASSET = (
    "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilSaddle/"
    "SM_LB_CoilSaddle_Candidate_v001.SM_LB_CoilSaddle_Candidate_v001"
)
CUBE = "/Engine/BasicShapes/Cube.Cube"
CYLINDER = "/Engine/BasicShapes/Cylinder.Cylinder"
CRANE_ASSETS = {
    "girder": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/"
        "SM_LB_Crane_BridgeGirder_4500_v001.SM_LB_Crane_BridgeGirder_4500_v001"
    ),
    "end_truck": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/"
        "SM_LB_Crane_EndTruck_v001.SM_LB_Crane_EndTruck_v001"
    ),
    "trolley": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/"
        "SM_LB_Crane_Trolley_v001.SM_LB_Crane_Trolley_v001"
    ),
    "hoist_block": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/"
        "SM_LB_Crane_HoistBlock_v001.SM_LB_Crane_HoistBlock_v001"
    ),
    "c_hook": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/"
        "SM_LB_Crane_CHook_v001.SM_LB_Crane_CHook_v001"
    ),
    "runway": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/"
        "SM_LB_Crane_RunwayBeam_3000_v001.SM_LB_Crane_RunwayBeam_3000_v001"
    ),
    "column": (
        "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/"
        "SM_LB_Crane_Column_14300_v001.SM_LB_Crane_Column_14300_v001"
    ),
}
VENDOR_ASSETS = {
    "lamp": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Lamp01.SM_Lamp01",
    "cable_set": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_CableSet_01.SM_CableSet_01",
    "cables": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Cables01.SM_Cables01",
    "electrical_cable": (
        "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/"
        "SM_ElectricalCable_01.SM_ElectricalCable_01"
    ),
    "pipe_long": (
        "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/"
        "SM_Pipe_round_long.SM_Pipe_round_long"
    ),
    "pipe_corner": (
        "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/"
        "SM_Pipe_round_corner1.SM_Pipe_round_corner1"
    ),
    "beam": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_MetalBeam01.SM_MetalBeam01",
    "motor": (
        "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/Crane/"
        "SM_ElectricMotor01.SM_ElectricMotor01"
    ),
}
DRESSING_ROOT = "/Game/LineBoss/IndustrialKit/PressShop/FrontEndDressing"
DRESSING_ASSETS = {
    "service_cabinet": f"{DRESSING_ROOT}/SM_LB_ServiceCabinet_1800_v001.SM_LB_ServiceCabinet_1800_v001",
    "trench_grate": f"{DRESSING_ROOT}/SM_LB_FloorTrenchGrate_1000_v001.SM_LB_FloorTrenchGrate_1000_v001",
    "bollard": f"{DRESSING_ROOT}/SM_LB_SafetyBollard_1000_v001.SM_LB_SafetyBollard_1000_v001",
    "inspection_mast": f"{DRESSING_ROOT}/SM_LB_InspectionMast_3000_v001.SM_LB_InspectionMast_3000_v001",
    "prep_bench": f"{DRESSING_ROOT}/SM_LB_PackagingPrepBench_2400_v001.SM_LB_PackagingPrepBench_2400_v001",
    "recovery_bin": f"{DRESSING_ROOT}/SM_LB_PackagingRecoveryBin_v001.SM_LB_PackagingRecoveryBin_v001",
    "estop": f"{DRESSING_ROOT}/SM_LB_EStopPedestal_1300_v001.SM_LB_EStopPedestal_1300_v001",
}
SAFETY_BARRIER_ASSETS = {
    "panel": (
        "/Game/LineBoss/IndustrialKit/Safety/Barrier/"
        "SM_LB_GuardPanel_2000_v001.SM_LB_GuardPanel_2000_v001"
    ),
    "post": (
        "/Game/LineBoss/IndustrialKit/Safety/Barrier/"
        "SM_LB_GuardPost_1500_v001.SM_LB_GuardPost_1500_v001"
    ),
    "gate": (
        "/Game/LineBoss/IndustrialKit/Safety/Barrier/"
        "SM_LB_InterlockedGate_1200_v001.SM_LB_InterlockedGate_1200_v001"
    ),
    "interlock": (
        "/Game/LineBoss/IndustrialKit/Safety/Barrier/"
        "SM_LB_GuardInterlockBox_v001.SM_LB_GuardInterlockBox_v001"
    ),
}
HMI_ROOT = "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling"
HMI_MODULES = (
    "SM_LB_HMI04_CabinetBody",
    "SM_LB_HMI04_DisplaySurface",
    "SM_LB_HMI04_ControlPower",
    "SM_LB_HMI04_ModeSelector",
    "SM_LB_HMI04_ResetButton",
    "SM_LB_HMI04_CycleStartButton",
    "SM_LB_HMI04_EmergencyStop",
    "SM_LB_HMI04_StackRed",
    "SM_LB_HMI04_StackAmber",
    "SM_LB_HMI04_StackGreen",
)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
levels.load_level(MAP)

for old_actor in actor_system.get_all_level_actors():
    if old_actor.get_actor_label().startswith(PREFIX):
        actor_system.destroy_actor(old_actor)


def material(asset_name):
    path = f"/Game/LineBoss/Materials/{asset_name}.{asset_name}"
    value = unreal.load_asset(path)
    if value is None:
        raise RuntimeError(f"Missing foundation material {path}")
    return value


MATS = {
    "concrete": material("M_LB_FactoryConcrete"),
    "dark": material("M_LB_StructureSteel"),
    "charcoal": material("M_LB_ShellCharcoal"),
    "yellow": material("M_LB_SafetyYellow"),
    "blue": material("M_LB_Zone_PRESS_RECEIVING"),
    "green": material("M_LB_Zone_PRESS_COIL_STORE"),
    "grey": material("M_LB_Zone_PRESS_FRONT_END"),
    "orange": material("M_LB_Zone_PRESS_LOGISTICS"),
}
FRONT_END_MATERIAL_ROOT = "/Game/LineBoss/Materials/FrontEnd"
for key, asset_name in {
    "floor_neutral": "MI_LB_Floor_Neutral",
    "floor_pr001": "MI_LB_Floor_PR001_Blue",
    "floor_pr002": "MI_LB_Floor_PR002_Orange",
    "floor_hold": "MI_LB_Floor_Hold_Red",
    "floor_pr003": "MI_LB_Floor_PR003_BlueGreen",
    "floor_pr004": "MI_LB_Floor_PR004_Grey",
    "floor_walkway": "MI_LB_Floor_Walkway_Green",
    "wall_concrete": "MI_LB_Wall_Concrete",
    "wall_service": "MI_LB_Wall_DarkService",
}.items():
    value = unreal.load_asset(f"{FRONT_END_MATERIAL_ROOT}/{asset_name}.{asset_name}")
    if value is None:
        raise RuntimeError(f"Missing front-end release material candidate {asset_name}")
    MATS[key] = value
MATS["vendor_column"] = unreal.load_asset(
    "/Game/LineBoss/Vendor/FactoryEnvironment/Materials/MI_Column_Painted_01.MI_Column_Painted_01"
)
MATS["vendor_pipe"] = unreal.load_asset(
    "/Game/LineBoss/Vendor/FactoryEnvironment/Materials/MI_Round_Pipes_01.MI_Round_Pipes_01"
)
MATS["vendor_cable"] = unreal.load_asset(
    "/Game/LineBoss/Vendor/FactoryEnvironment/Materials/MI_Cables.MI_Cables"
)
MATS["vendor_glass"] = unreal.load_asset(
    "/Game/LineBoss/Vendor/FactoryEnvironment/Materials/MI_Glass03.MI_Glass03"
)
if any(MATS[key] is None for key in ("vendor_column", "vendor_pipe", "vendor_cable", "vendor_glass")):
    raise RuntimeError("Missing curated vendor support material")
MATS["red"] = unreal.load_asset(
    "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003/Materials/"
    "M_HMI04_Red.M_HMI04_Red"
)
if MATS["red"] is None:
    raise RuntimeError("Missing controlled safety-red material for HOLD/NCR zone")


def tags(*values):
    return [unreal.Name(value) for value in values]


def spawn_mesh(
    label,
    mesh_path,
    location,
    scale=(1, 1, 1),
    rotation=(0, 0, 0),
    mat=None,
    actor_tags=(),
    mobility=unreal.ComponentMobility.STATIC,
):
    actor = actor_system.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(*location),
        unreal.Rotator(rotation[0], rotation[1], rotation[2]),
    )
    actor.set_actor_label(PREFIX + label)
    component = actor.get_editor_property("static_mesh_component")
    mesh = unreal.load_asset(mesh_path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing static mesh {mesh_path}")
    component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    if mat is not None:
        component.set_material(0, mat)
    component.set_editor_property("mobility", mobility)
    actor.set_editor_property("tags", tags("LB.Integration.PressShop", "LB.Asset.Candidate.v001", *actor_tags))
    return actor


def cube(
    label, location, size_cm, mat, actor_tags=(), rotation=(0, 0, 0),
    mobility=unreal.ComponentMobility.STATIC,
):
    return spawn_mesh(
        label, CUBE, location,
        (size_cm[0] / 100.0, size_cm[1] / 100.0, size_cm[2] / 100.0),
        rotation, mat, actor_tags, mobility,
    )


def cylinder(
    label, location, size_cm, mat, actor_tags=(), rotation=(0, 0, 0),
    mobility=unreal.ComponentMobility.STATIC,
):
    # Engine cylinder is 100 cm diameter and 100 cm high along local Z.
    return spawn_mesh(
        label, CYLINDER, location,
        (size_cm[0] / 100.0, size_cm[0] / 100.0, size_cm[1] / 100.0),
        rotation, mat, actor_tags, mobility,
    )


created_by_type = {}


def count(kind, amount=1):
    created_by_type[kind] = created_by_type.get(kind, 0) + amount


def spawn_text(
    label,
    text,
    location,
    rotation=(0.0, 0.0, 0.0),
    world_size=42.0,
    colour=unreal.Color(225, 230, 232, 255),
    actor_tags=(),
):
    """Spawn deterministic station signage without baking text into hero meshes."""
    actor = actor_system.spawn_actor_from_class(
        unreal.TextRenderActor,
        unreal.Vector(*location),
        unreal.Rotator(roll=rotation[0], pitch=rotation[1], yaw=rotation[2]),
    )
    actor.set_actor_label(PREFIX + label)
    component = actor.get_editor_property("text_render")
    component.set_text(text)
    component.set_world_size(world_size)
    component.set_text_render_color(colour)
    try:
        component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
        component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    except Exception:
        pass
    actor.set_editor_property(
        "tags",
        tags("LB.Integration.PressShop", "LB.Asset.Candidate.v001", "LB.Module.Signage", *actor_tags),
    )
    count("text_signs")
    return actor


def add_station_wall_sign(label, station_id, title, x, width_cm):
    cube(
        f"{label}_Backplate", (x, -5866, 1190), (width_cm, 10, 150), MATS["charcoal"],
        ("LB.Module.StationSign", f"LB.Station.{station_id}"),
    )
    spawn_text(
        f"{label}_ID", station_id, (x, -5858, 1228), rotation=(0, 0, 90),
        world_size=52, colour=unreal.Color(240, 182, 35, 255),
        actor_tags=(f"LB.Station.{station_id}",),
    )
    spawn_text(
        f"{label}_Title", title, (x, -5858, 1174), rotation=(0, 0, 90),
        world_size=23, colour=unreal.Color(225, 230, 232, 255),
        actor_tags=(f"LB.Station.{station_id}",),
    )
    count("station_wall_signs")


def add_hmi(hmi_id, x, y, yaw, station):
    """Assemble the shared cross-shop HMI from its validated modular pieces."""
    for module in HMI_MODULES:
        interaction_tag = "LB.Interaction.HMI"
        if "EmergencyStop" in module:
            interaction_tag = "LB.Interaction.EStop"
        elif "DisplaySurface" in module:
            interaction_tag = "LB.Interaction.HMI.Screen"
        elif "CycleStart" in module:
            interaction_tag = "LB.Interaction.CycleStart"
        elif "ResetButton" in module:
            interaction_tag = "LB.Interaction.Reset"
        path = f"{HMI_ROOT}/{module}.{module}"
        spawn_mesh(
            f"{hmi_id}_{module.replace('SM_LB_HMI04_', '')}", path, (x, y, 8),
            rotation=(0, 0, yaw),
            actor_tags=(
                "LB.Module.SharedHMI", f"LB.HMI.{hmi_id}",
                f"LB.Station.{station}", interaction_tag,
            ),
        )
        count("hmi_modules")
    count("shared_hmi_cabinets")


def add_fence_post(label, x, y, station, gate=False):
    post_tags = ["LB.Module.SafetyFencePost", f"LB.Station.{station}"]
    if gate:
        post_tags.append("LB.Safety.InterlockedGate")
    spawn_mesh(
        label, SAFETY_BARRIER_ASSETS["post"], (x, y, 8),
        actor_tags=tuple(post_tags),
    )
    count("safety_fence_posts")


def add_fence_line(label, start, end, station):
    """Tile the open-mesh two-metre safety panel between exact end posts."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length < 1.0:
        return
    yaw = math.degrees(math.atan2(dy, dx))
    pieces = max(1, math.ceil(length / 200.0))
    piece_length = length / pieces
    ux, uy = dx / length, dy / length
    for index in range(pieces):
        ex = start[0] + ux * piece_length * (index + 0.5)
        ey = start[1] + uy * piece_length * (index + 0.5)
        spawn_mesh(
            f"{label}_Panel_{index + 1:02d}", SAFETY_BARRIER_ASSETS["panel"], (ex, ey, 8),
            scale=(piece_length / 200.0, 1.0, 1.0), rotation=(0, 0, yaw),
            actor_tags=("LB.Module.SafetyFence", f"LB.Station.{station}"),
        )
        count("safety_fence_panels")
    # Every panel joint receives a real bolted structural post.  The previous
    # candidate only placed posts at the two ends of an entire run, which made
    # long fences read as unsupported mesh from normal gameplay distance.
    for joint in range(pieces + 1):
        px = start[0] + ux * piece_length * joint
        py = start[1] + uy * piece_length * joint
        add_fence_post(f"{label}_Post_{joint + 1:02d}", px, py, station)


def add_interlocked_gate(label, start, end, station):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    yaw = math.degrees(math.atan2(dy, dx))
    spawn_mesh(
        f"{label}_Leaf", SAFETY_BARRIER_ASSETS["gate"], (start[0], start[1], 8),
        scale=(length / 120.0, 1.0, 1.0), rotation=(0, 0, yaw),
        actor_tags=(
            "LB.Module.SafetyGate", "LB.Safety.InterlockedGate",
            "LB.Motion.SafetyGate", f"LB.Station.{station}",
        ),
        mobility=unreal.ComponentMobility.MOVABLE,
    )
    add_fence_post(f"{label}_HingePost", start[0], start[1], station, gate=True)
    add_fence_post(f"{label}_LatchPost", end[0], end[1], station, gate=True)
    spawn_mesh(
        f"{label}_Interlock", SAFETY_BARRIER_ASSETS["interlock"], (end[0], end[1], 8),
        rotation=(0, 0, yaw),
        actor_tags=(
            "LB.Module.GateInterlock", "LB.Safety.InterlockedGate",
            "LB.Interaction.GateStatus", f"LB.Station.{station}",
        ),
    )
    count("gate_interlock_boxes")
    count("interlocked_gates")


# ---------------------------------------------------------------------------
# Release-reference floor language: PR-001 blue, PR-002 orange, Hold/NCR red,
# PR-003 blue-green, PR-004 grey transfer and yellow protected walkways.
# ---------------------------------------------------------------------------
paint_z = 7.0
paint_h = 1.2
floor_pads = (
    ("Floor_PR001", station_pos("PR-001", z=paint_z), (1500, 2400, paint_h), MATS["floor_pr001"], "LB.Zone.PR-001"),
    ("Floor_PR002", station_pos("PR-002", z=paint_z), (1500, 3000, paint_h), MATS["floor_pr002"], "LB.Zone.PR-002"),
    ("Floor_HOLD", (-10100, -1000, paint_z), (1500, 1700, paint_h), MATS["floor_hold"], "LB.Zone.HOLD-NCR"),
    ("Floor_PR003", station_pos("PR-003", z=paint_z), (1900, 6000, paint_h), MATS["floor_pr003"], "LB.Zone.PR-003"),
    ("Floor_PR004", station_pos("PR-004", z=paint_z), (900, 6000, paint_h), MATS["floor_pr004"], "LB.Zone.PR-004"),
)
for label, pos, size, mat, zone_tag in floor_pads:
    cube(label, pos, size, mat, ("LB.Floor.Paint", zone_tag))
    count("floor_pads")

for label, text_value, location, size, colour, station in (
    ("FloorText_PR001", "PR-001  COIL RECEIPT", station_pos("PR-001", dx=-520, z=10.4), 46, unreal.Color(220, 228, 235, 255), "PR-001"),
    ("FloorText_PR002", "PR-002  INSPECTION", station_pos("PR-002", dx=-520, z=10.4), 38, unreal.Color(236, 222, 205, 255), "PR-002"),
    ("FloorText_HOLD", "HOLD / NCR", (-10580, -1000, 10.4), 38, unreal.Color(244, 222, 220, 255), "HOLD-NCR"),
    ("FloorText_PR003", "PR-003  COIL STORE", station_pos("PR-003", dx=-760, z=10.4), 46, unreal.Color(220, 232, 236, 255), "PR-003"),
    ("FloorText_PR004", "PR-004", station_pos("PR-004", dx=-300, z=10.4), 42, unreal.Color(225, 230, 232, 255), "PR-004"),
):
    spawn_text(
        label, text_value, location, rotation=(0, -90, -90), world_size=size,
        colour=colour, actor_tags=(f"LB.Station.{station}", "LB.Floor.Stencil"),
    )

# Boundary and pedestrian-route lines. Thin geometry is intentional here: it
# remains crisp from the management camera and can later be replaced by decals.
for zone_id, cx, cy, sx, sy in (
    ("PR001", STATION_ANCHORS["PR-001"][0], STATION_ANCHORS["PR-001"][1], 1500, 2400),
    ("PR002", STATION_ANCHORS["PR-002"][0], STATION_ANCHORS["PR-002"][1], 1500, 3000),
    ("HOLD", -10100, -1000, 1500, 1700),
    ("PR003", STATION_ANCHORS["PR-003"][0], STATION_ANCHORS["PR-003"][1], 1900, 6000),
    ("PR004", STATION_ANCHORS["PR-004"][0], STATION_ANCHORS["PR-004"][1], 900, 6000),
):
    for edge, pos, size in (
        ("N", (cx, cy - sy / 2, 8.2), (sx, 10, 1.2)),
        ("S", (cx, cy + sy / 2, 8.2), (sx, 10, 1.2)),
        ("W", (cx - sx / 2, cy, 8.2), (10, sy, 1.2)),
        ("E", (cx + sx / 2, cy, 8.2), (10, sy, 1.2)),
    ):
        cube(f"Line_{zone_id}_{edge}", pos, size, MATS["yellow"], ("LB.Floor.Line", f"LB.Zone.{zone_id}"))
        count("floor_lines")

# Protected pedestrian route across the full front-end frontage.  The textured
# green walking surface and yellow edge lines match the operational drawings;
# compact centre dashes retain readability without the former ladder effect.
cube("PedestrianRoute", (-6600, 1250, 8.3), (6200, 220, 1.3), MATS["floor_walkway"], ("LB.Route.Pedestrian",))
for side in (-1, 1):
    cube(
        f"PedestrianRouteEdge_{side:+d}", (-6600, 1250 + side * 106, 9.2),
        (6200, 10, 1.1), MATS["yellow"], ("LB.Route.Pedestrian", "LB.Floor.Line"),
    )
for x in range(-9600, -3549, 450):
    cube(f"PedRouteInset_{abs(x)}", (x, 1250, 9.2), (135, 16, 1.0), MATS["yellow"], ("LB.Route.Pedestrian",))
    count("pedestrian_route_insets")

# Crane-zone outlines: orange for 30 t and green/blue for 40 t. The requested
# colours are represented with existing validated materials at candidate stage.
for zone, cx, sx, mat in (
    ("30T", -8200, 2200, MATS["orange"]),
    ("40T", -5900, 3000, MATS["green"]),
):
    for edge, pos, size in (
        ("N", (cx, -5650, 9.4), (sx, 14, 1.0)),
        ("S", (cx, 1050, 9.4), (sx, 14, 1.0)),
        ("W", (cx - sx / 2, -2300, 9.4), (14, 6700, 1.0)),
        ("E", (cx + sx / 2, -2300, 9.4), (14, 6700, 1.0)),
    ):
        cube(f"CraneZone_{zone}_{edge}", pos, size, mat, ("LB.Floor.CraneZone", f"LB.Crane.{zone}"))
        count("crane_zone_lines")


# ---------------------------------------------------------------------------
# Release-distance hall context. This north/west wall system fills close-camera
# backgrounds without roofing over the management view.
# ---------------------------------------------------------------------------
cube(
    "NorthWallLowerLiner", (-7000, -5928, 285), (8200, 24, 570), MATS["wall_concrete"],
    ("LB.Module.FactoryWall", "LB.Streaming.Press.FrontEnd"),
)
cube(
    "NorthWallUpperLiner", (-7000, -5930, 1375), (8200, 20, 1610), MATS["wall_service"],
    ("LB.Module.FactoryWall", "LB.Streaming.Press.FrontEnd"),
)
cube(
    "WestWallLiner", (-10972, -3250, 1200), (24, 5300, 2400), MATS["wall_service"],
    ("LB.Module.FactoryWall", "LB.Streaming.Press.FrontEnd"),
)
count("factory_wall_liners", 3)

# Wall panel seams, structural knees and a clerestory band make the shell read
# at close range instead of as a single featureless grey plane.
for index, x in enumerate(range(-10800, -2799, 600), 1):
    cube(
        f"NorthWallColumn_{index:02d}", (x, -5885, 1160), (34, 42, 2280), MATS["vendor_column"],
        ("LB.Module.StructuralColumn", "LB.Streaming.Press.FrontEnd"),
    )
    cube(
        f"NorthWallClerestory_{index:02d}", (x + 285, -5890, 1720), (470, 12, 190), MATS["vendor_glass"],
        ("LB.Module.Clerestory", "LB.Streaming.Press.FrontEnd"),
    )
    count("wall_bay_columns")
    count("clerestory_panels")

for x in range(-10800, -2799, 600):
    spawn_mesh(
        f"NorthWallBeam_{abs(x)}", VENDOR_ASSETS["beam"], (x, -5845, 2030),
        actor_tags=("LB.Module.StructuralBeam", "LB.Streaming.Press.FrontEnd"),
    )
    count("wall_beam_modules")

# Three utility pipe runs and a cable tray are continuous across the chapter.
# They provide service logic and useful parallax behind the moving cranes.
for bank_index, (z, scale, y) in enumerate(((720, 0.22, -5835), (790, 0.18, -5800), (855, 0.14, -5770)), 1):
    for x in range(-10650, -2849, 300):
        spawn_mesh(
            f"NorthUtilityPipe_{bank_index}_{abs(x)}", VENDOR_ASSETS["pipe_long"], (x, y, z),
            scale=(scale, 1.50, scale), rotation=(0, 0, 90),
            actor_tags=("LB.Module.UtilityPipe", f"LB.Utility.Bank{bank_index}", "LB.Streaming.Press.FrontEnd"),
        )
        count("utility_pipe_modules")
for x in range(-10400, -2999, 400):
    spawn_mesh(
        f"NorthCableTray_{abs(x)}", VENDOR_ASSETS["cables"], (x, -5745, 980),
        rotation=(0, 0, 90), actor_tags=("LB.Module.CableTray", "LB.Streaming.Press.FrontEnd"),
    )
    count("cable_tray_modules")

# Reusable service cabinets are protected by bollards and connected to the
# overhead distribution route.
service_cabinets = (
    ("PR001", -8750, "PR-001"),
    ("PR002", -7950, "PR-002"),
    ("PR003A", -6900, "PR-003"),
    ("PR003B", -6200, "PR-003"),
    ("PR004", -4900, "PR-004"),
)
for cabinet_id, x, station in service_cabinets:
    spawn_mesh(
        f"ServiceCabinet_{cabinet_id}", DRESSING_ASSETS["service_cabinet"], (x, -5655, 8),
        rotation=(0, 0, 180), actor_tags=("LB.Module.ServiceCabinet", f"LB.Station.{station}"),
    )
    spawn_mesh(
        f"ServiceCable_{cabinet_id}", VENDOR_ASSETS["electrical_cable"], (x, -5790, 180),
        scale=(0.32, 0.32, 1.0), actor_tags=("LB.Module.ElectricalCable", f"LB.Station.{station}"),
    )
    for side in (-1, 1):
        spawn_mesh(
            f"CabinetBollard_{cabinet_id}_{side:+d}", DRESSING_ASSETS["bollard"],
            (x + side * 70, -5570, 8), actor_tags=("LB.Module.ImpactProtection", f"LB.Station.{station}"),
        )
        count("safety_bollards")
    count("service_cabinets")

add_station_wall_sign("Sign_PR001_002", "PR-001", "COIL RECEIPT  /  PR-002 INSPECTION", -8200, 1500)
add_station_wall_sign("Sign_PR003", "PR-003", "SINGLE-LEVEL COIL STORE", -6450, 1200)
add_station_wall_sign("Sign_PR004", "PR-004", "CRANE TRANSFER & PACKAGING", -5050, 950)

# Real open drainage modules replace painted black rectangles. They remain
# outside all coil-support footprints and tile into reusable one-metre trenches.
for trench_id, x0, x1, y, station in (
    ("PR001", -8700, -7700, -2750, "PR-001"),
    ("PR002", -8700, -7700, 520, "PR-002"),
    ("PR003", -7250, -5650, 650, "PR-003"),
    ("PR004", -5400, -4800, 650, "PR-004"),
):
    for index, x in enumerate(range(x0, x1 + 1, 100), 1):
        spawn_mesh(
            f"Drain_{trench_id}_{index:02d}", DRESSING_ASSETS["trench_grate"], (x, y, 8),
            actor_tags=("LB.Module.FloorDrainage", f"LB.Station.{station}"),
        )
        count("floor_trench_modules")


# ---------------------------------------------------------------------------
# Modular coil saddle and material population.
# ---------------------------------------------------------------------------
coil_mesh = unreal.load_asset(COIL_ASSET)
if not isinstance(coil_mesh, unreal.StaticMesh):
    raise RuntimeError(f"Master-coil candidate missing: {COIL_ASSET}")


def add_saddle(slot_id, x, y, station, z=8.0):
    spawn_mesh(
        f"{slot_id}_CoilSaddle", SADDLE_ASSET, (x, y, z),
        actor_tags=("LB.Module.CoilSaddle", "LB.Safety.Padded", f"LB.Station.{station}"),
    )
    count("coil_saddles")


def add_coil(slot_id, x, y, z=146, station="PR-003", yaw=90.0):
    actor = spawn_mesh(
        # Unreal Rotator positional order is roll, pitch, yaw. The FBX coil axis
        # is X, so yaw maps it horizontally onto Y; pitch would stand it on end.
        f"{slot_id}_MasterCoil", COIL_ASSET, (x, y, z), rotation=(0, 0, yaw),
        actor_tags=("LB.Material.MasterCoil", f"LB.Inventory.{station}.{slot_id}", f"LB.Station.{station}"),
    )
    count("master_coils")
    return actor


# Exactly 12 PR-003 positions: the authoritative 4 x 3 single-level store.
# Appendix A defines four positions across the strip axis and three positions
# along material flow.  The former candidate transposed that grid.
store_positions = []
slot_number = 1
for flow_offset in (-300, 0, 300):
    for across_offset in (-450, -150, 150, 450):
        slot = f"CS-{slot_number:02d}"
        x = STATION_ANCHORS["PR-003"][0] + flow_offset
        y = STATION_ANCHORS["PR-003"][1] - across_offset
        add_saddle(slot, x, y, "PR-003")
        add_coil(slot, x, y)
        # Bay corner marks improve exact slot readability from near top-down.
        for sx in (-1, 1):
            for sy in (-1, 1):
                cube(
                    f"{slot}_BayMark_{sx}_{sy}",
                    (x + sx * 125, y + sy * 125, 9.6), (42, 8, 1.0), MATS["yellow"],
                    ("LB.Floor.CoilBay", f"LB.Inventory.PR-003.{slot}"),
                )
        store_positions.append({"slot": slot, "world_cm": [x, y, 146]})
        slot_number += 1

# Receipt and inspection positions are separate physical coils in this visual
# validation map; stable IDs prevent them being mistaken for the store stock.
# PR-001 receipt uses a visible load-cell scale platform. PR-002 is a recessed
# inspection/weighing deck. Their raised saddle/coil heights are deliberate.
for label, x, y, sx, sy, height, mat, station in (
    ("PR001_ReceivingScale", STATION_ANCHORS["PR-001"][0], STATION_ANCHORS["PR-001"][1], 360, 240, 20, MATS["dark"], "PR-001"),
    ("PR002_InspectionScale", STATION_ANCHORS["PR-002"][0], STATION_ANCHORS["PR-002"][1], 340, 230, 16, MATS["grey"], "PR-002"),
):
    cube(label + "_Base", (x, y, 18), (sx, sy, height), mat, ("LB.Module.CoilScale", f"LB.Station.{station}"))
    cube(label + "_Deck", (x, y, 30), (sx - 18, sy - 18, 5), MATS["dark"], ("LB.Module.CoilScaleDeck", f"LB.Station.{station}"))
    for ix in (-1, 1):
        for iy in (-1, 1):
            cylinder(
                f"{label}_LoadCell_{ix}_{iy}", (x + ix * (sx / 2 - 28), y + iy * (sy / 2 - 28), 29),
                (18, 10), MATS["charcoal"], ("LB.Sensor.LoadCell", f"LB.Station.{station}"),
            )
    count("coil_scale_platforms")

add_saddle("PR001-IN-01", *station_pos("PR-001")[:2], "PR-001", z=33)
add_coil("PR001-IN-01", *station_pos("PR-001")[:2], z=171, station="PR-001")
add_saddle("PR002-QA-01", *station_pos("PR-002")[:2], "PR-002", z=33)
add_coil("PR002-QA-01", *station_pos("PR-002")[:2], z=171, station="PR-002")

# The HOLD/NCR saddle remains empty so the quarantine function reads clearly.
add_saddle("HOLD-NCR-01", -10100, -1000, "HOLD-NCR", z=8)

# PR-004 carries one in-process coil on its preparation cradle. This is a
# distinct visual material state, ready for the later packaging-removal task.
add_saddle("PR004-PREP-01", *station_pos("PR-004")[:2], "PR-004", z=8)
add_coil("PR004-PREP-01", *station_pos("PR-004")[:2], station="PR-004")


# ---------------------------------------------------------------------------
# Inspection, packaging and operator equipment.
# ---------------------------------------------------------------------------
# PR-002 camera/light bridge makes the inspection function visible from both
# management and close-control views. Tagged heads become real sensors later.
for side, x in (
    ("W", STATION_ANCHORS["PR-002"][0] - 270),
    ("E", STATION_ANCHORS["PR-002"][0] + 270),
):
    for end, y in (
        ("N", STATION_ANCHORS["PR-002"][1] - 150),
        ("S", STATION_ANCHORS["PR-002"][1] + 150),
    ):
        cube(
            f"PR002_InspectionPost_{side}_{end}", (x, y, 125), (16, 16, 235), MATS["yellow"],
            ("LB.Module.InspectionFrame", "LB.Station.PR-002"),
        )
    cube(
        f"PR002_InspectionCrossbar_{side}", (x, STATION_ANCHORS["PR-002"][1], 238), (18, 330, 18), MATS["dark"],
        ("LB.Module.InspectionFrame", "LB.Station.PR-002"),
    )
    cube(
        f"PR002_VisionHead_{side}", (x, STATION_ANCHORS["PR-002"][1], 208), (34, 28, 25), MATS["charcoal"],
        ("LB.Sensor.MachineVision", "LB.Interaction.Inspect", "LB.Station.PR-002"),
    )
    cylinder(
        f"PR002_VisionLens_{side}", (x + (8 if side == "W" else -8), STATION_ANCHORS["PR-002"][1], 208),
        (12, 10), MATS["dark"],
        ("LB.Sensor.MachineVision", "LB.Station.PR-002"), rotation=(0, 90, 0),
    )
count("inspection_frames", 1)

for side, y, yaw in (
    ("N", STATION_ANCHORS["PR-002"][1] - 320, 90),
    ("S", STATION_ANCHORS["PR-002"][1] + 320, -90),
):
    spawn_mesh(
        f"PR002_InspectionMast_{side}", DRESSING_ASSETS["inspection_mast"], (STATION_ANCHORS["PR-002"][0], y, 8),
        rotation=(0, 0, yaw),
        actor_tags=("LB.Module.InspectionMast", "LB.Sensor.MachineVision", "LB.Station.PR-002"),
    )
    spawn_mesh(
        f"PR002_EStop_{side}", DRESSING_ASSETS["estop"], (STATION_ANCHORS["PR-002"][0] - 330, y, 8),
        rotation=(0, 0, 180),
        actor_tags=("LB.Interaction.EStop", "LB.Safety.EmergencyStop", "LB.Station.PR-002"),
    )
    count("inspection_masts")
    count("estop_pedestals")

# PR-004 packaging/preparation equipment uses real modular props with readable
# workholding, wrap/banding tools, recovery streams and casters.
spawn_mesh(
    "PR004_PackagingPrepBench", DRESSING_ASSETS["prep_bench"], station_pos("PR-004", dx=50, dy=800, z=8),
    rotation=(0, 0, 90),
    actor_tags=("LB.Module.PackagingBench", "LB.Interaction.RemovePackaging", "LB.Station.PR-004"),
)
for index, (y, mat, purpose) in enumerate((
    (STATION_ANCHORS["PR-004"][1] + 1250, MATS["charcoal"], "Banding"),
    (STATION_ANCHORS["PR-004"][1] + 1500, MATS["red"], "RejectedPackaging"),
    (STATION_ANCHORS["PR-004"][1] + 1750, MATS["grey"], "EdgeProtectors"),
), 1):
    bin_actor = spawn_mesh(
        f"PR004_Bin_{index}_{purpose}", DRESSING_ASSETS["recovery_bin"], (STATION_ANCHORS["PR-004"][0] + 50, y, 8),
        rotation=(0, 0, 180),
        actor_tags=("LB.Module.MaterialBin", f"LB.Inventory.PR-004.{purpose}", "LB.Station.PR-004"),
    )
    bin_actor.get_editor_property("static_mesh_component").set_material(1, mat)
    spawn_text(
        f"PR004_BinLabel_{index}_{purpose}", purpose.replace("Packaging", " PACKAGING ").upper(),
        (STATION_ANCHORS["PR-004"][0] + 50, y + 45, 68), rotation=(0, 0, 90), world_size=15,
        colour=unreal.Color(22, 25, 27, 255), actor_tags=("LB.Station.PR-004",),
    )
count("packaging_benches")
count("material_bins", 3)

# Shared cross-shop cabinet platform: identical hardware, station-specific tags.
add_hmi("HMI-PR002-01", -8900, 1120, 90, "PR-002")
add_hmi("HMI-PR003-01", -7000, 1120, 0, "PR-003")
add_hmi("HMI-PR004-01", -4850, 1120, 0, "PR-004")
for index, (x, y, yaw, station) in enumerate((
    (-8720, 1120, 0, "PR-002"),
    (-6820, 1120, 0, "PR-003"),
    (-4670, 1120, 0, "PR-004"),
), 1):
    spawn_mesh(
        f"HMIImpactBollard_{index:02d}", DRESSING_ASSETS["bollard"], (x, y, 8),
        actor_tags=("LB.Module.ImpactProtection", f"LB.Station.{station}"),
    )
    spawn_mesh(
        f"HMIServiceCable_{index:02d}", VENDOR_ASSETS["cable_set"], (x - 70, y, 8),
        rotation=(0, 0, yaw), actor_tags=("LB.Module.CableEntry", f"LB.Station.{station}"),
    )
    count("hmi_protection_bollards")
    count("hmi_service_cables")

# The downloaded fence was rejected because its material rendered as an opaque
# checkerboard wall.  This custom open-mesh kit keeps sightlines clear and gives
# every moving gate a real hinge pivot plus a separate coded interlock box.
add_fence_line("PR001_WestBoundary", (-9300, -5450), (-9300, 1050), "PR-001")
add_fence_line("PR001_Front_W", (-9300, 1050), (-8400, 1050), "PR-001")
add_interlocked_gate("PR001_AccessGate", (-8400, 1050), (-8200, 1050), "PR-001")
add_fence_line("PR001_Front_E", (-8200, 1050), (-7200, 1050), "PR-001")
add_fence_line("PR001_EastBoundary", (-7200, -5450), (-7200, 1050), "PR-001")

add_fence_line("PR003_WestBoundary", (-7450, -5450), (-7450, 1050), "PR-003")
add_fence_line("PR003_Front_W", (-7450, 1050), (-6550, 1050), "PR-003")
add_interlocked_gate("PR003_AccessGate", (-6550, 1050), (-6350, 1050), "PR-003")
add_fence_line("PR003_Front_E", (-6350, 1050), (-5500, 1050), "PR-003")

add_fence_line("PR004_Front_W", (-5500, 1050), (-5150, 1050), "PR-004")
add_interlocked_gate("PR004_AccessGate", (-5150, 1050), (-4950, 1050), "PR-004")
add_fence_line("PR004_Front_E", (-4950, 1050), (-4600, 1050), "PR-004")
add_fence_line("PR004_PR005Boundary_N", (-4600, -5450), (-4600, -2150), "PR-004")
add_interlocked_gate("PR004_PR005TransferGate", (-4600, -2150), (-4600, -1850), "PR-004")
add_fence_line("PR004_PR005Boundary_S", (-4600, -1850), (-4600, 1050), "PR-004")

for gate_id, x, y, yaw, station in (
    ("PR001", -8150, 1120, 180, "PR-001"),
    ("PR003", -6300, 1120, 180, "PR-003"),
    ("PR004", -4900, 1120, 180, "PR-004"),
    ("PR004Transfer", -4535, -2000, 90, "PR-004"),
):
    spawn_mesh(
        f"GateEStop_{gate_id}", DRESSING_ASSETS["estop"], (x, y, 8), rotation=(0, 0, yaw),
        actor_tags=("LB.Interaction.EStop", "LB.Safety.EmergencyStop", f"LB.Station.{station}"),
    )
    count("estop_pedestals")


# ---------------------------------------------------------------------------
# Overhead-crane modular kit. Each moving assembly has a stable gameplay tag.
# ---------------------------------------------------------------------------
def add_overhead_crane(crane_id, capacity, x_min, x_max, bridge_x, double_girder=False, hook_y=-3300):
    runway_y = (-5550, 720)
    bridge_span = runway_y[1] - runway_y[0]
    run_length = x_max - x_min
    run_centre = (x_min + x_max) / 2
    for side, y in (("N", runway_y[0]), ("S", runway_y[1])):
        # Preserve the designed I-section and rail profile by scaling the
        # reusable three-metre module only along the runway direction.
        spawn_mesh(
            f"{crane_id}_Runway_{side}", CRANE_ASSETS["runway"], (run_centre, y, 1435),
            scale=(run_length / 300.0, 1.0, 1.0),
            actor_tags=(
                "LB.Module.CraneRunway", f"LB.Crane.{crane_id}",
                f"LB.Capacity.{capacity}t",
            ),
        )
        count("crane_runway_modules")
        for x in range(int(x_min), int(x_max) + 1, 600):
            spawn_mesh(
                f"{crane_id}_Column_{side}_{abs(x)}", CRANE_ASSETS["column"], (x, y, 5),
                actor_tags=("LB.Module.CraneColumn", f"LB.Crane.{crane_id}"),
            )
            count("crane_column_modules")

    # The bridge modules include inspection decks, handrails and capacity
    # plate geometry. The 40 t bridge correctly uses a double-girder pair.
    girder_specs = ((-105, 0), (105, 180)) if double_girder else ((0, 0),)
    for index, (offset, yaw) in enumerate(girder_specs, 1):
        spawn_mesh(
            f"{crane_id}_BridgeGirder_{index}", CRANE_ASSETS["girder"],
            (bridge_x + offset, sum(runway_y) / 2.0, 1500),
            scale=(1.0, bridge_span / 4500.0, 1.0),
            rotation=(0, 0, yaw),
            actor_tags=(
                "LB.Motion.CraneBridge", f"LB.Crane.{crane_id}",
                f"LB.Capacity.{capacity}t", "LB.Animation.Pivot.Bridge",
            ),
            mobility=unreal.ComponentMobility.MOVABLE,
        )
        count("crane_bridge_modules")
    for end, y in (("N", runway_y[0] + 30), ("S", runway_y[1] - 30)):
        spawn_mesh(
            f"{crane_id}_EndTruck_{end}", CRANE_ASSETS["end_truck"],
            (bridge_x, y, 1490),
            scale=(1.8 if double_girder else 1.0, 1.0, 1.0),
            actor_tags=(
                "LB.Motion.CraneBridge", f"LB.Crane.{crane_id}",
                "LB.Animation.Pivot.Bridge",
            ),
            mobility=unreal.ComponentMobility.MOVABLE,
        )
        count("crane_end_truck_modules")

    spawn_mesh(
        f"{crane_id}_Trolley", CRANE_ASSETS["trolley"], (bridge_x, hook_y, 1600),
        actor_tags=(
            "LB.Motion.CraneTrolley", f"LB.Crane.{crane_id}",
            "LB.Animation.Pivot.Trolley",
        ),
        mobility=unreal.ComponentMobility.MOVABLE,
    )
    count("crane_trolley_modules")

    # Hoist block, reeving and C-hook stay independent. The future runtime
    # adapter can therefore drive bridge X, trolley Y and hoist/hook Z without
    # deforming a combined mesh.
    hoist_z = 1120
    spawn_mesh(
        f"{crane_id}_HoistBlock", CRANE_ASSETS["hoist_block"], (bridge_x, hook_y, hoist_z),
        actor_tags=(
            "LB.Motion.Hoist", f"LB.Crane.{crane_id}",
            "LB.Animation.Pivot.Hoist",
        ),
        mobility=unreal.ComponentMobility.MOVABLE,
    )
    count("crane_hoist_modules")
    chain_top = 1565
    chain_bottom = hoist_z + 43
    chain_length = chain_top - chain_bottom
    for side in (-1, 1):
        cylinder(
            f"{crane_id}_Reeving_{side}",
            (bridge_x + side * 22, hook_y, chain_bottom + chain_length / 2),
            (3.0, chain_length), MATS["charcoal"],
            ("LB.Motion.Hoist", f"LB.Crane.{crane_id}", "LB.Module.HoistReeving"),
            mobility=unreal.ComponentMobility.MOVABLE,
        )
        count("crane_reeving_lines")

    hook_z = 820
    spawn_mesh(
        f"{crane_id}_CHook", CRANE_ASSETS["c_hook"], (bridge_x, hook_y, hook_z),
        rotation=(0, 0, 90),
        actor_tags=(
            "LB.Motion.CHook", f"LB.Crane.{crane_id}", "LB.Safety.Padded",
            "LB.Animation.Pivot.CHook",
        ),
        mobility=unreal.ComponentMobility.MOVABLE,
    )
    count("crane_c_hook_modules")
    connector_top = hoist_z - 43
    connector_bottom = hook_z + 119
    connector_length = max(12.0, connector_top - connector_bottom)
    cylinder(
        f"{crane_id}_HookLink", (bridge_x, hook_y, connector_bottom + connector_length / 2),
        (8.0, connector_length), MATS["dark"],
        ("LB.Motion.CHook", f"LB.Crane.{crane_id}", "LB.Module.HookLink"),
        mobility=unreal.ComponentMobility.MOVABLE,
    )
    count("crane_hook_links")
    count("overhead_cranes")


add_overhead_crane("30T", 30, -9300, -7150, -8200, double_girder=False, hook_y=-4000)
add_overhead_crane("40T", 40, -7500, -4500, -5050, double_girder=True, hook_y=-2000)

# PR-004 parked C-hook cradle makes transfer tooling location explicit.
cube("PR004_CHookStand_Base", station_pos("PR-004", dy=1050, z=28), (260, 220, 35), MATS["dark"], ("LB.Module.CHookStand", "LB.Station.PR-004"))
for side in (-1, 1):
    cube(
        f"PR004_CHookStand_Post_{side}", station_pos("PR-004", dx=side * 78, dy=1050, z=105), (26, 28, 150), MATS["yellow"],
        ("LB.Module.CHookStand", "LB.Station.PR-004"),
    )
count("c_hook_stands")

# Cutaway camera rule: the west front-end chapter hides only shell columns that
# physically cut through the management view. They remain present in-editor and
# can be shown for eye-level/exterior shots.
cutaway_hidden = []
for shell_actor in actor_system.get_all_level_actors():
    label = shell_actor.get_actor_label()
    if label.startswith("LB_PRESS_Column_") and shell_actor.get_actor_location().x < -4500:
        shell_actor.set_actor_hidden_in_game(True)
        cutaway_hidden.append(label)

# Broad, soft factory luminaires make the coils and floor legible under the
# cranes without recreating the earlier overexposed test. Omnidirectional fill
# is intentional because a RectLight's local facing proved unreliable in the
# unattended renderer used by the validation gate.
for actor in actor_system.get_all_level_actors():
    if actor.get_actor_label() == "LB_PRESS_DirectionalFill":
        actor.get_editor_property("directional_light_component").set_editor_properties({
            "intensity": 4.00,
            "light_source_angle": 10.0,
            "cast_shadows": False,
            "light_color": unreal.Color(235, 239, 245, 255),
        })

# A roofed automotive hall has broad inter-reflection from walls, roof liners
# and luminaires.  The cutaway review map has no physical roof, so add one
# restrained, shadowless counter-directional rather than relying on unstable
# auto exposure to fake that ambient bounce.
ambient_fill = actor_system.spawn_actor_from_class(
    unreal.DirectionalLight, unreal.Vector(), unreal.Rotator(-62.0, 145.0, 0.0)
)
ambient_fill.set_actor_label(PREFIX + "FrontEndAmbientBounce")
ambient_fill.get_editor_property("directional_light_component").set_editor_properties({
    "intensity": 1.20,
    "light_source_angle": 8.0,
    "cast_shadows": False,
    "light_color": unreal.Color(228, 234, 242, 255),
})
ambient_fill.set_editor_property("tags", tags("LB.Lighting.Candidate", "LB.Streaming.Press.FrontEnd"))
count("factory_ambient_fill_lights")

high_bay_positions = tuple(
    (x, y)
    for x in (-10400, -8600, -6800, -5100, -3500)
    for y in (-4700, -2600, -500)
)
for index, (x, y) in enumerate(high_bay_positions, 1):
    spawn_mesh(
        f"FactoryLampFixture_{index:02d}", VENDOR_ASSETS["lamp"], (x, y, 1710),
        scale=(0.12, 0.12, 0.12), actor_tags=("LB.Module.FactoryLuminaire",),
    )
    count("factory_lamp_fixtures")
    light = actor_system.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, 1640), unreal.Rotator())
    light.set_actor_label(PREFIX + f"FactoryFill_{index:02d}")
    component = light.get_editor_property("point_light_component")
    component.set_editor_properties({
        "intensity": 5000.0,
        "attenuation_radius": 2000.0,
        "source_radius": 70.0,
        "soft_source_radius": 160.0,
        "source_length": 120.0,
        "cast_shadows": True,
        "light_color": unreal.Color(255, 238, 215, 255),
    })
    light.set_editor_property("tags", tags("LB.Lighting.Candidate", "LB.Streaming.Press.FrontEnd"))
    count("factory_fill_lights")

# Deterministic fixed exposure prevents a black, roofless shell from forcing
# auto exposure to bleach the coils while leaving the machinery unreadable.
exposure = actor_system.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
exposure.set_actor_label(PREFIX + "FrontEndFixedExposure")
exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0})
exposure_settings = exposure.get_editor_property("settings")
exposure_settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 0.50,
    "override_ambient_occlusion_intensity": True,
    "ambient_occlusion_intensity": 0.55,
    "override_ambient_occlusion_radius": True,
    "ambient_occlusion_radius": 90.0,
    "override_vignette_intensity": True,
    "vignette_intensity": 0.08,
})
exposure.set_editor_property("settings", exposure_settings)
count("fixed_exposure_volumes")


# Fixed review cameras. These are validation/game-framing candidates, not an
# approval of assets or normal-gameplay zoom limits.
camera_specs = (
    ("CAM_FrontEndOverview", (-10600, 450, 6500), (-6250, -2350, 220), 60.0, None),
    ("CAM_CoilStoreCrane", (-7450, 430, 1280), (-6250, -2350, 240), 50.0, None),
    # Stay just inside the west shell (wall at X=-11000) and look through the
    # protected frontage toward receipt and inspection.  The former X=-11500
    # position photographed the outside face of the wall instead of the cell.
    ("CAM_PR001_PR002", (-9700, 430, 1050), (-8200, -2500, 190), 50.0, None),
    ("CAM_FrontEndTop", (-6750, -2250, 10500), None, 50.0, 11500.0),
    # Detail cameras sit inside the south runway line so the crane-support
    # columns cannot fill the foreground of the validation image.
    ("CAM_CraneDetail", (-6900, 430, 820), (-5150, -2250, 1120), 50.0, None),
    ("CAM_PR004Prep", (-5850, 430, 700), (-5050, -1900, 220), 50.0, None),
    ("CAM_FrontEndEyeLevel", (-7350, 430, 172), (-6200, -2400, 165), 52.0, None),
)
camera_labels = []
for spec in camera_specs:
    # Backward-compatible unpacking keeps the still-useful coil-store view.
    label, location, target, fov = spec[:4]
    ortho_width = spec[4] if len(spec) > 4 else None
    camera = actor_system.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(PREFIX + label)
    component = camera.get_editor_property("camera_component")
    if ortho_width is not None:
        camera.set_actor_rotation(
            unreal.Rotator(roll=0.0, pitch=-90.0, yaw=-90.0), False
        )
        component.set_editor_properties({
            "projection_mode": unreal.CameraProjectionMode.ORTHOGRAPHIC,
            "ortho_width": ortho_width,
            "aspect_ratio": 16.0 / 9.0,
            "constrain_aspect_ratio": True,
        })
    else:
        camera.set_actor_rotation(
            unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False
        )
        component.set_editor_property("field_of_view", fov)
    camera.set_editor_property("tags", tags("LB.Camera.Validation", "LB.Streaming.Press.FrontEnd"))
    camera_labels.append(PREFIX + label)

if not levels.save_current_level():
    raise RuntimeError("Failed saving populated Press Shop integration candidate")

result = {
    "status": "INTEGRATION_CANDIDATE_NOT_PROMOTED",
    "map": MAP,
    "master_coil_asset": COIL_ASSET,
    "authoritative_pr003_slot_count": 12,
    "pr003_slots": store_positions,
    "visual_master_coil_count": created_by_type.get("master_coils", 0),
    "cranes": [
        {"id": "30T", "capacity_tonnes": 30, "type": "single-girder", "stations": ["PR-001", "PR-002"]},
        {"id": "40T", "capacity_tonnes": 40, "type": "double-girder", "stations": ["PR-003", "PR-004"]},
    ],
    "created_by_type": created_by_type,
    "fixed_cameras": camera_labels,
    "cutaway_hidden_shell_columns": len(cutaway_hidden),
    "promotion_blockers": [
        "Fresh fixed-camera screenshots must be inspected against Pro references.",
        "Candidate master-coil shading and face profile require close visual validation.",
        "Crane proportions and clearances require visual validation before gameplay animation.",
        "Candidate safety barrier and gate require fresh close and overview visual validation.",
        "No candidate asset is promoted by this build.",
    ],
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(
    "LINE_BOSS_FRONT_END_POPULATION_PASS "
    f"coils={result['visual_master_coil_count']} slots={len(store_positions)} cranes=2 map={MAP}"
)
