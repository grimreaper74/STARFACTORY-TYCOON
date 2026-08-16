"""One-shot, fail-closed Body Shop environment and LOD release-candidate patch.

This script is intentionally limited to the isolated Body Shop prototype map
and the nine frozen BodyShopUnderbodySlice_v001 final static meshes.  It backs
up every package it can change into Saved before mutation, verifies the exact
known source hashes and actor/package inventories, and protects Press Shop v913.

Run with UnrealEditor-Cmd only after a static review of this script.  It is not
an importer, does not touch gameplay/config/save data, and never removes the
18 retained legacy LOD staging packages.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import traceback

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
EXPECTED_MAP_SHA256 = "7FFE0AE159F3CB89E994DA22ABC6AB393F3032C11CFBB7A9829D433D278D7E53"
PRESS_MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
PRESS_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
EXPECTED_PRESS_SHA256 = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"

NAMESPACE = "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001"
STAGING = NAMESPACE + "/__LegacyLODStaging"
MAP_TAG = "LB.BodyShop.Experimental.v001"
GRID_TAG = "LB.BodyShop.Environment.Grid.100cm"
LIGHTING_TAG = "LB.BodyShop.Environment.Lighting"
TARGET_LOD_SCREENS = [1.0, 0.55, 0.25]
ACTIVE_RECT_INTENSITY = 1050.0
ACTIVE_RECT_COORDS = {(-6000, -1800), (-3000, -1800), (0, -1800)}
EXPECTED_CLASS_COUNTS = {
    "CameraActor": 2,
    "DirectionalLight": 1,
    "LBBodyShopPrototypeWorldBootstrap": 1,
    "PlayerStart": 1,
    "PostProcessVolume": 1,
    "RectLight": 15,
    "SkyLight": 1,
    "StaticMeshActor": 314,
}
CAMERA_SPECS = {
    "LB_BodyShop_Prototype_ReviewCamera_Overview_v001": {
        "location": (-7200.0, -4000.0, 1050.0),
        "target": (-4450.0, -1800.0, 180.0),
        "fov": 50.0,
    },
    "LB_BodyShop_Prototype_ReviewCamera_Flow_v001": {
        "location": (-5250.0, -3300.0, 900.0),
        "target": (-4500.0, -1800.0, 140.0),
        "fov": 46.0,
    },
}

FINAL_SPECS = {
    "SM_LB_BodyShop_UnderbodyFixture_v001": {
        "asset": NAMESPACE + "/Fixture/SM_LB_BodyShop_UnderbodyFixture_v001",
        "sha256": "0E973C5DA249A6D605ED43C29641C0AF9BA9C38D6215F9E17D34DD0E0FA51217",
        "triangles": [6528, 4398, 2570],
    },
    "SM_LB_BodyShop_VisionGate_v001": {
        "asset": NAMESPACE + "/Vision/SM_LB_BodyShop_VisionGate_v001",
        "sha256": "4F32C8598605BC6E0902E0D4B43D3F8EE39C021AC40DE81830D63A7CF8FAAA17",
        "triangles": [1728, 1584, 1440],
    },
    "SM_LB_BodyShopRobot_Base_v001": {
        "asset": NAMESPACE + "/Robot/SM_LB_BodyShopRobot_Base_v001",
        "sha256": "8DA21C4895F94517D24EC62088E5D6891AD94550DBAD8EF8DBF9862983FC7738",
        "triangles": [20558, 9544, 3670],
    },
    "SM_LB_BodyShopRobot_J1_v001": {
        "asset": NAMESPACE + "/Robot/SM_LB_BodyShopRobot_J1_v001",
        "sha256": "EE1C950F05D57D654AC1F6796BF9D9E3E6B6548CB4CCA8FEC7333A0A8CC6EFE1",
        "triangles": [21818, 10130, 3894],
    },
    "SM_LB_BodyShopRobot_J2_v001": {
        "asset": NAMESPACE + "/Robot/SM_LB_BodyShopRobot_J2_v001",
        "sha256": "89AB87EB3395C41221A7F5AAC819429C41DBC82DCD2EA8D366F503F6C09A60B5",
        "triangles": [16337, 7597, 2923],
    },
    "SM_LB_BodyShopRobot_J3_v001": {
        "asset": NAMESPACE + "/Robot/SM_LB_BodyShopRobot_J3_v001",
        "sha256": "F416288DB704F63C7B3A36F4E11AB07C84852A2441C8DCE7E9BF1E53585EA64B",
        "triangles": [17138, 7968, 3068],
    },
    "SM_LB_BodyShopRobot_J4_v001": {
        "asset": NAMESPACE + "/Robot/SM_LB_BodyShopRobot_J4_v001",
        "sha256": "CC6EFAC3E266AD92ECAE8A9C13B0FD7CA7DB0E56466025B42099B7222E62C74B",
        "triangles": [9758, 4530, 1742],
    },
    "SM_LB_BodyShopRobot_J5_v001": {
        "asset": NAMESPACE + "/Robot/SM_LB_BodyShopRobot_J5_v001",
        "sha256": "587FB612F1E1BE63C2A0E8D7A2A26B8A8020214772EC0DD9BEE7425088817E67",
        "triangles": [76, 52, 28],
    },
    "SM_LB_BodyShopTool_PanelPick8Cup_v001": {
        "asset": NAMESPACE + "/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001",
        "sha256": "2B1559A2C4DF16DD535A18FA56B2BCF37633DD3B01EE152C09700C77A42DAB47",
        "triangles": [2696, 2152, 1880],
    },
}

STAGING_HASHES = {
    "SM_LB_BodyShopRobot_Base_v001__LegacySourceLOD1": "294147C17F0ED3AFE2C362E75012720C9A6314496CFE397FCE8C8CC324916668",
    "SM_LB_BodyShopRobot_Base_v001__LegacySourceLOD2": "7C8631E405D6F4DCDE8A40D2B46515C4981401F25CC09FD5F4FB74FB90FFAAFB",
    "SM_LB_BodyShopRobot_J1_v001__LegacySourceLOD1": "C0C5B3BCA45859C1FFE52BF05047159F8CB7D9058EE51B3A13C5B34252E79DC6",
    "SM_LB_BodyShopRobot_J1_v001__LegacySourceLOD2": "12D0C80DB76AE202C212283ADA9583CFD9DB84D0AA11213422AAC124B799A0A5",
    "SM_LB_BodyShopRobot_J2_v001__LegacySourceLOD1": "C88C045961BD8C3A5FCA35885F200102696FA7F1835083E08C046755E212E824",
    "SM_LB_BodyShopRobot_J2_v001__LegacySourceLOD2": "0498416F2F5F0194C575CCE61300D8BBBAB4FC4CC6CBD94D397FF0C4A9E40FF7",
    "SM_LB_BodyShopRobot_J3_v001__LegacySourceLOD1": "A4915D839FC6BF1A1B93C8E886A80392BE80BC399E023E75D938BFA57742C492",
    "SM_LB_BodyShopRobot_J3_v001__LegacySourceLOD2": "A761DC0E2EFB497FE1DA9BF0EDD07103C9A647C4F01DBDFD281BAB651FFD7857",
    "SM_LB_BodyShopRobot_J4_v001__LegacySourceLOD1": "C208A052DF850E698DE6493A31AD0C2E3481F34B2A6A619C7B40F23AD63E8D02",
    "SM_LB_BodyShopRobot_J4_v001__LegacySourceLOD2": "2DE7E40B47636C1748FA2269B6EE9F07A2A7F5B3D66FE55E427847740F27E26C",
    "SM_LB_BodyShopRobot_J5_v001__LegacySourceLOD1": "455FD3027F27E898D784F3FCBA8EE210ED3D2F77112139E7E294CEF3EF0F3C67",
    "SM_LB_BodyShopRobot_J5_v001__LegacySourceLOD2": "4F3132CCAEFE679B69FD3F8882737F70DD4A4AC7246B16339FDBA8A2D4643B74",
    "SM_LB_BodyShopTool_PanelPick8Cup_v001__LegacySourceLOD1": "7E77CC2158B647454B739741F4204DA84DC4305C09AB23F9D037157D51C59020",
    "SM_LB_BodyShopTool_PanelPick8Cup_v001__LegacySourceLOD2": "365D92F50230438A8009E55DDED7E41E16141FF11EAE3CC528FDECF2A9BD5250",
    "SM_LB_BodyShop_UnderbodyFixture_v001__LegacySourceLOD1": "5DDCDB1F7E130E9A6A8651F41C5AAD4AC19E39FC124FCBEA7105065612211DFC",
    "SM_LB_BodyShop_UnderbodyFixture_v001__LegacySourceLOD2": "620D4D69F2A8E72ADE97729B1EC3168A2DEC906E091A778102547A252D41B6D2",
    "SM_LB_BodyShop_VisionGate_v001__LegacySourceLOD1": "9236BDDB35DEA603BA044BD95216E51E2B51C81F9EADC9B028241F2EB878238E",
    "SM_LB_BodyShop_VisionGate_v001__LegacySourceLOD2": "4EED6BECC117ECBA14E13A401CA8C0CB553B64F812092A5679D93C83CC8C7FAF",
}

AUDIT_DIR = PROJECT / "Saved/Audits/BodyShop/Experimental_v001"
RECEIPT = AUDIT_DIR / "environment_lod_release_candidate_patch_v001.json"
FAILURE = AUDIT_DIR / "environment_lod_release_candidate_patch_failure_v001.json"
BACKUP_ROOT = PROJECT / "Saved/Quarantine/BodyShop/EnvironmentLODReleaseCandidate_v001/prepatch_exact"
lib = unreal.EditorAssetLibrary


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_ENVIRONMENT_LOD_RELEASE_CANDIDATE_V001_FAIL: " + message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def package_disk(asset_path: str) -> Path:
    return PROJECT / "Content" / Path(asset_path.removeprefix("/Game/")).with_suffix(".uasset")


def normalize_registry_path(value) -> str:
    return str(value).rsplit(".", 1)[0]


def vec3(value) -> list[float]:
    return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]


def close(a: float, b: float, tolerance: float = 0.01) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def tags_of(actor) -> set[str]:
    return {str(tag) for tag in actor.get_editor_property("tags")}


def all_expected_packages() -> dict[str, str]:
    output = {spec["asset"]: spec["sha256"] for spec in FINAL_SPECS.values()}
    output.update({STAGING + "/" + name: value for name, value in STAGING_HASHES.items()})
    return output


def expected_actor_labels() -> set[str]:
    labels = {
        "LB_BS_ENV_Floor_180m_x_90m",
        "LB_BS_ENV_Wall_North", "LB_BS_ENV_Wall_South",
        "LB_BS_ENV_Wall_West", "LB_BS_ENV_Wall_East",
        "LB_BS_ENV_BuildArea_North", "LB_BS_ENV_BuildArea_South",
        "LB_BS_ENV_BuildArea_West", "LB_BS_ENV_BuildArea_East",
        "LB_BS_ENV_PedestrianProtectedLane", "LB_BS_ENV_FLTProtectedRoute",
        "LB_BS_ENV_NorthServiceBoundary", "LB_BS_ENV_SouthServiceBoundary",
        "LB_BS_INTERFACE_InputDockDatum", "LB_BS_INTERFACE_EDOutputDatum",
        "LB_BS_ENV_DirectionalLight", "LB_BS_ENV_SkyLight",
        "LB_BS_ENV_NeutralExposure",
        "LB_BodyShop_Prototype_PlayerStart_v001",
        "LB_BodyShop_Prototype_ReviewCamera_Overview_v001",
        "LB_BodyShop_Prototype_ReviewCamera_Flow_v001",
        "LB_BodyShop_PrototypeBootstrap_v001",
    }
    labels.update(f"LB_BS_ENV_GridX_{x:+05d}" for x in range(-9000, 9001, 100))
    labels.update(f"LB_BS_ENV_GridY_{y:+05d}" for y in range(-4500, 4501, 100))
    for x in range(-8000, 8001, 2000):
        labels.add(f"LB_BS_ENV_Column_North_{x:+05d}")
        labels.add(f"LB_BS_ENV_Column_South_{x:+05d}")
        labels.add(f"LB_BS_ENV_Truss_{x:+05d}")
    for x in (-6000, -3000, 0, 3000, 6000):
        for y in (-1800, 0, 1800):
            labels.add(f"LB_BS_ENV_Light_{x:+05d}_{y:+05d}")
    return labels


def assert_project_and_disk_preflight() -> dict:
    if PROJECT != EXPECTED_PROJECT:
        fail("wrong project path: " + str(PROJECT))
    if str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("wrong game identity")
    if RECEIPT.exists():
        fail("success receipt already exists; this tool is one-shot")
    if BACKUP_ROOT.exists():
        fail("pre-patch backup already exists; inspect it before any retry")
    if not MAP_FILE.is_file() or digest(MAP_FILE) != EXPECTED_MAP_SHA256:
        fail("isolated Body Shop map hash drift")
    if not PRESS_FILE.is_file() or digest(PRESS_FILE) != EXPECTED_PRESS_SHA256:
        fail("protected Press Shop v913 hash drift")

    expected = all_expected_packages()
    registry = {
        normalize_registry_path(value)
        for value in lib.list_assets(NAMESPACE, recursive=True, include_folder=False)
    }
    if registry != set(expected):
        fail("Body Shop art registry inventory drift: " + json.dumps(sorted(registry)))
    disk_root = PROJECT / "Content/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001"
    disk_inventory = {
        path for path in disk_root.rglob("*") if path.is_file()
    }
    expected_disk = {package_disk(path) for path in expected}
    if disk_inventory != expected_disk:
        fail("Body Shop art disk inventory drift")
    hashes = {}
    for asset_path, expected_hash in sorted(expected.items()):
        path = package_disk(asset_path)
        actual = digest(path) if path.is_file() else None
        if actual != expected_hash:
            fail("package hash drift: " + asset_path + ":" + str(actual))
        hashes[asset_path] = actual
    return {
        "map": digest(MAP_FILE),
        "press_v913": digest(PRESS_FILE),
        "packages": hashes,
    }


def assert_map_inventory(actors_api) -> tuple[list, dict[str, object]]:
    actors = list(actors_api.get_all_level_actors())
    labels = [actor.get_actor_label() for actor in actors]
    duplicates = sorted(label for label, count in Counter(labels).items() if count != 1)
    expected_labels = expected_actor_labels()
    if duplicates or set(labels) != expected_labels:
        fail("map actor-label inventory drift: duplicates=" + str(duplicates)
             + " missing=" + str(sorted(expected_labels - set(labels)))
             + " unexpected=" + str(sorted(set(labels) - expected_labels)))
    class_counts = dict(sorted(Counter(actor.get_class().get_name() for actor in actors).items()))
    if class_counts != EXPECTED_CLASS_COUNTS:
        fail("map class inventory drift: " + json.dumps(class_counts, sort_keys=True))
    untagged = sorted(actor.get_actor_label() for actor in actors if MAP_TAG not in tags_of(actor))
    if untagged:
        fail("map-owned actor tag drift: " + str(untagged))
    grid = [actor for actor in actors if GRID_TAG in tags_of(actor)]
    expected_grid_labels = {
        f"LB_BS_ENV_GridX_{x:+05d}" for x in range(-9000, 9001, 100)
    } | {
        f"LB_BS_ENV_GridY_{y:+05d}" for y in range(-4500, 4501, 100)
    }
    if len(grid) != 272 or {actor.get_actor_label() for actor in grid} != expected_grid_labels:
        fail("100 cm grid inventory/tag drift")
    lighting = [actor for actor in actors if LIGHTING_TAG in tags_of(actor)]
    if len(lighting) != 18:
        fail("lighting tag inventory drift: " + str(len(lighting)))
    forbidden = (
        "LBBodyShopCellActor", "LBBodyShopBuildAuthority", "LBBodyShopPrototypeRuntime",
        "LBBodyWeldLineActor", "LBPressShop", "LBGameMode", "LBECoatLineActor",
        "LBFactoryMachineBuilderSubsystem",
    )
    found_forbidden = [
        actor.get_actor_label() for actor in actors
        if any(fragment in actor.get_class().get_name() for fragment in forbidden)
    ]
    if found_forbidden:
        fail("production/legacy actor baked into isolated map: " + str(found_forbidden))
    return actors, {
        "actor_count": len(actors),
        "class_counts": class_counts,
        "map_tagged_actor_count": len(actors) - len(untagged),
        "grid_actor_count": len(grid),
        "lighting_tagged_actor_count": len(lighting),
    }


def lod_bounds(mesh, lod_index: int) -> list[float]:
    dynamic_mesh = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    requested_lod = unreal.GeometryScriptMeshReadLOD()
    requested_lod.set_editor_properties({
        "lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL,
        "lod_index": lod_index,
    })
    dynamic_mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic_mesh, options, requested_lod, False)
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail("LOD bounds extraction failed: " + mesh.get_name() + ":" + str(lod_index))
    box = dynamic_mesh.get_mesh_bounding_box()
    return [round(float(box.max.x - box.min.x), 5),
            round(float(box.max.y - box.min.y), 5),
            round(float(box.max.z - box.min.z), 5)]


def mesh_fingerprint(mesh, subsystem) -> dict:
    lod_count = int(mesh.get_num_lods())
    body = mesh.get_editor_property("body_setup")
    if lod_count != 3 or body is None:
        fail("mesh LOD/body setup drift: " + mesh.get_name())
    materials = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        material = mesh.get_material(index)
        materials.append({
            "index": index,
            "slot": str(slot.get_editor_property("material_slot_name")),
            "material": material.get_path_name() if material else None,
        })
    return {
        "lod_count": lod_count,
        "triangles": [int(mesh.get_num_triangles(index)) for index in range(lod_count)],
        "vertices": [int(mesh.get_num_vertices(index)) for index in range(lod_count)],
        "lod_bounds_cm": [lod_bounds(mesh, index) for index in range(lod_count)],
        "lod_screen_sizes": [round(float(value), 4)
                             for value in subsystem.get_lod_screen_sizes(mesh)],
        "materials": materials,
        "simple_collision_count": int(subsystem.get_simple_collision_count(mesh)),
        "convex_collision_count": int(subsystem.get_convex_collision_count(mesh)),
        "collision_trace_flag": str(body.get_editor_property("collision_trace_flag")),
        "nanite_enabled": bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled")),
    }


def immutable_mesh_fingerprint(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "lod_screen_sizes"}


def load_and_preflight_meshes(subsystem) -> tuple[dict[str, object], dict[str, dict]]:
    meshes = {}
    facts = {}
    for name, spec in sorted(FINAL_SPECS.items()):
        mesh = lib.load_asset(spec["asset"])
        if not isinstance(mesh, unreal.StaticMesh):
            fail("missing final static mesh: " + spec["asset"])
        if mesh.get_path_name() != spec["asset"] + "." + name:
            fail("final object-path drift: " + name)
        row = mesh_fingerprint(mesh, subsystem)
        if row["triangles"] != spec["triangles"]:
            fail("triangle contract drift: " + name + ":" + str(row["triangles"]))
        if row["lod_screen_sizes"] != [1.0, 0.45, 0.18]:
            fail("pre-patch LOD screen contract drift: " + name + ":" + str(row["lod_screen_sizes"]))
        meshes[name] = mesh
        facts[name] = row
    return meshes, facts


def backup_changed_packages() -> dict[str, dict]:
    changed_files = [MAP_FILE] + [package_disk(spec["asset"]) for spec in FINAL_SPECS.values()]
    records = {}
    for source in sorted(changed_files):
        relative = source.relative_to(PROJECT)
        destination = BACKUP_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if digest(destination) != digest(source):
            fail("backup hash mismatch: " + str(relative))
        records[str(relative).replace("\\", "/")] = {
            "source_sha256": digest(source),
            "backup": str(destination),
            "backup_sha256": digest(destination),
        }
    manifest = {
        "$schema": "lineboss/quarantine/bodyshop-environment-lod-prepatch/v1",
        "generated_utc": now(),
        "status": "RECOVERABLE_EXACT_PREPATCH_BACKUP",
        "files": records,
        "restore_policy": "Restore only with Unreal closed and after explicit review.",
    }
    (BACKUP_ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return records


def rect_coords(actor) -> tuple[int, int]:
    location = actor.get_actor_location()
    return int(round(float(location.x))), int(round(float(location.y)))


def patch_map(actors: list) -> None:
    by_label = {actor.get_actor_label(): actor for actor in actors}
    grid = [actor for actor in actors if GRID_TAG in tags_of(actor)]
    for actor in grid:
        actor.set_actor_hidden_in_game(True)

    rect_lights = [actor for actor in actors if isinstance(actor, unreal.RectLight)]
    if len(rect_lights) != 15:
        fail("RectLight count drift immediately before patch")
    for actor in rect_lights:
        component = actor.get_component_by_class(unreal.RectLightComponent)
        if component is None:
            fail("RectLight component missing: " + actor.get_actor_label())
        active = rect_coords(actor) in ACTIVE_RECT_COORDS
        component.set_intensity(ACTIVE_RECT_INTENSITY if active else 0.0)
        component.set_visibility(active, True)
        component.set_hidden_in_game(not active, True)
        component.set_cast_shadows(False)
        actor.set_actor_hidden_in_game(not active)

    sun = by_label["LB_BS_ENV_DirectionalLight"]
    sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sun_component.set_editor_properties({
        "intensity": 1.2,
        "cast_shadows": True,
        "light_source_angle": 4.0,
        "visible": True,
        "hidden_in_game": False,
    })
    sun.set_actor_hidden_in_game(False)

    sky = by_label["LB_BS_ENV_SkyLight"]
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    sky_component.set_editor_properties({"intensity": 1.1, "visible": True, "hidden_in_game": False})
    sky.set_actor_hidden_in_game(False)

    exposure = by_label["LB_BS_ENV_NeutralExposure"]
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
        "auto_exposure_bias": 0.25,
    })
    exposure.set_editor_property("settings", settings)

    for label, spec in CAMERA_SPECS.items():
        camera = by_label[label]
        location = unreal.Vector(*spec["location"])
        target = unreal.Vector(*spec["target"])
        camera.set_actor_location(location, False, False)
        camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
        component = camera.get_component_by_class(unreal.CameraComponent)
        component.set_editor_properties({
            "field_of_view": float(spec["fov"]),
            "aspect_ratio": 16.0 / 9.0,
            "constrain_aspect_ratio": True,
        })


def assert_post_map_state(actors_api) -> dict:
    actors, inventory = assert_map_inventory(actors_api)
    by_label = {actor.get_actor_label(): actor for actor in actors}
    grid = [actor for actor in actors if GRID_TAG in tags_of(actor)]
    not_hidden = [actor.get_actor_label() for actor in grid
                  if not bool(actor.get_editor_property("hidden"))]
    if not_hidden:
        fail("grid actors not hidden in game: " + str(not_hidden[:10]))

    rect_rows = {}
    active_count = 0
    for actor in [item for item in actors if isinstance(item, unreal.RectLight)]:
        component = actor.get_component_by_class(unreal.RectLightComponent)
        coords = rect_coords(actor)
        active = coords in ACTIVE_RECT_COORDS
        row = {
            "coords_cm": list(coords),
            "intensity": round(float(component.get_editor_property("intensity")), 4),
            "visible": bool(component.get_editor_property("visible")),
            "component_hidden_in_game": bool(component.get_editor_property("hidden_in_game")),
            "actor_hidden_in_game": bool(actor.get_editor_property("hidden")),
            "cast_shadows": bool(component.get_editor_property("cast_shadows")),
        }
        expected_intensity = ACTIVE_RECT_INTENSITY if active else 0.0
        if (not close(row["intensity"], expected_intensity)
                or row["visible"] is not active
                or row["component_hidden_in_game"] is active
                or row["actor_hidden_in_game"] is active
                or row["cast_shadows"]):
            fail("RectLight release state drift: " + actor.get_actor_label() + ":" + str(row))
        if active:
            active_count += 1
        rect_rows[actor.get_actor_label()] = row
    if active_count != 3:
        fail("active broad-fill count drift: " + str(active_count))

    sun_component = by_label["LB_BS_ENV_DirectionalLight"].get_component_by_class(
        unreal.DirectionalLightComponent)
    sun = {
        "intensity": round(float(sun_component.get_editor_property("intensity")), 4),
        "cast_shadows": bool(sun_component.get_editor_property("cast_shadows")),
        "light_source_angle": round(float(sun_component.get_editor_property("light_source_angle")), 4),
    }
    if not close(sun["intensity"], 1.2) or not sun["cast_shadows"] or not close(sun["light_source_angle"], 4.0):
        fail("directional soft-shadow state drift: " + str(sun))

    sky_component = by_label["LB_BS_ENV_SkyLight"].get_component_by_class(unreal.SkyLightComponent)
    sky_intensity = round(float(sky_component.get_editor_property("intensity")), 4)
    if not close(sky_intensity, 1.1):
        fail("SkyLight intensity drift: " + str(sky_intensity))

    exposure = by_label["LB_BS_ENV_NeutralExposure"]
    settings = exposure.get_editor_property("settings")
    exposure_row = {
        "unbound": bool(exposure.get_editor_property("unbound")),
        "blend_weight": round(float(exposure.get_editor_property("blend_weight")), 4),
        "bias": round(float(settings.get_editor_property("auto_exposure_bias")), 4),
        "min_brightness": round(float(settings.get_editor_property("auto_exposure_min_brightness")), 4),
        "max_brightness": round(float(settings.get_editor_property("auto_exposure_max_brightness")), 4),
    }
    if (not exposure_row["unbound"] or not close(exposure_row["blend_weight"], 1.0)
            or not close(exposure_row["bias"], 0.25)
            or not close(exposure_row["min_brightness"], 1.0)
            or not close(exposure_row["max_brightness"], 1.0)):
        fail("fixed exposure state drift: " + str(exposure_row))

    camera_rows = {}
    for label, spec in CAMERA_SPECS.items():
        actor = by_label[label]
        component = actor.get_component_by_class(unreal.CameraComponent)
        expected_rotation = unreal.MathLibrary.find_look_at_rotation(
            unreal.Vector(*spec["location"]), unreal.Vector(*spec["target"]))
        actual_rotation = actor.get_actor_rotation()
        row = {
            "location_cm": vec3(actor.get_actor_location()),
            "rotation": [round(float(actual_rotation.pitch), 4),
                         round(float(actual_rotation.yaw), 4),
                         round(float(actual_rotation.roll), 4)],
            "fov": round(float(component.get_editor_property("field_of_view")), 4),
        }
        expected_location = [round(value, 4) for value in spec["location"]]
        expected_angles = [float(expected_rotation.pitch), float(expected_rotation.yaw), float(expected_rotation.roll)]
        if (row["location_cm"] != expected_location
                or not close(row["fov"], spec["fov"])
                or any(not close(actual, expected, 0.02)
                       for actual, expected in zip(row["rotation"], expected_angles))):
            fail("review camera state drift: " + label + ":" + str(row))
        camera_rows[label] = row

    inventory.update({
        "grid_hidden_in_game_count": len(grid) - len(not_hidden),
        "active_rect_lights": active_count,
        "rect_lights": rect_rows,
        "directional": sun,
        "sky_intensity": sky_intensity,
        "exposure": exposure_row,
        "cameras": camera_rows,
    })
    return inventory


def current_package_hashes(asset_paths) -> dict[str, str | None]:
    return {
        path: digest(package_disk(path)) if package_disk(path).is_file() else None
        for path in sorted(asset_paths)
    }


def main() -> None:
    evidence = {
        "$schema": "lineboss/audit/bodyshop/environment-lod-release-candidate-patch-v001/v1",
        "generated_utc": now(),
        "map": MAP,
        "press_map_protected": PRESS_MAP,
        "target_lod_screen_sizes": TARGET_LOD_SCREENS,
        "content_scope": [MAP] + sorted(spec["asset"] for spec in FINAL_SPECS.values()),
        "staging_cleanup": "NOT_PERFORMED__18_PACKAGES_RETAINED",
        "source_assets_mutated": False,
        "config_or_save_changes": [],
        "meshy_credits_used_by_codex": 0,
    }
    before = None
    try:
        before = assert_project_and_disk_preflight()
        evidence["preflight_hashes"] = before
        levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if not levels or not actors_api or not subsystem:
            fail("required editor subsystem unavailable")
        if not lib.does_asset_exist(MAP) or not levels.load_level(MAP):
            fail("isolated map could not be loaded")
        actors, map_inventory_before = assert_map_inventory(actors_api)
        meshes, mesh_fingerprints_before = load_and_preflight_meshes(subsystem)
        evidence["map_inventory_before"] = map_inventory_before
        evidence["mesh_fingerprints_before"] = mesh_fingerprints_before

        backup = backup_changed_packages()
        evidence["recoverable_prepatch_backup"] = backup

        patch_map(actors)
        for name, mesh in sorted(meshes.items()):
            if not subsystem.set_lod_screen_sizes(mesh, TARGET_LOD_SCREENS):
                fail("LOD screen patch failed: " + name)
            if not lib.save_loaded_asset(mesh, only_if_is_dirty=False):
                fail("mesh save failed: " + name)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        if not levels.save_current_level():
            fail("isolated map save failed")
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

        map_inventory_after = assert_post_map_state(actors_api)
        mesh_fingerprints_after = {}
        for name, mesh in sorted(meshes.items()):
            row = mesh_fingerprint(mesh, subsystem)
            if row["lod_screen_sizes"] != TARGET_LOD_SCREENS:
                fail("post-save LOD screen drift: " + name + ":" + str(row["lod_screen_sizes"]))
            if immutable_mesh_fingerprint(row) != immutable_mesh_fingerprint(mesh_fingerprints_before[name]):
                fail("geometry/material/collision/Nanite drift: " + name)
            mesh_fingerprints_after[name] = row

        press_after = digest(PRESS_FILE)
        if press_after != EXPECTED_PRESS_SHA256:
            fail("protected Press Shop v913 changed")
        map_after = digest(MAP_FILE)
        if map_after == EXPECTED_MAP_SHA256:
            fail("isolated map package hash did not change")
        staging_paths = [STAGING + "/" + name for name in STAGING_HASHES]
        staging_after = current_package_hashes(staging_paths)
        expected_staging = {STAGING + "/" + name: value for name, value in STAGING_HASHES.items()}
        if staging_after != dict(sorted(expected_staging.items())):
            fail("legacy staging packages changed")
        final_after = current_package_hashes(spec["asset"] for spec in FINAL_SPECS.values())
        if any(value is None for value in final_after.values()):
            fail("final package missing after save")
        if any(final_after[path] == before["packages"][path] for path in final_after):
            fail("one or more final packages did not record the LOD screen update")

        evidence.update({
            "status": "PASS__ISOLATED_BODYSHOP_ENVIRONMENT_AND_LOD_RELEASE_CANDIDATE_V001",
            "map_sha256_before": EXPECTED_MAP_SHA256,
            "map_sha256_after": map_after,
            "press_v913_sha256_before": before["press_v913"],
            "press_v913_sha256_after": press_after,
            "map_inventory_after": map_inventory_after,
            "mesh_fingerprints_after": mesh_fingerprints_after,
            "final_package_hashes_before": {
                spec["asset"]: spec["sha256"] for spec in FINAL_SPECS.values()},
            "final_package_hashes_after": final_after,
            "staging_package_hashes_before_and_after": staging_after,
            "changed_package_count": 10,
            "unchanged_geometry_material_collision_nanite_count": 9,
            "failures": [],
        })
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        unreal.log("LINE_BOSS_BODYSHOP_ENVIRONMENT_LOD_RELEASE_CANDIDATE_V001_PASS")
        print(json.dumps(evidence, indent=2))
    except Exception as error:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        failure = {
            **evidence,
            "status": "FAIL_CLOSED__BODYSHOP_ENVIRONMENT_LOD_RELEASE_CANDIDATE_V001",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "map_sha256_current": digest(MAP_FILE) if MAP_FILE.is_file() else None,
            "press_v913_sha256_current": digest(PRESS_FILE) if PRESS_FILE.is_file() else None,
            "final_package_hashes_current": current_package_hashes(
                spec["asset"] for spec in FINAL_SPECS.values()),
            "staging_package_hashes_current": current_package_hashes(
                STAGING + "/" + name for name in STAGING_HASHES),
            "automatic_restore": "NOT_PERFORMED__exact backups retained for explicit offline recovery",
            "recoverable_backup_root": str(BACKUP_ROOT) if BACKUP_ROOT.exists() else None,
        }
        FAILURE.write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(failure, indent=2))
        raise


if __name__ == "__main__":
    main()
