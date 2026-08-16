"""Import and assemble the pivot-safe shared HMI candidate in Unreal 5.8."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT_ROOT = Path(unreal.Paths.project_dir())
MANIFEST_PATH = PROJECT_ROOT / "SourceAssets/Shared/HMI/v003_ue001/hmi_unreal_manifest.json"
DESTINATION = "/Game/LineBoss/Shared/HMI/IND_HMI_001"
MAP_PATH = "/Game/LineBoss/Developer/Validation/LB_HMI_Validation"
AUDIT_PATH = PROJECT_ROOT / "Saved/Audits/shared_hmi_unreal_import.json"


def import_module(record):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", record["fbx"])
    task.set_editor_property("destination_path", DESTINATION)
    task.set_editor_property("destination_name", record["asset_name"])
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("replace_existing_settings", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", True)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    static_options = options.get_editor_property("static_mesh_import_data")
    static_options.set_editor_property("combine_meshes", True)
    static_options.set_editor_property("convert_scene", True)
    static_options.set_editor_property("convert_scene_unit", True)
    static_options.set_editor_property("force_front_x_axis", False)
    static_options.set_editor_property("generate_lightmap_u_vs", True)
    static_options.set_editor_property("auto_generate_collision", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.get_editor_property("imported_object_paths"))
    if not paths:
        raise RuntimeError(f"Unreal imported no object for {record['asset_name']}")
    expected = f"{DESTINATION}/{record['asset_name']}"
    asset = unreal.EditorAssetLibrary.load_asset(expected)
    if asset is None:
        candidates = [path for path in paths if path.rsplit(".", 1)[0].endswith(record["asset_name"])]
        if not candidates:
            raise RuntimeError(f"Expected mesh {expected} was not found; imported {paths}")
        asset = unreal.EditorAssetLibrary.load_asset(candidates[0])
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"{record['asset_name']} imported as {asset.get_class().get_name()}, not StaticMesh")
    return asset, paths


def spawn_mesh(mesh, label):
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    return actor


def build_validation_map(imported):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    library = unreal.EditorAssetLibrary
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if library.does_asset_exist(MAP_PATH):
        levels.load_level(MAP_PATH)
        for actor in actors.get_all_level_actors():
            actors.destroy_actor(actor)
    elif not levels.new_level(MAP_PATH):
        raise RuntimeError(f"Could not create validation map {MAP_PATH}")

    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -5), unreal.Rotator())
    floor.set_actor_label("LB_HMI_ValidationFloor")
    floor.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
    floor.set_actor_scale3d(unreal.Vector(8.0, 8.0, 0.1))
    floor_material = unreal.load_asset("/Game/LineBoss/Materials/M_LB_FactoryConcrete")
    if floor_material is not None:
        floor.static_mesh_component.set_material(0, floor_material)

    for asset_name, mesh in imported.items():
        spawn_mesh(mesh, f"LB_HMI_MODULE_{asset_name}")

    sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(), unreal.Rotator(-35, -35, 0))
    sun.set_actor_label("LB_HMI_KeyLight")
    sun.get_editor_property("directional_light_component").set_editor_property("intensity", 1.25)
    fill = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(-120, -140, 180), unreal.Rotator())
    fill.set_actor_label("LB_HMI_FillLight")
    fill.get_editor_property("point_light_component").set_editor_property("intensity", 180.0)
    fill.get_editor_property("point_light_component").set_editor_property("attenuation_radius", 600.0)

    exposure = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
    exposure.set_actor_label("LB_HMI_FixedExposure")
    exposure.set_editor_property("unbound", True)
    exposure.set_editor_property("blend_weight", 1.0)
    settings = exposure.get_editor_property("settings")
    settings.set_editor_property("override_auto_exposure_method", True)
    settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_BASIC)
    settings.set_editor_property("override_auto_exposure_min_brightness", True)
    settings.set_editor_property("override_auto_exposure_max_brightness", True)
    settings.set_editor_property("auto_exposure_min_brightness", 8.0)
    settings.set_editor_property("auto_exposure_max_brightness", 8.0)
    settings.set_editor_property("override_auto_exposure_bias", True)
    settings.set_editor_property("auto_exposure_bias", 0.0)
    exposure.set_editor_property("settings", settings)

    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-180, -150, 118), unreal.Rotator())
    camera.set_actor_label("LB_CAM_HMI_FrontValidation")
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0, 0, 80)),
        False,
    )
    camera.camera_component.set_editor_property("field_of_view", 42.0)
    if not levels.save_current_level():
        raise RuntimeError("Failed to save the shared-HMI validation map")
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
    return camera


def main():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    imported = {}
    records = []
    for module in manifest["modules"]:
        mesh, paths = import_module(module)
        imported[module["asset_name"]] = mesh
        box = mesh.get_bounding_box()
        records.append(
            {
                "asset_name": module["asset_name"],
                "object_path": mesh.get_path_name(),
                "imported_paths": paths,
                "source_bounds_cm": module["bounds"],
                "unreal_bounds_cm": {
                    "min": [round(box.min.x, 3), round(box.min.y, 3), round(box.min.z, 3)],
                    "max": [round(box.max.x, 3), round(box.max.y, 3), round(box.max.z, 3)],
                },
            }
        )
    build_validation_map(imported)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(
        json.dumps(
            {
                "status": "UNREAL_CANDIDATE_NOT_PROMOTED",
                "manifest": str(MANIFEST_PATH),
                "destination": DESTINATION,
                "validation_map": MAP_PATH,
                "module_count": len(records),
                "modules": records,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    unreal.log(f"LINE_BOSS_HMI_UNREAL_IMPORT_PASS modules={len(records)} audit={AUDIT_PATH}")


main()
