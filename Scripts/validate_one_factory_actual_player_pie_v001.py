"""Real-RHI, actual-player PIE proof for the frozen OneFactory shell.

The saved Moorcross Works map is never modified or saved.  The validator starts
PIE with the map-local ``LBOneFactoryGameMode``, proves the actual player owns
the native management pawn/HUD/UMG route, and presses the same HUD action used by
the UMG ``New Factory`` button.  The Press starter data and presentation exist
only in the duplicated PIE world and disappear when PIE ends.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from typing import Any

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
MAP_FILE = (
    ROOT
    / "Content/LineBoss/Factory/OneFactory/v001/Maps/"
      "LB_MoorcrossWorks_OneFactory_v001.umap"
)
CREATE_RECEIPT = ROOT / "Saved/Audits/OneFactory/v001/one_factory_shell_create_v001.json"
SHELL_VALIDATION_RECEIPT = (
    ROOT / "Saved/Audits/OneFactory/v001/one_factory_shell_validation_v001.json"
)
SCRIPT_FILE = Path(__file__).resolve()

EXPECTED_MAP_SHA256 = "750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682"
EXPECTED_CREATE_RECEIPT_SHA256 = (
    "7D26748BBCE53A11CFE6EEC71FFEE54CBC1504EA48950CADC3E236B2AE16DDB7"
)
EXPECTED_SHELL_VALIDATION_RECEIPT_SHA256 = (
    "26F332294FA1640CDACA1D73F23C2F3B8185A6F3EA67A1DEA976AFB09632791E"
)
EXPECTED_BUILDER_SCRIPT_SHA256 = (
    "4EE0A437A9BCC3A5431C39B2D27BB05067FA74F1A6A586B5C2DF05E412131728"
)
EXPECTED_SHELL_VALIDATOR_SHA256 = (
    "2043ED396DFD366CB857F208A38054EE9CCE4906A04EA53C4ABD86ADF1CB5E61"
)

EXPECTED_CREATE_SCHEMA = "lineboss/audit/one-factory/shell-create-v001/v1"
EXPECTED_CREATE_STATUS = (
    "PASS__ONE_FACTORY_NATIVE_HISM_SHELL_ONE_BOOTSTRAP_ONE_PRESS_AUTHORITY_"
    "ZERO_PRODUCTION_MACHINE_OR_WIP"
)
EXPECTED_SHELL_VALIDATION_SCHEMA = (
    "lineboss/audit/one-factory/shell-validation-v001/v1"
)
EXPECTED_SHELL_VALIDATION_STATUS = (
    "PASS__FRESH_RELOAD_ONE_FACTORY_NATIVE_HISM_SHELL_EXACT_AUTHORITIES_"
    "ZERO_PRODUCTION_MACHINE_OR_WIP"
)

EXPECTED_CLASSES = {
    "game_mode": "/Script/LineBossCarFactory.LBOneFactoryGameMode",
    "pawn": "/Script/LineBossCarFactory.LBManagementPawn",
    "hud": "/Script/LineBossCarFactory.LBControlRoomHUD",
    "widget": "/Script/LineBossCarFactory.LBManagementRootWidget",
    "bootstrap": "/Script/LineBossCarFactory.LBOneFactoryBootstrap",
    "press_build_authority": "/Script/LineBossCarFactory.LBPressShopBuildAuthority",
    "starter_authority": (
        "/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"
    ),
    "starter_presentation": (
        "/Script/LineBossCarFactory.LBOneFactoryPressStarterPresentationActor"
    ),
    "capture_bridge": "/Script/LineBossCarFactory.LBOneFactoryCaptureBridge",
}

EXPECTED_STATIONS = (
    ("INBOUND_COIL_RECEIVING", "OF_PRESS_INBOUND_RECEIVING_001", 18),
    ("WRAPPED_COIL_STORAGE", "OF_PRESS_WRAPPED_COIL_STORE_001", 37),
    ("BLANK_PREPARATION", "OF_PRESS_BLANK_PREP_001", 31),
    ("PREPARED_BLANK_BUFFER", "OF_PRESS_PREPARED_BLANK_BUFFER_001", 34),
    ("CONFIGURABLE_PRESS_TRAIN", "OF_PRESS_TRAIN_001", 89),
    ("PANEL_INSPECTION", "OF_PRESS_PANEL_INSPECTION_001", 19),
    ("PANEL_STILLAGE_DISPATCH", "OF_PRESS_PANEL_DISPATCH_001", 40),
)
EXPECTED_CONNECTION_IDS = (
    "OF_PRESS_ROUTE_01_RECEIVING_TO_COIL_STORE",
    "OF_PRESS_ROUTE_02_COIL_STORE_TO_BLANK_PREP",
    "OF_PRESS_ROUTE_03_BLANK_PREP_TO_BUFFER",
    "OF_PRESS_ROUTE_04_BUFFER_TO_PRESS",
    "OF_PRESS_ROUTE_05_PRESS_TO_INSPECTION",
    "OF_PRESS_ROUTE_06_INSPECTION_TO_DISPATCH",
)
EXPECTED_BATCHES = {
    "GraphiteCubeBatch": ("GRAPHITE_CUBE", 32, "/Engine/BasicShapes/Cube.Cube"),
    "TealStructureCubeBatch": (
        "TEAL_STRUCTURE_CUBE", 88, "/Engine/BasicShapes/Cube.Cube"
    ),
    "SteelCubeBatch": ("STEEL_CUBE", 34, "/Engine/BasicShapes/Cube.Cube"),
    "SafetyCubeBatch": ("SAFETY_CUBE", 38, "/Engine/BasicShapes/Cube.Cube"),
    "StatusCubeBatch": ("STATUS_CUBE", 18, "/Engine/BasicShapes/Cube.Cube"),
    "GraphiteCylinderBatch": (
        "GRAPHITE_CYLINDER", 16, "/Engine/BasicShapes/Cylinder.Cylinder"
    ),
    "SteelCylinderBatch": (
        "STEEL_CYLINDER", 8, "/Engine/BasicShapes/Cylinder.Cylinder"
    ),
    "FloorRouteCubeBatch": (
        "FLOOR_ROUTE_CUBE", 34, "/Engine/BasicShapes/Cube.Cube"
    ),
}
EXPECTED_BASE_MATERIAL = "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"

FORBIDDEN_REFERENCE_TOKENS = (
    "meshy",
    "runtimeglb",
    "externalgenerated",
    "originalhighpoly",
    "/downloads/",
    "/developer/validation/",
    "/candidates/",
    "/runtime/pressshop/",
    "/stations/press/",
    "vendor",
)
WIP_TAG_PREFIXES = ("lb.wip", "lb.inventory", "lb.material.unit")

SCREENSHOT_NAMES = (
    "01_empty_factory_management_overview.png",
    "02_populated_press_starter_wide_overview.png",
    "03_press_train_dispatch_agv_close.png",
    "04_populated_press_starter_with_umg.png",
)
SCREENSHOT_SIZE = (1920, 1080)
MINIMUM_SCREENSHOT_BYTES = 32 * 1024

STAMP = os.environ.get("LB_ONE_FACTORY_ACTUAL_PLAYER_STAMP") or datetime.now(
    timezone.utc
).strftime("%Y%m%dT%H%M%SZ")
if re.fullmatch(r"\d{8}T\d{6}(?:\d{3})?Z", STAMP) is None:
    raise RuntimeError(f"Unsafe OneFactory actual-player run stamp: {STAMP!r}")
RUN_DIR = ROOT / "Saved/Audits/OneFactory/v001/ActualPlayerPIE/Runs" / STAMP
CAPTURE_DIR = (
    ROOT / "Saved/ValidationScreenshots/OneFactory/v001/ActualPlayerPIE" / STAMP
)
AUDIT = RUN_DIR / "one_factory_actual_player_pie_v001.json"

CRITICAL_PROTECTED_HASHES = {
    "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap":
        "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
    "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap":
        "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5",
    "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap":
        "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F",
    "Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap":
        "2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069",
    "Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap":
        EXPECTED_MAP_SHA256,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def project_relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT)).replace("\\", "/")


def enum_name(value: Any) -> str:
    text = str(value).rsplit(".", 1)[-1]
    return text.split(":", 1)[0].strip("<> ")


def class_path(value: Any) -> str:
    return value.get_class().get_path_name()


def actor_label(actor: Any) -> str:
    try:
        return str(actor.get_actor_label())
    except Exception:
        return str(actor.get_name())


def actor_tags(actor: Any) -> list[str]:
    return sorted(str(tag) for tag in actor.get_editor_property("tags"))


def vector_dict(value: Any) -> dict[str, float]:
    return {"x": float(value.x), "y": float(value.y), "z": float(value.z)}


def vector_near(value: Any, expected: tuple[float, float, float], tolerance=0.02) -> bool:
    return all(
        math.isfinite(float(component)) and abs(float(component) - target) <= tolerance
        for component, target in zip((value.x, value.y, value.z), expected)
    )


def rotation_near(value: Any, expected: tuple[float, float, float], tolerance=0.02) -> bool:
    return all(
        math.isfinite(float(component)) and abs(float(component) - target) <= tolerance
        for component, target in zip((value.roll, value.pitch, value.yaw), expected)
    )


def actor_transform_is_identity(actor: Any) -> bool:
    return (
        vector_near(actor.get_actor_location(), (0.0, 0.0, 0.0))
        and rotation_near(actor.get_actor_rotation(), (0.0, 0.0, 0.0))
        and vector_near(actor.get_actor_scale3d(), (1.0, 1.0, 1.0))
    )


def transform_near(left: Any, right: Any, tolerance=0.02) -> bool:
    right_rotation = right.rotation.rotator()
    return (
        vector_near(
            left.translation,
            (
                float(right.translation.x),
                float(right.translation.y),
                float(right.translation.z),
            ),
            tolerance,
        )
        and vector_near(
            left.scale3d,
            (
                float(right.scale3d.x),
                float(right.scale3d.y),
                float(right.scale3d.z),
            ),
            tolerance,
        )
        and rotation_near(
            left.rotation.rotator(),
            (
                float(right_rotation.roll),
                float(right_rotation.pitch),
                float(right_rotation.yaw),
            ),
            tolerance,
        )
    )


def actors_of(world: Any, actor_class: Any) -> list[Any]:
    return list(unreal.GameplayStatics.get_all_actors_of_class(world, actor_class))


def require_one(world: Any, actor_class: Any, label: str) -> Any:
    rows = actors_of(world, actor_class)
    if len(rows) != 1:
        raise RuntimeError(f"Expected exactly one {label}, found {len(rows)}")
    return rows[0]


def get_builder(world: Any) -> Any:
    rows = [
        obj
        for obj in unreal.ObjectIterator(unreal.LBOneFactoryPlayerBuilderSubsystem)
        if obj.get_world() == world
    ]
    if len(rows) != 1:
        raise RuntimeError(
            f"Expected exactly one PIE OneFactory player-builder subsystem, found {len(rows)}"
        )
    return rows[0]


def get_widgets(world: Any) -> list[Any]:
    return [
        widget
        for widget in unreal.ObjectIterator(unreal.LBManagementRootWidget)
        if widget.get_world() == world
    ]


def png_dimensions(path: Path) -> list[int] | None:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return [
        int.from_bytes(data[16:20], "big"),
        int.from_bytes(data[20:24], "big"),
    ]


def file_ready(path: Path) -> bool:
    return path.is_file() and path.stat().st_size >= MINIMUM_SCREENSHOT_BYTES


def protected_paths() -> list[Path]:
    rows: set[Path] = {
        ROOT / relative for relative in CRITICAL_PROTECTED_HASHES
    }
    rows.update((CREATE_RECEIPT, SHELL_VALIDATION_RECEIPT))

    config_root = ROOT / "Config"
    if config_root.is_dir():
        rows.update(path for path in config_root.rglob("*") if path.is_file())

    save_root = ROOT / "Saved/SaveGames"
    if save_root.is_dir():
        rows.update(path for path in save_root.rglob("*") if path.is_file())

    for relative in (
        "Source/LineBossCarFactory/LBOneFactoryBootstrap.h",
        "Source/LineBossCarFactory/LBOneFactoryBootstrap.cpp",
        "Source/LineBossCarFactory/LBOneFactoryGameMode.h",
        "Source/LineBossCarFactory/LBOneFactoryGameMode.cpp",
        "Source/LineBossCarFactory/LBOneFactoryPlayerBuilderSubsystem.h",
        "Source/LineBossCarFactory/LBOneFactoryPlayerBuilderSubsystem.cpp",
        "Source/LineBossCarFactory/LBOneFactoryPressStarterLayout.h",
        "Source/LineBossCarFactory/LBOneFactoryPressStarterLayout.cpp",
        "Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.h",
        "Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp",
        "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.h",
        "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.cpp",
        "Source/LineBossCarFactory/LBManagementPawn.h",
        "Source/LineBossCarFactory/LBManagementPawn.cpp",
        "Source/LineBossCarFactory/LBControlRoomHUD.h",
        "Source/LineBossCarFactory/LBControlRoomHUD.cpp",
        "Source/LineBossCarFactory/LBManagementRootWidget.h",
        "Source/LineBossCarFactory/LBManagementRootWidget.cpp",
    ):
        rows.add(ROOT / relative)
    return sorted(rows, key=lambda path: project_relative(path).lower())


def protected_snapshot() -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for path in protected_paths():
        relative = project_relative(path)
        if not path.is_file():
            snapshot[relative] = {"exists": False, "bytes": None, "sha256": None}
        else:
            snapshot[relative] = {
                "exists": True,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
    return snapshot


def protected_changes(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    changes = []
    for relative in sorted(set(before) | set(after)):
        old = before.get(relative)
        new = after.get(relative)
        if old != new:
            changes.append({"path": relative, "before": old, "after": new})
    return changes


def validate_frozen_prerequisites() -> dict[str, Any]:
    required = (MAP_FILE, CREATE_RECEIPT, SHELL_VALIDATION_RECEIPT, SCRIPT_FILE)
    for path in required:
        if not path.is_file():
            raise RuntimeError(f"Missing OneFactory prerequisite: {path}")
    if sha256(MAP_FILE) != EXPECTED_MAP_SHA256:
        raise RuntimeError(f"OneFactory map hash drift: {sha256(MAP_FILE)}")
    if sha256(CREATE_RECEIPT) != EXPECTED_CREATE_RECEIPT_SHA256:
        raise RuntimeError("OneFactory shell creation receipt hash drift")
    if sha256(SHELL_VALIDATION_RECEIPT) != EXPECTED_SHELL_VALIDATION_RECEIPT_SHA256:
        raise RuntimeError("OneFactory independent shell-validation receipt hash drift")

    create = load_json(CREATE_RECEIPT)
    validation = load_json(SHELL_VALIDATION_RECEIPT)
    if (
        create.get("$schema") != EXPECTED_CREATE_SCHEMA
        or create.get("status") != EXPECTED_CREATE_STATUS
        or create.get("map") != MAP
        or create.get("map_sha256") != EXPECTED_MAP_SHA256
        or create.get("builder_script_sha256") != EXPECTED_BUILDER_SCRIPT_SHA256
        or create.get("failures")
    ):
        raise RuntimeError("OneFactory shell creation receipt contract drift")
    if (
        validation.get("$schema") != EXPECTED_SHELL_VALIDATION_SCHEMA
        or validation.get("status") != EXPECTED_SHELL_VALIDATION_STATUS
        or validation.get("map") != MAP
        or validation.get("map_sha256") != EXPECTED_MAP_SHA256
        or validation.get("builder_script_sha256") != EXPECTED_BUILDER_SCRIPT_SHA256
        or validation.get("validator_script_sha256") != EXPECTED_SHELL_VALIDATOR_SHA256
        or validation.get("creation_receipt_sha256")
        != EXPECTED_CREATE_RECEIPT_SHA256
        or validation.get("writes_to_content_config_or_saves") is not False
        or validation.get("failures")
    ):
        raise RuntimeError("OneFactory independent shell-validation receipt contract drift")

    for relative, expected in CRITICAL_PROTECTED_HASHES.items():
        path = ROOT / relative
        actual = sha256(path) if path.is_file() else None
        if actual != expected:
            raise RuntimeError(
                f"Protected anchor drift before OneFactory PIE: {relative}={actual}"
            )
    return {
        "map_sha256": EXPECTED_MAP_SHA256,
        "create_receipt_sha256": EXPECTED_CREATE_RECEIPT_SHA256,
        "shell_validation_receipt_sha256": EXPECTED_SHELL_VALIDATION_RECEIPT_SHA256,
        "builder_script_sha256": EXPECTED_BUILDER_SCRIPT_SHA256,
        "shell_validator_script_sha256": EXPECTED_SHELL_VALIDATOR_SHA256,
    }


PREREQUISITES = validate_frozen_prerequisites()
MAP_SHA_BEFORE = sha256(MAP_FILE)
PROTECTED_BEFORE = protected_snapshot()
missing_protected = [
    relative for relative, row in PROTECTED_BEFORE.items() if not row["exists"]
]
if missing_protected:
    raise RuntimeError("Required protected files are missing: " + ", ".join(missing_protected))

RUN_DIR.mkdir(parents=True, exist_ok=True)
if AUDIT.exists():
    raise RuntimeError(f"Refusing to overwrite OneFactory PIE receipt: {AUDIT}")
if CAPTURE_DIR.exists():
    raise RuntimeError(f"Fresh OneFactory screenshot directory already exists: {CAPTURE_DIR}")
CAPTURE_DIR.mkdir(parents=True, exist_ok=False)

payload: dict[str, Any] = {
    "$schema": "lineboss/audit/one-factory/actual-player-pie-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "IN_PROGRESS",
    "failures": [],
    "stamp": STAMP,
    "map": MAP,
    "map_sha256_before": MAP_SHA_BEFORE,
    "map_sha256_after": None,
    "map_hash_unchanged": False,
    "validator_script": project_relative(SCRIPT_FILE),
    "validator_script_sha256": sha256(SCRIPT_FILE),
    "command_line": str(unreal.SystemLibrary.get_command_line()),
    "real_rhi_contract": {
        "nullrhi_forbidden": True,
        "command_line_has_nullrhi": "nullrhi" in str(
            unreal.SystemLibrary.get_command_line()
        ).lower(),
        "requested_resolution": list(SCREENSHOT_SIZE),
        "render_proof": (
            "three completed high-res tasks plus one native UI-inclusive capture "
            "restricted to an arranged 1920x1080 PIE SViewport"
        ),
        "ui_capture_resize_bridge": EXPECTED_CLASSES["capture_bridge"],
    },
    "prerequisites": PREREQUISITES,
    "writes_to_content_config_source_or_saves_requested": False,
    "pie_transient_only": True,
    "checks": {},
    "screenshots": {},
    "protected": {
        "before": PROTECTED_BEFORE,
        "after": None,
        "changes": None,
    },
}

if payload["real_rhi_contract"]["command_line_has_nullrhi"]:
    raise RuntimeError("Actual-player OneFactory PIE refuses a NullRHI command line")

LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EDITOR_WORLDS = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

started = time.monotonic()
phase_started = started
phase = "starting"
tick_handle = None
capture_task = None
capture_path: Path | None = None
capture_next_phase: str | None = None
capture_kind: str | None = None
ui_resize_last_attempt = 0.0
ui_resize_exact_since: float | None = None
final_status_requested: str | None = None
final_detail = ""


def add_check(name: str, evidence: Any) -> None:
    payload["checks"][name] = {"passed": True, "evidence": evidence}


def record_screenshot(path: Path, source: str, hud_required: bool) -> None:
    if not file_ready(path):
        raise RuntimeError(f"Screenshot is absent or too small: {path}")
    dimensions = png_dimensions(path)
    if dimensions != list(SCREENSHOT_SIZE):
        raise RuntimeError(
            f"OneFactory screenshot is not 1920x1080: {path.name}={dimensions}"
        )
    payload["screenshots"][path.name] = {
        "path": str(path),
        "project_relative_path": project_relative(path),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "dimensions": dimensions,
        "source": source,
        "hud_required": hud_required,
        "real_rhi": True,
    }


def scan_actor_references(world: Any) -> dict[str, Any]:
    actors = actors_of(world, unreal.Actor)
    references: list[dict[str, str]] = []
    production = []
    wip = []
    forbidden_legacy = []
    forbidden_references = []
    for actor in actors:
        class_name = actor.get_class().get_name()
        path = class_path(actor)
        label = actor_label(actor)
        tags = actor_tags(actor)
        identity = f"{path} {actor.get_name()} {label} {' '.join(tags)}"
        if unreal.LBOneFactoryLayoutLibrary.is_map_owned_production_actor_class_name(
            class_name
        ):
            production.append(identity)
        if unreal.LBOneFactoryLayoutLibrary.is_forbidden_legacy_actor_class_name(
            class_name
        ):
            forbidden_legacy.append(identity)
        lowered_tags = [tag.lower() for tag in tags]
        if any(
            tag == "processwip" or tag.startswith(WIP_TAG_PREFIXES)
            for tag in lowered_tags
        ):
            wip.append(identity)

        actor_refs = [path, str(actor.get_name()), label, *tags]
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            actor_refs.extend((component.get_path_name(), component.get_name()))
            mesh = component.get_editor_property("static_mesh")
            if mesh is not None:
                actor_refs.append(mesh.get_path_name())
            for index in range(int(component.get_num_materials())):
                material = component.get_material(index)
                if material is not None:
                    actor_refs.append(material.get_path_name())
                    try:
                        base = material.get_base_material()
                    except Exception:
                        base = None
                    if base is not None:
                        actor_refs.append(base.get_path_name())
        for reference in actor_refs:
            row = {"actor": label, "reference": str(reference)}
            references.append(row)
            lowered = str(reference).replace("\\", "/").lower()
            if any(token in lowered for token in FORBIDDEN_REFERENCE_TOKENS):
                forbidden_references.append(row)
    return {
        "actor_count": len(actors),
        "production": sorted(production),
        "wip": sorted(wip),
        "forbidden_legacy": sorted(forbidden_legacy),
        "forbidden_references": forbidden_references,
        "reference_count": len(references),
    }


def authority_inventory(authority: Any) -> dict[str, Any]:
    def ids(property_name: str, id_property: str) -> list[str]:
        return [
            str(row.get_editor_property(id_property))
            for row in authority.get_editor_property(property_name)
        ]

    return {
        "build_bays": ids("build_bays", "bay_id"),
        "protected_areas": ids("protected_areas", "area_id"),
        "utility_spines": ids("utility_spines", "spine_id"),
        "logistics_spines": ids("logistics_spines", "spine_id"),
        "storage_bay_count": len(authority.get_editor_property("storage_bays")),
    }


def validate_lighting(world: Any) -> dict[str, Any]:
    lights = [
        actor
        for actor in actors_of(world, unreal.RectLight)
        if actor.actor_has_tag(
            unreal.Name("LB.OneFactory.Lighting.Authority.5000K.v001")
        )
    ]
    exposures = [
        actor
        for actor in actors_of(world, unreal.PostProcessVolume)
        if actor.actor_has_tag(
            unreal.Name("LB.OneFactory.Lighting.FixedExposure.v001")
        )
    ]
    if len(lights) != 1 or len(exposures) != 1:
        raise RuntimeError(
            f"Expected one 5000K light and one fixed exposure authority, found "
            f"{len(lights)} / {len(exposures)}"
        )
    component = lights[0].get_component_by_class(unreal.RectLightComponent)
    settings = exposures[0].get_editor_property("settings")
    light = {
        "intensity": float(component.get_editor_property("intensity")),
        "intensity_units": str(component.get_editor_property("intensity_units")),
        "attenuation_radius": float(component.get_editor_property("attenuation_radius")),
        "source_width": float(component.get_editor_property("source_width")),
        "source_height": float(component.get_editor_property("source_height")),
        "use_temperature": bool(component.get_editor_property("use_temperature")),
        "temperature": float(component.get_editor_property("temperature")),
    }
    exposure = {
        "unbound": bool(exposures[0].get_editor_property("unbound")),
        "blend_weight": float(exposures[0].get_editor_property("blend_weight")),
        "override_method": bool(
            settings.get_editor_property("override_auto_exposure_method")
        ),
        "method": str(settings.get_editor_property("auto_exposure_method")),
        "override_min": bool(
            settings.get_editor_property("override_auto_exposure_min_brightness")
        ),
        "override_max": bool(
            settings.get_editor_property("override_auto_exposure_max_brightness")
        ),
        "minimum": float(settings.get_editor_property("auto_exposure_min_brightness")),
        "maximum": float(settings.get_editor_property("auto_exposure_max_brightness")),
        "override_bias": bool(
            settings.get_editor_property("override_auto_exposure_bias")
        ),
        "bias": float(settings.get_editor_property("auto_exposure_bias")),
    }
    if not (
        abs(light["intensity"] - 800_000.0) <= 0.01
        and light["intensity_units"] == str(unreal.LightUnits.LUMENS)
        and abs(light["attenuation_radius"] - 45_000.0) <= 0.01
        and abs(light["source_width"] - 60_000.0) <= 0.01
        and abs(light["source_height"] - 29_000.0) <= 0.01
        and light["use_temperature"]
        and abs(light["temperature"] - 5_000.0) <= 0.01
        and exposure["unbound"]
        and abs(exposure["blend_weight"] - 1.0) <= 0.01
        and exposure["override_method"]
        and settings.get_editor_property("auto_exposure_method")
        == unreal.AutoExposureMethod.AEM_BASIC
        and exposure["override_min"]
        and exposure["override_max"]
        and abs(exposure["minimum"] - 1.0) <= 0.01
        and abs(exposure["maximum"] - 1.0) <= 0.01
        and exposure["override_bias"]
        and abs(exposure["bias"]) <= 0.01
    ):
        raise RuntimeError("OneFactory 5000K/fixed-exposure contract drift")
    return {"lighting_authority": light, "fixed_exposure_authority": exposure}


def validate_actual_player_empty_shell(world: Any) -> tuple[Any, Any, Any, Any]:
    game_mode = require_one(world, unreal.LBOneFactoryGameMode, "OneFactory GameMode")
    bootstrap = require_one(world, unreal.LBOneFactoryBootstrap, "OneFactory bootstrap")
    press_authority = require_one(
        world, unreal.LBPressShopBuildAuthority, "map-authored Press build authority"
    )
    pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
    hud = require_one(world, unreal.LBControlRoomHUD, "native management HUD")
    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    builder = get_builder(world)
    widgets = get_widgets(world)
    if controller is None:
        raise RuntimeError("Actual-player OneFactory PIE has no player controller")
    if (
        class_path(game_mode) != EXPECTED_CLASSES["game_mode"]
        or class_path(pawn) != EXPECTED_CLASSES["pawn"]
        or class_path(hud) != EXPECTED_CLASSES["hud"]
        or unreal.GameplayStatics.get_player_pawn(world, 0) != pawn
        or controller.get_controlled_pawn() != pawn
        or controller.get_view_target() != pawn
        or controller.get_hud() != hud
    ):
        raise RuntimeError("Player controller is not possessing/viewing the exact management pawn/HUD")
    if (
        not game_mode.has_valid_one_factory_shell()
        or game_mode.get_one_factory_bootstrap() != bootstrap
        or str(game_mode.get_factory_display_name()) != "Moorcross Works"
        or "MOORCROSS WORKS ONEFACTORY PLAYER SHELL READY"
        not in str(game_mode.get_one_factory_startup_status())
    ):
        raise RuntimeError("OneFactory GameMode did not validate the exact Moorcross Works shell")
    if (
        not bootstrap.has_valid_shell()
        or not bootstrap.was_validation_attempted()
        or enum_name(bootstrap.get_bootstrap_state()) != "READY"
        or bootstrap.get_press_build_authority() != press_authority
    ):
        raise RuntimeError("OneFactory bootstrap is not Ready and bound to the map Press authority")
    if (
        class_path(bootstrap) != EXPECTED_CLASSES["bootstrap"]
        or class_path(press_authority) != EXPECTED_CLASSES["press_build_authority"]
        or bootstrap.get_owner() is not None
        or bootstrap.get_attach_parent_actor() is not None
        or actor_label(bootstrap) != "LB_OneFactoryBootstrap_v001"
        or press_authority.get_owner() is not None
        or press_authority.get_attach_parent_actor() is not None
        or actor_label(press_authority)
        != "LB_OneFactory_PressBuildAuthority_v001"
        or bootstrap.get_outer() != press_authority.get_outer()
        or not actor_transform_is_identity(bootstrap)
        or not actor_transform_is_identity(press_authority)
        or actor_tags(bootstrap)
        != ["LB.OneFactory.Bootstrap.v001", "LB.Provenance.NativeOnly"]
        or actor_tags(press_authority)
        != [
            "LB.OneFactory.MapAuthored.PressBuildAuthority.v001",
            "LB.Provenance.NativeOnly",
        ]
    ):
        raise RuntimeError("Bootstrap/map-authored Press authority identity relationship drift")

    layout = bootstrap.get_shell_layout_snapshot()
    if unreal.LBOneFactoryLayoutLibrary.validate_moorcross_works_layout(layout) is None:
        raise RuntimeError("Bootstrap shell layout no longer validates as Moorcross Works")
    if (
        unreal.LBOneFactoryLayoutLibrary.validate_press_build_authority_contract(
            layout, press_authority
        )
        is None
    ):
        raise RuntimeError("Map-authored Press build authority no longer matches shell layout")
    inventory = authority_inventory(press_authority)
    if inventory != {
        "build_bays": [
            "OF_BAY_PRESS_01",
            "OF_BAY_BODY_01",
            "OF_BAY_PAINT_01",
            "OF_BAY_ASSEMBLY_01",
        ],
        "protected_areas": [
            "OF_SPINE_LOGISTICS_EW_01",
            "OF_SPINE_SERVICE_EW_01",
        ],
        "utility_spines": ["OF_SPINE_SERVICE_EW_01"],
        "logistics_spines": ["OF_SPINE_LOGISTICS_EW_01"],
        "storage_bay_count": 0,
    }:
        raise RuntimeError(f"Map-authored Press authority array contract drift: {inventory}")
    if actors_of(world, unreal.LBOneFactoryPressStarterLayoutAuthority) or actors_of(
        world, unreal.LBOneFactoryPressStarterPresentationActor
    ):
        raise RuntimeError("Frozen OneFactory shell was not empty before New Factory")

    scan = scan_actor_references(world)
    if scan["production"] or scan["wip"] or scan["forbidden_legacy"] or scan[
        "forbidden_references"
    ]:
        raise RuntimeError(f"Empty OneFactory world isolation scan failed: {scan}")
    audit = unreal.LBOneFactoryWorldAudit(
        bootstrap_count=1,
        press_build_authority_count=1,
        map_owned_production_actor_count=0,
        map_owned_wip_actor_count=0,
        forbidden_legacy_actor_count=0,
        forbidden_provenance_actor_count=0,
        bootstrap_unowned=True,
        press_build_authority_unowned=True,
        press_build_authority_map_tagged=True,
        bootstrap_and_authority_share_level=True,
        protected_map_package=False,
    )
    audit_reason = unreal.LBOneFactoryLayoutLibrary.validate_world_audit(audit)
    if audit_reason is None:
        raise RuntimeError("Reflected OneFactory world-audit library rejected the empty PIE shell")

    hud.open_factory_build()
    if (
        not hud.is_management_visible()
        or hud.get_management_page() != unreal.LBManagementPage.FACTORY_BUILD
        or int(hud.get_management_action_count()) != 5
        or not builder.is_one_factory_builder_world()
        or len(widgets) != 1
        or class_path(widgets[0]) != EXPECTED_CLASSES["widget"]
        or not widgets[0].is_in_viewport()
        or widgets[0].get_visibility() != unreal.SlateVisibility.VISIBLE
    ):
        raise RuntimeError("Native OneFactory UMG Build surface is not visibly player-owned")
    actions = list(builder.get_umg_actions())
    if (
        len(actions) != 5
        or [int(action.action_index) for action in actions] != list(range(5))
        or str(actions[0].title) != "New Factory"
        or not bool(actions[0].enabled)
        or any(bool(action.enabled) for action in actions[1:])
    ):
        raise RuntimeError("Empty OneFactory UMG action model drift")
    summary = str(builder.get_umg_summary())
    if "BOOTSTRAP: READY" not in summary or "PRESS: NOT CREATED" not in summary:
        raise RuntimeError(f"Empty OneFactory UMG summary drift: {summary}")

    rejection_result = builder.commission_press_starter()
    rejection_reason = str(builder.get_last_action_reason())
    if (
        rejection_result is not None
        or "PRESS STARTER REQUIRES ONE DATA AUTHORITY AND ONE NATIVE PRESENTATION"
        not in rejection_reason
        or actors_of(world, unreal.LBOneFactoryPressStarterLayoutAuthority)
        or actors_of(world, unreal.LBOneFactoryPressStarterPresentationActor)
    ):
        raise RuntimeError(
            "Safe commission-before-creation rejection failed closed: "
            f"result={rejection_result!r} reason={rejection_reason}"
        )

    add_check(
        "actual_player_empty_shell",
        {
            "game_mode": class_path(game_mode),
            "pawn": class_path(pawn),
            "hud": class_path(hud),
            "widget": class_path(widgets[0]),
            "controller_possesses_pawn": True,
            "controller_views_pawn": True,
            "bootstrap_state": enum_name(bootstrap.get_bootstrap_state()),
            "bootstrap_status": str(bootstrap.get_bootstrap_status()),
            "press_authority": inventory,
            "zero_starter_pair": True,
            "zero_production_machine_or_wip": True,
            "reflected_world_audit": str(audit_reason),
            "umg_summary": summary,
            "viewport": list(controller.get_viewport_size()),
        },
    )
    add_check(
        "safe_commission_rejection_before_creation",
        {"result": None, "reason": rejection_reason, "starter_pair_after": [0, 0]},
    )
    add_check("fixed_5000k_lighting_and_exposure", validate_lighting(world))
    return pawn, hud, builder, controller


def station_rows(state: Any) -> list[dict[str, Any]]:
    rows = []
    for station in state.stations:
        rows.append(
            {
                "station_id": str(station.station_id),
                "role": enum_name(station.role),
                "location": vector_dict(station.world_transform.translation),
                "panel_type_id": str(station.panel_type_id),
                "die_id": str(station.die_id),
                "player_reconfigurable": bool(station.player_reconfigurable),
                "active_or_reserved_unit_ids": [
                    str(value) for value in station.active_or_reserved_unit_ids
                ],
            }
        )
    return rows


def validate_starter_pair(world: Any, expected_revision: int, commissioned: bool) -> tuple[Any, Any]:
    authority = require_one(
        world,
        unreal.LBOneFactoryPressStarterLayoutAuthority,
        "PIE Press starter data authority",
    )
    presentation = require_one(
        world,
        unreal.LBOneFactoryPressStarterPresentationActor,
        "PIE Press starter presentation",
    )
    if (
        class_path(authority) != EXPECTED_CLASSES["starter_authority"]
        or class_path(presentation) != EXPECTED_CLASSES["starter_presentation"]
        or str(authority.get_name()) != "LB_OneFactory_PressStarter_Data_v001"
        or str(presentation.get_name())
        != "LB_OneFactory_PressStarter_Presentation_v001"
        or actor_tags(authority)
        != [
            "LB.OneFactory.Press.StarterLayoutAuthority.v001",
            "LB.Provenance.NativeOnly",
        ]
        or actor_tags(presentation)
        != [
            "LB.Environment.VisualOnly",
            "LB.NotProcessWIP",
            "LB.OneFactory.PressStarter.NativeProcedural",
            "LB.OneFactory.PressStarter.Presentation.v001",
        ]
        or authority.get_owner() is not None
        or presentation.get_owner() is not None
        or authority.get_attach_parent_actor() is not None
        or presentation.get_attach_parent_actor() is not None
        or authority.get_outer() != presentation.get_outer()
        or not actor_transform_is_identity(authority)
        or not actor_transform_is_identity(presentation)
    ):
        raise RuntimeError("PIE Press starter pair identity/provenance relationship drift")

    state = authority.capture_layout()
    rows = station_rows(state)
    expected_role_id = [(role, station_id) for role, station_id, _count in EXPECTED_STATIONS]
    if (
        int(state.version) != 1
        or str(state.layout_id) != "MOORCROSS_PRESS_STARTER_NATIVE_V001"
        or int(state.revision) != expected_revision
        or bool(state.commissioned) is not commissioned
        or bool(authority.is_commissioned()) is not commissioned
        or len(rows) != 7
        or len(state.connections) != 6
        or [(row["role"], row["station_id"]) for row in rows] != expected_role_id
        or [str(connection.connection_id) for connection in state.connections]
        != list(EXPECTED_CONNECTION_IDS)
        or any(row["active_or_reserved_unit_ids"] for row in rows)
        or unreal.LBOneFactoryPressStarterLayoutLibrary.validate_starter_layout(state)
        is None
    ):
        raise RuntimeError(f"Press starter topology/revision/WIP contract drift: {rows}")

    components = list(
        presentation.get_components_by_class(
            unreal.HierarchicalInstancedStaticMeshComponent
        )
    )
    by_name = {component.get_name(): component for component in components}
    if set(by_name) != set(EXPECTED_BATCHES) or len(components) != 8:
        raise RuntimeError(f"Press presentation HISM batch inventory drift: {sorted(by_name)}")
    batch_rows = []
    for name, (enum_member, expected_count, expected_mesh) in EXPECTED_BATCHES.items():
        component = by_name[name]
        mesh = component.get_editor_property("static_mesh")
        material = component.get_material(0)
        base = material.get_base_material() if material is not None else None
        batch_enum = getattr(unreal.LBOneFactoryPressPresentationBatch, enum_member)
        row = {
            "component": name,
            "enum": enum_member,
            "instances": int(component.get_instance_count()),
            "instance_getter": int(presentation.get_instance_count_for_batch(batch_enum)),
            "mesh": None if mesh is None else mesh.get_path_name(),
            "material": None if material is None else material.get_path_name(),
            "base_material": None if base is None else base.get_path_name(),
            "visible": bool(component.is_visible()),
            "hidden_in_game": bool(component.get_editor_property("hidden_in_game")),
        }
        if not (
            row["instances"] == expected_count
            and row["instance_getter"] == expected_count
            and row["mesh"] == expected_mesh
            and row["base_material"] == EXPECTED_BASE_MATERIAL
            and row["visible"]
            and not row["hidden_in_game"]
        ):
            raise RuntimeError(f"Press presentation HISM batch contract drift: {row}")
        batch_rows.append(row)

    role_rows = []
    for station, (role_name, station_id, expected_count) in zip(
        state.stations, EXPECTED_STATIONS
    ):
        items = list(presentation.get_configured_items_for_role(station.role))
        role_count = int(presentation.get_instance_count_for_role(station.role))
        configured_transform = presentation.get_configured_station_transform(
            station.station_id
        )
        row = {
            "role": role_name,
            "station_id": station_id,
            "instances": role_count,
            "item_count": len(items),
            "all_items_zero_wip": all(
                not bool(item.represents_process_wip) for item in items
            ),
            "transform_matches_data": configured_transform is not None
            and transform_near(configured_transform, station.world_transform),
        }
        if not (
            row["instances"] == expected_count
            and row["item_count"] == expected_count
            and row["all_items_zero_wip"]
            and row["transform_matches_data"]
        ):
            raise RuntimeError(f"Press presentation role contract drift: {row}")
        role_rows.append(row)

    scan = scan_actor_references(world)
    if (
        scan["production"]
        or scan["wip"]
        or scan["forbidden_legacy"]
        or scan["forbidden_references"]
        or not presentation.is_presentation_configured()
        or presentation.represents_process_wip()
        or int(presentation.get_visual_batch_count()) != 8
        or int(presentation.get_visible_instance_count()) != 268
        or str(presentation.get_configured_layout_id())
        != "MOORCROSS_PRESS_STARTER_NATIVE_V001"
        or int(presentation.get_configured_layout_revision()) != expected_revision
        or sum(row["instances"] for row in batch_rows) != 268
        or sum(row["instances"] for row in role_rows) != 268
    ):
        raise RuntimeError(
            "Press presentation NativeOnly/268/zero-WIP contract failed: "
            f"scan={scan}"
        )
    return authority, presentation


def validate_wide_render(world: Any) -> dict[str, Any]:
    _authority, presentation = validate_starter_pair(world, 0, False)
    rows = []
    for component in presentation.get_components_by_class(
        unreal.HierarchicalInstancedStaticMeshComponent
    ):
        row = {
            "component": component.get_name(),
            "instances": int(component.get_instance_count()),
            "visible": bool(component.is_visible()),
            "recently_rendered": bool(component.was_recently_rendered(5.0)),
        }
        if not row["visible"] or not row["recently_rendered"]:
            raise RuntimeError(f"Press HISM batch was not rendered in wide overview: {row}")
        rows.append(row)
    return {"batch_count": len(rows), "visible_instances": 268, "batches": rows}


def project_station(controller: Any, station: Any) -> dict[str, Any]:
    projected = unreal.GameplayStatics.project_world_to_screen(
        controller, station.world_transform.translation, player_viewport_relative=True
    )
    viewport = controller.get_viewport_size()
    on_screen = (
        projected is not None
        and 0.0 <= float(projected.x) <= float(viewport[0])
        and 0.0 <= float(projected.y) <= float(viewport[1])
    )
    return {
        "station_id": str(station.station_id),
        "projected": None
        if projected is None
        else [float(projected.x), float(projected.y)],
        "viewport": [int(viewport[0]), int(viewport[1])],
        "on_screen": on_screen,
    }


def validate_close_render(world: Any) -> dict[str, Any]:
    authority, presentation = validate_starter_pair(world, 2, True)
    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    by_id = {str(station.station_id): station for station in authority.capture_layout().stations}
    projections = [
        project_station(controller, by_id[station_id])
        for station_id in ("OF_PRESS_TRAIN_001", "OF_PRESS_PANEL_DISPATCH_001")
    ]
    if not all(row["on_screen"] for row in projections):
        raise RuntimeError(
            f"Press train and dispatch AGV responsibility were not both on screen: {projections}"
        )
    if not all(
        component.was_recently_rendered(5.0)
        for component in presentation.get_components_by_class(
            unreal.HierarchicalInstancedStaticMeshComponent
        )
    ):
        raise RuntimeError("Press presentation was not recently rendered in the close view")
    return {"projections": projections, "visible_instances": 268}


def start_scene_capture(world: Any, filename: str, next_phase: str) -> None:
    global phase, phase_started, capture_task, capture_path, capture_next_phase, capture_kind
    path = CAPTURE_DIR / filename
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite OneFactory screenshot: {path}")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        SCREENSHOT_SIZE[0],
        SCREENSHOT_SIZE[1],
        str(path),
        force_game_view=False,
    )
    if not task.is_valid_task():
        raise RuntimeError(f"Invalid OneFactory high-resolution task: {filename}")
    capture_task = task
    capture_path = path
    capture_next_phase = next_phase
    capture_kind = "scene"
    phase = "wait_capture"
    phase_started = time.monotonic()


def start_ui_capture(world: Any, filename: str, next_phase: str) -> None:
    global phase, phase_started, capture_task, capture_path, capture_next_phase, capture_kind
    path = CAPTURE_DIR / filename
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite OneFactory UI screenshot: {path}")
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    accepted = unreal.LBOneFactoryCaptureBridge.request_pie_restricted_ui_screenshot(
        world,
        str(path),
        SCREENSHOT_SIZE[0],
        SCREENSHOT_SIZE[1],
    )
    if not accepted:
        raise RuntimeError(
            "Native restricted UI screenshot request was refused at 1920x1080"
        )
    capture_task = None
    capture_path = path
    capture_next_phase = next_phase
    capture_kind = "ui"
    phase = "wait_capture"
    phase_started = time.monotonic()


def continue_capture(world: Any, now: float) -> None:
    global phase, phase_started, capture_task, capture_path, capture_next_phase, capture_kind
    if capture_kind == "scene":
        if now - phase_started < 1.5 or not capture_task.is_task_done():
            return
        if not file_ready(capture_path):
            return
        path = capture_path
        capture_task = None
        record_screenshot(path, "actual_possessed_LBManagementPawn_high_res", False)
        if path.name == "02_populated_press_starter_wide_overview.png":
            add_check("populated_press_wide_render", validate_wide_render(world))
    elif capture_kind == "ui":
        if now - phase_started < 1.0:
            return
        if not file_ready(capture_path):
            return
        record_screenshot(
            capture_path,
            "actual_possessed_LBManagementPawn_native_restricted_SViewport_UI",
            True,
        )
    else:
        raise RuntimeError("Unknown OneFactory screenshot capture kind")

    next_phase = capture_next_phase
    capture_path = None
    capture_next_phase = None
    capture_kind = None
    phase = next_phase
    phase_started = now


def request_finish(status: str, detail: str = "") -> None:
    global phase, phase_started, final_status_requested, final_detail, capture_task
    if phase in {"ending_pie", "finalizing"}:
        return
    capture_task = None
    final_status_requested = status
    final_detail = detail
    phase = "ending_pie"
    phase_started = time.monotonic()
    LEVELS.editor_request_end_play()


def fail(message: str) -> None:
    unreal.log_error("LINE_BOSS_ONE_FACTORY_ACTUAL_PLAYER_PIE_FAIL " + message)
    if message not in payload["failures"]:
        payload["failures"].append(message)
    try:
        request_finish("FAIL__ONE_FACTORY_ACTUAL_PLAYER_PIE_V001", message)
    except Exception as nested:
        payload["failures"].append(f"Failure cleanup request also failed: {nested}")


def finalize_after_pie() -> None:
    global tick_handle, phase
    phase = "finalizing"
    try:
        editor_world = EDITOR_WORLDS.get_editor_world()
        editor_pair = [
            len(actors_of(editor_world, unreal.LBOneFactoryPressStarterLayoutAuthority)),
            len(actors_of(editor_world, unreal.LBOneFactoryPressStarterPresentationActor)),
        ]
        editor_shell = [
            len(actors_of(editor_world, unreal.LBOneFactoryBootstrap)),
            len(actors_of(editor_world, unreal.LBPressShopBuildAuthority)),
        ]
        if editor_pair != [0, 0] or editor_shell != [1, 1]:
            payload["failures"].append(
                f"Post-PIE editor-world cleanup drift: pair={editor_pair} shell={editor_shell}"
            )
        else:
            add_check(
                "pie_transient_pair_destroyed_and_editor_shell_retained",
                {"starter_pair": editor_pair, "bootstrap_press_authority": editor_shell},
            )
    except Exception as exc:
        payload["failures"].append(f"Post-PIE editor-world cleanup audit failed: {exc}")

    payload["map_sha256_after"] = sha256(MAP_FILE)
    payload["map_hash_unchanged"] = (
        payload["map_sha256_after"] == MAP_SHA_BEFORE == EXPECTED_MAP_SHA256
    )
    if not payload["map_hash_unchanged"]:
        payload["failures"].append("Saved OneFactory map hash changed during PIE")

    try:
        after = protected_snapshot()
        changes = protected_changes(PROTECTED_BEFORE, after)
        payload["protected"]["after"] = after
        payload["protected"]["changes"] = changes
        if changes:
            payload["failures"].append(
                "Protected maps/Config/SaveGames/source anchors changed: "
                + ", ".join(row["path"] for row in changes[:12])
            )
        else:
            add_check(
                "protected_anchors_unchanged",
                {"file_count": len(after), "changes": []},
            )
    except Exception as exc:
        payload["failures"].append(f"Protected-anchor final snapshot failed: {exc}")

    required_checks = (
        "actual_player_empty_shell",
        "safe_commission_rejection_before_creation",
        "fixed_5000k_lighting_and_exposure",
        "new_factory_via_native_umg_hud_route",
        "native_only_press_starter_7_roles_8_batches_268_instances",
        "populated_press_wide_render",
        "programme_change_and_commission_success_via_umg_hud_route",
        "press_train_dispatch_agv_close_render",
        "populated_native_umg_visible",
        "native_ui_capture_viewport_1920x1080",
        "pie_transient_pair_destroyed_and_editor_shell_retained",
        "protected_anchors_unchanged",
    )
    missing = [
        name for name in required_checks if not payload["checks"].get(name, {}).get("passed")
    ]
    if missing:
        payload["failures"].append("Missing required live checks: " + ", ".join(missing))
    if set(payload["screenshots"]) != set(SCREENSHOT_NAMES):
        payload["failures"].append(
            "Actual-player screenshot inventory mismatch: "
            + ", ".join(sorted(payload["screenshots"]))
        )
    for name, record in payload["screenshots"].items():
        path = Path(record["path"])
        if (
            not file_ready(path)
            or sha256(path) != record["sha256"]
            or png_dimensions(path) != list(SCREENSHOT_SIZE)
        ):
            payload["failures"].append(
                f"Screenshot changed/disappeared before receipt finalization: {name}"
            )

    payload["status"] = (
        "PASS__ONE_FACTORY_ACTUAL_PLAYER_NATIVE_UMG_PRESS_STARTER_REAL_RHI_PIE_V001"
        if final_status_requested
        == "PASS__ONE_FACTORY_ACTUAL_PLAYER_NATIVE_UMG_PRESS_STARTER_REAL_RHI_PIE_V001"
        and not payload["failures"]
        else "FAIL__ONE_FACTORY_ACTUAL_PLAYER_PIE_V001"
    )
    payload["detail"] = final_detail
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds: float) -> None:
    global phase, phase_started, ui_resize_last_attempt, ui_resize_exact_since
    now = time.monotonic()
    world = EDITOR_WORLDS.get_game_world()
    if phase == "ending_pie":
        if world is None:
            finalize_after_pie()
        elif now - phase_started > 20.0:
            payload["failures"].append("OneFactory PIE did not end within 20 seconds")
            finalize_after_pie()
        return
    if phase == "finalizing":
        return
    if now - started > 180.0:
        fail("Timed out in OneFactory live PIE phase " + phase)
        return
    if world is None:
        return
    try:
        if phase == "wait_capture":
            continue_capture(world, now)
            return

        pawn = require_one(world, unreal.LBManagementPawn, "management pawn")
        hud = require_one(world, unreal.LBControlRoomHUD, "management HUD")
        builder = get_builder(world)
        controller = unreal.GameplayStatics.get_player_controller(world, 0)

        if phase == "wait_world":
            if now - phase_started < 4.0:
                return
            pawn, hud, builder, controller = validate_actual_player_empty_shell(world)
            if not pawn.set_automation_camera(
                unreal.Vector(-14_500.0, 7_000.0, 0.0), -50.0, 30_000.0
            ):
                raise RuntimeError("Could not set actual management camera for empty overview")
            start_scene_capture(
                world,
                "01_empty_factory_management_overview.png",
                "create_factory",
            )
            return

        if phase == "create_factory":
            hud.open_factory_build()
            before_actions = [
                {
                    "index": int(action.action_index),
                    "title": str(action.title),
                    "enabled": bool(action.enabled),
                    "detail": str(action.detail),
                }
                for action in builder.get_umg_actions()
            ]
            if not hud.activate_management_action(0):
                raise RuntimeError(
                    "Native UMG/HUD New Factory action rejected: "
                    + str(builder.get_last_action_reason())
                )
            reason = str(builder.get_last_action_reason())
            authority, presentation = validate_starter_pair(world, 0, False)
            if (
                str(builder.get_selected_target_id()) != "OF_PRESS_TRAIN_001"
                or enum_name(builder.get_selected_target_kind())
                != "PRESS_STARTER_STATION"
                or "NEW FACTORY CREATED" not in reason
            ):
                raise RuntimeError("New Factory did not select the canonical Press train")
            summary = str(builder.get_umg_summary())
            if "PRESS: AWAITING COMMISSION" not in summary or "NATIVE-ONLY PASS" not in summary:
                raise RuntimeError(f"New Factory NativeOnly UMG summary drift: {summary}")
            add_check(
                "new_factory_via_native_umg_hud_route",
                {
                    "call": "LBControlRoomHUD.activate_management_action(0)",
                    "before_actions": before_actions,
                    "result": True,
                    "reason": reason,
                    "selected_target": str(builder.get_selected_target_id()),
                    "summary": summary,
                    "starter_authority": class_path(authority),
                    "presentation": class_path(presentation),
                },
            )
            state = authority.capture_layout()
            role_evidence = []
            for station, (role_name, station_id, expected_count) in zip(
                state.stations, EXPECTED_STATIONS
            ):
                role_evidence.append(
                    {
                        "role": role_name,
                        "station_id": station_id,
                        "instances": int(
                            presentation.get_instance_count_for_role(station.role)
                        ),
                        "expected_instances": expected_count,
                    }
                )
            batches = [
                {
                    "component": component.get_name(),
                    "instances": int(component.get_instance_count()),
                    "mesh": component.get_editor_property("static_mesh").get_path_name(),
                }
                for component in presentation.get_components_by_class(
                    unreal.HierarchicalInstancedStaticMeshComponent
                )
            ]
            provenance_scan = scan_actor_references(world)
            add_check(
                "native_only_press_starter_7_roles_8_batches_268_instances",
                {
                    "layout_id": str(state.layout_id),
                    "revision": int(state.revision),
                    "commissioned": bool(state.commissioned),
                    "stations": station_rows(state),
                    "roles": role_evidence,
                    "connections": [
                        str(connection.connection_id) for connection in state.connections
                    ],
                    "batches": batches,
                    "visual_batch_count": int(presentation.get_visual_batch_count()),
                    "visible_instance_count": int(
                        presentation.get_visible_instance_count()
                    ),
                    "represents_process_wip": bool(
                        presentation.represents_process_wip()
                    ),
                    "authority_tags": actor_tags(authority),
                    "presentation_tags": actor_tags(presentation),
                    "authority_name": str(authority.get_name()),
                    "presentation_name": str(presentation.get_name()),
                    "builder_summary": summary,
                    "forbidden_reference_tokens": list(FORBIDDEN_REFERENCE_TOKENS),
                    "reference_count": provenance_scan["reference_count"],
                    "forbidden_reference_hits": provenance_scan[
                        "forbidden_references"
                    ],
                    "production_actor_hits": provenance_scan["production"],
                    "process_wip_hits": provenance_scan["wip"],
                },
            )
            if not pawn.set_automation_camera(
                unreal.Vector(-14_500.0, 7_000.0, 0.0), -50.0, 30_000.0
            ):
                raise RuntimeError("Could not set populated Press wide camera")
            start_scene_capture(
                world,
                "02_populated_press_starter_wide_overview.png",
                "programme_and_commission",
            )
            return

        if phase == "programme_and_commission":
            authority, _presentation = validate_starter_pair(world, 0, False)
            before = authority.capture_layout()
            if not hud.activate_management_action(2):
                raise RuntimeError(
                    "Native UMG/HUD programme action rejected: "
                    + str(builder.get_last_action_reason())
                )
            programme_reason = str(builder.get_last_action_reason())
            authority, _presentation = validate_starter_pair(world, 1, False)
            programmed = authority.capture_layout()
            before_programmes = sorted(
                {str(row.panel_type_id) for row in before.stations if str(row.panel_type_id) != "None"}
            )
            after_programmes = sorted(
                {
                    str(row.panel_type_id)
                    for row in programmed.stations
                    if str(row.panel_type_id) != "None"
                }
            )
            if (
                before_programmes != ["HOOD_PANEL"]
                or len(after_programmes) != 1
                or after_programmes == before_programmes
                or "PRESS PROGRAMME CHANGED" not in programme_reason
            ):
                raise RuntimeError(
                    f"Atomic programme selection drift: before={before_programmes} "
                    f"after={after_programmes} reason={programme_reason}"
                )
            if not hud.activate_management_action(0):
                raise RuntimeError(
                    "Native UMG/HUD Press commission action rejected: "
                    + str(builder.get_last_action_reason())
                )
            commission_reason = str(builder.get_last_action_reason())
            authority, _presentation = validate_starter_pair(world, 2, True)
            actions = list(builder.get_umg_actions())
            summary = str(builder.get_umg_summary())
            if (
                "PRESS STARTER COMMISSIONED" not in commission_reason
                or str(actions[0].title) != "Press commissioned"
                or bool(actions[0].enabled)
                or "PRESS: COMMISSIONED" not in summary
                or "NATIVE-ONLY PASS" not in summary
            ):
                raise RuntimeError(f"Commissioned UMG state drift: {summary}")
            add_check(
                "programme_change_and_commission_success_via_umg_hud_route",
                {
                    "programme_call": "LBControlRoomHUD.activate_management_action(2)",
                    "programme_reason": programme_reason,
                    "programme_before": before_programmes,
                    "programme_after": after_programmes,
                    "revision_after_programme": int(programmed.revision),
                    "commission_call": "LBControlRoomHUD.activate_management_action(0)",
                    "commission_reason": commission_reason,
                    "revision_after_commission": int(authority.capture_layout().revision),
                    "commissioned": True,
                    "active_or_reserved_wip_count": 0,
                    "umg_action_zero": {
                        "title": str(actions[0].title),
                        "enabled": bool(actions[0].enabled),
                        "detail": str(actions[0].detail),
                    },
                    "summary": summary,
                },
            )
            hud.close_management()
            if hud.is_management_visible():
                raise RuntimeError("Native UMG did not close for unobstructed close Press view")
            if not pawn.set_automation_camera(
                unreal.Vector(-5_500.0, 10_000.0, 0.0), -50.0, 11_000.0
            ):
                raise RuntimeError("Could not set close Press train/AGV camera")
            start_scene_capture(
                world,
                "03_press_train_dispatch_agv_close.png",
                "validate_close_and_open_umg",
            )
            return

        if phase == "validate_close_and_open_umg":
            add_check("press_train_dispatch_agv_close_render", validate_close_render(world))
            hud.open_factory_build()
            if not pawn.set_automation_camera(
                unreal.Vector(-14_500.0, 7_000.0, 0.0), -50.0, 30_000.0
            ):
                raise RuntimeError("Could not restore populated Press overview for UMG")
            phase = "wait_umg_refresh"
            phase_started = now
            return

        if phase == "wait_umg_refresh":
            if now - phase_started < 1.0:
                return
            widgets = get_widgets(world)
            actions = list(builder.get_umg_actions())
            if (
                len(widgets) != 1
                or not widgets[0].is_in_viewport()
                or widgets[0].get_visibility() != unreal.SlateVisibility.VISIBLE
                or not hud.is_management_visible()
                or hud.get_management_page() != unreal.LBManagementPage.FACTORY_BUILD
                or int(hud.get_management_action_count()) != 5
                or str(actions[0].title) != "Press commissioned"
                or bool(actions[0].enabled)
            ):
                raise RuntimeError("Populated native UMG did not reach visible commissioned state")
            add_check(
                "populated_native_umg_visible",
                {
                    "widget": class_path(widgets[0]),
                    "in_viewport": True,
                    "visibility": str(widgets[0].get_visibility()),
                    "management_page": enum_name(hud.get_management_page()),
                    "action_count": int(hud.get_management_action_count()),
                    "action_zero_title": str(actions[0].title),
                    "action_zero_enabled": bool(actions[0].enabled),
                    "summary": str(builder.get_umg_summary()),
                },
            )
            initial_size = unreal.LBOneFactoryCaptureBridge.resize_pie_window_for_game_widget_size(
                world, SCREENSHOT_SIZE[0], SCREENSHOT_SIZE[1]
            )
            initial_draw_size = [int(initial_size.x), int(initial_size.y)]
            if initial_draw_size[0] <= 0 or initial_draw_size[1] <= 0:
                raise RuntimeError(
                    "Native PIE game-widget/window resize request was refused: "
                    f"{initial_draw_size}"
                )
            ui_resize_last_attempt = now
            ui_resize_exact_since = None
            phase = "wait_native_ui_capture_size"
            phase_started = now
            return

        if phase == "wait_native_ui_capture_size":
            reflected = unreal.LBOneFactoryCaptureBridge.get_pie_game_widget_draw_size(world)
            arranged_size = [int(reflected.x), int(reflected.y)]
            player_size = [int(value) for value in controller.get_viewport_size()]
            if arranged_size != list(SCREENSHOT_SIZE):
                ui_resize_exact_since = None
                if now - phase_started >= 10.0:
                    raise RuntimeError(
                        "Native PIE arranged game-widget size did not settle at "
                        f"1920x1080: arranged={arranged_size} player={player_size}"
                    )
                if now - ui_resize_last_attempt >= 0.75:
                    result = unreal.LBOneFactoryCaptureBridge.resize_pie_window_for_game_widget_size(
                        world, SCREENSHOT_SIZE[0], SCREENSHOT_SIZE[1]
                    )
                    result_size = [int(result.x), int(result.y)]
                    if result_size[0] <= 0 or result_size[1] <= 0:
                        raise RuntimeError(
                            "Native PIE game-widget/window corrective resize was refused"
                        )
                    ui_resize_last_attempt = now
                return
            if ui_resize_exact_since is None:
                ui_resize_exact_since = now
                return
            if now - ui_resize_exact_since < 0.5:
                return
            confirmed = unreal.LBOneFactoryCaptureBridge.get_pie_game_widget_draw_size(
                world
            )
            confirmed_size = [int(confirmed.x), int(confirmed.y)]
            if confirmed_size != list(SCREENSHOT_SIZE):
                ui_resize_exact_since = None
                if now - phase_started >= 10.0:
                    raise RuntimeError(
                        "Native PIE arranged game-widget size changed before capture: "
                        f"{confirmed_size}"
                    )
                return
            if now - phase_started < 1.0:
                return
            widgets = get_widgets(world)
            if (
                len(widgets) != 1
                or not widgets[0].is_in_viewport()
                or widgets[0].get_visibility() != unreal.SlateVisibility.VISIBLE
                or not hud.is_management_visible()
                or hud.get_management_page() != unreal.LBManagementPage.FACTORY_BUILD
            ):
                raise RuntimeError(
                    "Native UMG was not visible after exact arranged-widget resize"
                )
            add_check(
                "native_ui_capture_viewport_1920x1080",
                {
                    "bridge": EXPECTED_CLASSES["capture_bridge"],
                    "resize_api": "SWindow.ReshapeWindow",
                    "query_api": "SViewport.GetCachedGeometry().GetDrawSize",
                    "capture_api": (
                        "FScreenshotRequest.RequestScreenshot"
                        "(bShowUI=true,bRestrictToGameViewport=true)"
                    ),
                    "arranged_game_widget": confirmed_size,
                    "actual_player_viewport": player_size,
                    "native_umg_visible_after_resize": True,
                    "post_processing": False,
                },
            )
            start_ui_capture(
                world,
                "04_populated_press_starter_with_umg.png",
                "finish",
            )
            return

        if phase == "finish":
            request_finish(
                "PASS__ONE_FACTORY_ACTUAL_PLAYER_NATIVE_UMG_PRESS_STARTER_REAL_RHI_PIE_V001"
            )
    except Exception as exc:
        fail(str(exc))


try:
    editor_world_before = EDITOR_WORLDS.get_editor_world()
    if editor_world_before is not None and (
        actors_of(editor_world_before, unreal.LBOneFactoryPressStarterLayoutAuthority)
        or actors_of(editor_world_before, unreal.LBOneFactoryPressStarterPresentationActor)
    ):
        raise RuntimeError("Editor world already contains a starter pair before map load")
    if not LEVELS.load_level(MAP):
        raise RuntimeError(f"Could not load frozen OneFactory map: {MAP}")
    editor_world = EDITOR_WORLDS.get_editor_world()
    if (
        len(actors_of(editor_world, unreal.LBOneFactoryBootstrap)) != 1
        or len(actors_of(editor_world, unreal.LBPressShopBuildAuthority)) != 1
        or actors_of(editor_world, unreal.LBOneFactoryPressStarterLayoutAuthority)
        or actors_of(editor_world, unreal.LBOneFactoryPressStarterPresentationActor)
    ):
        raise RuntimeError("Fresh-loaded editor map is not the exact empty OneFactory shell")
    add_check(
        "fresh_loaded_editor_shell_before_pie",
        {"bootstrap": 1, "press_build_authority": 1, "starter_pair": [0, 0]},
    )
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    phase = "wait_world"
    phase_started = time.monotonic()
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
except Exception as exc:
    payload["failures"].append(str(exc))
    payload["status"] = "FAIL__ONE_FACTORY_ACTUAL_PLAYER_PIE_V001"
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    payload["map_sha256_after"] = sha256(MAP_FILE) if MAP_FILE.is_file() else None
    payload["map_hash_unchanged"] = payload["map_sha256_after"] == MAP_SHA_BEFORE
    try:
        after = protected_snapshot()
        payload["protected"]["after"] = after
        payload["protected"]["changes"] = protected_changes(PROTECTED_BEFORE, after)
    except Exception as nested:
        payload["failures"].append(f"Pre-PIE failure snapshot also failed: {nested}")
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()
    raise
