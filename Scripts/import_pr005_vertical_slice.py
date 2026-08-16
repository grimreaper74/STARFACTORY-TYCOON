"""Import and assemble the modular PR-005 candidate in Unreal 5.8."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir())
SOURCE = PROJECT / "SourceAssets/PR005"
DEST = "/Game/LineBoss/Stations/Press/PR005/Candidate_v001"
MAT_DEST = DEST + "/Materials"
MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation"
AUDIT = PROJECT / "Saved/Audits/pr005_modular_unreal_import_v001.json"

MATERIALS = {
    "SafetyYellow": ((0.72, 0.32, 0.018), 0.66, 0.34),
    "DarkMachine": ((0.025, 0.032, 0.038), 0.72, 0.38),
    "MachinedSteel": ((0.34, 0.38, 0.41), 0.92, 0.22),
    "Stainless": ((0.43, 0.47, 0.49), 0.88, 0.31),
    "Galvanised": ((0.25, 0.28, 0.30), 0.78, 0.42),
    "CoilSteel": ((0.42, 0.45, 0.47), 0.91, 0.26),
    "Rubber": ((0.008, 0.010, 0.012), 0.02, 0.74),
    "SafetyRed": ((0.50, 0.010, 0.004), 0.10, 0.30),
    "Concrete": ((0.11, 0.105, 0.095), 0.02, 0.88),
    "Screen": ((0.004, 0.028, 0.040), 0.08, 0.20),
    "White": ((0.68, 0.71, 0.72), 0.05, 0.50),
    "Blue": ((0.015, 0.10, 0.34), 0.18, 0.38),
}


def material(name, spec):
    path = f"{MAT_DEST}/M_PR005_{name}"
    existing = unreal.EditorAssetLibrary.load_asset(path)
    if existing:
        return existing
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        f"M_PR005_{name}", MAT_DEST, unreal.Material, unreal.MaterialFactoryNew())
    colour, metallic, roughness = spec
    mel = unreal.MaterialEditingLibrary
    base = mel.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -420, -60)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -420, 60)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -420, 160)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


def choose_material(slot, materials):
    key = slot.lower()
    rules = (
        (("yellow",), "SafetyYellow"), (("red",), "SafetyRed"),
        (("rubber", "hose", "elastomer"), "Rubber"),
        (("coil", "strip", "galvan"), "CoilSteel"),
        (("stainless", "ss304"), "Stainless"),
        (("machined", "chrome", "shaft", "roller"), "MachinedSteel"),
        (("concrete", "floor"), "Concrete"), (("screen", "display"), "Screen"),
        (("blue",), "Blue"), (("white", "label", "legend"), "White"),
        (("mesh", "guard"), "Galvanised"),
    )
    for needles, name in rules:
        if any(needle in key for needle in needles):
            return materials[name]
    return materials["DarkMachine"]


def import_mesh(record, destination):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": record["fbx"], "destination_path": destination,
        "destination_name": record["asset_name"], "automated": True,
        "replace_existing": True, "replace_existing_settings": True, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "generate_lightmap_u_vs": True,
        "auto_generate_collision": not record["is_mover"], "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.EditorAssetLibrary.load_asset(f"{destination}/{record['asset_name']}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Failed importing {record['asset_name']}")
    return mesh


def assign_materials(mesh, materials):
    slots = mesh.get_editor_property("static_materials")
    assigned = []
    for index, slot in enumerate(slots):
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
        selected = choose_material(slot_name, materials)
        # Editing the copied StaticMaterial struct array does not persist in
        # UE 5.8.  StaticMesh.set_material updates the asset's real slot.
        mesh.set_material(index, selected)
        assigned.append({"slot": slot_name, "material": selected.get_path_name()})
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    return assigned


def ue_location(pivot):
    return unreal.Vector(float(pivot[0]) * 100.0, -float(pivot[1]) * 100.0, float(pivot[2]) * 100.0)


def build_validation_map(records, materials):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        levels.load_level(MAP)
        for actor in actors.get_all_level_actors():
            actors.destroy_actor(actor)
    elif not levels.new_level(MAP):
        raise RuntimeError(f"Unable to create {MAP}")

    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -10), unreal.Rotator())
    floor.set_actor_label("LB_PR005_ValidationFloor")
    floor.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
    floor.set_actor_scale3d(unreal.Vector(13.0, 7.0, 0.10))
    floor.static_mesh_component.set_material(0, materials["Concrete"])

    for record in records:
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, ue_location(record["pivot_blender_m"]), unreal.Rotator())
        actor.set_actor_label(f"LB_PR005_{record['module_id']}_{record['semantic_group']}")
        actor.static_mesh_component.set_static_mesh(record["mesh"])
        actor.static_mesh_component.set_editor_property(
            "mobility", unreal.ComponentMobility.MOVABLE if record["is_mover"] else unreal.ComponentMobility.STATIC)

    key = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(-300, 180, 550), unreal.Rotator())
    key.set_actor_label("LB_PR005_Key")
    key.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(key.get_actor_location(), unreal.Vector(0, 0, 110)), False)
    key.get_editor_property("rect_light_component").set_editor_properties({
        "intensity": 1050.0, "attenuation_radius": 1600.0,
        "source_width": 500.0, "source_height": 300.0,
    })
    fill = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(500, -260, 420), unreal.Rotator())
    fill.set_actor_label("LB_PR005_Fill")
    fill.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(fill.get_actor_location(), unreal.Vector(0, 0, 100)), False)
    fill.get_editor_property("rect_light_component").set_editor_properties({
        "intensity": 650.0, "attenuation_radius": 1400.0,
        "source_width": 450.0, "source_height": 250.0,
    })
    exposure = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
    exposure.set_actor_label("LB_PR005_FixedExposure")
    exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0})
    settings = exposure.get_editor_property("settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
        "override_auto_exposure_bias": True, "auto_exposure_bias": 0.0,
    })
    exposure.set_editor_property("settings", settings)
    camera_specs = (
        ("LB_CAM_PR005_Overview", unreal.Vector(850, 1050, 850), unreal.Vector(0, 0, 100), 42.0),
        ("LB_CAM_PR005_Process", unreal.Vector(540, 690, 330), unreal.Vector(0, 0, 105), 40.0),
        ("LB_CAM_PR005_Top", unreal.Vector(0, 0, 1450), unreal.Vector(0, 0, 0), 48.0),
    )
    for label, location, target, fov in camera_specs:
        camera = actors.spawn_actor_from_class(unreal.CameraActor, location, unreal.Rotator())
        camera.set_actor_label(label)
        camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
        camera.camera_component.set_editor_property("field_of_view", fov)
    if not levels.save_current_level():
        raise RuntimeError("Failed saving PR-005 validation map")


def main():
    manifests = sorted(SOURCE.glob("*/module_manifest.json"))
    if not manifests:
        raise RuntimeError(f"No PR-005 export manifests found under {SOURCE}")
    materials = {name: material(name, spec) for name, spec in MATERIALS.items()}
    records = []
    for path in manifests:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        module_id = manifest["module_id"]
        module_dest = f"{DEST}/{module_id}"
        for group in manifest["groups"]:
            mesh = import_mesh(group, module_dest)
            records.append({**group, "module_id": module_id, "mesh": mesh, "asset": mesh.get_path_name()})
    # FBX builds are asynchronous.  Assigning slots while the final meshes are
    # still compiling lets their late import finalization restore WorldGrid.
    # Complete every build first, then bind and save materials in a second pass.
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    for record in records:
        record["materials"] = assign_materials(record["mesh"], materials)
    unreal.EditorAssetLibrary.save_directory(DEST, only_if_is_dirty=False, recursive=True)
    build_validation_map(records, materials)
    audit_records = [{key: value for key, value in record.items() if key != "mesh"} for record in records]
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps({
        "status": "UNREAL_PR005_CANDIDATE_NOT_PROMOTED",
        "validation_map": MAP, "manifest_count": len(manifests),
        "asset_count": len(records), "records": audit_records,
    }, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_PR005_IMPORT_PASS manifests={len(manifests)} assets={len(records)} audit={AUDIT}")


main()
