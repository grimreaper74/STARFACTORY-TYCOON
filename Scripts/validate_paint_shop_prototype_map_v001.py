"""Fresh-load and independently validate the isolated Paint Shop v001 map.

This validator deliberately does not import the map builder.  Its constants freeze
the independently reviewed actor contract and the exact creation-artifact chain.
It is read-only for Content, Config and Source; its only write is the validation
receipt under Saved/Audits/PaintShop/Experimental_v001.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
SCRIPT_FILE = ROOT / "Scripts/validate_paint_shop_prototype_map_v001.py"
BUILDER_FILE = ROOT / "Scripts/create_paint_shop_prototype_map_v001.py"
CREATE_RECEIPT = (
    ROOT
    / "Saved/Audits/PaintShop/Experimental_v001/paint_shop_prototype_map_create_v001.json"
)
AUDIT = (
    ROOT
    / "Saved/Audits/PaintShop/Experimental_v001/paint_shop_prototype_map_validation_v001.json"
)

MAP = "/Game/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001"
MAP_OBJECT = f"{MAP}.{MAP.rsplit('/', 1)[-1]}"
MAP_FILE = (
    ROOT
    / "Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap"
)

VALIDATION_SCHEMA = "lineboss/audit/paint-shop/prototype-map-validation-v001/v1"
PASS_STATUS = "PASS__FRESH_RELOAD_PAINT_SHOP_PROTOTYPE_MAP_V001"
FAIL_STATUS = "FAIL"

CREATE_RECEIPT_SCHEMA = "lineboss/audit/paint-shop/prototype-map-create-v001/v1"
CREATE_RECEIPT_STATUS = (
    "PASS__ISOLATED_PAINT_SHOP_ONE_BOOTSTRAP_ZERO_MAP_OWNED_PRODUCTION"
)
BUILDER_RELATIVE = "Scripts/create_paint_shop_prototype_map_v001.py"
CREATE_RECEIPT_RELATIVE = (
    "Saved/Audits/PaintShop/Experimental_v001/"
    "paint_shop_prototype_map_create_v001.json"
)
VALIDATOR_RELATIVE = "Scripts/validate_paint_shop_prototype_map_v001.py"
MAP_FILE_RELATIVE = (
    "Content/LineBoss/PaintShop/Experimental/v001/Maps/"
    "LB_PaintShop_Prototype_v001.umap"
)

# These are the exact authoritative inputs reviewed when this validator was
# authored.  Replacing the builder, receipt and map together cannot silently
# move the validation baseline.
EXPECTED_BUILDER_SHA256 = "6922346EA0BA04C8388BA808FF22D7A1FFCC932B87AA37AEBAA52D3A26645FCA"
EXPECTED_CREATE_RECEIPT_SHA256 = (
    "4E65E671CB25D8615F3A775B1697E7D72C523D58FFA7481356A5BF8D5941AC09"
)
EXPECTED_MAP_SHA256 = "2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069"

EXPECTED_PROTECTED_HASHES = {
    "Config/DefaultEditor.ini":
        "BBE05501998265524E8ACD5319DBC42E748DDE39FB25463C8BB0D431AC746D16",
    "Config/DefaultEditorPerProjectUserSettings.ini":
        "9255BE413FFFB3970BAD3C921E8E5BFE3DD41A0B01F45348354FCAAC01E9E6D4",
    "Config/DefaultEngine.ini":
        "A1A3B4E5EC0327BB9AD05B094B7749CE9CE9795B1D065CFA4196C1AD3EFB82D3",
    "Config/DefaultGame.ini":
        "1DE2055DB7A0F4EA1653E9656A33EE692CBEF133B8761A08A31B090B3832484C",
    "Config/DefaultGameUserSettings.ini":
        "D4E55BBFC7F843097D40E3335B1FE57AE12F804D981564F904AEBCDA34F35F3E",
    "Config/DefaultInput.ini":
        "8DCE19104C744A1DA03413EC234CF9D0BAD1BF40BD718C1F770D68CBD42D2F00",
    "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap":
        "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
    "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap":
        "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F",
    "Source/LineBossCarFactory/LBECoatLineActor.h":
        "0F976B66B9D425E1D198FBDF9657292C1A1AE295DA5F10F96F88649232A862A1",
    "Source/LineBossCarFactory/LBECoatLineActor.cpp":
        "01A314D5576FFCFE592FED55E2410A1C1454665C5528D6D17986B2FA6EF31D02",
    "Saved/SaveGames/LB_AUTOMATION_SUPPORT_FLEET_V269_DISK_ROUNDTRIP.sav":
        "9C3AC306FEF9535E9115F3E5B568CE9A113515635D64418438EE14760BD20114",
    "Saved/SaveGames/LineBoss_BodyShopExperimental_v001.sav":
        "6C7CBE88D14E10B198CC482FFE07C8C997AA2D31B0068BA4CB306DFB9F976486",
}

PROTECTED_FIXED_RELATIVE = (
    "Config/DefaultEditor.ini",
    "Config/DefaultEditorPerProjectUserSettings.ini",
    "Config/DefaultEngine.ini",
    "Config/DefaultGame.ini",
    "Config/DefaultGameUserSettings.ini",
    "Config/DefaultInput.ini",
    "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap",
    "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap",
    "Source/LineBossCarFactory/LBECoatLineActor.h",
    "Source/LineBossCarFactory/LBECoatLineActor.cpp",
)

GAME_MODE_CLASS_PATH = "/Script/LineBossCarFactory.LBPaintShopPrototypeGameMode"
PAWN_CLASS_PATH = "/Script/LineBossCarFactory.LBPaintShopManagementPawn"
HUD_CLASS_PATH = "/Script/LineBossCarFactory.LBPaintShopPrototypeHUD"
BOOTSTRAP_CLASS_PATH = (
    "/Script/LineBossCarFactory.LBPaintShopPrototypeWorldBootstrap"
)
BUILD_AUTHORITY_CLASS_PATH = "/Script/LineBossCarFactory.LBPaintShopBuildAuthority"
RUNTIME_CLASS_PATH = "/Script/LineBossCarFactory.LBPaintShopPrototypeRuntime"
CELL_CLASS_PATH = "/Script/LineBossCarFactory.LBPaintShopCellActor"

REQUIRED_CLASS_PATHS = (
    GAME_MODE_CLASS_PATH,
    PAWN_CLASS_PATH,
    HUD_CLASS_PATH,
    BOOTSTRAP_CLASS_PATH,
    BUILD_AUTHORITY_CLASS_PATH,
    RUNTIME_CLASS_PATH,
    CELL_CLASS_PATH,
)

MAP_TAG = "LB.PaintShop.Experimental.v001"
ENV_TAG = "LB.PaintShop.Environment"
ENGINE_FOUNDATION_CLASS_PATHS = {
    "/Script/Engine.WorldSettings",
    "/Script/Engine.DefaultPhysicsVolume",
}

STATIC_MESH_ACTOR_PATH = "/Script/Engine.StaticMeshActor"
DIRECTIONAL_LIGHT_PATH = "/Script/Engine.DirectionalLight"
SKY_LIGHT_PATH = "/Script/Engine.SkyLight"
POST_PROCESS_VOLUME_PATH = "/Script/Engine.PostProcessVolume"
PLAYER_START_PATH = "/Script/Engine.PlayerStart"
CAMERA_ACTOR_PATH = "/Script/Engine.CameraActor"
RECT_LIGHT_PATH = "/Script/Engine.RectLight"
STATIC_MESH_COMPONENT_PATH = "/Script/Engine.StaticMeshComponent"

CUBE_PATH = "/Engine/BasicShapes/Cube.Cube"
FLOOR_MATERIAL_PATH = (
    "/Game/LineBoss/Materials/Environment/"
    "MI_LB_SealedFactoryConcrete_Neutral_v001."
    "MI_LB_SealedFactoryConcrete_Neutral_v001"
)
WALL_MATERIAL_PATH = (
    "/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal"
)
YELLOW_MATERIAL_PATH = (
    "/Game/LineBoss/Materials/M_LB_SafetyYellow.M_LB_SafetyYellow"
)

LOCATION_TOLERANCE_CM = 0.02
ROTATION_TOLERANCE_DEG = 0.02
SCALE_TOLERANCE = 0.0002
PROPERTY_TOLERANCE = 0.01
RECT_LIGHT_INTENSITY = 12_000.0


def _tags(*semantic: str) -> tuple[str, ...]:
    return tuple(sorted((MAP_TAG, *semantic)))


# location_cm, dimensions_cm, material, collision profile, semantic tags, shadow
BOX_SPECS = {
    "LB_PS_ENV_Floor_60m_x_40m": {
        "location": (0.0, 0.0, -25.0),
        "dimensions": (6_000.0, 4_000.0, 50.0),
        "material": FLOOR_MATERIAL_PATH,
        "collision_profile": "BlockAll",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.Shell"),
        "cast_shadow": True,
    },
    "LB_PS_ENV_Wall_North": {
        "location": (0.0, 2_000.0, 750.0),
        "dimensions": (6_000.0, 40.0, 1_500.0),
        "material": WALL_MATERIAL_PATH,
        "collision_profile": "BlockAll",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.Shell"),
        "cast_shadow": True,
    },
    "LB_PS_ENV_Wall_South": {
        "location": (0.0, -2_000.0, 750.0),
        "dimensions": (6_000.0, 40.0, 1_500.0),
        "material": WALL_MATERIAL_PATH,
        "collision_profile": "BlockAll",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.Shell"),
        "cast_shadow": True,
    },
    "LB_PS_ENV_Wall_West": {
        "location": (-3_000.0, 0.0, 750.0),
        "dimensions": (40.0, 4_000.0, 1_500.0),
        "material": WALL_MATERIAL_PATH,
        "collision_profile": "BlockAll",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.Shell"),
        "cast_shadow": True,
    },
    "LB_PS_ENV_Wall_East": {
        "location": (3_000.0, 0.0, 750.0),
        "dimensions": (40.0, 4_000.0, 1_500.0),
        "material": WALL_MATERIAL_PATH,
        "collision_profile": "BlockAll",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.Shell"),
        "cast_shadow": True,
    },
    "LB_PS_ENV_EDCellBoundary_North": {
        "location": (0.0, 650.0, 1.0),
        "dimensions": (1_900.0, 10.0, 1.0),
        "material": YELLOW_MATERIAL_PATH,
        "collision_profile": "NoCollision",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.EDCellBoundary"),
        "cast_shadow": False,
    },
    "LB_PS_ENV_EDCellBoundary_South": {
        "location": (0.0, -650.0, 1.0),
        "dimensions": (1_900.0, 10.0, 1.0),
        "material": YELLOW_MATERIAL_PATH,
        "collision_profile": "NoCollision",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.EDCellBoundary"),
        "cast_shadow": False,
    },
    "LB_PS_ENV_EDCellBoundary_WestNorth": {
        "location": (-950.0, 475.0, 1.0),
        "dimensions": (10.0, 350.0, 1.0),
        "material": YELLOW_MATERIAL_PATH,
        "collision_profile": "NoCollision",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.EDCellBoundary"),
        "cast_shadow": False,
    },
    "LB_PS_ENV_EDCellBoundary_WestSouth": {
        "location": (-950.0, -475.0, 1.0),
        "dimensions": (10.0, 350.0, 1.0),
        "material": YELLOW_MATERIAL_PATH,
        "collision_profile": "NoCollision",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.EDCellBoundary"),
        "cast_shadow": False,
    },
    "LB_PS_ENV_EDCellBoundary_EastNorth": {
        "location": (950.0, 475.0, 1.0),
        "dimensions": (10.0, 350.0, 1.0),
        "material": YELLOW_MATERIAL_PATH,
        "collision_profile": "NoCollision",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.EDCellBoundary"),
        "cast_shadow": False,
    },
    "LB_PS_ENV_EDCellBoundary_EastSouth": {
        "location": (950.0, -475.0, 1.0),
        "dimensions": (10.0, 350.0, 1.0),
        "material": YELLOW_MATERIAL_PATH,
        "collision_profile": "NoCollision",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.EDCellBoundary"),
        "cast_shadow": False,
    },
    "LB_PS_INTERFACE_CarrierInput": {
        "location": (-1_350.0, 0.0, 1.0),
        "dimensions": (700.0, 500.0, 1.0),
        "material": YELLOW_MATERIAL_PATH,
        "collision_profile": "NoCollision",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Interface.CarrierInput"),
        "cast_shadow": False,
    },
    "LB_PS_INTERFACE_CarrierOutput": {
        "location": (1_350.0, 0.0, 1.0),
        "dimensions": (700.0, 500.0, 1.0),
        "material": YELLOW_MATERIAL_PATH,
        "collision_profile": "NoCollision",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Interface.CarrierOutput"),
        "cast_shadow": False,
    },
    "LB_PS_ENV_ServiceWalkway_North": {
        "location": (0.0, 1_450.0, 0.8),
        "dimensions": (5_400.0, 300.0, 0.8),
        "material": WALL_MATERIAL_PATH,
        "collision_profile": "NoCollision",
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.ServiceWalkway"),
        "cast_shadow": False,
    },
}

REVIEW_CAMERA_SPECS = {
    "LB_PaintShop_ReviewCamera_Overview_v001": {
        "location": (-3_400.0, -2_800.0, 2_300.0),
        "target": (0.0, 0.0, 260.0),
        "fov": 52.0,
    },
    "LB_PaintShop_ReviewCamera_EDCell_v001": {
        "location": (-2_400.0, -1_900.0, 1_350.0),
        "target": (0.0, 0.0, 300.0),
        "fov": 48.0,
    },
}

EXPECTED_ACTORS: dict[str, dict[str, Any]] = {}
for _label, _box in BOX_SPECS.items():
    EXPECTED_ACTORS[_label] = {
        "class": STATIC_MESH_ACTOR_PATH,
        "tags": _box["tags"],
        "location": _box["location"],
        "rotation": (0.0, 0.0, 0.0),  # pitch, yaw, roll
        "scale": tuple(value / 100.0 for value in _box["dimensions"]),
    }

for _x in (-1_500.0, 0.0, 1_500.0):
    for _y in (-850.0, 850.0):
        _label = f"LB_PS_ENV_Light_{int(_x):+05d}_{int(_y):+04d}"
        EXPECTED_ACTORS[_label] = {
            "class": RECT_LIGHT_PATH,
            "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.Lighting"),
            "location": (_x, _y, 1_300.0),
            "rotation": (-90.0, 0.0, 0.0),
            "scale": (1.0, 1.0, 1.0),
        }

EXPECTED_ACTORS.update({
    "LB_PS_ENV_DirectionalLight": {
        "class": DIRECTIONAL_LIGHT_PATH,
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.Lighting"),
        "location": (0.0, 0.0, 1_400.0),
        "rotation": (-52.0, -28.0, 0.0),
        # UE 5.8 intentionally makes the DirectionalLight root 2.5x so its
        # editor icon is readable (Engine/Private/Light.cpp). This is the
        # native class default, not a map-authoring scale drift.
        "scale": (2.5, 2.5, 2.5),
    },
    "LB_PS_ENV_SkyLight": {
        "class": SKY_LIGHT_PATH,
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.Lighting"),
        "location": (0.0, 0.0, 1_300.0),
        "rotation": (0.0, 0.0, 0.0),
        "scale": (1.0, 1.0, 1.0),
    },
    "LB_PS_ENV_NeutralExposure": {
        "class": POST_PROCESS_VOLUME_PATH,
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.Lighting"),
        "location": (0.0, 0.0, 0.0),
        "rotation": (0.0, 0.0, 0.0),
        "scale": (1.0, 1.0, 1.0),
    },
    "LB_PaintShop_Prototype_PlayerStart_v001": {
        "class": PLAYER_START_PATH,
        "tags": _tags("LB.PaintShop.Prototype.PlayerStart"),
        "location": (0.0, 0.0, 180.0),
        "rotation": (0.0, 0.0, 0.0),
        "scale": (1.0, 1.0, 1.0),
    },
    "LB_PaintShop_PrototypeBootstrap_v001": {
        "class": BOOTSTRAP_CLASS_PATH,
        "tags": _tags(
            "LB.PaintShop.Prototype.Bootstrap",
            "LB.PaintShop.Experimental.WorldBootstrap.v001",
        ),
        "location": (0.0, 0.0, 0.0),
        "rotation": (0.0, 0.0, 0.0),
        "scale": (1.0, 1.0, 1.0),
    },
})

for _label, _camera in REVIEW_CAMERA_SPECS.items():
    EXPECTED_ACTORS[_label] = {
        "class": CAMERA_ACTOR_PATH,
        "tags": _tags(ENV_TAG, "LB.PaintShop.Environment.ReviewCamera"),
        "location": _camera["location"],
        "look_at": _camera["target"],
        "scale": (1.0, 1.0, 1.0),
    }

if len(EXPECTED_ACTORS) != 27:
    raise AssertionError("The independent Paint map contract must contain exactly 27 actors")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


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


def close_tuple(actual: Any, expected: Any, tolerance: float) -> bool:
    return (
        actual is not None
        and len(actual) == len(expected)
        and all(abs(float(left) - float(right)) <= tolerance
                for left, right in zip(actual, expected))
    )


def tags_of(actor: Any) -> list[str]:
    return [str(tag) for tag in actor.get_editor_property("tags")]


def add_check(state: dict[str, Any], name: str, passed: bool,
              expected: Any = None, actual: Any = None) -> None:
    item = {"name": name, "passed": bool(passed)}
    if expected is not None:
        item["expected"] = expected
    if actual is not None:
        item["actual"] = actual
    state["checks"].append(item)
    if not passed:
        failure = {"check": name}
        if expected is not None:
            failure["expected"] = expected
        if actual is not None:
            failure["actual"] = actual
        state["failures"].append(failure)


def add_exception(state: dict[str, Any], name: str, exc: Exception) -> None:
    add_check(
        state,
        name,
        False,
        "operation completes without exception",
        f"{type(exc).__name__}: {exc}",
    )


def protected_snapshot() -> tuple[dict[str, str], list[str]]:
    relative_paths = list(PROTECTED_FIXED_RELATIVE)
    save_root = ROOT / "Saved/SaveGames"
    if save_root.exists():
        relative_paths.extend(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in sorted(save_root.rglob("*.sav"))
        )
    result: dict[str, str] = {}
    missing: list[str] = []
    for relative in relative_paths:
        path = ROOT / relative
        if not path.is_file():
            missing.append(relative)
            continue
        result[relative] = sha256(path)
    return result, missing


def hash_or_none(path: Path) -> str | None:
    return sha256(path) if path.is_file() else None


def get_editor_world():
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if subsystem is not None:
        return subsystem.get_editor_world()
    fallback = getattr(unreal, "EditorLevelLibrary", None)
    return fallback.get_editor_world() if fallback is not None else None


def world_partition_evidence(world: Any) -> dict[str, Any]:
    getter = getattr(world, "get_world_partition", None)
    if callable(getter):
        try:
            partition = getter()
            return {
                "api": "get_world_partition",
                "enabled": partition is not None,
                "object": path_name(partition),
            }
        except Exception as exc:
            return {
                "api": "get_world_partition",
                "enabled": None,
                "error": f"{type(exc).__name__}: {exc}",
            }
    # UWorld::GetWorldPartition is public C++ but is not reflected into UE
    # Python. The reflected VisibleAnywhere property lives on WorldSettings.
    try:
        settings = world.get_world_settings()
        if settings is None:
            raise RuntimeError("loaded world has no WorldSettings")
        partition = settings.get_editor_property("world_partition")
        return {
            "api": "WorldSettings.world_partition property",
            "enabled": partition is not None,
            "object": path_name(partition),
        }
    except Exception as exc:
        return {
            "api": None,
            "enabled": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def expected_rotation(spec: dict[str, Any]):
    if "look_at" in spec:
        return unreal.MathLibrary.find_look_at_rotation(
            unreal.Vector(*spec["location"]), unreal.Vector(*spec["look_at"])
        )
    pitch, yaw, roll = spec["rotation"]
    return unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw)


def object_is_a(actor: Any, expected_class: Any) -> bool:
    if actor is None or expected_class is None:
        return False
    method = getattr(actor, "is_a", None)
    if callable(method):
        try:
            return bool(method(expected_class))
        except Exception:
            pass
    current = actor.get_class()
    visited: set[str] = set()
    while current is not None:
        current_path = path_name(current)
        if current == expected_class:
            return True
        if current_path in visited:
            break
        visited.add(current_path)
        getter = getattr(current, "get_super_class", None)
        if not callable(getter):
            break
        try:
            current = getter()
        except Exception:
            break
    return False


def validate_creation_chain(state: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    actual_hashes = {
        "builder_script_sha256": hash_or_none(BUILDER_FILE),
        "creation_receipt_sha256": hash_or_none(CREATE_RECEIPT),
        "map_sha256": hash_or_none(MAP_FILE),
    }
    facts["artifact_hashes_before_load"] = actual_hashes
    add_check(state, "builder_script_exists", BUILDER_FILE.is_file(), True,
              BUILDER_FILE.is_file())
    add_check(state, "creation_receipt_exists", CREATE_RECEIPT.is_file(), True,
              CREATE_RECEIPT.is_file())
    add_check(state, "map_file_exists", MAP_FILE.is_file(), True, MAP_FILE.is_file())
    add_check(
        state, "frozen_builder_script_sha256",
        actual_hashes["builder_script_sha256"] == EXPECTED_BUILDER_SHA256,
        EXPECTED_BUILDER_SHA256, actual_hashes["builder_script_sha256"],
    )
    add_check(
        state, "frozen_creation_receipt_sha256",
        actual_hashes["creation_receipt_sha256"] == EXPECTED_CREATE_RECEIPT_SHA256,
        EXPECTED_CREATE_RECEIPT_SHA256, actual_hashes["creation_receipt_sha256"],
    )
    add_check(
        state, "frozen_map_sha256",
        actual_hashes["map_sha256"] == EXPECTED_MAP_SHA256,
        EXPECTED_MAP_SHA256, actual_hashes["map_sha256"],
    )

    receipt: dict[str, Any] = {}
    if CREATE_RECEIPT.is_file():
        try:
            loaded = json.loads(CREATE_RECEIPT.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise TypeError("creation receipt root must be a JSON object")
            receipt = loaded
            add_check(state, "creation_receipt_json", True, "valid JSON object", "valid")
        except Exception as exc:
            add_exception(state, "creation_receipt_json", exc)
    else:
        add_check(state, "creation_receipt_json", False, "valid JSON object", "missing")

    if receipt:
        receipt_binding = {
            "$schema": receipt.get("$schema"),
            "status": receipt.get("status"),
            "builder_script": receipt.get("builder_script"),
            "builder_script_sha256": receipt.get("builder_script_sha256"),
            "map": receipt.get("map"),
            "map_sha256": receipt.get("map_sha256"),
            "failures": receipt.get("failures"),
        }
        expected_binding = {
            "$schema": CREATE_RECEIPT_SCHEMA,
            "status": CREATE_RECEIPT_STATUS,
            "builder_script": BUILDER_RELATIVE,
            "builder_script_sha256": EXPECTED_BUILDER_SHA256,
            "map": MAP,
            "map_sha256": EXPECTED_MAP_SHA256,
            "failures": [],
        }
        add_check(
            state, "creation_receipt_exact_binding",
            receipt_binding == expected_binding, expected_binding, receipt_binding,
        )
        receipt_facts = receipt.get("facts")
        expected_fact_binding = {
            "world": MAP_OBJECT,
            "actor_count": 27,
            "map_owned_actor_count": 27,
            "expected_map_owned_actor_count": 27,
            "bootstrap_count": 1,
            "forbidden_actor_count": 0,
            "game_mode": GAME_MODE_CLASS_PATH,
            "pawn_class": PAWN_CLASS_PATH,
            "hud_class": HUD_CLASS_PATH,
            "requested_world_partition": False,
        }
        actual_fact_binding = {
            key: receipt_facts.get(key) if isinstance(receipt_facts, dict) else None
            for key in expected_fact_binding
        }
        add_check(
            state, "creation_receipt_fact_binding",
            actual_fact_binding == expected_fact_binding,
            expected_fact_binding, actual_fact_binding,
        )
        receipt_protected = receipt.get("protected_hashes")
        add_check(
            state, "creation_receipt_exact_protected_hashes",
            receipt_protected == EXPECTED_PROTECTED_HASHES,
            EXPECTED_PROTECTED_HASHES, receipt_protected,
        )
    else:
        add_check(state, "creation_receipt_exact_binding", False,
                  "authoritative creation receipt fields", None)
        add_check(state, "creation_receipt_fact_binding", False,
                  "authoritative creation facts", None)
        add_check(state, "creation_receipt_exact_protected_hashes", False,
                  EXPECTED_PROTECTED_HASHES, None)

    current_protected, missing = protected_snapshot()
    facts["protected_hashes_before_load"] = current_protected
    add_check(state, "protected_files_present", not missing, [], missing)
    add_check(
        state, "current_exact_protected_hashes",
        current_protected == EXPECTED_PROTECTED_HASHES,
        EXPECTED_PROTECTED_HASHES, current_protected,
    )
    return receipt


def validate_actor_base_contract(
        state: dict[str, Any], label: str, actor: Any,
        spec: dict[str, Any]) -> dict[str, Any]:
    actual_class = path_name(actor.get_class())
    actual_tags = tags_of(actor)
    actual_location = vector_tuple(actor.get_actor_location())
    actual_rotation_object = actor.get_actor_rotation()
    actual_rotation = rotator_tuple(actual_rotation_object)
    actual_scale = vector_tuple(actor.get_actor_scale3d())
    expected_rotation_object = expected_rotation(spec)
    expected_rotation_values = rotator_tuple(expected_rotation_object)
    class_ok = actual_class == spec["class"]
    tags_ok = (
        sorted(actual_tags) == list(spec["tags"])
        and len(actual_tags) == len(set(actual_tags))
    )
    location_ok = close_tuple(
        actual_location, spec["location"], LOCATION_TOLERANCE_CM
    )
    rotation_ok = actual_rotation_object.is_near_equal(
        expected_rotation_object, ROTATION_TOLERANCE_DEG
    )
    scale_ok = close_tuple(actual_scale, spec["scale"], SCALE_TOLERANCE)
    evidence = {
        "class": actual_class,
        "tags": actual_tags,
        "location_cm": list(actual_location),
        "rotation_pitch_yaw_roll_deg": list(actual_rotation),
        "scale": list(actual_scale),
        "class_ok": class_ok,
        "tags_ok": tags_ok,
        "location_ok": location_ok,
        "rotation_ok": rotation_ok,
        "scale_ok": scale_ok,
    }
    expected = {
        "class": spec["class"],
        "tags": list(spec["tags"]),
        "location_cm": list(spec["location"]),
        "rotation_pitch_yaw_roll_deg": list(expected_rotation_values),
        "scale": list(spec["scale"]),
    }
    add_check(
        state, f"exact_actor_contract::{label}",
        class_ok and tags_ok and location_ok and rotation_ok and scale_ok,
        expected, evidence,
    )
    return evidence


def validate_static_mesh_contracts(
        state: dict[str, Any], by_label: dict[str, list[Any]],
        facts: dict[str, Any]) -> None:
    rows: dict[str, Any] = {}
    for label, spec in BOX_SPECS.items():
        actors = by_label.get(label, [])
        if len(actors) != 1:
            continue
        actor = actors[0]
        try:
            component = actor.get_editor_property("static_mesh_component")
            mesh = component.get_editor_property("static_mesh") if component else None
            material = component.get_material(0) if component else None
            collision = component.get_collision_enabled() if component else None
            profile = (str(component.get_collision_profile_name())
                       if component else None)
            navigation = (component.get_editor_property("can_ever_affect_navigation")
                          if component else None)
            cast_shadow = (component.get_editor_property("cast_shadow")
                           if component else None)
            expected_collision = (
                unreal.CollisionEnabled.QUERY_AND_PHYSICS
                if spec["collision_profile"] == "BlockAll"
                else unreal.CollisionEnabled.NO_COLLISION
            )
            actual = {
                "component_class": path_name(component.get_class()) if component else None,
                "mesh": path_name(mesh),
                "material_slot_0": path_name(material),
                "collision_enabled": str(collision),
                "collision_profile": profile,
                "can_ever_affect_navigation": navigation,
                "cast_shadow": cast_shadow,
            }
            expected = {
                "component_class": STATIC_MESH_COMPONENT_PATH,
                "mesh": CUBE_PATH,
                "material_slot_0": spec["material"],
                "collision_enabled": str(expected_collision),
                "collision_profile": spec["collision_profile"],
                "can_ever_affect_navigation": False,
                "cast_shadow": spec["cast_shadow"],
            }
            valid = (
                component is not None
                and actual["component_class"] == STATIC_MESH_COMPONENT_PATH
                and actual["mesh"] == CUBE_PATH
                and actual["material_slot_0"] == spec["material"]
                and collision == expected_collision
                and profile == spec["collision_profile"]
                and navigation is False
                and cast_shadow is spec["cast_shadow"]
            )
            rows[label] = {"valid": valid, **actual}
            add_check(state, f"static_mesh_component_contract::{label}",
                      valid, expected, actual)
        except Exception as exc:
            rows[label] = {"valid": False, "error": f"{type(exc).__name__}: {exc}"}
            add_exception(state, f"static_mesh_component_contract::{label}", exc)
    facts["static_mesh_contracts"] = rows


def validate_rect_lights(
        state: dict[str, Any], by_label: dict[str, list[Any]],
        facts: dict[str, Any]) -> None:
    rows: dict[str, Any] = {}
    for x in (-1_500.0, 0.0, 1_500.0):
        for y in (-850.0, 850.0):
            label = f"LB_PS_ENV_Light_{int(x):+05d}_{int(y):+04d}"
            actors = by_label.get(label, [])
            if len(actors) != 1:
                continue
            try:
                component = actors[0].get_component_by_class(unreal.RectLightComponent)
                actual_units = (component.get_editor_property("intensity_units")
                                if component else None)
                actual = {
                    "component_class": path_name(component.get_class()) if component else None,
                    "intensity": (float(component.get_editor_property("intensity"))
                                  if component else None),
                    "intensity_units": str(actual_units),
                    "attenuation_radius_cm": (
                        float(component.get_editor_property("attenuation_radius"))
                        if component else None
                    ),
                    "source_width_cm": (
                        float(component.get_editor_property("source_width"))
                        if component else None
                    ),
                    "source_height_cm": (
                        float(component.get_editor_property("source_height"))
                        if component else None
                    ),
                    "use_temperature": (
                        component.get_editor_property("use_temperature")
                        if component else None
                    ),
                    "temperature_kelvin": (
                        float(component.get_editor_property("temperature"))
                        if component else None
                    ),
                }
                expected = {
                    "component_class": "/Script/Engine.RectLightComponent",
                    "intensity": RECT_LIGHT_INTENSITY,
                    "intensity_units": str(unreal.LightUnits.LUMENS),
                    "attenuation_radius_cm": 3_200.0,
                    "source_width_cm": 650.0,
                    "source_height_cm": 160.0,
                    "use_temperature": True,
                    "temperature_kelvin": 5_000.0,
                }
                valid = (
                    component is not None
                    and actual["component_class"] == expected["component_class"]
                    and abs(actual["intensity"] - RECT_LIGHT_INTENSITY)
                        <= PROPERTY_TOLERANCE
                    and actual_units == unreal.LightUnits.LUMENS
                    and abs(actual["attenuation_radius_cm"] - 3_200.0)
                        <= PROPERTY_TOLERANCE
                    and abs(actual["source_width_cm"] - 650.0)
                        <= PROPERTY_TOLERANCE
                    and abs(actual["source_height_cm"] - 160.0)
                        <= PROPERTY_TOLERANCE
                    and actual["use_temperature"] is True
                    and abs(actual["temperature_kelvin"] - 5_000.0)
                        <= PROPERTY_TOLERANCE
                )
                rows[label] = {"valid": valid, **actual}
                add_check(state, f"rect_light_contract::{label}", valid, expected, actual)
            except Exception as exc:
                rows[label] = {"valid": False, "error": f"{type(exc).__name__}: {exc}"}
                add_exception(state, f"rect_light_contract::{label}", exc)
    facts["rect_light_contracts"] = rows


def validate_environment_lighting(
        state: dict[str, Any], by_label: dict[str, list[Any]],
        facts: dict[str, Any]) -> None:
    rows: dict[str, Any] = {}
    for label, component_class, expected_class_path in (
        (
            "LB_PS_ENV_DirectionalLight",
            unreal.DirectionalLightComponent,
            "/Script/Engine.DirectionalLightComponent",
        ),
        (
            "LB_PS_ENV_SkyLight",
            unreal.SkyLightComponent,
            "/Script/Engine.SkyLightComponent",
        ),
    ):
        actors = by_label.get(label, [])
        if len(actors) != 1:
            continue
        try:
            component = actors[0].get_component_by_class(component_class)
            actual = {
                "component_class": path_name(component.get_class()) if component else None,
                "intensity": (float(component.get_editor_property("intensity"))
                              if component else None),
            }
            expected = {"component_class": expected_class_path, "intensity": 0.8}
            valid = (
                component is not None
                and actual["component_class"] == expected_class_path
                and abs(actual["intensity"] - 0.8) <= PROPERTY_TOLERANCE
            )
            rows[label] = {"valid": valid, **actual}
            add_check(state, f"environment_light_contract::{label}",
                      valid, expected, actual)
        except Exception as exc:
            rows[label] = {"valid": False, "error": f"{type(exc).__name__}: {exc}"}
            add_exception(state, f"environment_light_contract::{label}", exc)

    exposure_label = "LB_PS_ENV_NeutralExposure"
    exposure_actors = by_label.get(exposure_label, [])
    if len(exposure_actors) == 1:
        try:
            exposure = exposure_actors[0]
            settings = exposure.get_editor_property("settings")
            actual_method = settings.get_editor_property("auto_exposure_method")
            actual = {
                "unbound": exposure.get_editor_property("unbound"),
                "blend_weight": float(exposure.get_editor_property("blend_weight")),
                "override_auto_exposure_method": settings.get_editor_property(
                    "override_auto_exposure_method"
                ),
                "auto_exposure_method": str(actual_method),
                "override_auto_exposure_min_brightness": settings.get_editor_property(
                    "override_auto_exposure_min_brightness"
                ),
                "override_auto_exposure_max_brightness": settings.get_editor_property(
                    "override_auto_exposure_max_brightness"
                ),
                "auto_exposure_min_brightness": float(settings.get_editor_property(
                    "auto_exposure_min_brightness"
                )),
                "auto_exposure_max_brightness": float(settings.get_editor_property(
                    "auto_exposure_max_brightness"
                )),
                "override_auto_exposure_bias": settings.get_editor_property(
                    "override_auto_exposure_bias"
                ),
                "auto_exposure_bias": float(settings.get_editor_property(
                    "auto_exposure_bias"
                )),
            }
            expected = {
                "unbound": True,
                "blend_weight": 1.0,
                "override_auto_exposure_method": True,
                "auto_exposure_method": str(unreal.AutoExposureMethod.AEM_BASIC),
                "override_auto_exposure_min_brightness": True,
                "override_auto_exposure_max_brightness": True,
                "auto_exposure_min_brightness": 1.0,
                "auto_exposure_max_brightness": 1.0,
                "override_auto_exposure_bias": True,
                "auto_exposure_bias": 0.0,
            }
            valid = (
                actual["unbound"] is True
                and abs(actual["blend_weight"] - 1.0) <= PROPERTY_TOLERANCE
                and actual["override_auto_exposure_method"] is True
                and actual_method == unreal.AutoExposureMethod.AEM_BASIC
                and actual["override_auto_exposure_min_brightness"] is True
                and actual["override_auto_exposure_max_brightness"] is True
                and abs(actual["auto_exposure_min_brightness"] - 1.0)
                    <= PROPERTY_TOLERANCE
                and abs(actual["auto_exposure_max_brightness"] - 1.0)
                    <= PROPERTY_TOLERANCE
                and actual["override_auto_exposure_bias"] is True
                and abs(actual["auto_exposure_bias"]) <= PROPERTY_TOLERANCE
            )
            rows[exposure_label] = {"valid": valid, **actual}
            add_check(state, "neutral_fixed_exposure_contract", valid, expected, actual)
        except Exception as exc:
            rows[exposure_label] = {
                "valid": False, "error": f"{type(exc).__name__}: {exc}"
            }
            add_exception(state, "neutral_fixed_exposure_contract", exc)
    facts["environment_lighting_contracts"] = rows


def validate_review_cameras(
        state: dict[str, Any], by_label: dict[str, list[Any]],
        facts: dict[str, Any]) -> None:
    rows: dict[str, Any] = {}
    for label, spec in REVIEW_CAMERA_SPECS.items():
        actors = by_label.get(label, [])
        if len(actors) != 1:
            continue
        try:
            component = actors[0].get_editor_property("camera_component")
            actual = {
                "component_class": path_name(component.get_class()) if component else None,
                "field_of_view": (
                    float(component.get_editor_property("field_of_view"))
                    if component else None
                ),
                "aspect_ratio": (
                    float(component.get_editor_property("aspect_ratio"))
                    if component else None
                ),
                "constrain_aspect_ratio": (
                    component.get_editor_property("constrain_aspect_ratio")
                    if component else None
                ),
                "target_cm": list(spec["target"]),
            }
            expected = {
                "component_class": "/Script/Engine.CameraComponent",
                "field_of_view": spec["fov"],
                "aspect_ratio": 16.0 / 9.0,
                "constrain_aspect_ratio": True,
                "target_cm": list(spec["target"]),
            }
            valid = (
                component is not None
                and actual["component_class"] == expected["component_class"]
                and abs(actual["field_of_view"] - spec["fov"])
                    <= PROPERTY_TOLERANCE
                and abs(actual["aspect_ratio"] - 16.0 / 9.0)
                    <= 0.0001
                and actual["constrain_aspect_ratio"] is True
            )
            rows[label] = {"valid": valid, **actual}
            add_check(state, f"review_camera_component_contract::{label}",
                      valid, expected, actual)
        except Exception as exc:
            rows[label] = {"valid": False, "error": f"{type(exc).__name__}: {exc}"}
            add_exception(state, f"review_camera_component_contract::{label}", exc)
    facts["review_camera_contracts"] = rows


def validate_loaded_map(state: dict[str, Any], facts: dict[str, Any]) -> None:
    library = unreal.EditorAssetLibrary
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    asset_exists = bool(library.does_asset_exist(MAP))
    add_check(state, "map_asset_exists", asset_exists, True, asset_exists)
    add_check(state, "level_editor_subsystem_available", levels is not None, True,
              levels is not None)
    add_check(state, "editor_actor_subsystem_available", actors_api is not None, True,
              actors_api is not None)

    loaded_classes: dict[str, Any] = {}
    for class_path in REQUIRED_CLASS_PATHS:
        try:
            loaded_class = unreal.load_class(None, class_path)
        except Exception as exc:
            loaded_class = None
            add_exception(state, f"compiled_class_load::{class_path}", exc)
        else:
            add_check(state, f"compiled_class_load::{class_path}",
                      loaded_class is not None, class_path, path_name(loaded_class))
        loaded_classes[class_path] = loaded_class
    facts["compiled_classes"] = {
        class_path: path_name(value) for class_path, value in loaded_classes.items()
    }

    if not asset_exists or levels is None or actors_api is None:
        return
    try:
        loaded = bool(levels.load_level(MAP))
    except Exception as exc:
        add_exception(state, "fresh_load_exact_map", exc)
        return
    add_check(state, "fresh_load_exact_map", loaded, True, loaded)
    if not loaded:
        return

    world = get_editor_world()
    add_check(state, "editor_world_available_after_load", world is not None, True,
              world is not None)
    if world is None:
        return
    world_path = world.get_path_name()
    facts["world"] = world_path
    add_check(state, "exact_loaded_world", world_path == MAP_OBJECT,
              MAP_OBJECT, world_path)

    partition = world_partition_evidence(world)
    facts["world_partition"] = partition
    add_check(state, "non_world_partition_map", partition.get("enabled") is False,
              False, partition)

    settings = world.get_world_settings()
    game_mode = (settings.get_editor_property("default_game_mode")
                 if settings is not None else None)
    expected_game_mode = loaded_classes.get(GAME_MODE_CLASS_PATH)
    add_check(
        state, "world_settings_exact_game_mode",
        game_mode is not None and game_mode == expected_game_mode,
        GAME_MODE_CLASS_PATH, path_name(game_mode),
    )

    game_mode_cdo = (unreal.get_default_object(expected_game_mode)
                     if expected_game_mode is not None else None)
    default_pawn = (game_mode_cdo.get_editor_property("default_pawn_class")
                    if game_mode_cdo is not None else None)
    default_hud = (game_mode_cdo.get_editor_property("hud_class")
                   if game_mode_cdo is not None else None)
    add_check(
        state, "game_mode_cdo_exact_management_pawn",
        default_pawn is not None
        and default_pawn == loaded_classes.get(PAWN_CLASS_PATH),
        PAWN_CLASS_PATH, path_name(default_pawn),
    )
    add_check(
        state, "game_mode_cdo_exact_prototype_hud",
        default_hud is not None and default_hud == loaded_classes.get(HUD_CLASS_PATH),
        HUD_CLASS_PATH, path_name(default_hud),
    )
    facts["player_shell"] = {
        "game_mode": path_name(game_mode),
        "default_pawn_class": path_name(default_pawn),
        "hud_class": path_name(default_hud),
    }

    map_actors = list(actors_api.get_all_level_actors())
    actor_records = []
    for actor in map_actors:
        actor_records.append({
            "label": actor.get_actor_label(),
            "class": path_name(actor.get_class()),
            "tags": tags_of(actor),
        })
    map_owned = [actor for actor in map_actors if MAP_TAG in tags_of(actor)]
    nonfoundation = [
        actor for actor in map_actors
        if path_name(actor.get_class()) not in ENGINE_FOUNDATION_CLASS_PATHS
    ]
    facts["actor_count"] = len(map_actors)
    facts["map_owned_actor_count"] = len(map_owned)
    facts["nonfoundation_actor_count"] = len(nonfoundation)
    facts["all_actor_inventory"] = sorted(
        actor_records, key=lambda item: (item["label"], item["class"])
    )
    add_check(state, "exact_27_map_owned_actors", len(map_owned) == 27,
              27, len(map_owned))

    untagged_nonfoundation = [
        {"label": actor.get_actor_label(), "class": path_name(actor.get_class())}
        for actor in nonfoundation if MAP_TAG not in tags_of(actor)
    ]
    add_check(state, "zero_untagged_nonfoundation_actors",
              not untagged_nonfoundation, [], untagged_nonfoundation)
    add_check(state, "exact_27_nonfoundation_actors", len(nonfoundation) == 27,
              27, len(nonfoundation))

    by_label: dict[str, list[Any]] = {}
    for actor in map_owned:
        by_label.setdefault(actor.get_actor_label(), []).append(actor)
    actual_labels = set(by_label)
    expected_labels = set(EXPECTED_ACTORS)
    label_evidence = {
        "missing": sorted(expected_labels - actual_labels),
        "unexpected": sorted(actual_labels - expected_labels),
        "duplicates": sorted(
            label for label, actors in by_label.items() if len(actors) != 1
        ),
    }
    add_check(
        state, "exact_map_owned_label_set_and_cardinality",
        not any(label_evidence.values()),
        {"labels": sorted(expected_labels), "count_per_label": 1},
        label_evidence,
    )

    actor_contract_rows: dict[str, Any] = {}
    for label, spec in EXPECTED_ACTORS.items():
        actors = by_label.get(label, [])
        if len(actors) != 1:
            continue
        try:
            actor_contract_rows[label] = validate_actor_base_contract(
                state, label, actors[0], spec
            )
        except Exception as exc:
            actor_contract_rows[label] = {
                "valid": False, "error": f"{type(exc).__name__}: {exc}"
            }
            add_exception(state, f"exact_actor_contract::{label}", exc)
    facts["map_owned_actor_contracts"] = actor_contract_rows

    bootstrap_class = loaded_classes.get(BOOTSTRAP_CLASS_PATH)
    bootstraps = [
        actor for actor in map_actors
        if bootstrap_class is not None and actor.get_class() == bootstrap_class
    ]
    add_check(
        state, "exactly_one_saved_bootstrap",
        len(bootstraps) == 1,
        1,
        [{"label": actor.get_actor_label(), "class": path_name(actor.get_class())}
         for actor in bootstraps],
    )
    if len(bootstraps) == 1:
        try:
            collision_enabled = bootstraps[0].get_actor_enable_collision()
            add_check(state, "bootstrap_actor_collision_disabled",
                      collision_enabled is False, False, collision_enabled)
        except Exception as exc:
            add_exception(state, "bootstrap_actor_collision_disabled", exc)

    paint_forbidden_classes = {
        BUILD_AUTHORITY_CLASS_PATH: loaded_classes.get(BUILD_AUTHORITY_CLASS_PATH),
        RUNTIME_CLASS_PATH: loaded_classes.get(RUNTIME_CLASS_PATH),
        CELL_CLASS_PATH: loaded_classes.get(CELL_CLASS_PATH),
    }
    saved_paint_production = []
    for actor in map_actors:
        matches = [
            class_path for class_path, loaded_class in paint_forbidden_classes.items()
            if object_is_a(actor, loaded_class)
        ]
        actor_class_path = path_name(actor.get_class())
        if matches or any(
                fragment in actor_class_path for fragment in (
                    "LBPaintShopBuildAuthority",
                    "LBPaintShopPrototypeRuntime",
                    "LBPaintShopCellActor",
                )):
            saved_paint_production.append({
                "label": actor.get_actor_label(),
                "class": actor_class_path,
                "matches": matches,
            })
    add_check(
        state, "zero_saved_paint_authority_runtime_or_cell_actors",
        not saved_paint_production, [], saved_paint_production,
    )

    forbidden_fragments = (
        "LBECoatLineActor",
        "LBGameMode",
        "LBBodyWeldLineActor",
        "LBBodyShop",
        "LBPressShop",
        "LBPressTrain",
        "LBPlayerBuiltPress",
    )
    forbidden_legacy_press_body = [
        {"label": actor.get_actor_label(), "class": path_name(actor.get_class())}
        for actor in map_actors
        if any(fragment in path_name(actor.get_class())
               for fragment in forbidden_fragments)
    ]
    add_check(
        state, "zero_forbidden_legacy_press_or_body_shop_production_actors",
        not forbidden_legacy_press_body, [], forbidden_legacy_press_body,
    )

    unapproved_project_actors = [
        {"label": actor.get_actor_label(), "class": path_name(actor.get_class())}
        for actor in map_actors
        if path_name(actor.get_class()).startswith("/Script/LineBossCarFactory.")
        and path_name(actor.get_class()) != BOOTSTRAP_CLASS_PATH
    ]
    add_check(state, "zero_unapproved_native_project_actors",
              not unapproved_project_actors, [], unapproved_project_actors)

    validate_static_mesh_contracts(state, by_label, facts)
    validate_rect_lights(state, by_label, facts)
    validate_environment_lighting(state, by_label, facts)
    validate_review_cameras(state, by_label, facts)


def finish_immutability_checks(state: dict[str, Any], facts: dict[str, Any]) -> None:
    artifact_hashes_after = {
        "builder_script_sha256": hash_or_none(BUILDER_FILE),
        "creation_receipt_sha256": hash_or_none(CREATE_RECEIPT),
        "map_sha256": hash_or_none(MAP_FILE),
    }
    facts["artifact_hashes_after_load"] = artifact_hashes_after
    expected = {
        "builder_script_sha256": EXPECTED_BUILDER_SHA256,
        "creation_receipt_sha256": EXPECTED_CREATE_RECEIPT_SHA256,
        "map_sha256": EXPECTED_MAP_SHA256,
    }
    add_check(state, "frozen_artifact_hashes_unchanged_after_load",
              artifact_hashes_after == expected, expected, artifact_hashes_after)

    current_protected, missing = protected_snapshot()
    facts["protected_hashes_after_load"] = current_protected
    add_check(state, "protected_files_still_present_after_load", not missing, [], missing)
    add_check(
        state, "protected_hashes_unchanged_after_load",
        current_protected == EXPECTED_PROTECTED_HASHES,
        EXPECTED_PROTECTED_HASHES, current_protected,
    )


def write_result(state: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    status = PASS_STATUS if not state["failures"] else FAIL_STATUS
    result = {
        "$schema": VALIDATION_SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "validator_script": VALIDATOR_RELATIVE,
        "validator_script_sha256": hash_or_none(SCRIPT_FILE),
        "builder_script": BUILDER_RELATIVE,
        "builder_script_sha256": hash_or_none(BUILDER_FILE),
        "creation_receipt": CREATE_RECEIPT_RELATIVE,
        "creation_receipt_sha256": hash_or_none(CREATE_RECEIPT),
        "map": MAP,
        "map_file": MAP_FILE_RELATIVE,
        "map_sha256": hash_or_none(MAP_FILE),
        "expected_map_owned_actor_count": 27,
        "facts": facts,
        "checks": state["checks"],
        "protected_hashes": facts.get("protected_hashes_after_load", {}),
        "writes_to_content_config_or_source": False,
        "failures": state["failures"],
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    state: dict[str, Any] = {"checks": [], "failures": []}
    facts: dict[str, Any] = {
        "fresh_load_requested": MAP,
        "expected_world": MAP_OBJECT,
        "expected_map_owned_actor_count": 27,
    }
    try:
        validate_creation_chain(state, facts)
        validate_loaded_map(state, facts)
    except Exception as exc:
        add_exception(state, "unhandled_validation_exception", exc)
    try:
        finish_immutability_checks(state, facts)
    except Exception as exc:
        add_exception(state, "post_validation_immutability_checks", exc)

    result = write_result(state, facts)
    if result["status"] == PASS_STATUS:
        unreal.log(
            "LINE_BOSS_PAINT_SHOP_PROTOTYPE_MAP_VALIDATION_V001_PASS "
            f"map={MAP} audit={AUDIT}"
        )
        return

    failed_names = [failure["check"] for failure in result["failures"]]
    unreal.log_error(
        "LINE_BOSS_PAINT_SHOP_PROTOTYPE_MAP_VALIDATION_V001_FAIL failed="
        + ",".join(failed_names)
    )
    raise RuntimeError(
        "Paint Shop prototype map validation failed: " + ", ".join(failed_names)
    )


if __name__ == "__main__":
    main()
