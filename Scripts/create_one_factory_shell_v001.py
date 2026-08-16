"""Create the protected Moorcross Works One Factory shell exactly once.

This is a one-shot Unreal Editor Python authoring script.  It creates only
``/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001``
as a basic non-World-Partition level.  The map owns the common hall,
management/navigation context, exact canonical department/route datums, one
``ALBOneFactoryBootstrap`` and one map-authored
``ALBPressShopBuildAuthority``.  It deliberately owns zero production
machines, cells, stations, robots, vehicles or WIP.

The script refuses an existing destination or receipt.  Press v913, restored
Press, isolated Body/Paint maps, every Config file and every SaveGames file are
hashed before authoring and must remain byte-identical afterwards.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
SCRIPT_FILE = ROOT / "Scripts/create_one_factory_shell_v001.py"
MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
MAP_OBJECT = f"{MAP}.{MAP.rsplit('/', 1)[-1]}"
MAP_FILE = (
    ROOT
    / "Content/LineBoss/Factory/OneFactory/v001/Maps/"
      "LB_MoorcrossWorks_OneFactory_v001.umap"
)
AUDIT = ROOT / "Saved/Audits/OneFactory/v001/one_factory_shell_create_v001.json"

GAME_MODE_CLASS_PATH = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
PAWN_CLASS_PATH = "/Script/LineBossCarFactory.LBManagementPawn"
HUD_CLASS_PATH = "/Script/LineBossCarFactory.LBControlRoomHUD"
BOOTSTRAP_CLASS_PATH = "/Script/LineBossCarFactory.LBOneFactoryBootstrap"
PRESS_AUTHORITY_CLASS_PATH = "/Script/LineBossCarFactory.LBPressShopBuildAuthority"
ENGINE_NAVIGATION_ACTOR_LABEL = "RecastNavMesh-Default"
ENGINE_NAVIGATION_ACTOR_CLASS_PATH = "/Script/NavigationSystem.RecastNavMesh"
EXPECTED_MAP_AUTHORED_ACTOR_COUNT = 25
EXPECTED_FRESH_RELOAD_NONFOUNDATION_ACTOR_COUNT = 26

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

# Canonical gameplay envelope supplied by the native One Factory authority.
# The order is part of the save/migration contract.
BUILD_BAYS = (
    {
        "id": "OF_BAY_PRESS_01",
        "department": "Press",
        "centre": (-14_500.0, 8_000.0, 1_000.0),
        "half_extent": (16_000.0, 6_500.0, 1_000.0),
        "floor_material": "press",
    },
    {
        "id": "OF_BAY_BODY_01",
        "department": "Body",
        "centre": (-11_000.0, -8_500.0, 1_000.0),
        "half_extent": (9_000.0, 5_000.0, 1_000.0),
        "floor_material": "body",
    },
    {
        "id": "OF_BAY_PAINT_01",
        "department": "Paint",
        "centre": (10_000.0, -8_500.0, 1_000.0),
        "half_extent": (11_000.0, 5_000.0, 1_000.0),
        "floor_material": "paint",
    },
    {
        "id": "OF_BAY_ASSEMBLY_01",
        "department": "Assembly",
        "centre": (16_500.0, 8_500.0, 1_000.0),
        "half_extent": (14_000.0, 6_000.0, 1_000.0),
        "floor_material": "assembly",
    },
)

PROTECTED_AREAS = (
    {
        "id": "OF_SPINE_LOGISTICS_EW_01",
        "centre": (0.0, 0.0, 200.0),
        "half_extent": (30_500.0, 600.0, 200.0),
    },
    {
        "id": "OF_SPINE_SERVICE_EW_01",
        "centre": (0.0, -14_500.0, 200.0),
        "half_extent": (30_500.0, 300.0, 200.0),
    },
)

UTILITY_SPINES = (
    {
        "id": "OF_SPINE_SERVICE_EW_01",
        "start": (-30_500.0, -14_500.0, 0.0),
        "end": (30_500.0, -14_500.0, 0.0),
        "maximum_connection_distance_cm": 30_000.0,
    },
)

LOGISTICS_SPINES = (
    {
        "id": "OF_SPINE_LOGISTICS_EW_01",
        "start": (-30_500.0, 0.0, 0.0),
        "end": (30_500.0, 0.0, 0.0),
        "maximum_access_distance_cm": 1_200.0,
    },
)

HISM_ACTORS = {
    "LB_OF_ENV_HISM_FloorSlabs_v001": {
        "component_tag": "LB.OneFactory.HISM.FloorSlabs.v001",
        "material": "floor",
        "collision_profile": "BlockAll",
        "cast_shadow": True,
        "semantic_tags": ("LB.OneFactory.Environment.Floor",),
    },
    "LB_OF_ENV_HISM_CutawayWalls_v001": {
        "component_tag": "LB.OneFactory.HISM.CutawayWalls.v001",
        "material": "charcoal",
        "collision_profile": "BlockAll",
        "cast_shadow": True,
        "semantic_tags": (
            "LB.OneFactory.Environment.Shell",
            "LB.OneFactory.Environment.ManagementCutaway",
        ),
    },
    "LB_OF_ENV_HISM_Columns_v001": {
        "component_tag": "LB.OneFactory.HISM.Columns.v001",
        "material": "steel",
        "collision_profile": "BlockAll",
        "cast_shadow": True,
        "semantic_tags": ("LB.OneFactory.Environment.Structure",),
    },
    "LB_OF_ENV_HISM_OpenRoofFrame_v001": {
        "component_tag": "LB.OneFactory.HISM.OpenRoofFrame.v001",
        "material": "steel",
        "collision_profile": "BlockAll",
        "cast_shadow": True,
        "semantic_tags": (
            "LB.OneFactory.Environment.Structure",
            "LB.OneFactory.Environment.OpenRoof",
            "LB.OneFactory.Environment.ManagementCutaway",
        ),
    },
    "LB_OF_ENV_HISM_Grid100cm_v001": {
        "component_tag": "LB.OneFactory.HISM.Grid100cm.v001",
        "material": "charcoal",
        "collision_profile": "NoCollision",
        "cast_shadow": False,
        "semantic_tags": (GRID_TAG,),
    },
    "LB_OF_ENV_HISM_SafetyLines_v001": {
        "component_tag": "LB.OneFactory.HISM.SafetyLines.v001",
        "material": "yellow",
        "collision_profile": "NoCollision",
        "cast_shadow": False,
        "semantic_tags": (
            "LB.OneFactory.Environment.PaintedFloor",
            "LB.OneFactory.Environment.BayBoundaries",
            "LB.OneFactory.Environment.LogisticsBoundaries",
        ),
    },
}

for _bay in BUILD_BAYS:
    HISM_ACTORS[f"LB_OF_ENV_HISM_DepartmentFloor_{_bay['department']}_v001"] = {
        "component_tag": f"LB.OneFactory.HISM.DepartmentFloor.{_bay['department']}.v001",
        "material": _bay["floor_material"],
        "collision_profile": "NoCollision",
        "cast_shadow": False,
        "semantic_tags": (
            "LB.OneFactory.Environment.PaintedFloor",
            "LB.OneFactory.DepartmentBay",
            f"LB.OneFactory.Department.{_bay['department']}",
            f"LB.OneFactory.BuildBay.{_bay['id']}",
            GRID_TAG,
        ),
    }


def floor_instances() -> list[dict[str, tuple[float, float, float]]]:
    rows = []
    for x_index in range(20):
        x = -29_450.0 + x_index * 3_100.0
        for y_index in range(10):
            y = -13_950.0 + y_index * 3_100.0
            rows.append({"location": (x, y, -25.0), "dimensions": (3_100.0, 3_100.0, 50.0)})
    return rows


def cutaway_wall_instances() -> list[dict[str, tuple[float, float, float]]]:
    # South wall and roof panels are intentionally absent for the management cutaway.
    return [
        {"location": (0.0, 15_500.0, 600.0), "dimensions": (62_000.0, 40.0, 1_200.0)},
        {"location": (-31_000.0, 0.0, 600.0), "dimensions": (40.0, 31_000.0, 1_200.0)},
        {"location": (31_000.0, 0.0, 600.0), "dimensions": (40.0, 31_000.0, 1_200.0)},
    ]


def column_instances() -> list[dict[str, tuple[float, float, float]]]:
    return [
        {"location": (x, y, 1_500.0), "dimensions": (90.0, 90.0, 3_000.0)}
        for x in (float(value) for value in range(-30_500, 30_501, 6_100))
        for y in (0.0, 14_500.0)
    ]


def open_roof_frame_instances() -> list[dict[str, tuple[float, float, float]]]:
    rows = [
        {"location": (x, 0.0, 3_000.0), "dimensions": (90.0, 29_000.0, 90.0)}
        for x in (float(value) for value in range(-30_500, 30_501, 6_100))
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


def safety_line_instances() -> list[dict[str, tuple[float, float, float]]]:
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


def department_floor_instances(department: str) -> list[dict[str, tuple[float, float, float]]]:
    bay = next(row for row in BUILD_BAYS if row["department"] == department)
    x, y, _ = bay["centre"]
    half_x, half_y, _ = bay["half_extent"]
    return [{
        "location": (x, y, 0.25),
        "dimensions": (half_x * 2.0 - 40.0, half_y * 2.0 - 40.0, 0.5),
    }]


def expected_hism_instances() -> dict[str, list[dict[str, tuple[float, float, float]]]]:
    rows = {
        "LB_OF_ENV_HISM_FloorSlabs_v001": floor_instances(),
        "LB_OF_ENV_HISM_CutawayWalls_v001": cutaway_wall_instances(),
        "LB_OF_ENV_HISM_Columns_v001": column_instances(),
        "LB_OF_ENV_HISM_OpenRoofFrame_v001": open_roof_frame_instances(),
        "LB_OF_ENV_HISM_Grid100cm_v001": grid_instances(),
        "LB_OF_ENV_HISM_SafetyLines_v001": safety_line_instances(),
    }
    for bay in BUILD_BAYS:
        rows[f"LB_OF_ENV_HISM_DepartmentFloor_{bay['department']}_v001"] = (
            department_floor_instances(bay["department"])
        )
    return rows


DATUM_ACTORS = {
    **{
        f"LB_OF_DATUM_Bay_{bay['department']}_v001": {
            "class": "/Script/Engine.TargetPoint",
            "location": bay["centre"],
            "rotation": (0.0, 0.0, 0.0),
            "scale": (1.0, 1.0, 1.0),
            "tags": tuple(sorted((
                MAP_TAG,
                NATIVE_TAG,
                "LB.OneFactory.DepartmentBay",
                f"LB.OneFactory.Department.{bay['department']}",
                f"LB.OneFactory.BuildBay.{bay['id']}",
                GRID_TAG,
            ))),
        }
        for bay in BUILD_BAYS
    },
    "LB_OF_DATUM_LogisticsSpine_EW_v001": {
        "class": "/Script/Engine.TargetPoint",
        "location": (0.0, 0.0, 200.0),
        "rotation": (0.0, 0.0, 0.0),
        "scale": (1.0, 1.0, 1.0),
        "tags": tuple(sorted((
            MAP_TAG, NATIVE_TAG, "LB.OneFactory.Logistics",
            "LB.OneFactory.ProtectedArea.OF_SPINE_LOGISTICS_EW_01",
            "LB.OneFactory.LogisticsSpine.OF_SPINE_LOGISTICS_EW_01",
            "LB.OneFactory.Route.Start.-30500.0.0",
            "LB.OneFactory.Route.End.30500.0.0",
            "LB.OneFactory.Route.MaximumAccessCm.1200",
        ))),
    },
    "LB_OF_DATUM_ServiceSpine_EW_v001": {
        "class": "/Script/Engine.TargetPoint",
        "location": (0.0, -14_500.0, 200.0),
        "rotation": (0.0, 0.0, 0.0),
        "scale": (1.0, 1.0, 1.0),
        "tags": tuple(sorted((
            MAP_TAG, NATIVE_TAG, "LB.OneFactory.Service",
            "LB.OneFactory.ProtectedArea.OF_SPINE_SERVICE_EW_01",
            "LB.OneFactory.UtilitySpine.OF_SPINE_SERVICE_EW_01",
            "LB.OneFactory.Route.Start.-30500.-14500.0",
            "LB.OneFactory.Route.End.30500.-14500.0",
            "LB.OneFactory.Route.MaximumConnectionCm.30000",
        ))),
    },
    "LB_OF_INTERFACE_CoilReceiving_v001": {
        "class": "/Script/Engine.TargetPoint",
        "location": (-30_500.0, 0.0, 0.0),
        "rotation": (0.0, 0.0, 0.0),
        "scale": (1.0, 1.0, 1.0),
        "tags": tuple(sorted((
            MAP_TAG, NATIVE_TAG, "LB.OneFactory.Interface.CoilReceiving",
            "LB.OneFactory.LogisticsSpine.OF_SPINE_LOGISTICS_EW_01",
        ))),
    },
    "LB_OF_INTERFACE_FinishedVehicleDispatch_v001": {
        "class": "/Script/Engine.TargetPoint",
        "location": (30_500.0, 0.0, 0.0),
        "rotation": (0.0, 0.0, 0.0),
        "scale": (1.0, 1.0, 1.0),
        "tags": tuple(sorted((
            MAP_TAG, NATIVE_TAG, "LB.OneFactory.Interface.FinishedVehicleDispatch",
            "LB.OneFactory.LogisticsSpine.OF_SPINE_LOGISTICS_EW_01",
        ))),
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def project_relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def protected_snapshot() -> dict[str, str]:
    paths = [ROOT / relative for relative in CRITICAL_PROTECTED_HASHES]
    config_root = ROOT / "Config"
    if not config_root.is_dir():
        raise RuntimeError("Protected Config directory is missing")
    paths.extend(sorted(path for path in config_root.rglob("*") if path.is_file()))
    save_root = ROOT / "Saved/SaveGames"
    if save_root.exists():
        paths.extend(sorted(path for path in save_root.rglob("*") if path.is_file()))
    missing = [project_relative(path) for path in paths if not path.is_file()]
    if missing:
        raise RuntimeError("Protected file(s) missing: " + ", ".join(missing))
    result = {project_relative(path): sha256(path) for path in paths}
    for relative, expected in CRITICAL_PROTECTED_HASHES.items():
        if result.get(relative) != expected:
            raise RuntimeError(
                f"Protected anchor hash drift: {relative}: "
                f"{result.get(relative)} != {expected}"
            )
    return dict(sorted(result.items()))


def require_class(path: str):
    value = unreal.load_class(None, path)
    if value is None:
        raise RuntimeError(
            "Required compiled One Factory class is unavailable. Build/reload the "
            f"editor module before map creation: {path}"
        )
    return value


def require_asset(path: str, expected_type=None):
    value = unreal.EditorAssetLibrary.load_asset(path) or unreal.load_asset(path)
    if value is None or (expected_type is not None and not isinstance(value, expected_type)):
        raise RuntimeError(f"Required native shell asset is unavailable: {path}")
    return value


def path_name(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return value.get_path_name()
    except Exception:
        return str(value)


def tags_of(actor: Any) -> tuple[str, ...]:
    return tuple(sorted(str(tag) for tag in actor.get_editor_property("tags")))


def set_exact_tags(actor: Any, tags: Iterable[str]) -> None:
    actor.set_editor_property("tags", [unreal.Name(tag) for tag in sorted(set(tags))])


def get_editor_world():
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if subsystem is not None:
        return subsystem.get_editor_world()
    return unreal.EditorLevelLibrary.get_editor_world()


def world_partition_enabled(world: Any) -> bool | None:
    getter = getattr(world, "get_world_partition", None)
    if callable(getter):
        return getter() is not None
    try:
        return world.get_world_settings().get_editor_property("world_partition") is not None
    except Exception:
        return None


def component_from_handle(handle: Any):
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    data = library.get_data(handle)
    getter = getattr(library, "get_associated_object", None)
    if callable(getter):
        return getter(data)
    return library.get_object(data)


def add_hism_component(actor: Any, component_tag: str):
    """Add one persistent HISM component to a generic map-authored actor."""
    component = None
    subsystem_class = getattr(unreal, "SubobjectDataSubsystem", None)
    params_class = getattr(unreal, "AddNewSubobjectParams", None)
    if subsystem_class is not None and params_class is not None:
        subsystem = unreal.get_engine_subsystem(subsystem_class)
        handles = subsystem.k2_gather_subobject_data_for_instance(actor) if subsystem else []
        if subsystem is not None and handles:
            params = params_class()
            params.set_editor_property("parent_handle", handles[0])
            params.set_editor_property(
                "new_class", unreal.HierarchicalInstancedStaticMeshComponent
            )
            params.set_editor_property("blueprint_context", None)
            result = subsystem.add_new_subobject(params)
            handle = result[0] if isinstance(result, tuple) else result
            failure_reason = str(result[1]) if isinstance(result, tuple) and len(result) > 1 else ""
            if unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(handle):
                component = component_from_handle(handle)
            elif failure_reason:
                unreal.log_warning(
                    f"One Factory SubobjectData HISM path unavailable: {failure_reason}"
                )

    if component is None:
        add_method = getattr(actor, "add_component_by_class", None)
        if not callable(add_method):
            raise RuntimeError(
                "UE 5.8 exposes neither SubobjectData instance component creation nor "
                "Actor.add_component_by_class; refusing a StaticMeshActor fallback"
            )
        component = add_method(
            unreal.HierarchicalInstancedStaticMeshComponent,
            False,
            unreal.Transform(),
            False,
        )
    if component is None or not isinstance(
        component, unreal.HierarchicalInstancedStaticMeshComponent
    ):
        raise RuntimeError(f"Could not create native HISM component {component_tag}")
    component.set_editor_property("component_tags", [unreal.Name(component_tag)])
    return component


def transform_for_instance(spec: dict[str, tuple[float, float, float]]):
    dimensions = spec["dimensions"]
    return unreal.Transform(
        location=unreal.Vector(*spec["location"]),
        rotation=unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0),
        scale=unreal.Vector(
            dimensions[0] / 100.0,
            dimensions[1] / 100.0,
            dimensions[2] / 100.0,
        ),
    )


def spawn_hism_actor(actors: Any, cube: Any, materials: dict[str, Any],
                     label: str, spec: dict[str, Any], instances: list[dict[str, Any]]):
    actor = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector(), unreal.Rotator())
    if actor is None:
        raise RuntimeError(f"Could not spawn HISM shell actor {label}")
    actor.set_actor_label(label)
    set_exact_tags(actor, (MAP_TAG, NATIVE_TAG, ENV_TAG, HISM_TAG, *spec["semantic_tags"]))
    component = add_hism_component(actor, spec["component_tag"])
    component.set_static_mesh(cube)
    component.set_material(0, materials[spec["material"]])
    component.set_collision_profile_name(spec["collision_profile"])
    component.set_editor_property("can_ever_affect_navigation", False)
    component.set_cast_shadow(bool(spec["cast_shadow"]))
    try:
        component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    except Exception:
        pass
    for index, instance in enumerate(instances):
        added = component.add_instance(transform_for_instance(instance), False)
        if int(added) != index:
            raise RuntimeError(
                f"HISM instance order drift for {label}: added {added}, expected {index}"
            )
    if int(component.get_instance_count()) != len(instances):
        raise RuntimeError(f"HISM instance count drift for {label}")
    return actor


def make_struct(struct_type: Any, values: dict[str, Any]):
    result = struct_type()
    for name, value in values.items():
        result.set_editor_property(name, value)
    return result


def configure_press_authority(authority: Any) -> None:
    build_bays = [
        make_struct(unreal.LBPressShopBuildBay, {
            "bay_id": unreal.Name(row["id"]),
            "centre": unreal.Vector(*row["centre"]),
            "half_extent": unreal.Vector(*row["half_extent"]),
        })
        for row in BUILD_BAYS
    ]
    protected = [
        make_struct(unreal.LBPressShopProtectedArea, {
            "area_id": unreal.Name(row["id"]),
            "centre": unreal.Vector(*row["centre"]),
            "half_extent": unreal.Vector(*row["half_extent"]),
        })
        for row in PROTECTED_AREAS
    ]
    utilities = [
        make_struct(unreal.LBPressShopUtilitySpine, {
            "spine_id": unreal.Name(row["id"]),
            "start": unreal.Vector(*row["start"]),
            "end": unreal.Vector(*row["end"]),
            "maximum_connection_distance_cm": row["maximum_connection_distance_cm"],
        })
        for row in UTILITY_SPINES
    ]
    logistics = [
        make_struct(unreal.LBPressShopLogisticsSpine, {
            "spine_id": unreal.Name(row["id"]),
            "start": unreal.Vector(*row["start"]),
            "end": unreal.Vector(*row["end"]),
            "maximum_access_distance_cm": row["maximum_access_distance_cm"],
        })
        for row in LOGISTICS_SPINES
    ]
    authority.set_editor_property("build_bays", build_bays)
    authority.set_editor_property("protected_areas", protected)
    authority.set_editor_property("utility_spines", utilities)
    authority.set_editor_property("storage_bays", [])
    authority.set_editor_property("logistics_spines", logistics)


def validate_bootstrap(bootstrap: Any) -> dict[str, Any]:
    method = getattr(bootstrap, "validate_and_lock_shell", None)
    if not callable(method):
        raise RuntimeError("LBOneFactoryBootstrap.ValidateAndLockShell is not reflected")
    result = method()
    if isinstance(result, tuple):
        passed = bool(result[0])
        reason = str(result[1]) if len(result) > 1 else ""
    else:
        passed = bool(result)
        reason = ""
    valid_method = getattr(bootstrap, "has_valid_shell", None)
    has_valid_shell = bool(valid_method()) if callable(valid_method) else False
    if not passed or not has_valid_shell:
        raise RuntimeError(
            f"One Factory bootstrap rejected the canonical shell: passed={passed}, "
            f"has_valid_shell={has_valid_shell}, reason={reason}"
        )
    return {"validate_and_lock_shell": passed, "has_valid_shell": has_valid_shell,
            "reason": reason}


def spawn_target(actors: Any, label: str, spec: dict[str, Any]) -> Any:
    actor = actors.spawn_actor_from_class(
        unreal.TargetPoint,
        unreal.Vector(*spec["location"]),
        unreal.Rotator(
            roll=spec["rotation"][2],
            pitch=spec["rotation"][0],
            yaw=spec["rotation"][1],
        ),
    )
    if actor is None:
        raise RuntimeError(f"Could not spawn datum {label}")
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*spec["scale"]))
    set_exact_tags(actor, spec["tags"])
    return actor


def vector_tuple(value: Any) -> tuple[float, float, float]:
    return float(value.x), float(value.y), float(value.z)


def rotator_tuple(value: Any) -> tuple[float, float, float]:
    return float(value.pitch), float(value.yaw), float(value.roll)


def close_tuple(actual: Iterable[float], expected: Iterable[float], tolerance: float) -> bool:
    return all(abs(float(left) - float(right)) <= tolerance
               for left, right in zip(actual, expected))


def validate_authority_arrays(authority: Any) -> dict[str, Any]:
    failures = []
    rows: dict[str, Any] = {}

    actual_bays = list(authority.get_editor_property("build_bays"))
    bay_rows = []
    for index, expected in enumerate(BUILD_BAYS):
        actual = actual_bays[index] if index < len(actual_bays) else None
        row = {
            "id": str(actual.get_editor_property("bay_id")) if actual else None,
            "centre": list(vector_tuple(actual.get_editor_property("centre"))) if actual else None,
            "half_extent": list(vector_tuple(actual.get_editor_property("half_extent"))) if actual else None,
        }
        valid = (
            actual is not None
            and row["id"] == expected["id"]
            and close_tuple(row["centre"], expected["centre"], 0.02)
            and close_tuple(row["half_extent"], expected["half_extent"], 0.02)
        )
        row["valid"] = valid
        bay_rows.append(row)
        if not valid:
            failures.append(f"build bay drift at index {index}")
    if len(actual_bays) != len(BUILD_BAYS):
        failures.append(f"build bay count {len(actual_bays)} != {len(BUILD_BAYS)}")
    rows["build_bays"] = bay_rows

    def validate_spatial_array(property_name: str, expected_rows: tuple[dict[str, Any], ...],
                               id_property: str, vector_properties: tuple[str, ...],
                               scalar_property: str | None = None) -> list[dict[str, Any]]:
        actual_values = list(authority.get_editor_property(property_name))
        evidence = []
        if len(actual_values) != len(expected_rows):
            failures.append(
                f"{property_name} count {len(actual_values)} != {len(expected_rows)}"
            )
        for index, expected in enumerate(expected_rows):
            actual = actual_values[index] if index < len(actual_values) else None
            item = {"id": str(actual.get_editor_property(id_property)) if actual else None}
            valid = actual is not None and item["id"] == expected["id"]
            for vector_property in vector_properties:
                value = (list(vector_tuple(actual.get_editor_property(vector_property)))
                         if actual else None)
                item[vector_property] = value
                valid = valid and close_tuple(value, expected[vector_property], 0.02)
            if scalar_property:
                value = float(actual.get_editor_property(scalar_property)) if actual else None
                item[scalar_property] = value
                valid = valid and abs(value - expected[scalar_property]) <= 0.01
            item["valid"] = bool(valid)
            evidence.append(item)
            if not valid:
                failures.append(f"{property_name} drift at index {index}")
        return evidence

    rows["protected_areas"] = validate_spatial_array(
        "protected_areas", PROTECTED_AREAS, "area_id", ("centre", "half_extent")
    )
    rows["utility_spines"] = validate_spatial_array(
        "utility_spines", UTILITY_SPINES, "spine_id", ("start", "end"),
        "maximum_connection_distance_cm"
    )
    rows["logistics_spines"] = validate_spatial_array(
        "logistics_spines", LOGISTICS_SPINES, "spine_id", ("start", "end"),
        "maximum_access_distance_cm"
    )
    storage_count = len(list(authority.get_editor_property("storage_bays")))
    rows["storage_bay_count"] = storage_count
    if storage_count != 0:
        failures.append(f"storage bay count {storage_count} != 0")
    if failures:
        raise RuntimeError("Press authority canonical array contract failed: " + " | ".join(failures))
    return rows


def validate_current_map(classes: dict[str, Any], actors_api: Any,
                         run_bootstrap_validation: bool) -> dict[str, Any]:
    world = get_editor_world()
    if world is None:
        raise RuntimeError("Editor world is unavailable")
    if world.get_path_name() != MAP_OBJECT:
        raise RuntimeError(f"Wrong loaded world: {world.get_path_name()} != {MAP_OBJECT}")
    if world_partition_enabled(world) is not False:
        raise RuntimeError("One Factory shell must be a basic non-World-Partition map")
    settings = world.get_world_settings()
    game_mode = settings.get_editor_property("default_game_mode")
    if game_mode != classes["game_mode"]:
        raise RuntimeError("One Factory map-local GameMode override drifted")
    game_mode_cdo = unreal.get_default_object(classes["game_mode"])
    if game_mode_cdo.get_editor_property("default_pawn_class") != classes["pawn"]:
        raise RuntimeError("LBOneFactoryGameMode default pawn is not LBManagementPawn")
    if game_mode_cdo.get_editor_property("hud_class") != classes["hud"]:
        raise RuntimeError("LBOneFactoryGameMode HUD is not LBControlRoomHUD")

    actors = list(actors_api.get_all_level_actors())
    nonfoundation = [
        actor for actor in actors
        if path_name(actor.get_class()) not in {
            "/Script/Engine.WorldSettings", "/Script/Engine.DefaultPhysicsVolume"
        }
    ]
    map_authored_labels = (
        set(HISM_ACTORS)
        | set(DATUM_ACTORS)
        | {
            "LB_OF_ENV_LightingAuthority_5000K_v001",
            "LB_OF_ENV_FixedExposureAuthority_v001",
            "LB_OF_PlayerStart_Management_v001",
            "LB_OF_ManagementCamera_Overview_v001",
            "LB_OF_NavBounds_FactoryEnvelope_v001",
            "LB_OneFactoryBootstrap_v001",
            "LB_OneFactory_PressBuildAuthority_v001",
        }
    )
    by_label: dict[str, list[Any]] = {}
    for actor in nonfoundation:
        by_label.setdefault(actor.get_actor_label(), []).append(actor)
    actual_labels = set(by_label)
    navigation_rows = by_label.get(ENGINE_NAVIGATION_ACTOR_LABEL, [])
    # Nav data is generated by the exact map-authored NavMeshBoundsVolume.  It
    # can be absent before the first save, but a fresh reload must contain one
    # exact Recast actor.  No other engine actor is ignored here.
    expected_labels = set(map_authored_labels)
    if navigation_rows:
        expected_labels.add(ENGINE_NAVIGATION_ACTOR_LABEL)
    if run_bootstrap_validation:
        expected_labels.add(ENGINE_NAVIGATION_ACTOR_LABEL)
    if actual_labels != expected_labels:
        raise RuntimeError(
            "Exact One Factory actor label set drifted: missing="
            f"{sorted(expected_labels - actual_labels)} unexpected="
            f"{sorted(actual_labels - expected_labels)}"
        )
    duplicates = sorted(label for label, values in by_label.items() if len(values) != 1)
    if duplicates:
        raise RuntimeError("Duplicate One Factory actor label(s): " + ", ".join(duplicates))
    if run_bootstrap_validation and len(navigation_rows) != 1:
        raise RuntimeError(
            "Fresh reload must own exactly one RecastNavMesh-Default; got "
            f"{len(navigation_rows)}"
        )
    if len(navigation_rows) > 1:
        raise RuntimeError("Pre-save world contains duplicate RecastNavMesh-Default actors")
    if navigation_rows:
        navigation = navigation_rows[0]
        navigation_contract = {
            "class": path_name(navigation.get_class()),
            "tags": list(tags_of(navigation)),
            "location": list(vector_tuple(navigation.get_actor_location())),
            "rotation": list(rotator_tuple(navigation.get_actor_rotation())),
            "scale": list(vector_tuple(navigation.get_actor_scale3d())),
            "owner": path_name(navigation.get_owner()),
            "attach_parent_actor": path_name(navigation.get_attach_parent_actor()),
        }
        if navigation_contract != {
            "class": ENGINE_NAVIGATION_ACTOR_CLASS_PATH,
            "tags": [],
            "location": [0.0, 0.0, 0.0],
            "rotation": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
            "owner": None,
            "attach_parent_actor": None,
        }:
            raise RuntimeError(
                "Exact engine-generated Recast navigation actor contract drifted: "
                + repr(navigation_contract)
            )
    else:
        navigation_contract = None

    map_authored_count = len(nonfoundation) - len(navigation_rows)
    if map_authored_count != EXPECTED_MAP_AUTHORED_ACTOR_COUNT:
        raise RuntimeError(
            f"Map-authored actor count {map_authored_count} != "
            f"{EXPECTED_MAP_AUTHORED_ACTOR_COUNT}"
        )
    if (run_bootstrap_validation
            and len(nonfoundation) != EXPECTED_FRESH_RELOAD_NONFOUNDATION_ACTOR_COUNT):
        raise RuntimeError(
            f"Fresh reload non-foundation actor count {len(nonfoundation)} != "
            f"{EXPECTED_FRESH_RELOAD_NONFOUNDATION_ACTOR_COUNT}"
        )

    bootstraps = [actor for actor in actors if actor.get_class() == classes["bootstrap"]]
    authorities = [actor for actor in actors if actor.get_class() == classes["press_authority"]]
    if len(bootstraps) != 1 or len(authorities) != 1:
        raise RuntimeError(
            f"Expected one bootstrap and one Press authority; got {len(bootstraps)}, "
            f"{len(authorities)}"
        )
    if navigation_rows:
        same_level = navigation_rows[0].get_outer() == bootstraps[0].get_outer()
        if not same_level:
            raise RuntimeError(
                "RecastNavMesh-Default must share the bootstrap's persistent level"
            )
        navigation_contract["same_persistent_level_as_bootstrap"] = True
    if tags_of(bootstraps[0]) != tuple(sorted((
        "LB.OneFactory.Bootstrap.v001", NATIVE_TAG
    ))):
        raise RuntimeError("Bootstrap exact tag set drifted")
    expected_authority_tags = tuple(sorted((
        "LB.OneFactory.MapAuthored.PressBuildAuthority.v001", NATIVE_TAG
    )))
    if tags_of(authorities[0]) != expected_authority_tags:
        raise RuntimeError("Press authority exact tag set drifted")
    if (authorities[0].get_owner() is not None
            or authorities[0].get_attach_parent_actor() is not None
            or authorities[0].get_outer() != bootstraps[0].get_outer()):
        raise RuntimeError(
            "Press authority must be unowned, unattached and in the bootstrap's persistent level"
        )

    unapproved_project_actors = [
        (actor.get_actor_label(), path_name(actor.get_class()))
        for actor in actors
        if path_name(actor.get_class()).startswith("/Script/LineBossCarFactory.")
        and actor.get_class() not in {classes["bootstrap"], classes["press_authority"]}
    ]
    if unapproved_project_actors:
        raise RuntimeError(
            "Production/project actors are forbidden in the shell: "
            + repr(unapproved_project_actors)
        )
    # The FinishedVehicleDispatch datum is an interface marker, not a vehicle actor.
    forbidden_terms = ("WIP", "Machine", "Station", "Robot", "CellActor")
    forbidden_labels_or_tags = []
    for actor in actors:
        identity = (actor.get_actor_label(), *tags_of(actor))
        if any(term.lower() in value.lower() for term in forbidden_terms for value in identity):
            forbidden_labels_or_tags.append(identity)
    if forbidden_labels_or_tags:
        raise RuntimeError("Shell contains production/WIP identity: " + repr(forbidden_labels_or_tags))

    hism_instances = expected_hism_instances()
    hism_rows = {}
    for label, spec in HISM_ACTORS.items():
        actor = by_label[label][0]
        components = actor.get_components_by_class(
            unreal.HierarchicalInstancedStaticMeshComponent
        )
        if len(components) != 1:
            raise RuntimeError(f"{label} must own exactly one HISM component")
        component = components[0]
        component_tags = tuple(sorted(
            str(tag) for tag in component.get_editor_property("component_tags")
        ))
        expected_component_tags = (spec["component_tag"],)
        count = int(component.get_instance_count())
        if component_tags != expected_component_tags or count != len(hism_instances[label]):
            raise RuntimeError(f"HISM tag/count drift for {label}")
        hism_rows[label] = {
            "component_class": path_name(component.get_class()),
            "component_tags": list(component_tags),
            "instance_count": count,
            "collision_profile": str(component.get_collision_profile_name()),
            "mesh": path_name(component.get_editor_property("static_mesh")),
            "material": path_name(component.get_material(0)),
        }

    authority_rows = validate_authority_arrays(authorities[0])
    # Never lock the bootstrap before the map is saved: its visible validation
    # state is intentionally an actor-lifetime result and must not be serialized
    # as a pre-validated map.  The post-save fresh reload and the independent
    # validator each exercise the native audit without saving afterwards.
    bootstrap_rows = (
        validate_bootstrap(bootstraps[0])
        if run_bootstrap_validation
        else {"deferred_until_fresh_reload": True}
    )
    return {
        "world": world.get_path_name(),
        "world_partition_enabled": False,
        "game_mode": path_name(game_mode),
        "default_pawn": path_name(game_mode_cdo.get_editor_property("default_pawn_class")),
        "hud": path_name(game_mode_cdo.get_editor_property("hud_class")),
        "nonfoundation_actor_count": len(nonfoundation),
        "map_authored_actor_count": map_authored_count,
        "engine_generated_navigation_actor_count": len(navigation_rows),
        "engine_generated_navigation_actor": navigation_contract,
        "exact_actor_labels": sorted(expected_labels),
        "bootstrap": bootstrap_rows,
        "press_authority": authority_rows,
        "hism": hism_rows,
        "hism_actor_count": len(HISM_ACTORS),
        "hism_instance_count": sum(len(rows) for rows in hism_instances.values()),
        "production_machine_or_wip_actor_count": 0,
        "factory_envelope": {
            "centre_cm": list(FACTORY_CENTRE_CM),
            "size_cm": list(FACTORY_SIZE_CM),
        },
    }


def main() -> None:
    library = unreal.EditorAssetLibrary
    if library.does_asset_exist(MAP) or MAP_FILE.exists():
        raise RuntimeError(f"Refusing to overwrite protected One Factory destination: {MAP}")
    if AUDIT.exists():
        raise RuntimeError(f"Refusing to overwrite One Factory creation receipt: {AUDIT}")

    before = protected_snapshot()
    classes = {
        "game_mode": require_class(GAME_MODE_CLASS_PATH),
        "pawn": require_class(PAWN_CLASS_PATH),
        "hud": require_class(HUD_CLASS_PATH),
        "bootstrap": require_class(BOOTSTRAP_CLASS_PATH),
        "press_authority": require_class(PRESS_AUTHORITY_CLASS_PATH),
    }
    cube = require_asset(CUBE_PATH, unreal.StaticMesh)
    materials = {
        name: require_asset(path, unreal.MaterialInterface)
        for name, path in MATERIALS.items()
    }
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if levels is None or actors is None:
        raise RuntimeError("Required UE 5.8 editor subsystems are unavailable")
    if not levels.new_level(MAP, False):
        raise RuntimeError(f"Could not create basic non-WP One Factory map: {MAP}")
    world = get_editor_world()
    if world is None:
        raise RuntimeError("One Factory level creation did not produce an editor world")
    world.get_world_settings().set_editor_property("default_game_mode", classes["game_mode"])

    instances = expected_hism_instances()
    for label, spec in HISM_ACTORS.items():
        spawn_hism_actor(actors, cube, materials, label, spec, instances[label])

    light = actors.spawn_actor_from_class(
        unreal.RectLight,
        unreal.Vector(0.0, 0.0, 6_500.0),
        unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0),
    )
    if light is None:
        raise RuntimeError("Could not create the single One Factory lighting authority")
    light.set_actor_label("LB_OF_ENV_LightingAuthority_5000K_v001")
    set_exact_tags(light, (MAP_TAG, NATIVE_TAG, ENV_TAG, LIGHTING_AUTHORITY_TAG))
    light_component = light.get_component_by_class(unreal.RectLightComponent)
    light_component.set_editor_properties({
        "intensity": 800_000.0,
        "intensity_units": unreal.LightUnits.LUMENS,
        "attenuation_radius": 45_000.0,
        "source_width": 60_000.0,
        "source_height": 29_000.0,
        "use_temperature": True,
        "temperature": 5_000.0,
    })
    try:
        light_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    except Exception:
        pass

    exposure = actors.spawn_actor_from_class(
        unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator()
    )
    if exposure is None:
        raise RuntimeError("Could not create One Factory fixed exposure authority")
    exposure.set_actor_label("LB_OF_ENV_FixedExposureAuthority_v001")
    set_exact_tags(exposure, (MAP_TAG, NATIVE_TAG, ENV_TAG, FIXED_EXPOSURE_TAG))
    exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0})
    settings = exposure.get_editor_property("settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": 0.0,
    })
    exposure.set_editor_property("settings", settings)

    player_start = actors.spawn_actor_from_class(
        unreal.PlayerStart,
        unreal.Vector(-28_000.0, -13_500.0, 200.0),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0),
    )
    if player_start is None:
        raise RuntimeError("Could not create One Factory PlayerStart")
    player_start.set_actor_label("LB_OF_PlayerStart_Management_v001")
    set_exact_tags(player_start, (
        MAP_TAG, NATIVE_TAG, "LB.OneFactory.PlayerStart.Management.v001"
    ))

    camera_location = unreal.Vector(0.0, -43_000.0, 36_000.0)
    camera = actors.spawn_actor_from_class(unreal.CameraActor, camera_location, unreal.Rotator())
    if camera is None:
        raise RuntimeError("Could not create One Factory management camera")
    camera.set_actor_label("LB_OF_ManagementCamera_Overview_v001")
    set_exact_tags(camera, (
        MAP_TAG, NATIVE_TAG, "LB.OneFactory.ManagementView.Overview.v001"
    ))
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera_location, unreal.Vector()), False
    )
    camera_component = camera.get_editor_property("camera_component")
    camera_component.set_editor_properties({
        "field_of_view": 48.0,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })

    nav = actors.spawn_actor_from_class(
        unreal.NavMeshBoundsVolume,
        unreal.Vector(*FACTORY_CENTRE_CM),
        unreal.Rotator(),
    )
    if nav is None:
        raise RuntimeError("Could not create One Factory navigation volume")
    nav.set_actor_label("LB_OF_NavBounds_FactoryEnvelope_v001")
    nav.set_actor_scale3d(unreal.Vector(310.0, 155.0, 15.0))
    set_exact_tags(nav, (
        MAP_TAG, NATIVE_TAG, "LB.OneFactory.Navigation.FactoryEnvelope.v001"
    ))

    for label, spec in DATUM_ACTORS.items():
        spawn_target(actors, label, spec)

    authority = actors.spawn_actor_from_class(
        classes["press_authority"], unreal.Vector(), unreal.Rotator()
    )
    if authority is None:
        raise RuntimeError("Could not create map-authored Press build authority")
    authority.set_actor_label("LB_OneFactory_PressBuildAuthority_v001")
    set_exact_tags(authority, (
        "LB.OneFactory.MapAuthored.PressBuildAuthority.v001", NATIVE_TAG
    ))
    configure_press_authority(authority)

    bootstrap = actors.spawn_actor_from_class(
        classes["bootstrap"], unreal.Vector(), unreal.Rotator()
    )
    if bootstrap is None:
        raise RuntimeError("Could not create map-authored One Factory bootstrap")
    bootstrap.set_actor_label("LB_OneFactoryBootstrap_v001")
    set_exact_tags(bootstrap, ("LB.OneFactory.Bootstrap.v001", NATIVE_TAG))

    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    facts = validate_current_map(classes, actors, run_bootstrap_validation=False)
    if not levels.save_current_level():
        raise RuntimeError("Could not save One Factory shell map")
    if not levels.load_level(MAP):
        raise RuntimeError("Could not fresh-reload the saved One Factory shell map")
    facts = validate_current_map(classes, actors, run_bootstrap_validation=True)
    if not MAP_FILE.is_file():
        raise RuntimeError(f"Saved One Factory map file is missing: {MAP_FILE}")

    after = protected_snapshot()
    if before != after:
        changed = sorted(
            relative for relative in set(before) | set(after)
            if before.get(relative) != after.get(relative)
        )
        raise RuntimeError(
            "Protected Press/Body/Paint/Config/SaveGames hashes changed: "
            + ", ".join(changed)
        )
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "$schema": "lineboss/audit/one-factory/shell-create-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "PASS__ONE_FACTORY_NATIVE_HISM_SHELL_ONE_BOOTSTRAP_ONE_PRESS_AUTHORITY_"
            "ZERO_PRODUCTION_MACHINE_OR_WIP"
        ),
        "builder_script": project_relative(SCRIPT_FILE),
        "builder_script_sha256": sha256(SCRIPT_FILE),
        "map": MAP,
        "map_file": project_relative(MAP_FILE),
        "map_sha256": sha256(MAP_FILE),
        "facts": facts,
        "protected_hashes": after,
        "config_file_count": sum(key.startswith("Config/") for key in after),
        "savegames_file_count": sum(key.startswith("Saved/SaveGames/") for key in after),
        "default_engine_modified": False,
        "failures": [],
    }
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(
        "LINE_BOSS_ONE_FACTORY_SHELL_CREATE_V001_PASS "
        f"map={MAP} sha256={payload['map_sha256']}"
    )


if __name__ == "__main__":
    main()
