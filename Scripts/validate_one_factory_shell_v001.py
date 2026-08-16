"""Fresh-process validation for the protected One Factory shell v001.

This validator is intentionally independent: it does not import the builder.
It fresh-loads the exact map, checks the frozen actor/HISM/layout contract, and
proves the load left the map, protected department maps, every Config file and
every SaveGames file byte-identical.  Its only write is its JSON receipt below
``Saved/Audits/OneFactory/v001``.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
SCRIPT_FILE = ROOT / "Scripts/validate_one_factory_shell_v001.py"
BUILDER_FILE = ROOT / "Scripts/create_one_factory_shell_v001.py"
CREATE_RECEIPT = ROOT / "Saved/Audits/OneFactory/v001/one_factory_shell_create_v001.json"
AUDIT = ROOT / "Saved/Audits/OneFactory/v001/one_factory_shell_validation_v001.json"

MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
MAP_OBJECT = f"{MAP}.{MAP.rsplit('/', 1)[-1]}"
MAP_FILE = (
    ROOT
    / "Content/LineBoss/Factory/OneFactory/v001/Maps/"
      "LB_MoorcrossWorks_OneFactory_v001.umap"
)

PASS_STATUS = (
    "PASS__FRESH_RELOAD_ONE_FACTORY_NATIVE_HISM_SHELL_EXACT_AUTHORITIES_"
    "ZERO_PRODUCTION_MACHINE_OR_WIP"
)
CREATE_STATUS = (
    "PASS__ONE_FACTORY_NATIVE_HISM_SHELL_ONE_BOOTSTRAP_ONE_PRESS_AUTHORITY_"
    "ZERO_PRODUCTION_MACHINE_OR_WIP"
)
EXPECTED_BUILDER_SHA256 = "4EE0A437A9BCC3A5431C39B2D27BB05067FA74F1A6A586B5C2DF05E412131728"

GAME_MODE_CLASS_PATH = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
PAWN_CLASS_PATH = "/Script/LineBossCarFactory.LBManagementPawn"
HUD_CLASS_PATH = "/Script/LineBossCarFactory.LBControlRoomHUD"
BOOTSTRAP_CLASS_PATH = "/Script/LineBossCarFactory.LBOneFactoryBootstrap"
PRESS_AUTHORITY_CLASS_PATH = "/Script/LineBossCarFactory.LBPressShopBuildAuthority"
ENGINE_NAVIGATION_ACTOR_LABEL = "RecastNavMesh-Default"
ENGINE_NAVIGATION_ACTOR_CLASS_PATH = "/Script/NavigationSystem.RecastNavMesh"
EXPECTED_MAP_AUTHORED_ACTOR_COUNT = 25

CRITICAL_PROTECTED_HASHES = {
    "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap":
        "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
    "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap":
        "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5",
    "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap":
        "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F",
    "Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap":
        "2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069",
}

MAP_TAG = "LB.OneFactory.Shell.v001"
NATIVE_TAG = "LB.Provenance.NativeOnly"
ENV_TAG = "LB.OneFactory.Environment"
HISM_TAG = "LB.OneFactory.Environment.HISM"
GRID_TAG = "LB.OneFactory.Grid.100cm"
LIGHTING_AUTHORITY_TAG = "LB.OneFactory.Lighting.Authority.5000K.v001"
FIXED_EXPOSURE_TAG = "LB.OneFactory.Lighting.FixedExposure.v001"

FACTORY_CENTRE_CM = (0.0, 0.0, 1_500.0)
FACTORY_SIZE_CM = (62_000.0, 31_000.0, 3_000.0)
GRID_SIZE_CM = 100.0

CUBE_PATH = "/Engine/BasicShapes/Cube.Cube"
MATERIALS = {
    "floor": (
        "/Game/LineBoss/Materials/Environment/"
        "MI_LB_SealedFactoryConcrete_Neutral_v001."
        "MI_LB_SealedFactoryConcrete_Neutral_v001"
    ),
    "charcoal": "/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal",
    "steel": "/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel",
    "yellow": "/Game/LineBoss/Materials/M_LB_SafetyYellow.M_LB_SafetyYellow",
    "press": (
        "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_PR003_BlueGreen."
        "MI_LB_Floor_PR003_BlueGreen"
    ),
    "body": (
        "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_PR001_Blue."
        "MI_LB_Floor_PR001_Blue"
    ),
    "paint": (
        "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_PR004_Grey."
        "MI_LB_Floor_PR004_Grey"
    ),
    "assembly": (
        "/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_PR002_Orange."
        "MI_LB_Floor_PR002_Orange"
    ),
}

BUILD_BAYS = (
    {
        "id": "OF_BAY_PRESS_01", "department": "Press",
        "centre": (-14_500.0, 8_000.0, 1_000.0),
        "half_extent": (16_000.0, 6_500.0, 1_000.0), "floor_material": "press",
    },
    {
        "id": "OF_BAY_BODY_01", "department": "Body",
        "centre": (-11_000.0, -8_500.0, 1_000.0),
        "half_extent": (9_000.0, 5_000.0, 1_000.0), "floor_material": "body",
    },
    {
        "id": "OF_BAY_PAINT_01", "department": "Paint",
        "centre": (10_000.0, -8_500.0, 1_000.0),
        "half_extent": (11_000.0, 5_000.0, 1_000.0), "floor_material": "paint",
    },
    {
        "id": "OF_BAY_ASSEMBLY_01", "department": "Assembly",
        "centre": (16_500.0, 8_500.0, 1_000.0),
        "half_extent": (14_000.0, 6_000.0, 1_000.0), "floor_material": "assembly",
    },
)

PROTECTED_AREAS = (
    {"id": "OF_SPINE_LOGISTICS_EW_01", "centre": (0.0, 0.0, 200.0),
     "half_extent": (30_500.0, 600.0, 200.0)},
    {"id": "OF_SPINE_SERVICE_EW_01", "centre": (0.0, -14_500.0, 200.0),
     "half_extent": (30_500.0, 300.0, 200.0)},
)

UTILITY_SPINES = (
    {"id": "OF_SPINE_SERVICE_EW_01", "start": (-30_500.0, -14_500.0, 0.0),
     "end": (30_500.0, -14_500.0, 0.0),
     "maximum_connection_distance_cm": 30_000.0},
)

LOGISTICS_SPINES = (
    {"id": "OF_SPINE_LOGISTICS_EW_01", "start": (-30_500.0, 0.0, 0.0),
     "end": (30_500.0, 0.0, 0.0), "maximum_access_distance_cm": 1_200.0},
)

HISM_ACTORS = {
    "LB_OF_ENV_HISM_FloorSlabs_v001": {
        "component_tag": "LB.OneFactory.HISM.FloorSlabs.v001", "material": "floor",
        "collision_profile": "BlockAll", "cast_shadow": True,
        "tags": (MAP_TAG, NATIVE_TAG, ENV_TAG, HISM_TAG,
                 "LB.OneFactory.Environment.Floor"),
    },
    "LB_OF_ENV_HISM_CutawayWalls_v001": {
        "component_tag": "LB.OneFactory.HISM.CutawayWalls.v001", "material": "charcoal",
        "collision_profile": "BlockAll", "cast_shadow": True,
        "tags": (MAP_TAG, NATIVE_TAG, ENV_TAG, HISM_TAG,
                 "LB.OneFactory.Environment.Shell",
                 "LB.OneFactory.Environment.ManagementCutaway"),
    },
    "LB_OF_ENV_HISM_Columns_v001": {
        "component_tag": "LB.OneFactory.HISM.Columns.v001", "material": "steel",
        "collision_profile": "BlockAll", "cast_shadow": True,
        "tags": (MAP_TAG, NATIVE_TAG, ENV_TAG, HISM_TAG,
                 "LB.OneFactory.Environment.Structure"),
    },
    "LB_OF_ENV_HISM_OpenRoofFrame_v001": {
        "component_tag": "LB.OneFactory.HISM.OpenRoofFrame.v001", "material": "steel",
        "collision_profile": "BlockAll", "cast_shadow": True,
        "tags": (MAP_TAG, NATIVE_TAG, ENV_TAG, HISM_TAG,
                 "LB.OneFactory.Environment.Structure",
                 "LB.OneFactory.Environment.OpenRoof",
                 "LB.OneFactory.Environment.ManagementCutaway"),
    },
    "LB_OF_ENV_HISM_Grid100cm_v001": {
        "component_tag": "LB.OneFactory.HISM.Grid100cm.v001", "material": "charcoal",
        "collision_profile": "NoCollision", "cast_shadow": False,
        "tags": (MAP_TAG, NATIVE_TAG, ENV_TAG, HISM_TAG, GRID_TAG),
    },
    "LB_OF_ENV_HISM_SafetyLines_v001": {
        "component_tag": "LB.OneFactory.HISM.SafetyLines.v001", "material": "yellow",
        "collision_profile": "NoCollision", "cast_shadow": False,
        "tags": (MAP_TAG, NATIVE_TAG, ENV_TAG, HISM_TAG,
                 "LB.OneFactory.Environment.PaintedFloor",
                 "LB.OneFactory.Environment.BayBoundaries",
                 "LB.OneFactory.Environment.LogisticsBoundaries"),
    },
}
for _bay in BUILD_BAYS:
    HISM_ACTORS[f"LB_OF_ENV_HISM_DepartmentFloor_{_bay['department']}_v001"] = {
        "component_tag": f"LB.OneFactory.HISM.DepartmentFloor.{_bay['department']}.v001",
        "material": _bay["floor_material"], "collision_profile": "NoCollision",
        "cast_shadow": False,
        "tags": (MAP_TAG, NATIVE_TAG, ENV_TAG, HISM_TAG,
                 "LB.OneFactory.Environment.PaintedFloor",
                 "LB.OneFactory.DepartmentBay",
                 f"LB.OneFactory.Department.{_bay['department']}",
                 f"LB.OneFactory.BuildBay.{_bay['id']}", GRID_TAG),
    }


def floor_instances() -> list[dict[str, tuple[float, float, float]]]:
    return [
        {"location": (-29_450.0 + x_index * 3_100.0,
                      -13_950.0 + y_index * 3_100.0, -25.0),
         "dimensions": (3_100.0, 3_100.0, 50.0)}
        for x_index in range(20) for y_index in range(10)
    ]


def cutaway_wall_instances() -> list[dict[str, tuple[float, float, float]]]:
    return [
        {"location": (0.0, 15_500.0, 600.0), "dimensions": (62_000.0, 40.0, 1_200.0)},
        {"location": (-31_000.0, 0.0, 600.0), "dimensions": (40.0, 31_000.0, 1_200.0)},
        {"location": (31_000.0, 0.0, 600.0), "dimensions": (40.0, 31_000.0, 1_200.0)},
    ]


def column_instances() -> list[dict[str, tuple[float, float, float]]]:
    return [
        {"location": (float(x), y, 1_500.0), "dimensions": (90.0, 90.0, 3_000.0)}
        for x in range(-30_500, 30_501, 6_100) for y in (0.0, 14_500.0)
    ]


def roof_instances() -> list[dict[str, tuple[float, float, float]]]:
    rows = [
        {"location": (float(x), 0.0, 3_000.0), "dimensions": (90.0, 29_000.0, 90.0)}
        for x in range(-30_500, 30_501, 6_100)
    ]
    rows.extend([
        {"location": (0.0, 0.0, 3_000.0), "dimensions": (61_000.0, 90.0, 90.0)},
        {"location": (0.0, 14_500.0, 3_000.0), "dimensions": (61_000.0, 90.0, 90.0)},
    ])
    return rows


def grid_instances() -> list[dict[str, tuple[float, float, float]]]:
    rows = [
        {"location": (float(x), 0.0, 0.65), "dimensions": (0.6, 31_000.0, 0.6)}
        for x in range(-31_000, 31_001, 100)
    ]
    rows.extend(
        {"location": (0.0, float(y), 0.70), "dimensions": (62_000.0, 0.6, 0.6)}
        for y in range(-15_500, 15_501, 100)
    )
    return rows


def safety_instances() -> list[dict[str, tuple[float, float, float]]]:
    rows = []
    for bay in BUILD_BAYS:
        x, y, _ = bay["centre"]
        half_x, half_y, _ = bay["half_extent"]
        rows.extend([
            {"location": (x - half_x, y, 1.20), "dimensions": (12.0, half_y * 2.0, 1.0)},
            {"location": (x + half_x, y, 1.20), "dimensions": (12.0, half_y * 2.0, 1.0)},
            {"location": (x, y - half_y, 1.20), "dimensions": (half_x * 2.0, 12.0, 1.0)},
            {"location": (x, y + half_y, 1.20), "dimensions": (half_x * 2.0, 12.0, 1.0)},
        ])
    rows.extend([
        {"location": (0.0, -600.0, 1.25), "dimensions": (61_000.0, 12.0, 1.0)},
        {"location": (0.0, 600.0, 1.25), "dimensions": (61_000.0, 12.0, 1.0)},
        {"location": (0.0, -14_800.0, 1.25), "dimensions": (61_000.0, 12.0, 1.0)},
        {"location": (0.0, -14_200.0, 1.25), "dimensions": (61_000.0, 12.0, 1.0)},
    ])
    return rows


def expected_hism_instances() -> dict[str, list[dict[str, Any]]]:
    rows = {
        "LB_OF_ENV_HISM_FloorSlabs_v001": floor_instances(),
        "LB_OF_ENV_HISM_CutawayWalls_v001": cutaway_wall_instances(),
        "LB_OF_ENV_HISM_Columns_v001": column_instances(),
        "LB_OF_ENV_HISM_OpenRoofFrame_v001": roof_instances(),
        "LB_OF_ENV_HISM_Grid100cm_v001": grid_instances(),
        "LB_OF_ENV_HISM_SafetyLines_v001": safety_instances(),
    }
    for bay in BUILD_BAYS:
        x, y, _ = bay["centre"]
        half_x, half_y, _ = bay["half_extent"]
        rows[f"LB_OF_ENV_HISM_DepartmentFloor_{bay['department']}_v001"] = [{
            "location": (x, y, 0.25),
            "dimensions": (half_x * 2.0 - 40.0, half_y * 2.0 - 40.0, 0.5),
        }]
    return rows


DATUM_ACTORS = {
    **{
        f"LB_OF_DATUM_Bay_{bay['department']}_v001": {
            "class": "/Script/Engine.TargetPoint", "location": bay["centre"],
            "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
            "tags": (MAP_TAG, NATIVE_TAG, "LB.OneFactory.DepartmentBay",
                     f"LB.OneFactory.Department.{bay['department']}",
                     f"LB.OneFactory.BuildBay.{bay['id']}", GRID_TAG),
        }
        for bay in BUILD_BAYS
    },
    "LB_OF_DATUM_LogisticsSpine_EW_v001": {
        "class": "/Script/Engine.TargetPoint", "location": (0.0, 0.0, 200.0),
        "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
        "tags": (MAP_TAG, NATIVE_TAG, "LB.OneFactory.Logistics",
                 "LB.OneFactory.ProtectedArea.OF_SPINE_LOGISTICS_EW_01",
                 "LB.OneFactory.LogisticsSpine.OF_SPINE_LOGISTICS_EW_01",
                 "LB.OneFactory.Route.Start.-30500.0.0",
                 "LB.OneFactory.Route.End.30500.0.0",
                 "LB.OneFactory.Route.MaximumAccessCm.1200"),
    },
    "LB_OF_DATUM_ServiceSpine_EW_v001": {
        "class": "/Script/Engine.TargetPoint", "location": (0.0, -14_500.0, 200.0),
        "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
        "tags": (MAP_TAG, NATIVE_TAG, "LB.OneFactory.Service",
                 "LB.OneFactory.ProtectedArea.OF_SPINE_SERVICE_EW_01",
                 "LB.OneFactory.UtilitySpine.OF_SPINE_SERVICE_EW_01",
                 "LB.OneFactory.Route.Start.-30500.-14500.0",
                 "LB.OneFactory.Route.End.30500.-14500.0",
                 "LB.OneFactory.Route.MaximumConnectionCm.30000"),
    },
    "LB_OF_INTERFACE_CoilReceiving_v001": {
        "class": "/Script/Engine.TargetPoint", "location": (-30_500.0, 0.0, 0.0),
        "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
        "tags": (MAP_TAG, NATIVE_TAG, "LB.OneFactory.Interface.CoilReceiving",
                 "LB.OneFactory.LogisticsSpine.OF_SPINE_LOGISTICS_EW_01"),
    },
    "LB_OF_INTERFACE_FinishedVehicleDispatch_v001": {
        "class": "/Script/Engine.TargetPoint", "location": (30_500.0, 0.0, 0.0),
        "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
        "tags": (MAP_TAG, NATIVE_TAG,
                 "LB.OneFactory.Interface.FinishedVehicleDispatch",
                 "LB.OneFactory.LogisticsSpine.OF_SPINE_LOGISTICS_EW_01"),
    },
}


def expected_actor_specs() -> dict[str, dict[str, Any]]:
    specs = {
        label: {
            "class": "/Script/Engine.Actor", "location": (0.0, 0.0, 0.0),
            "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
            "tags": tuple(sorted(row["tags"])),
        }
        for label, row in HISM_ACTORS.items()
    }
    specs.update({
        label: {**row, "tags": tuple(sorted(row["tags"]))}
        for label, row in DATUM_ACTORS.items()
    })
    camera_location = (0.0, -43_000.0, 36_000.0)
    specs.update({
        "LB_OF_ENV_LightingAuthority_5000K_v001": {
            "class": "/Script/Engine.RectLight", "location": (0.0, 0.0, 6_500.0),
            "rotation": (-90.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
            "tags": tuple(sorted((MAP_TAG, NATIVE_TAG, ENV_TAG, LIGHTING_AUTHORITY_TAG))),
        },
        "LB_OF_ENV_FixedExposureAuthority_v001": {
            "class": "/Script/Engine.PostProcessVolume", "location": (0.0, 0.0, 0.0),
            "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
            "tags": tuple(sorted((MAP_TAG, NATIVE_TAG, ENV_TAG, FIXED_EXPOSURE_TAG))),
        },
        "LB_OF_PlayerStart_Management_v001": {
            "class": "/Script/Engine.PlayerStart",
            "location": (-28_000.0, -13_500.0, 200.0),
            "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
            "tags": tuple(sorted((MAP_TAG, NATIVE_TAG,
                                  "LB.OneFactory.PlayerStart.Management.v001"))),
        },
        "LB_OF_ManagementCamera_Overview_v001": {
            "class": "/Script/Engine.CameraActor", "location": camera_location,
            "look_at": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
            "tags": tuple(sorted((MAP_TAG, NATIVE_TAG,
                                  "LB.OneFactory.ManagementView.Overview.v001"))),
        },
        "LB_OF_NavBounds_FactoryEnvelope_v001": {
            "class": "/Script/NavigationSystem.NavMeshBoundsVolume",
            "location": FACTORY_CENTRE_CM, "rotation": (0.0, 0.0, 0.0),
            "scale": (310.0, 155.0, 15.0),
            "tags": tuple(sorted((MAP_TAG, NATIVE_TAG,
                                  "LB.OneFactory.Navigation.FactoryEnvelope.v001"))),
        },
        "LB_OneFactoryBootstrap_v001": {
            "class": BOOTSTRAP_CLASS_PATH, "location": (0.0, 0.0, 0.0),
            "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
            "tags": tuple(sorted(("LB.OneFactory.Bootstrap.v001", NATIVE_TAG))),
        },
        "LB_OneFactory_PressBuildAuthority_v001": {
            "class": PRESS_AUTHORITY_CLASS_PATH, "location": (0.0, 0.0, 0.0),
            "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
            "tags": tuple(sorted((
                "LB.OneFactory.MapAuthored.PressBuildAuthority.v001", NATIVE_TAG
            ))),
        },
        ENGINE_NAVIGATION_ACTOR_LABEL: {
            "class": ENGINE_NAVIGATION_ACTOR_CLASS_PATH,
            "location": (0.0, 0.0, 0.0),
            "rotation": (0.0, 0.0, 0.0), "scale": (1.0, 1.0, 1.0),
            "tags": (),
        },
    })
    return specs


EXPECTED_ACTORS = expected_actor_specs()
EXPECTED_NONFOUNDATION_ACTOR_COUNT = 26
EXPECTED_HISM_INSTANCE_COUNTS = {
    label: len(rows) for label, rows in expected_hism_instances().items()
}
EXPECTED_TOTAL_HISM_INSTANCES = 1_194

if len(EXPECTED_ACTORS) != EXPECTED_NONFOUNDATION_ACTOR_COUNT:
    raise AssertionError("Frozen One Factory actor cardinality must remain exactly 26")
if sum(EXPECTED_HISM_INSTANCE_COUNTS.values()) != EXPECTED_TOTAL_HISM_INSTANCES:
    raise AssertionError("Frozen One Factory HISM cardinality must remain exactly 1194")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def project_relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def path_name(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return value.get_path_name()
    except Exception:
        return str(value)


def vector_tuple(value: Any) -> tuple[float, float, float]:
    return float(value.x), float(value.y), float(value.z)


def rotator_tuple(value: Any) -> tuple[float, float, float]:
    return float(value.pitch), float(value.yaw), float(value.roll)


def close_tuple(actual: Iterable[float] | None, expected: Iterable[float],
                tolerance: float) -> bool:
    if actual is None:
        return False
    actual_values = tuple(actual)
    expected_values = tuple(expected)
    return len(actual_values) == len(expected_values) and all(
        abs(float(left) - float(right)) <= tolerance
        for left, right in zip(actual_values, expected_values)
    )


def tags_of(actor: Any) -> tuple[str, ...]:
    return tuple(sorted(str(tag) for tag in actor.get_editor_property("tags")))


def protected_snapshot() -> dict[str, str]:
    paths = [ROOT / relative for relative in CRITICAL_PROTECTED_HASHES]
    config_root = ROOT / "Config"
    if config_root.is_dir():
        paths.extend(sorted(path for path in config_root.rglob("*") if path.is_file()))
    save_root = ROOT / "Saved/SaveGames"
    if save_root.exists():
        paths.extend(sorted(path for path in save_root.rglob("*") if path.is_file()))
    result = {}
    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"Protected file is missing: {project_relative(path)}")
        result[project_relative(path)] = sha256(path)
    for relative, expected in CRITICAL_PROTECTED_HASHES.items():
        if result.get(relative) != expected:
            raise RuntimeError(f"Protected critical hash drift: {relative}")
    return dict(sorted(result.items()))


def get_editor_world():
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if subsystem is not None:
        return subsystem.get_editor_world()
    return unreal.EditorLevelLibrary.get_editor_world()


def world_partition_evidence(world: Any) -> dict[str, Any]:
    getter = getattr(world, "get_world_partition", None)
    if callable(getter):
        partition = getter()
        return {"api": "get_world_partition", "enabled": partition is not None,
                "object": path_name(partition)}
    try:
        partition = world.get_world_settings().get_editor_property("world_partition")
        return {"api": "WorldSettings.world_partition", "enabled": partition is not None,
                "object": path_name(partition)}
    except Exception as exc:
        return {"api": None, "enabled": None, "error": f"{type(exc).__name__}: {exc}"}


def add_check(state: dict[str, Any], name: str, passed: bool,
              expected: Any = None, actual: Any = None) -> None:
    row = {"name": name, "passed": bool(passed)}
    if expected is not None:
        row["expected"] = expected
    if actual is not None:
        row["actual"] = actual
    state["checks"].append(row)
    if not passed:
        state["failures"].append({key: value for key, value in row.items() if key != "passed"})


def expected_rotation(spec: dict[str, Any]):
    if "look_at" in spec:
        return unreal.MathLibrary.find_look_at_rotation(
            unreal.Vector(*spec["location"]), unreal.Vector(*spec["look_at"])
        )
    pitch, yaw, roll = spec["rotation"]
    return unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw)


def validate_actor_contract(state: dict[str, Any], label: str, actor: Any,
                            spec: dict[str, Any]) -> dict[str, Any]:
    actual_rotation = actor.get_actor_rotation()
    expected_rotator = expected_rotation(spec)
    actual = {
        "class": path_name(actor.get_class()),
        "location": list(vector_tuple(actor.get_actor_location())),
        "rotation": list(rotator_tuple(actual_rotation)),
        "scale": list(vector_tuple(actor.get_actor_scale3d())),
        "tags": list(tags_of(actor)),
    }
    expected = {
        "class": spec["class"], "location": list(spec["location"]),
        "rotation": list(rotator_tuple(expected_rotator)), "scale": list(spec["scale"]),
        "tags": list(spec["tags"]),
    }
    valid = (
        actual["class"] == expected["class"]
        and close_tuple(actual["location"], expected["location"], 0.02)
        and actual_rotation.is_near_equal(expected_rotator, 0.02)
        and close_tuple(actual["scale"], expected["scale"], 0.0002)
        and actual["tags"] == expected["tags"]
    )
    add_check(state, f"exact_actor_contract::{label}", valid, expected, actual)
    return {"valid": valid, **actual}


def unpack_instance_transform(result: Any):
    if isinstance(result, tuple):
        if len(result) == 2 and isinstance(result[0], bool):
            if not result[0]:
                return None
            return result[1]
        if len(result) == 2 and isinstance(result[1], bool):
            if not result[1]:
                return None
            return result[0]
        return result[-1] if result else None
    return result


def transform_evidence(transform: Any) -> dict[str, Any] | None:
    if transform is None:
        return None
    rotation = transform.rotation
    return {
        "location": list(vector_tuple(transform.translation)),
        "scale": list(vector_tuple(transform.scale3d)),
        "quaternion": [float(rotation.x), float(rotation.y),
                       float(rotation.z), float(rotation.w)],
    }


def validate_hism_contracts(state: dict[str, Any], by_label: dict[str, list[Any]],
                            facts: dict[str, Any]) -> None:
    expected_instances = expected_hism_instances()
    rows = {}
    for label, spec in HISM_ACTORS.items():
        actors = by_label.get(label, [])
        if len(actors) != 1:
            continue
        components = actors[0].get_components_by_class(
            unreal.HierarchicalInstancedStaticMeshComponent
        )
        add_check(state, f"exact_one_hism_component::{label}", len(components) == 1,
                  1, len(components))
        if len(components) != 1:
            continue
        component = components[0]
        component_tags = tuple(sorted(
            str(tag) for tag in component.get_editor_property("component_tags")
        ))
        actual_base = {
            "class": path_name(component.get_class()),
            "component_tags": list(component_tags),
            "mesh": path_name(component.get_editor_property("static_mesh")),
            "material": path_name(component.get_material(0)),
            "collision_profile": str(component.get_collision_profile_name()),
            "can_ever_affect_navigation": component.get_editor_property(
                "can_ever_affect_navigation"
            ),
            "cast_shadow": component.get_editor_property("cast_shadow"),
            "instance_count": int(component.get_instance_count()),
        }
        expected_base = {
            "class": "/Script/Engine.HierarchicalInstancedStaticMeshComponent",
            "component_tags": [spec["component_tag"]], "mesh": CUBE_PATH,
            "material": MATERIALS[spec["material"]],
            "collision_profile": spec["collision_profile"],
            "can_ever_affect_navigation": False,
            "cast_shadow": spec["cast_shadow"],
            "instance_count": len(expected_instances[label]),
        }
        base_valid = actual_base == expected_base
        add_check(state, f"hism_component_contract::{label}", base_valid,
                  expected_base, actual_base)

        transform_failures = []
        transform_rows = []
        if actual_base["instance_count"] == expected_base["instance_count"]:
            for index, expected_instance in enumerate(expected_instances[label]):
                transform = unpack_instance_transform(
                    component.get_instance_transform(index, False)
                )
                actual_transform = transform_evidence(transform)
                expected_transform = {
                    "location": list(expected_instance["location"]),
                    "scale": [value / 100.0 for value in expected_instance["dimensions"]],
                    "quaternion": [0.0, 0.0, 0.0, 1.0],
                }
                valid = (
                    actual_transform is not None
                    and close_tuple(actual_transform["location"],
                                    expected_transform["location"], 0.02)
                    and close_tuple(actual_transform["scale"],
                                    expected_transform["scale"], 0.0002)
                    and close_tuple(actual_transform["quaternion"],
                                    expected_transform["quaternion"], 0.0002)
                )
                if not valid:
                    transform_failures.append({
                        "index": index, "expected": expected_transform,
                        "actual": actual_transform,
                    })
                if index < 4 or index >= len(expected_instances[label]) - 4:
                    transform_rows.append({"index": index, "valid": valid,
                                           "actual": actual_transform})
        else:
            transform_failures.append({
                "reason": "instance count mismatch blocks ordered transform validation"
            })
        add_check(state, f"all_ordered_hism_instance_transforms::{label}",
                  not transform_failures, [], transform_failures[:20])
        rows[label] = {
            "valid": base_valid and not transform_failures,
            **actual_base,
            "ordered_transform_failure_count": len(transform_failures),
            "first_and_last_transform_evidence": transform_rows,
        }
    facts["hism_contracts"] = rows
    facts["hism_actor_count"] = len(rows)
    facts["hism_total_instance_count"] = sum(
        row.get("instance_count", 0) for row in rows.values()
    )
    add_check(state, "exact_10_hism_actors", len(rows) == 10, 10, len(rows))
    add_check(state, "exact_1194_hism_instances",
              facts["hism_total_instance_count"] == EXPECTED_TOTAL_HISM_INSTANCES,
              EXPECTED_TOTAL_HISM_INSTANCES, facts["hism_total_instance_count"])


def struct_vector(row: Any, property_name: str) -> list[float]:
    return list(vector_tuple(row.get_editor_property(property_name)))


def validate_press_authority(state: dict[str, Any], authority: Any,
                             facts: dict[str, Any]) -> None:
    rows = {}
    actual_bays = list(authority.get_editor_property("build_bays"))
    bay_evidence = []
    for index, expected in enumerate(BUILD_BAYS):
        actual = actual_bays[index] if index < len(actual_bays) else None
        evidence = {
            "id": str(actual.get_editor_property("bay_id")) if actual else None,
            "centre": struct_vector(actual, "centre") if actual else None,
            "half_extent": struct_vector(actual, "half_extent") if actual else None,
        }
        valid = (
            actual is not None and evidence["id"] == expected["id"]
            and close_tuple(evidence["centre"], expected["centre"], 0.02)
            and close_tuple(evidence["half_extent"], expected["half_extent"], 0.02)
        )
        evidence["valid"] = valid
        bay_evidence.append(evidence)
    add_check(state, "press_authority_exact_four_build_bays",
              len(actual_bays) == len(BUILD_BAYS) and all(row["valid"] for row in bay_evidence),
              list(BUILD_BAYS), bay_evidence)
    rows["build_bays"] = bay_evidence

    def check_array(property_name: str, expected_rows: tuple[dict[str, Any], ...],
                    id_property: str, vector_properties: tuple[str, ...],
                    scalar_property: str | None = None) -> list[dict[str, Any]]:
        actual_values = list(authority.get_editor_property(property_name))
        evidence = []
        for index, expected in enumerate(expected_rows):
            actual = actual_values[index] if index < len(actual_values) else None
            item = {"id": str(actual.get_editor_property(id_property)) if actual else None}
            valid = actual is not None and item["id"] == expected["id"]
            for vector_property in vector_properties:
                item[vector_property] = struct_vector(actual, vector_property) if actual else None
                valid = valid and close_tuple(
                    item[vector_property], expected[vector_property], 0.02
                )
            if scalar_property:
                item[scalar_property] = (
                    float(actual.get_editor_property(scalar_property)) if actual else None
                )
                valid = valid and abs(
                    item[scalar_property] - expected[scalar_property]
                ) <= 0.01
            item["valid"] = bool(valid)
            evidence.append(item)
        add_check(state, f"press_authority_exact_{property_name}",
                  len(actual_values) == len(expected_rows)
                  and all(item["valid"] for item in evidence),
                  list(expected_rows), evidence)
        return evidence

    rows["protected_areas"] = check_array(
        "protected_areas", PROTECTED_AREAS, "area_id", ("centre", "half_extent")
    )
    rows["utility_spines"] = check_array(
        "utility_spines", UTILITY_SPINES, "spine_id", ("start", "end"),
        "maximum_connection_distance_cm"
    )
    rows["logistics_spines"] = check_array(
        "logistics_spines", LOGISTICS_SPINES, "spine_id", ("start", "end"),
        "maximum_access_distance_cm"
    )
    storage_count = len(list(authority.get_editor_property("storage_bays")))
    add_check(state, "press_authority_zero_storage_bays", storage_count == 0, 0, storage_count)
    rows["storage_bay_count"] = storage_count
    facts["press_authority_contract"] = rows


def validate_lighting_and_camera(state: dict[str, Any], by_label: dict[str, list[Any]],
                                 facts: dict[str, Any]) -> None:
    light = by_label.get("LB_OF_ENV_LightingAuthority_5000K_v001", [])
    if len(light) == 1:
        component = light[0].get_component_by_class(unreal.RectLightComponent)
        actual = {
            "intensity": float(component.get_editor_property("intensity")) if component else None,
            "intensity_units": str(component.get_editor_property("intensity_units")) if component else None,
            "attenuation_radius": float(component.get_editor_property("attenuation_radius")) if component else None,
            "source_width": float(component.get_editor_property("source_width")) if component else None,
            "source_height": float(component.get_editor_property("source_height")) if component else None,
            "use_temperature": component.get_editor_property("use_temperature") if component else None,
            "temperature": float(component.get_editor_property("temperature")) if component else None,
        }
        expected = {
            "intensity": 800_000.0, "intensity_units": str(unreal.LightUnits.LUMENS),
            "attenuation_radius": 45_000.0, "source_width": 60_000.0,
            "source_height": 29_000.0, "use_temperature": True,
            "temperature": 5_000.0,
        }
        valid = component is not None and all((
            abs(actual["intensity"] - expected["intensity"]) <= 0.01,
            actual["intensity_units"] == expected["intensity_units"],
            abs(actual["attenuation_radius"] - expected["attenuation_radius"]) <= 0.01,
            abs(actual["source_width"] - expected["source_width"]) <= 0.01,
            abs(actual["source_height"] - expected["source_height"]) <= 0.01,
            actual["use_temperature"] is True,
            abs(actual["temperature"] - expected["temperature"]) <= 0.01,
        ))
        add_check(state, "single_5000k_lighting_authority_contract", valid, expected, actual)
        facts["lighting_authority"] = actual

    exposure = by_label.get("LB_OF_ENV_FixedExposureAuthority_v001", [])
    if len(exposure) == 1:
        actor = exposure[0]
        settings = actor.get_editor_property("settings")
        method = settings.get_editor_property("auto_exposure_method")
        actual = {
            "unbound": actor.get_editor_property("unbound"),
            "blend_weight": float(actor.get_editor_property("blend_weight")),
            "override_method": settings.get_editor_property("override_auto_exposure_method"),
            "method": str(method),
            "override_min": settings.get_editor_property("override_auto_exposure_min_brightness"),
            "override_max": settings.get_editor_property("override_auto_exposure_max_brightness"),
            "min": float(settings.get_editor_property("auto_exposure_min_brightness")),
            "max": float(settings.get_editor_property("auto_exposure_max_brightness")),
            "override_bias": settings.get_editor_property("override_auto_exposure_bias"),
            "bias": float(settings.get_editor_property("auto_exposure_bias")),
        }
        valid = all((
            actual["unbound"] is True, abs(actual["blend_weight"] - 1.0) <= 0.01,
            actual["override_method"] is True,
            method == unreal.AutoExposureMethod.AEM_BASIC,
            actual["override_min"] is True, actual["override_max"] is True,
            abs(actual["min"] - 1.0) <= 0.01, abs(actual["max"] - 1.0) <= 0.01,
            actual["override_bias"] is True, abs(actual["bias"]) <= 0.01,
        ))
        add_check(state, "single_fixed_exposure_authority_contract", valid, True, actual)
        facts["fixed_exposure_authority"] = actual

    camera = by_label.get("LB_OF_ManagementCamera_Overview_v001", [])
    if len(camera) == 1:
        component = camera[0].get_editor_property("camera_component")
        actual = {
            "field_of_view": float(component.get_editor_property("field_of_view")),
            "aspect_ratio": float(component.get_editor_property("aspect_ratio")),
            "constrain_aspect_ratio": component.get_editor_property("constrain_aspect_ratio"),
        }
        valid = (
            abs(actual["field_of_view"] - 48.0) <= 0.01
            and abs(actual["aspect_ratio"] - 16.0 / 9.0) <= 0.0001
            and actual["constrain_aspect_ratio"] is True
        )
        add_check(state, "management_camera_component_contract", valid,
                  {"field_of_view": 48.0, "aspect_ratio": 16.0 / 9.0,
                   "constrain_aspect_ratio": True}, actual)
        facts["management_camera"] = actual


def validate_bootstrap(state: dict[str, Any], bootstrap: Any, facts: dict[str, Any]) -> None:
    method = getattr(bootstrap, "validate_and_lock_shell", None)
    callable_method = callable(method)
    add_check(state, "bootstrap_validate_and_lock_shell_reflected", callable_method, True,
              callable_method)
    passed = False
    reason = "method unavailable"
    if callable_method:
        result = method()
        if isinstance(result, tuple):
            passed = bool(result[0])
            reason = str(result[1]) if len(result) > 1 else ""
        else:
            passed = bool(result)
            reason = ""
    valid_method = getattr(bootstrap, "has_valid_shell", None)
    has_valid_shell = bool(valid_method()) if callable(valid_method) else False
    add_check(state, "bootstrap_validates_and_locks_exact_shell",
              passed and has_valid_shell, True,
              {"validate_and_lock_shell": passed, "has_valid_shell": has_valid_shell,
               "reason": reason})
    facts["bootstrap_validation"] = {
        "validate_and_lock_shell": passed, "has_valid_shell": has_valid_shell,
        "reason": reason,
    }


def validate_creation_chain(state: dict[str, Any], facts: dict[str, Any]) -> None:
    builder_hash = sha256(BUILDER_FILE) if BUILDER_FILE.is_file() else None
    add_check(state, "frozen_builder_hash", builder_hash == EXPECTED_BUILDER_SHA256,
              EXPECTED_BUILDER_SHA256, builder_hash)
    add_check(state, "creation_receipt_exists", CREATE_RECEIPT.is_file(), True,
              CREATE_RECEIPT.is_file())
    add_check(state, "map_file_exists", MAP_FILE.is_file(), True, MAP_FILE.is_file())
    if not CREATE_RECEIPT.is_file() or not MAP_FILE.is_file():
        return
    receipt = json.loads(CREATE_RECEIPT.read_text(encoding="utf-8-sig"))
    current_map_hash = sha256(MAP_FILE)
    facts["creation_receipt"] = {
        "path": project_relative(CREATE_RECEIPT), "sha256": sha256(CREATE_RECEIPT),
        "status": receipt.get("status"), "map_sha256": receipt.get("map_sha256"),
    }
    add_check(state, "creation_receipt_schema",
              receipt.get("$schema") == "lineboss/audit/one-factory/shell-create-v001/v1",
              "lineboss/audit/one-factory/shell-create-v001/v1", receipt.get("$schema"))
    add_check(state, "creation_receipt_status", receipt.get("status") == CREATE_STATUS,
              CREATE_STATUS, receipt.get("status"))
    add_check(state, "creation_receipt_exact_map", receipt.get("map") == MAP,
              MAP, receipt.get("map"))
    add_check(state, "creation_receipt_builder_hash",
              receipt.get("builder_script_sha256") == EXPECTED_BUILDER_SHA256,
              EXPECTED_BUILDER_SHA256, receipt.get("builder_script_sha256"))
    add_check(state, "current_map_hash_matches_creation_receipt",
              receipt.get("map_sha256") == current_map_hash,
              receipt.get("map_sha256"), current_map_hash)
    facts["map_sha256_before_load"] = current_map_hash
    facts["creation_protected_hashes"] = receipt.get("protected_hashes", {})


def validate_loaded_map(state: dict[str, Any], facts: dict[str, Any]) -> None:
    classes = {}
    for path in (
        GAME_MODE_CLASS_PATH, PAWN_CLASS_PATH, HUD_CLASS_PATH,
        BOOTSTRAP_CLASS_PATH, PRESS_AUTHORITY_CLASS_PATH,
    ):
        value = unreal.load_class(None, path)
        classes[path] = value
        add_check(state, f"compiled_class::{path}", value is not None, path, path_name(value))
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    add_check(state, "level_editor_subsystem", levels is not None, True, levels is not None)
    add_check(state, "editor_actor_subsystem", actors_api is not None, True, actors_api is not None)
    if levels is None or actors_api is None or not MAP_FILE.is_file():
        return
    loaded = bool(levels.load_level(MAP))
    add_check(state, "fresh_load_exact_map", loaded, True, loaded)
    if not loaded:
        return
    world = get_editor_world()
    add_check(state, "editor_world_after_load", world is not None, True, world is not None)
    if world is None:
        return
    facts["world"] = world.get_path_name()
    add_check(state, "exact_loaded_world", world.get_path_name() == MAP_OBJECT,
              MAP_OBJECT, world.get_path_name())
    partition = world_partition_evidence(world)
    facts["world_partition"] = partition
    add_check(state, "non_world_partition", partition.get("enabled") is False,
              False, partition)

    settings = world.get_world_settings()
    game_mode = settings.get_editor_property("default_game_mode") if settings else None
    add_check(state, "map_local_one_factory_game_mode",
              game_mode == classes[GAME_MODE_CLASS_PATH],
              GAME_MODE_CLASS_PATH, path_name(game_mode))
    game_mode_cdo = unreal.get_default_object(classes[GAME_MODE_CLASS_PATH]) \
        if classes[GAME_MODE_CLASS_PATH] else None
    default_pawn = game_mode_cdo.get_editor_property("default_pawn_class") \
        if game_mode_cdo else None
    hud_class = game_mode_cdo.get_editor_property("hud_class") if game_mode_cdo else None
    add_check(state, "one_factory_game_mode_management_pawn",
              default_pawn == classes[PAWN_CLASS_PATH], PAWN_CLASS_PATH,
              path_name(default_pawn))
    add_check(state, "one_factory_game_mode_control_room_hud",
              hud_class == classes[HUD_CLASS_PATH], HUD_CLASS_PATH, path_name(hud_class))
    facts["player_shell"] = {
        "game_mode": path_name(game_mode), "default_pawn": path_name(default_pawn),
        "hud": path_name(hud_class), "global_default_engine_untouched": True,
    }

    actors = list(actors_api.get_all_level_actors())
    nonfoundation = [
        actor for actor in actors
        if path_name(actor.get_class()) not in {
            "/Script/Engine.WorldSettings", "/Script/Engine.DefaultPhysicsVolume"
        }
    ]
    by_label: dict[str, list[Any]] = {}
    for actor in nonfoundation:
        by_label.setdefault(actor.get_actor_label(), []).append(actor)
    actual_labels = set(by_label)
    expected_labels = set(EXPECTED_ACTORS)
    label_evidence = {
        "missing": sorted(expected_labels - actual_labels),
        "unexpected": sorted(actual_labels - expected_labels),
        "duplicates": sorted(label for label, rows in by_label.items() if len(rows) != 1),
    }
    add_check(state, "exact_26_nonfoundation_actors",
              len(nonfoundation) == EXPECTED_NONFOUNDATION_ACTOR_COUNT,
              EXPECTED_NONFOUNDATION_ACTOR_COUNT, len(nonfoundation))
    add_check(state, "exact_actor_label_cardinality", not any(label_evidence.values()),
              {"labels": sorted(expected_labels), "count_per_label": 1}, label_evidence)
    facts["actor_count"] = len(actors)
    facts["nonfoundation_actor_count"] = len(nonfoundation)
    facts["map_authored_actor_count"] = len(nonfoundation) - len(
        by_label.get(ENGINE_NAVIGATION_ACTOR_LABEL, [])
    )
    facts["engine_generated_navigation_actor_count"] = len(
        by_label.get(ENGINE_NAVIGATION_ACTOR_LABEL, [])
    )
    add_check(state, "exact_25_map_authored_actors",
              facts["map_authored_actor_count"] == EXPECTED_MAP_AUTHORED_ACTOR_COUNT,
              EXPECTED_MAP_AUTHORED_ACTOR_COUNT, facts["map_authored_actor_count"])

    actor_rows = {}
    for label, spec in EXPECTED_ACTORS.items():
        matches = by_label.get(label, [])
        if len(matches) == 1:
            actor_rows[label] = validate_actor_contract(state, label, matches[0], spec)
    facts["actor_contracts"] = actor_rows

    bootstrap_class = classes[BOOTSTRAP_CLASS_PATH]
    authority_class = classes[PRESS_AUTHORITY_CLASS_PATH]
    bootstraps = [actor for actor in actors if bootstrap_class and actor.get_class() == bootstrap_class]
    authorities = [actor for actor in actors if authority_class and actor.get_class() == authority_class]
    add_check(state, "exactly_one_lb_one_factory_bootstrap", len(bootstraps) == 1,
              1, len(bootstraps))
    add_check(state, "exactly_one_map_authored_press_build_authority",
              len(authorities) == 1, 1, len(authorities))

    navigation_rows = by_label.get(ENGINE_NAVIGATION_ACTOR_LABEL, [])
    navigation = navigation_rows[0] if len(navigation_rows) == 1 else None
    bootstrap = bootstraps[0] if len(bootstraps) == 1 else None
    navigation_relationship = {
        "owner": path_name(navigation.get_owner()) if navigation else None,
        "attach_parent_actor": (
            path_name(navigation.get_attach_parent_actor()) if navigation else None
        ),
        "outer": path_name(navigation.get_outer()) if navigation else None,
        "bootstrap_outer": path_name(bootstrap.get_outer()) if bootstrap else None,
        "same_persistent_level_as_bootstrap": bool(
            navigation and bootstrap and navigation.get_outer() == bootstrap.get_outer()
        ),
    }
    add_check(
        state, "engine_generated_navigation_relationship_contract",
        navigation is not None
        and bootstrap is not None
        and navigation.get_owner() is None
        and navigation.get_attach_parent_actor() is None
        and navigation.get_outer() == bootstrap.get_outer(),
        {"owner": None, "attach_parent_actor": None,
         "same_persistent_level_as_bootstrap": True},
        navigation_relationship,
    )
    facts["engine_generated_navigation_relationship"] = navigation_relationship

    unapproved_project = [
        {"label": actor.get_actor_label(), "class": path_name(actor.get_class())}
        for actor in actors
        if path_name(actor.get_class()).startswith("/Script/LineBossCarFactory.")
        and actor.get_class() not in {bootstrap_class, authority_class}
    ]
    add_check(state, "zero_unapproved_project_or_production_actors",
              not unapproved_project, [], unapproved_project)
    # The FinishedVehicleDispatch datum is an interface marker, not a vehicle actor.
    forbidden_terms = ("WIP", "Machine", "Station", "Robot", "CellActor")
    forbidden_identity = []
    for actor in actors:
        identity = (actor.get_actor_label(), *tags_of(actor))
        if any(term.lower() in item.lower() for term in forbidden_terms for item in identity):
            forbidden_identity.append(list(identity))
    add_check(state, "zero_production_machine_or_wip_identity",
              not forbidden_identity, [], forbidden_identity)
    facts["production_machine_or_wip_actor_count"] = len(forbidden_identity)

    if len(authorities) == 1:
        authority_relationship = {
            "owner": path_name(authorities[0].get_owner()),
            "attach_parent_actor": path_name(authorities[0].get_attach_parent_actor()),
            "outer": path_name(authorities[0].get_outer()),
            "bootstrap_outer": path_name(bootstraps[0].get_outer())
                if len(bootstraps) == 1 else None,
        }
        add_check(
            state,
            "press_authority_map_authored_relationship_contract",
            authorities[0].get_owner() is None
            and authorities[0].get_attach_parent_actor() is None
            and len(bootstraps) == 1
            and authorities[0].get_outer() == bootstraps[0].get_outer(),
            {"owner": None, "attach_parent_actor": None,
             "same_persistent_level_as_bootstrap": True},
            authority_relationship,
        )
        facts["press_authority_map_authored_relationship"] = authority_relationship
        validate_press_authority(state, authorities[0], facts)
    if len(bootstraps) == 1:
        validate_bootstrap(state, bootstraps[0], facts)
    validate_hism_contracts(state, by_label, facts)
    validate_lighting_and_camera(state, by_label, facts)


def main() -> None:
    if AUDIT.exists():
        raise RuntimeError(f"Refusing to overwrite One Factory validation receipt: {AUDIT}")
    state: dict[str, Any] = {"checks": [], "failures": []}
    facts: dict[str, Any] = {
        "fresh_load_requested": MAP,
        "factory_envelope": {"centre_cm": list(FACTORY_CENTRE_CM),
                             "size_cm": list(FACTORY_SIZE_CM)},
        "grid_size_cm": GRID_SIZE_CM,
    }
    before_protected = {}
    try:
        before_protected = protected_snapshot()
        facts["protected_hashes_before_load"] = before_protected
        validate_creation_chain(state, facts)
        receipt = (json.loads(CREATE_RECEIPT.read_text(encoding="utf-8-sig"))
                   if CREATE_RECEIPT.is_file() else {})
        add_check(state, "creation_protected_hashes_match_current",
                  receipt.get("protected_hashes") == before_protected,
                  receipt.get("protected_hashes"), before_protected)
        validate_loaded_map(state, facts)
    except Exception as exc:
        add_check(state, "unhandled_validation_exception", False,
                  "no exception", f"{type(exc).__name__}: {exc}")

    try:
        after_protected = protected_snapshot()
        facts["protected_hashes_after_load"] = after_protected
        add_check(state, "protected_maps_all_config_and_all_saves_unchanged",
                  before_protected == after_protected, before_protected, after_protected)
        map_hash_after = sha256(MAP_FILE) if MAP_FILE.is_file() else None
        facts["map_sha256_after_load"] = map_hash_after
        add_check(state, "map_byte_identical_after_fresh_load",
                  facts.get("map_sha256_before_load") == map_hash_after,
                  facts.get("map_sha256_before_load"), map_hash_after)
    except Exception as exc:
        add_check(state, "post_load_immutability_exception", False,
                  "no exception", f"{type(exc).__name__}: {exc}")

    result = {
        "$schema": "lineboss/audit/one-factory/shell-validation-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": PASS_STATUS if not state["failures"] else "FAIL",
        "validator_script": project_relative(SCRIPT_FILE),
        "validator_script_sha256": sha256(SCRIPT_FILE),
        "builder_script": project_relative(BUILDER_FILE),
        "builder_script_sha256": sha256(BUILDER_FILE) if BUILDER_FILE.is_file() else None,
        "creation_receipt": project_relative(CREATE_RECEIPT),
        "creation_receipt_sha256": sha256(CREATE_RECEIPT) if CREATE_RECEIPT.is_file() else None,
        "map": MAP,
        "map_file": project_relative(MAP_FILE),
        "map_sha256": sha256(MAP_FILE) if MAP_FILE.is_file() else None,
        "facts": facts,
        "checks": state["checks"],
        "protected_hashes": facts.get("protected_hashes_after_load", {}),
        "writes_to_content_config_or_saves": False,
        "failures": state["failures"],
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if result["status"] == PASS_STATUS:
        unreal.log(
            "LINE_BOSS_ONE_FACTORY_SHELL_VALIDATION_V001_PASS "
            f"map={MAP} map_sha256={result['map_sha256']}"
        )
        return
    names = [row.get("name", "unknown") for row in state["failures"]]
    unreal.log_error(
        "LINE_BOSS_ONE_FACTORY_SHELL_VALIDATION_V001_FAIL " + ",".join(names)
    )
    raise RuntimeError("One Factory shell validation failed: " + ", ".join(names))


if __name__ == "__main__":
    main()
