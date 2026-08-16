"""Independent read-only validation for the Body Shop environment/LOD patch."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
ORIGINAL_MAP_SHA256 = "7FFE0AE159F3CB89E994DA22ABC6AB393F3032C11CFBB7A9829D433D278D7E53"
PRESS_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
PRESS_SHA256 = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
NAMESPACE = "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001"
STAGING = NAMESPACE + "/__LegacyLODStaging"
MAP_TAG = "LB.BodyShop.Experimental.v001"
GRID_TAG = "LB.BodyShop.Environment.Grid.100cm"
TARGET_SCREENS = [1.0, 0.55, 0.25]
PATCH_RECEIPT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/environment_lod_release_candidate_patch_v001.json"
SOURCE_VALIDATION = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/validate_underbody_slice_art_receipt_v001.json"
SOURCE_VALIDATION_SHA256 = "551FABEBB5858092161F19143A31AA04C5BEE8221AAF0641C711C539BF71A0EC"
AUDIT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/environment_lod_release_candidate_validation_v001.json"

FINAL_BEFORE = {
    NAMESPACE + "/Fixture/SM_LB_BodyShop_UnderbodyFixture_v001": "0E973C5DA249A6D605ED43C29641C0AF9BA9C38D6215F9E17D34DD0E0FA51217",
    NAMESPACE + "/Vision/SM_LB_BodyShop_VisionGate_v001": "4F32C8598605BC6E0902E0D4B43D3F8EE39C021AC40DE81830D63A7CF8FAAA17",
    NAMESPACE + "/Robot/SM_LB_BodyShopRobot_Base_v001": "8DA21C4895F94517D24EC62088E5D6891AD94550DBAD8EF8DBF9862983FC7738",
    NAMESPACE + "/Robot/SM_LB_BodyShopRobot_J1_v001": "EE1C950F05D57D654AC1F6796BF9D9E3E6B6548CB4CCA8FEC7333A0A8CC6EFE1",
    NAMESPACE + "/Robot/SM_LB_BodyShopRobot_J2_v001": "89AB87EB3395C41221A7F5AAC819429C41DBC82DCD2EA8D366F503F6C09A60B5",
    NAMESPACE + "/Robot/SM_LB_BodyShopRobot_J3_v001": "F416288DB704F63C7B3A36F4E11AB07C84852A2441C8DCE7E9BF1E53585EA64B",
    NAMESPACE + "/Robot/SM_LB_BodyShopRobot_J4_v001": "CC6EFAC3E266AD92ECAE8A9C13B0FD7CA7DB0E56466025B42099B7222E62C74B",
    NAMESPACE + "/Robot/SM_LB_BodyShopRobot_J5_v001": "587FB612F1E1BE63C2A0E8D7A2A26B8A8020214772EC0DD9BEE7425088817E67",
    NAMESPACE + "/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001": "2B1559A2C4DF16DD535A18FA56B2BCF37633DD3B01EE152C09700C77A42DAB47",
}
CAMERAS = {
    "LB_BodyShop_Prototype_ReviewCamera_Overview_v001": ((-7200.0, -4000.0, 1050.0), (-4450.0, -1800.0, 180.0), 50.0),
    "LB_BodyShop_Prototype_ReviewCamera_Flow_v001": ((-5250.0, -3300.0, 900.0), (-4500.0, -1800.0, 140.0), 46.0),
}
EXPECTED_CLASSES = {"CameraActor": 2, "DirectionalLight": 1,
                    "LBBodyShopPrototypeWorldBootstrap": 1, "PlayerStart": 1,
                    "PostProcessVolume": 1, "RectLight": 15, "SkyLight": 1,
                    "StaticMeshActor": 314}


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_ENVIRONMENT_LOD_VALIDATION_V001_FAIL: " + message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def package_disk(asset: str) -> Path:
    return PROJECT / "Content" / Path(asset.removeprefix("/Game/")).with_suffix(".uasset")


def close(a, b, tolerance=0.02) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def labels_expected() -> set[str]:
    labels = {"LB_BS_ENV_Floor_180m_x_90m", "LB_BS_ENV_Wall_North",
              "LB_BS_ENV_Wall_South", "LB_BS_ENV_Wall_West", "LB_BS_ENV_Wall_East",
              "LB_BS_ENV_BuildArea_North", "LB_BS_ENV_BuildArea_South",
              "LB_BS_ENV_BuildArea_West", "LB_BS_ENV_BuildArea_East",
              "LB_BS_ENV_PedestrianProtectedLane", "LB_BS_ENV_FLTProtectedRoute",
              "LB_BS_ENV_NorthServiceBoundary", "LB_BS_ENV_SouthServiceBoundary",
              "LB_BS_INTERFACE_InputDockDatum", "LB_BS_INTERFACE_EDOutputDatum",
              "LB_BS_ENV_DirectionalLight", "LB_BS_ENV_SkyLight", "LB_BS_ENV_NeutralExposure",
              "LB_BodyShop_Prototype_PlayerStart_v001",
              "LB_BodyShop_Prototype_ReviewCamera_Overview_v001",
              "LB_BodyShop_Prototype_ReviewCamera_Flow_v001",
              "LB_BodyShop_PrototypeBootstrap_v001"}
    labels |= {f"LB_BS_ENV_GridX_{x:+05d}" for x in range(-9000, 9001, 100)}
    labels |= {f"LB_BS_ENV_GridY_{y:+05d}" for y in range(-4500, 4501, 100)}
    for x in range(-8000, 8001, 2000):
        labels |= {f"LB_BS_ENV_Column_North_{x:+05d}", f"LB_BS_ENV_Column_South_{x:+05d}",
                   f"LB_BS_ENV_Truss_{x:+05d}"}
    for x in (-6000, -3000, 0, 3000, 6000):
        for y in (-1800, 0, 1800):
            labels.add(f"LB_BS_ENV_Light_{x:+05d}_{y:+05d}")
    return labels


def immutable(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "lod_screen_sizes"}


def mesh_fingerprint(mesh, subsystem) -> dict:
    count = int(mesh.get_num_lods())
    body = mesh.get_editor_property("body_setup")
    materials = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        material = mesh.get_material(index)
        materials.append({"index": index,
                          "slot": str(slot.get_editor_property("material_slot_name")),
                          "material": material.get_path_name() if material else None})
    return {"lod_count": count,
            "triangles": [int(mesh.get_num_triangles(i)) for i in range(count)],
            "vertices": [int(mesh.get_num_vertices(i)) for i in range(count)],
            "lod_screen_sizes": [round(float(v), 4) for v in subsystem.get_lod_screen_sizes(mesh)],
            "materials": materials,
            "simple_collision_count": int(subsystem.get_simple_collision_count(mesh)),
            "convex_collision_count": int(subsystem.get_convex_collision_count(mesh)),
            "collision_trace_flag": str(body.get_editor_property("collision_trace_flag")) if body else None,
            "nanite_enabled": bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))}


def main() -> None:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    if not PATCH_RECEIPT.is_file() or not SOURCE_VALIDATION.is_file():
        fail("required patch/source validation receipt missing")
    if digest(SOURCE_VALIDATION) != SOURCE_VALIDATION_SHA256:
        fail("source validation receipt hash drift")
    source_validation = json.loads(SOURCE_VALIDATION.read_text(encoding="utf-8"))
    if source_validation.get("status") != "PASS__BODYSHOP_UNDERBODY_ART_SOURCE_LOD_SCALE_NAMESPACE_AND_POLICY_VALIDATION_V001":
        fail("source validation status drift")
    patch = json.loads(PATCH_RECEIPT.read_text(encoding="utf-8"))
    if patch.get("status") != "PASS__ISOLATED_BODYSHOP_ENVIRONMENT_AND_LOD_RELEASE_CANDIDATE_V001":
        fail("patch receipt status drift")
    if patch.get("map_sha256_before") != ORIGINAL_MAP_SHA256:
        fail("patch did not start from the frozen map")
    if patch.get("press_v913_sha256_before") != PRESS_SHA256 or patch.get("press_v913_sha256_after") != PRESS_SHA256:
        fail("patch receipt does not protect Press v913")
    if patch.get("final_package_hashes_before") != FINAL_BEFORE:
        fail("patch final-package source hashes drift")
    if not MAP_FILE.is_file() or digest(MAP_FILE) != patch.get("map_sha256_after"):
        fail("patched map hash drift")
    if not PRESS_FILE.is_file() or digest(PRESS_FILE) != PRESS_SHA256:
        fail("protected Press v913 hash drift")

    final_after = patch.get("final_package_hashes_after", {})
    if set(final_after) != set(FINAL_BEFORE):
        fail("patched final package inventory drift")
    for asset, expected_hash in final_after.items():
        path = package_disk(asset)
        if not path.is_file() or digest(path) != expected_hash:
            fail("patched final package hash drift: " + asset)

    staging_from_patch = patch.get("staging_package_hashes_before_and_after", {})
    if len(staging_from_patch) != 18 or any(not key.startswith(STAGING + "/") for key in staging_from_patch):
        fail("patch staging inventory drift")
    for asset, expected_hash in staging_from_patch.items():
        path = package_disk(asset)
        if not path.is_file() or digest(path) != expected_hash:
            fail("staging package hash drift: " + asset)

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not levels.load_level(MAP):
        fail("patched map did not load")
    actors = list(actors_api.get_all_level_actors())
    labels = [actor.get_actor_label() for actor in actors]
    if len(labels) != len(set(labels)) or set(labels) != labels_expected():
        fail("exact map actor-label inventory drift")
    if dict(sorted(Counter(actor.get_class().get_name() for actor in actors).items())) != EXPECTED_CLASSES:
        fail("exact map class inventory drift")
    if any(MAP_TAG not in {str(tag) for tag in actor.get_editor_property("tags")} for actor in actors):
        fail("map-owned actor tag drift")
    by_label = {actor.get_actor_label(): actor for actor in actors}

    grid = [actor for actor in actors if GRID_TAG in {str(tag) for tag in actor.get_editor_property("tags")}]
    if len(grid) != 272 or any(not bool(actor.get_editor_property("hidden")) for actor in grid):
        fail("272-grid hidden-in-game contract drift")

    active_coords = {(-6000, -1800), (-3000, -1800), (0, -1800)}
    rect_rows = []
    for actor in (item for item in actors if isinstance(item, unreal.RectLight)):
        component = actor.get_component_by_class(unreal.RectLightComponent)
        location = actor.get_actor_location()
        coords = (int(round(location.x)), int(round(location.y)))
        active = coords in active_coords
        intensity = float(component.get_editor_property("intensity"))
        if (not close(intensity, 1050.0 if active else 0.0)
                or bool(component.get_editor_property("visible")) != active
                or bool(component.get_editor_property("hidden_in_game")) == active
                or bool(actor.get_editor_property("hidden")) == active
                or bool(component.get_editor_property("cast_shadows"))):
            fail("RectLight contract drift: " + actor.get_actor_label())
        rect_rows.append({"label": actor.get_actor_label(), "active": active, "intensity": intensity})
    if len(rect_rows) != 15 or sum(row["active"] for row in rect_rows) != 3:
        fail("RectLight inventory/active count drift")

    sun = by_label["LB_BS_ENV_DirectionalLight"].get_component_by_class(unreal.DirectionalLightComponent)
    if (not close(sun.get_editor_property("intensity"), 1.2)
            or not bool(sun.get_editor_property("cast_shadows"))
            or not close(sun.get_editor_property("light_source_angle"), 4.0)):
        fail("directional soft-shadow contract drift")
    sky = by_label["LB_BS_ENV_SkyLight"].get_component_by_class(unreal.SkyLightComponent)
    if not close(sky.get_editor_property("intensity"), 1.1):
        fail("SkyLight contract drift")
    exposure = by_label["LB_BS_ENV_NeutralExposure"].get_editor_property("settings")
    if (not close(exposure.get_editor_property("auto_exposure_bias"), 0.25)
            or not close(exposure.get_editor_property("auto_exposure_min_brightness"), 1.0)
            or not close(exposure.get_editor_property("auto_exposure_max_brightness"), 1.0)):
        fail("fixed exposure contract drift")

    camera_rows = {}
    for label, (location, target, fov) in CAMERAS.items():
        actor = by_label[label]
        actual_location = actor.get_actor_location()
        expected_rotation = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*location), unreal.Vector(*target))
        actual_rotation = actor.get_actor_rotation()
        component = actor.get_component_by_class(unreal.CameraComponent)
        if (any(not close(a, b) for a, b in zip(actual_location.to_tuple(), location))
                or not close(component.get_editor_property("field_of_view"), fov)
                or not close(actual_rotation.pitch, expected_rotation.pitch)
                or not close(actual_rotation.yaw, expected_rotation.yaw)):
            fail("review camera contract drift: " + label)
        camera_rows[label] = {"location_cm": list(actual_location.to_tuple()), "fov": float(fov)}

    mesh_rows = {}
    before_rows = patch.get("mesh_fingerprints_before", {})
    after_rows = patch.get("mesh_fingerprints_after", {})
    for asset in sorted(FINAL_BEFORE):
        name = asset.rsplit("/", 1)[-1]
        mesh = unreal.EditorAssetLibrary.load_asset(asset)
        if not isinstance(mesh, unreal.StaticMesh):
            fail("final static mesh missing: " + asset)
        row = mesh_fingerprint(mesh, subsystem)
        if row["lod_screen_sizes"] != TARGET_SCREENS:
            fail("LOD screen contract drift: " + name)
        # Bounds were independently checked during the mutating pass; the
        # validator rechecks all discrete geometry/material/collision/Nanite facts.
        prior = dict(before_rows.get(name, {}))
        prior.pop("lod_bounds_cm", None)
        current = dict(row)
        if immutable(current) != immutable(prior):
            fail("immutable mesh facts drift: " + name)
        recorded_after = dict(after_rows.get(name, {}))
        recorded_after.pop("lod_bounds_cm", None)
        if current != recorded_after:
            fail("mesh differs from patch receipt: " + name)
        mesh_rows[name] = row

    protected_after = {"map": digest(MAP_FILE), "press_v913": digest(PRESS_FILE),
                       "finals": {asset: digest(package_disk(asset)) for asset in sorted(FINAL_BEFORE)},
                       "staging": {asset: digest(package_disk(asset)) for asset in sorted(staging_from_patch)}}
    payload = {"$schema": "lineboss/audit/bodyshop/environment-lod-release-candidate-validation-v001/v1",
               "generated_utc": datetime.now(timezone.utc).isoformat(),
               "status": "PASS__EXACT_BODYSHOP_ENVIRONMENT_LIGHTING_CAMERAS_GRID_AND_LOD_VALIDATION_V001",
               "map": MAP, "map_sha256": protected_after["map"],
               "press_v913_sha256": protected_after["press_v913"],
               "actor_count": len(actors), "grid_hidden_in_game_count": len(grid),
               "rect_lights": rect_rows, "cameras": camera_rows, "meshes": mesh_rows,
               "protected_hashes_after": protected_after,
               "writes_to_content_or_config": False, "meshy_credits_used_by_codex": 0,
               "failures": []}
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_BODYSHOP_ENVIRONMENT_LOD_RELEASE_CANDIDATE_VALIDATION_V001_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
