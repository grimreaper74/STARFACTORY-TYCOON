"""Create the isolated one-cell Paint Shop prototype map exactly once.

The map owns only environment, player-review context and one Paint bootstrap.
The bootstrap creates the modular ED-coat cell and its two runtime authorities at
BeginPlay.  Legacy E-coat, Press Shop, Body Shop and campaign actors are forbidden.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
SCRIPT_FILE = ROOT / "Scripts/create_paint_shop_prototype_map_v001.py"
MAP = "/Game/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001"
MAP_FILE = ROOT / "Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap"
AUDIT = ROOT / "Saved/Audits/PaintShop/Experimental_v001/paint_shop_prototype_map_create_v001.json"

GAME_MODE_CLASS_PATH = "/Script/LineBossCarFactory.LBPaintShopPrototypeGameMode"
PAWN_CLASS_PATH = "/Script/LineBossCarFactory.LBPaintShopManagementPawn"
HUD_CLASS_PATH = "/Script/LineBossCarFactory.LBPaintShopPrototypeHUD"
BOOTSTRAP_CLASS_PATH = "/Script/LineBossCarFactory.LBPaintShopPrototypeWorldBootstrap"

MAP_TAG = "LB.PaintShop.Experimental.v001"
ENV_TAG = "LB.PaintShop.Environment"
WIDTH_CM = 6_000.0
DEPTH_CM = 4_000.0
CLEAR_HEIGHT_CM = 1_500.0
RECT_LIGHT_INTENSITY = 12_000.0

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

# The new basic level may enumerate WorldSettings/DefaultPhysicsVolume in some
# editor builds. Every other saved actor is authored here and must carry MAP_TAG.
ENGINE_FOUNDATION_CLASSES = {"WorldSettings", "DefaultPhysicsVolume"}
EXPECTED_MAP_ACTOR_CLASSES = {
    "LB_PS_ENV_Floor_60m_x_40m": "StaticMeshActor",
    "LB_PS_ENV_Wall_North": "StaticMeshActor",
    "LB_PS_ENV_Wall_South": "StaticMeshActor",
    "LB_PS_ENV_Wall_West": "StaticMeshActor",
    "LB_PS_ENV_Wall_East": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_North": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_South": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_WestNorth": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_WestSouth": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_EastNorth": "StaticMeshActor",
    "LB_PS_ENV_EDCellBoundary_EastSouth": "StaticMeshActor",
    "LB_PS_INTERFACE_CarrierInput": "StaticMeshActor",
    "LB_PS_INTERFACE_CarrierOutput": "StaticMeshActor",
    "LB_PS_ENV_ServiceWalkway_North": "StaticMeshActor",
    "LB_PS_ENV_DirectionalLight": "DirectionalLight",
    "LB_PS_ENV_SkyLight": "SkyLight",
    "LB_PS_ENV_NeutralExposure": "PostProcessVolume",
    "LB_PaintShop_Prototype_PlayerStart_v001": "PlayerStart",
    "LB_PaintShop_PrototypeBootstrap_v001": "LBPaintShopPrototypeWorldBootstrap",
    "LB_PaintShop_ReviewCamera_Overview_v001": "CameraActor",
    "LB_PaintShop_ReviewCamera_EDCell_v001": "CameraActor",
}
for _x in (-1_500.0, 0.0, 1_500.0):
    for _y in (-850.0, 850.0):
        EXPECTED_MAP_ACTOR_CLASSES[
            f"LB_PS_ENV_Light_{int(_x):+05d}_{int(_y):+04d}"
        ] = "RectLight"

EXPECTED_BOXES = {
    "LB_PS_ENV_Floor_60m_x_40m": ((0.0, 0.0, -25.0), (6_000.0, 4_000.0, 50.0), "floor", True),
    "LB_PS_ENV_Wall_North": ((0.0, 2_000.0, 750.0), (6_000.0, 40.0, 1_500.0), "wall", True),
    "LB_PS_ENV_Wall_South": ((0.0, -2_000.0, 750.0), (6_000.0, 40.0, 1_500.0), "wall", True),
    "LB_PS_ENV_Wall_West": ((-3_000.0, 0.0, 750.0), (40.0, 4_000.0, 1_500.0), "wall", True),
    "LB_PS_ENV_Wall_East": ((3_000.0, 0.0, 750.0), (40.0, 4_000.0, 1_500.0), "wall", True),
    "LB_PS_ENV_EDCellBoundary_North": ((0.0, 650.0, 1.0), (1_900.0, 10.0, 1.0), "yellow", False),
    "LB_PS_ENV_EDCellBoundary_South": ((0.0, -650.0, 1.0), (1_900.0, 10.0, 1.0), "yellow", False),
    "LB_PS_ENV_EDCellBoundary_WestNorth": ((-950.0, 475.0, 1.0), (10.0, 350.0, 1.0), "yellow", False),
    "LB_PS_ENV_EDCellBoundary_WestSouth": ((-950.0, -475.0, 1.0), (10.0, 350.0, 1.0), "yellow", False),
    "LB_PS_ENV_EDCellBoundary_EastNorth": ((950.0, 475.0, 1.0), (10.0, 350.0, 1.0), "yellow", False),
    "LB_PS_ENV_EDCellBoundary_EastSouth": ((950.0, -475.0, 1.0), (10.0, 350.0, 1.0), "yellow", False),
    "LB_PS_INTERFACE_CarrierInput": ((-1_350.0, 0.0, 1.0), (700.0, 500.0, 1.0), "yellow", False),
    "LB_PS_INTERFACE_CarrierOutput": ((1_350.0, 0.0, 1.0), (700.0, 500.0, 1.0), "yellow", False),
    "LB_PS_ENV_ServiceWalkway_North": ((0.0, 1_450.0, 0.8), (5_400.0, 300.0, 0.8), "wall", False),
}

REVIEW_CAMERA_SPECS = {
    # This camera is outside the plan envelope but above the open-roof wall
    # sightlines, giving an unobstructed whole-cell composition.
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def protected_snapshot() -> dict[str, str]:
    fixed = [ROOT / relative for relative in PROTECTED_FIXED_RELATIVE]
    missing = [str(path.relative_to(ROOT)).replace("\\", "/")
               for path in fixed if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required protected Paint-isolation files are missing: "
            + ", ".join(missing)
        )
    saves = sorted((ROOT / "Saved/SaveGames").rglob("*.sav")) \
        if (ROOT / "Saved/SaveGames").exists() else []
    paths = fixed + saves
    return {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in paths}


def require_class(path: str):
    value = unreal.load_class(None, path)
    if value is None:
        raise RuntimeError(f"Required compiled Paint Shop class is unavailable: {path}")
    return value


def require_asset(path: str, expected_type=None):
    value = unreal.EditorAssetLibrary.load_asset(path) or unreal.load_asset(path)
    if value is None or (expected_type is not None and not isinstance(value, expected_type)):
        raise RuntimeError(f"Required existing Paint environment asset is unavailable: {path}")
    return value


def set_tags(actor, *tags: str) -> None:
    # Preserve class-authored identity tags (notably the bootstrap's durable
    # experimental identity) while adding the map provenance tags exactly once.
    ordered = [str(tag) for tag in actor.get_editor_property("tags")]
    for tag in tags:
        if tag not in ordered:
            ordered.append(tag)
    actor.set_editor_property("tags", [unreal.Name(tag) for tag in ordered])


def get_editor_world():
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    return editor.get_editor_world() if editor is not None else None


def class_path(value) -> str | None:
    return value.get_path_name() if value is not None else None


def tags_of(actor) -> set[str]:
    return {str(tag) for tag in actor.get_editor_property("tags")}


def vector_tuple(value) -> tuple[float, float, float]:
    return float(value.x), float(value.y), float(value.z)


def close_vector(actual, expected, tolerance: float = 0.02) -> bool:
    return all(abs(a - b) <= tolerance for a, b in zip(actual, expected))


def box(actors, cube, material, label: str, location, dimensions, *,
        collision: bool, tags=(), cast_shadow: bool = False):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        raise RuntimeError(f"Could not create {label}")
    actor.set_actor_label(label)
    set_tags(actor, MAP_TAG, ENV_TAG, *tags)
    actor.set_actor_scale3d(unreal.Vector(
        dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component = actor.get_editor_property("static_mesh_component")
    if component is None:
        raise RuntimeError(f"Could not resolve StaticMeshComponent for {label}")
    component.set_static_mesh(cube)
    component.set_material(0, material)
    # UE 5.8's Python wrapper does not persist SetCollisionEnabled(NoCollision)
    # on a spawned StaticMeshComponent whose current profile is BlockAll. Apply
    # the named profile so both BodyInstance and the reflected collision state
    # agree on fresh reload.
    component.set_collision_profile_name("BlockAll" if collision else "NoCollision")
    component.set_editor_property("can_ever_affect_navigation", False)
    component.set_cast_shadow(cast_shadow)
    return actor


def rect_light(actors, label: str, location) -> None:
    actor = actors.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(*location),
        unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0))
    if actor is None:
        raise RuntimeError(f"Could not create {label}")
    actor.set_actor_label(label)
    set_tags(actor, MAP_TAG, ENV_TAG, "LB.PaintShop.Environment.Lighting")
    component = actor.get_component_by_class(unreal.RectLightComponent)
    if component is None:
        raise RuntimeError(f"Could not resolve RectLightComponent for {label}")
    component.set_editor_properties({
        # Match the readable modular Body Shop high-bay fixture standard; 800
        # lumens at this 13 m mounting height was a placeholder-level output.
        "intensity": RECT_LIGHT_INTENSITY,
        "intensity_units": unreal.LightUnits.LUMENS,
        "attenuation_radius": 3_200.0,
        "source_width": 650.0,
        "source_height": 160.0,
        "use_temperature": True,
        "temperature": 5_000.0,
    })


def review_camera(actors, label: str, location, target, fov: float) -> None:
    actor = actors.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    if actor is None:
        raise RuntimeError(f"Could not create {label}")
    actor.set_actor_label(label)
    set_tags(actor, MAP_TAG, ENV_TAG, "LB.PaintShop.Environment.ReviewCamera")
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    component = actor.get_editor_property("camera_component")
    if component is None:
        raise RuntimeError(f"Could not resolve CameraComponent for {label}")
    component.set_editor_properties({
        "field_of_view": float(fov),
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })


def validate_current_map(classes, assets, actors) -> tuple[list[str], dict]:
    failures: list[str] = []
    world = get_editor_world()
    if world is None:
        return ["Paint Shop editor world is unavailable"], {}

    expected_world_path = f"{MAP}.{MAP.rsplit('/', 1)[-1]}"
    world_path = world.get_path_name()
    if world_path != expected_world_path:
        failures.append(
            f"wrong editor world loaded: {world_path}; expected {expected_world_path}"
        )

    settings = world.get_world_settings()
    game_mode = settings.get_editor_property("default_game_mode")
    if game_mode != classes["game_mode"]:
        failures.append("Paint Shop GameMode is not authoritative")

    game_mode_cdo = unreal.get_default_object(classes["game_mode"])
    default_pawn = (game_mode_cdo.get_editor_property("default_pawn_class")
                    if game_mode_cdo is not None else None)
    default_hud = (game_mode_cdo.get_editor_property("hud_class")
                   if game_mode_cdo is not None else None)
    if default_pawn != classes["pawn"]:
        failures.append("Paint Shop GameMode does not own the management pawn class")
    if default_hud != classes["hud"]:
        failures.append("Paint Shop GameMode does not own the prototype HUD class")

    map_actors = list(actors.get_all_level_actors())
    bootstraps = [actor for actor in map_actors
                  if actor.get_class() == classes["bootstrap"]]
    if len(bootstraps) != 1:
        failures.append(f"expected exactly one Paint bootstrap, found {len(bootstraps)}")

    forbidden_fragments = (
        "LBPaintShopBuildAuthority", "LBPaintShopPrototypeRuntime",
        "LBPaintShopCellActor", "LBECoatLineActor", "LBBodyShop",
        "LBPressShop", "LBGameMode",
    )
    forbidden = []
    for actor in map_actors:
        actor_class = actor.get_class()
        actor_class_name = actor_class.get_name()
        actor_class_path = actor_class.get_path_name()
        is_unapproved_project_actor = (
            actor_class_path.startswith("/Script/LineBossCarFactory.")
            and actor_class != classes["bootstrap"]
        )
        if (is_unapproved_project_actor
                or any(fragment in actor_class_name for fragment in forbidden_fragments)):
            forbidden.append(f"{actor.get_actor_label()} ({actor_class_name})")
    if forbidden:
        failures.append("forbidden map-owned production actors: " + "; ".join(forbidden))

    map_owned = [actor for actor in map_actors if MAP_TAG in tags_of(actor)]
    untagged_nonfoundation = [
        f"{actor.get_actor_label()} ({actor.get_class().get_name()})"
        for actor in map_actors
        if actor.get_class().get_name() not in ENGINE_FOUNDATION_CLASSES
        and MAP_TAG not in tags_of(actor)
    ]
    if untagged_nonfoundation:
        failures.append(
            "saved non-foundation actors lack Paint map provenance: "
            + "; ".join(untagged_nonfoundation)
        )

    by_label = {}
    for actor in map_owned:
        by_label.setdefault(actor.get_actor_label(), []).append(actor)
    actual_labels = set(by_label)
    expected_labels = set(EXPECTED_MAP_ACTOR_CLASSES)
    missing = sorted(expected_labels - actual_labels)
    if missing:
        failures.append("missing required Paint shell actors: " + ", ".join(missing))
    unexpected = sorted(actual_labels - expected_labels)
    if unexpected:
        failures.append("unexpected Paint map-owned actors: " + ", ".join(unexpected))
    duplicate_labels = sorted(label for label, values in by_label.items() if len(values) != 1)
    if duplicate_labels:
        failures.append("duplicate Paint map-owned actor labels: " + ", ".join(duplicate_labels))
    if len(map_owned) != len(EXPECTED_MAP_ACTOR_CLASSES):
        failures.append(
            f"expected {len(EXPECTED_MAP_ACTOR_CLASSES)} Paint map-owned actors, "
            f"found {len(map_owned)}"
        )

    inventory_rows = {}
    for label, expected_class_name in EXPECTED_MAP_ACTOR_CLASSES.items():
        values = by_label.get(label, [])
        if len(values) != 1:
            continue
        actor = values[0]
        class_name = actor.get_class().get_name()
        actor_tags = tags_of(actor)
        if class_name != expected_class_name:
            failures.append(
                f"wrong actor class for {label}: {class_name}; expected {expected_class_name}"
            )
        required_tags = {MAP_TAG}
        if label not in {
            "LB_PaintShop_Prototype_PlayerStart_v001",
            "LB_PaintShop_PrototypeBootstrap_v001",
        }:
            required_tags.add(ENV_TAG)
        if label.startswith("LB_PS_ENV_EDCellBoundary_"):
            required_tags.add("LB.PaintShop.Environment.EDCellBoundary")
        elif label == "LB_PS_INTERFACE_CarrierInput":
            required_tags.add("LB.PaintShop.Interface.CarrierInput")
        elif label == "LB_PS_INTERFACE_CarrierOutput":
            required_tags.add("LB.PaintShop.Interface.CarrierOutput")
        elif label == "LB_PS_ENV_ServiceWalkway_North":
            required_tags.add("LB.PaintShop.Environment.ServiceWalkway")
        elif (label.startswith("LB_PS_ENV_Light_")
              or label in {"LB_PS_ENV_DirectionalLight", "LB_PS_ENV_SkyLight",
                           "LB_PS_ENV_NeutralExposure"}):
            required_tags.add("LB.PaintShop.Environment.Lighting")
        elif label.startswith("LB_PaintShop_ReviewCamera_"):
            required_tags.add("LB.PaintShop.Environment.ReviewCamera")
        elif label == "LB_PaintShop_Prototype_PlayerStart_v001":
            required_tags.add("LB.PaintShop.Prototype.PlayerStart")
        elif label == "LB_PaintShop_PrototypeBootstrap_v001":
            required_tags.update({
                "LB.PaintShop.Prototype.Bootstrap",
                "LB.PaintShop.Experimental.WorldBootstrap.v001",
            })
        if not required_tags.issubset(actor_tags):
            failures.append(
                f"missing provenance/semantic tags for {label}: "
                + ", ".join(sorted(required_tags - actor_tags))
            )
        inventory_rows[label] = {
            "class": class_name,
            "tags": sorted(actor_tags),
        }

    box_rows = {}
    for label, (expected_location, expected_dimensions, material_key,
                expected_collision) in EXPECTED_BOXES.items():
        values = by_label.get(label, [])
        if len(values) != 1:
            continue
        actor = values[0]
        component = actor.get_editor_property("static_mesh_component")
        location = vector_tuple(actor.get_actor_location())
        scale = vector_tuple(actor.get_actor_scale3d())
        dimensions = tuple(value * 100.0 for value in scale)
        mesh = component.get_editor_property("static_mesh") if component else None
        material = component.get_material(0) if component else None
        collision = component.get_collision_enabled() if component else None
        collision_profile = (str(component.get_collision_profile_name())
                             if component else None)
        navigation = (component.get_editor_property("can_ever_affect_navigation")
                      if component else None)
        valid = (
            component is not None
            and close_vector(location, expected_location)
            and close_vector(dimensions, expected_dimensions)
            and mesh == assets["cube"]
            and material == assets[material_key]
            and collision == (
                unreal.CollisionEnabled.QUERY_AND_PHYSICS
                if expected_collision else unreal.CollisionEnabled.NO_COLLISION
            )
            and collision_profile == ("BlockAll" if expected_collision else "NoCollision")
            and navigation is False
        )
        if not valid:
            failures.append(f"static shell/interface contract drift: {label}")
        box_rows[label] = {
            "valid": valid,
            "location_cm": list(location),
            "dimensions_cm": list(dimensions),
            "mesh": class_path(mesh),
            "material": class_path(material),
            "collision": str(collision),
            "collision_profile": collision_profile,
            "can_ever_affect_navigation": navigation,
        }

    camera_rows = {}
    for label, spec in REVIEW_CAMERA_SPECS.items():
        values = by_label.get(label, [])
        if len(values) != 1:
            continue
        actor = values[0]
        component = actor.get_editor_property("camera_component")
        location = vector_tuple(actor.get_actor_location())
        expected_rotation = unreal.MathLibrary.find_look_at_rotation(
            unreal.Vector(*spec["location"]), unreal.Vector(*spec["target"])
        )
        rotation_ok = actor.get_actor_rotation().is_near_equal(expected_rotation, 0.02)
        fov = (float(component.get_editor_property("field_of_view"))
               if component else None)
        valid = (component is not None
                 and close_vector(location, spec["location"])
                 and rotation_ok and abs(fov - spec["fov"]) <= 0.01)
        if not valid:
            failures.append(f"review camera composition contract drift: {label}")
        camera_rows[label] = {
            "valid": valid,
            "location_cm": list(location),
            "target_cm": list(spec["target"]),
            "field_of_view": fov,
        }

    rect_light_rows = {}
    for x in (-1_500.0, 0.0, 1_500.0):
        for y in (-850.0, 850.0):
            label = f"LB_PS_ENV_Light_{int(x):+05d}_{int(y):+04d}"
            values = by_label.get(label, [])
            if len(values) != 1:
                continue
            actor = values[0]
            component = actor.get_component_by_class(unreal.RectLightComponent)
            location = vector_tuple(actor.get_actor_location())
            expected_rotation = unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0)
            rotation_ok = actor.get_actor_rotation().is_near_equal(expected_rotation, 0.02)
            values_ok = component is not None and all((
                abs(float(component.get_editor_property("intensity"))
                    - RECT_LIGHT_INTENSITY) <= 0.01,
                abs(float(component.get_editor_property("attenuation_radius")) - 3_200.0) <= 0.01,
                abs(float(component.get_editor_property("source_width")) - 650.0) <= 0.01,
                abs(float(component.get_editor_property("source_height")) - 160.0) <= 0.01,
                component.get_editor_property("intensity_units") == unreal.LightUnits.LUMENS,
                component.get_editor_property("use_temperature") is True,
                abs(float(component.get_editor_property("temperature")) - 5_000.0) <= 0.01,
            ))
            valid = (close_vector(location, (x, y, 1_300.0))
                     and rotation_ok and values_ok)
            if not valid:
                failures.append(f"high-bay lighting contract drift: {label}")
            rect_light_rows[label] = {
                "valid": valid,
                "location_cm": list(location),
                "intensity": (float(component.get_editor_property("intensity"))
                              if component else None),
            }

    for label, component_class, expected_intensity in (
        ("LB_PS_ENV_DirectionalLight", unreal.DirectionalLightComponent, 0.8),
        ("LB_PS_ENV_SkyLight", unreal.SkyLightComponent, 0.8),
    ):
        values = by_label.get(label, [])
        if len(values) == 1:
            component = values[0].get_component_by_class(component_class)
            if (component is None or abs(float(component.get_editor_property("intensity"))
                                         - expected_intensity) > 0.01):
                failures.append(f"environment lighting intensity drift: {label}")

    exposure_values = by_label.get("LB_PS_ENV_NeutralExposure", [])
    if len(exposure_values) == 1:
        exposure = exposure_values[0]
        pp = exposure.get_editor_property("settings")
        exposure_valid = (
            exposure.get_editor_property("unbound") is True
            and abs(float(exposure.get_editor_property("blend_weight")) - 1.0) <= 0.01
            and pp.get_editor_property("override_auto_exposure_method") is True
            and pp.get_editor_property("auto_exposure_method")
                == unreal.AutoExposureMethod.AEM_BASIC
            and pp.get_editor_property("override_auto_exposure_min_brightness") is True
            and pp.get_editor_property("override_auto_exposure_max_brightness") is True
            and abs(float(pp.get_editor_property("auto_exposure_min_brightness")) - 1.0) <= 0.01
            and abs(float(pp.get_editor_property("auto_exposure_max_brightness")) - 1.0) <= 0.01
            and pp.get_editor_property("override_auto_exposure_bias") is True
            and abs(float(pp.get_editor_property("auto_exposure_bias"))) <= 0.01
        )
        if not exposure_valid:
            failures.append("neutral fixed-exposure contract drift")

    for label, expected_location in (
        ("LB_PaintShop_Prototype_PlayerStart_v001", (0.0, 0.0, 180.0)),
        ("LB_PaintShop_PrototypeBootstrap_v001", (0.0, 0.0, 0.0)),
    ):
        values = by_label.get(label, [])
        if (len(values) == 1
                and not close_vector(vector_tuple(values[0].get_actor_location()),
                                     expected_location)):
            failures.append(f"gameplay shell placement drift: {label}")

    facts = {
        "world": world_path,
        "actor_count": len(map_actors),
        "map_owned_actor_count": len(map_owned),
        "expected_map_owned_actor_count": len(EXPECTED_MAP_ACTOR_CLASSES),
        "bootstrap_count": len(bootstraps),
        "forbidden_actor_count": len(forbidden),
        "game_mode": class_path(game_mode),
        "pawn_class": class_path(default_pawn),
        "hud_class": class_path(default_hud),
        "requested_world_partition": False,
        "inventory": inventory_rows,
        "box_contract": box_rows,
        "review_cameras": camera_rows,
        "rect_lights": rect_light_rows,
        "rect_light_intensity": RECT_LIGHT_INTENSITY,
    }
    return failures, facts


def main() -> None:
    if MAP_FILE.exists() or unreal.EditorAssetLibrary.does_asset_exist(MAP):
        raise RuntimeError(f"Paint prototype map already exists and will not be overwritten: {MAP}")
    if AUDIT.exists():
        raise RuntimeError(f"Paint prototype map receipt already exists: {AUDIT}")

    before = protected_snapshot()
    classes = {
        "game_mode": require_class(GAME_MODE_CLASS_PATH),
        "pawn": require_class(PAWN_CLASS_PATH),
        "hud": require_class(HUD_CLASS_PATH),
        "bootstrap": require_class(BOOTSTRAP_CLASS_PATH),
    }
    cube = require_asset("/Engine/BasicShapes/Cube.Cube", unreal.StaticMesh)
    floor_material = require_asset(
        "/Game/LineBoss/Materials/Environment/MI_LB_SealedFactoryConcrete_Neutral_v001",
        unreal.MaterialInterface)
    wall_material = require_asset(
        "/Game/LineBoss/Materials/M_LB_ShellCharcoal", unreal.MaterialInterface)
    yellow_material = require_asset(
        "/Game/LineBoss/Materials/M_LB_SafetyYellow", unreal.MaterialInterface)
    assets = {
        "cube": cube,
        "floor": floor_material,
        "wall": wall_material,
        "yellow": yellow_material,
    }

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if levels is None or actors is None:
        raise RuntimeError("Required UE 5.8 editor subsystems are unavailable")
    if not levels.new_level(MAP, False):
        raise RuntimeError(f"Could not create isolated Paint Shop level: {MAP}")
    world = get_editor_world()
    if world is None:
        raise RuntimeError("New Paint Shop level did not produce an editor world")
    world.get_world_settings().set_editor_property("default_game_mode", classes["game_mode"])

    box(actors, cube, floor_material, "LB_PS_ENV_Floor_60m_x_40m",
        (0.0, 0.0, -25.0), (WIDTH_CM, DEPTH_CM, 50.0), collision=True,
        tags=("LB.PaintShop.Environment.Shell",), cast_shadow=True)
    walls = (
        ("North", (0.0, DEPTH_CM / 2.0, CLEAR_HEIGHT_CM / 2.0),
         (WIDTH_CM, 40.0, CLEAR_HEIGHT_CM)),
        ("South", (0.0, -DEPTH_CM / 2.0, CLEAR_HEIGHT_CM / 2.0),
         (WIDTH_CM, 40.0, CLEAR_HEIGHT_CM)),
        ("West", (-WIDTH_CM / 2.0, 0.0, CLEAR_HEIGHT_CM / 2.0),
         (40.0, DEPTH_CM, CLEAR_HEIGHT_CM)),
        ("East", (WIDTH_CM / 2.0, 0.0, CLEAR_HEIGHT_CM / 2.0),
         (40.0, DEPTH_CM, CLEAR_HEIGHT_CM)),
    )
    for name, location, dimensions in walls:
        box(actors, cube, wall_material, f"LB_PS_ENV_Wall_{name}", location,
            dimensions, collision=True, tags=("LB.PaintShop.Environment.Shell",),
            cast_shadow=True)

    # Exact 1900 x 1300 cm protected ED-cell envelope. Four corner-free strips
    # keep the carrier openings at X +/-950 cm visually unobstructed.
    for name, location, dimensions in (
        ("North", (0.0, 650.0, 1.0), (1_900.0, 10.0, 1.0)),
        ("South", (0.0, -650.0, 1.0), (1_900.0, 10.0, 1.0)),
        ("WestNorth", (-950.0, 475.0, 1.0), (10.0, 350.0, 1.0)),
        ("WestSouth", (-950.0, -475.0, 1.0), (10.0, 350.0, 1.0)),
        ("EastNorth", (950.0, 475.0, 1.0), (10.0, 350.0, 1.0)),
        ("EastSouth", (950.0, -475.0, 1.0), (10.0, 350.0, 1.0)),
    ):
        box(actors, cube, yellow_material, f"LB_PS_ENV_EDCellBoundary_{name}",
            location, dimensions, collision=False,
            tags=("LB.PaintShop.Environment.EDCellBoundary",))

    box(actors, cube, yellow_material, "LB_PS_INTERFACE_CarrierInput",
        (-1_350.0, 0.0, 1.0), (700.0, 500.0, 1.0), collision=False,
        tags=("LB.PaintShop.Interface.CarrierInput",))
    box(actors, cube, yellow_material, "LB_PS_INTERFACE_CarrierOutput",
        (1_350.0, 0.0, 1.0), (700.0, 500.0, 1.0), collision=False,
        tags=("LB.PaintShop.Interface.CarrierOutput",))
    box(actors, cube, wall_material, "LB_PS_ENV_ServiceWalkway_North",
        (0.0, 1_450.0, 0.8), (5_400.0, 300.0, 0.8), collision=False,
        tags=("LB.PaintShop.Environment.ServiceWalkway",))

    for x in (-1_500.0, 0.0, 1_500.0):
        for y in (-850.0, 850.0):
            rect_light(actors, f"LB_PS_ENV_Light_{int(x):+05d}_{int(y):+04d}",
                       (x, y, 1_300.0))
    sun = actors.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 1_400.0),
        unreal.Rotator(roll=0.0, pitch=-52.0, yaw=-28.0))
    if sun is None:
        raise RuntimeError("Could not create Paint Shop directional light")
    sun.set_actor_label("LB_PS_ENV_DirectionalLight")
    set_tags(sun, MAP_TAG, ENV_TAG, "LB.PaintShop.Environment.Lighting")
    sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
    if sun_component is None:
        raise RuntimeError("Could not resolve Paint Shop DirectionalLightComponent")
    sun_component.set_editor_property("intensity", 0.8)
    sky = actors.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0.0, 0.0, 1_300.0), unreal.Rotator())
    if sky is None:
        raise RuntimeError("Could not create Paint Shop skylight")
    sky.set_actor_label("LB_PS_ENV_SkyLight")
    set_tags(sky, MAP_TAG, ENV_TAG, "LB.PaintShop.Environment.Lighting")
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    if sky_component is None:
        raise RuntimeError("Could not resolve Paint Shop SkyLightComponent")
    sky_component.set_editor_property("intensity", 0.8)

    exposure = actors.spawn_actor_from_class(
        unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
    if exposure is None:
        raise RuntimeError("Could not create Paint Shop exposure volume")
    exposure.set_actor_label("LB_PS_ENV_NeutralExposure")
    set_tags(exposure, MAP_TAG, ENV_TAG, "LB.PaintShop.Environment.Lighting")
    exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0})
    pp = exposure.get_editor_property("settings")
    pp.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": 0.0,
    })
    exposure.set_editor_property("settings", pp)

    player_start = actors.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(0.0, 0.0, 180.0), unreal.Rotator())
    if player_start is None:
        raise RuntimeError("Could not create Paint Shop PlayerStart")
    player_start.set_actor_label("LB_PaintShop_Prototype_PlayerStart_v001")
    set_tags(player_start, MAP_TAG, "LB.PaintShop.Prototype.PlayerStart")
    for label, spec in REVIEW_CAMERA_SPECS.items():
        review_camera(actors, label, spec["location"], spec["target"], spec["fov"])

    bootstrap = actors.spawn_actor_from_class(
        classes["bootstrap"], unreal.Vector(), unreal.Rotator())
    if bootstrap is None:
        raise RuntimeError("Could not place the Paint Shop bootstrap")
    bootstrap.set_actor_label("LB_PaintShop_PrototypeBootstrap_v001")
    set_tags(bootstrap, MAP_TAG, "LB.PaintShop.Prototype.Bootstrap")

    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    failures, facts = validate_current_map(classes, assets, actors)
    if failures:
        raise RuntimeError("Pre-save Paint map contract failed: " + " | ".join(failures))
    if not levels.save_current_level() or not levels.load_level(MAP):
        raise RuntimeError("Could not save and fresh-reload the Paint prototype map")
    failures, facts = validate_current_map(classes, assets, actors)
    if failures:
        raise RuntimeError("Post-save Paint map contract failed: " + " | ".join(failures))

    after = protected_snapshot()
    if before != after:
        raise RuntimeError("Protected Press/BodyShop/config/save/legacy files changed")
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "$schema": "lineboss/audit/paint-shop/prototype-map-create-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__ISOLATED_PAINT_SHOP_ONE_BOOTSTRAP_ZERO_MAP_OWNED_PRODUCTION",
        "builder_script": str(SCRIPT_FILE.relative_to(ROOT)).replace("\\", "/"),
        "builder_script_sha256": sha256(SCRIPT_FILE),
        "map": MAP,
        "map_sha256": sha256(MAP_FILE),
        "facts": facts,
        "protected_hashes": after,
        "failures": [],
    }
    AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log("LINE_BOSS_PAINT_SHOP_PROTOTYPE_MAP_CREATE_V001_PASS")


if __name__ == "__main__":
    main()
