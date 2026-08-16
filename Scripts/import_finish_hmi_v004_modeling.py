"""Import, Geometry-Script finish and assemble the HMI v004 Unreal candidate."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir())
MANIFEST = PROJECT / "SourceAssets/Shared/HMI/v004_ue_modeling003/hmi_v004_unreal_manifest.json"
DEST = "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003"
MAT_DEST = DEST + "/Materials"
MAP = "/Game/LineBoss/Developer/Validation/LB_HMI04_ModelingValidation"
AUDIT = PROJECT / "Saved/Audits/shared_hmi_v004_unreal_modeling003.json"


MATERIALS = {
    "M_HMI04_SS304": ((0.20, 0.225, 0.24), 0.82, 0.30, None, 0.0),
    "M_HMI04_EdgeSteel": ((0.075, 0.085, 0.095), 0.80, 0.24, None, 0.0),
    "M_HMI04_Charcoal": ((0.018, 0.024, 0.030), 0.58, 0.34, None, 0.0),
    "M_HMI04_Rubber": ((0.006, 0.008, 0.010), 0.02, 0.72, None, 0.0),
    "M_HMI04_Chrome": ((0.43, 0.48, 0.52), 0.94, 0.16, None, 0.0),
    "M_HMI04_Screen": ((0.006, 0.025, 0.035), 0.08, 0.22, (0.01, 0.22, 0.32), 0.55),
    "M_HMI04_UI": ((0.12, 0.52, 0.70), 0.02, 0.28, (0.08, 0.52, 0.82), 1.5),
    "M_HMI04_White": ((0.70, 0.74, 0.76), 0.05, 0.44, None, 0.0),
    "M_HMI04_Red": ((0.52, 0.012, 0.006), 0.10, 0.26, (0.24, 0.0, 0.0), 0.16),
    "M_HMI04_Amber": ((0.88, 0.20, 0.006), 0.08, 0.24, (0.55, 0.06, 0.0), 0.40),
    "M_HMI04_Green": ((0.012, 0.40, 0.055), 0.08, 0.26, (0.0, 0.35, 0.025), 0.30),
    "M_HMI04_Blue": ((0.006, 0.15, 0.56), 0.08, 0.25, (0.0, 0.06, 0.22), 0.16),
    "M_HMI04_Yellow": ((0.86, 0.42, 0.006), 0.12, 0.31, None, 0.0),
    "M_HMI04_Copper": ((0.39, 0.12, 0.025), 0.82, 0.23, None, 0.0),
    "M_HMI04_WireDuct": ((0.48, 0.52, 0.53), 0.10, 0.52, None, 0.0),
}


def create_constant(material, expression_class, value, x, y):
    expression = unreal.MaterialEditingLibrary.create_material_expression(material, expression_class, x, y)
    if expression_class == unreal.MaterialExpressionConstant:
        expression.set_editor_property("r", value)
    else:
        expression.set_editor_property("constant", value)
    return expression


def build_material(name, spec):
    path = f"{MAT_DEST}/{name}"
    material = unreal.EditorAssetLibrary.load_asset(path)
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MAT_DEST, unreal.Material, unreal.MaterialFactoryNew()
        )
    if hasattr(unreal.MaterialEditingLibrary, "delete_all_material_expressions"):
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    base, metallic, roughness, emission, strength = spec
    colour = create_constant(material, unreal.MaterialExpressionConstant3Vector, unreal.LinearColor(*base, 1), -520, -80)
    metal = create_constant(material, unreal.MaterialExpressionConstant, metallic, -520, 40)
    rough = create_constant(material, unreal.MaterialExpressionConstant, roughness, -520, 150)
    unreal.MaterialEditingLibrary.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if emission is not None and strength > 0:
        emit_colour = create_constant(material, unreal.MaterialExpressionConstant3Vector, unreal.LinearColor(*emission, 1), -520, 270)
        emit_strength = create_constant(material, unreal.MaterialExpressionConstant, strength, -520, 370)
        multiply = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionMultiply, -280, 300)
        unreal.MaterialEditingLibrary.connect_material_expressions(emit_colour, "", multiply, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(emit_strength, "", multiply, "B")
        unreal.MaterialEditingLibrary.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def select_material(slot_name, materials):
    key = slot_name.lower()
    rules = (
        (("live_screen",), "M_HMI04_Screen"), (("ui_light",), "M_HMI04_UI"),
        (("ss304", "brushed_stainless"), "M_HMI04_SS304"), (("folded_edge",), "M_HMI04_EdgeSteel"),
        (("charcoal",), "M_HMI04_Charcoal"), (("elastomer", "rubber", "black"), "M_HMI04_Rubber"),
        (("stainless_controls", "chrome"), "M_HMI04_Chrome"), (("engraved_white", "white"), "M_HMI04_White"),
        (("safety_red",), "M_HMI04_Red"), (("status_amber",), "M_HMI04_Amber"),
        (("status_green",), "M_HMI04_Green"), (("reset_blue",), "M_HMI04_Blue"),
        (("safety_yellow",), "M_HMI04_Yellow"), (("copper",), "M_HMI04_Copper"),
        (("wire_duct",), "M_HMI04_WireDuct"), (("dark", "edge_steel"), "M_HMI04_EdgeSteel"),
    )
    for needles, material_name in rules:
        if any(needle in key for needle in needles):
            return materials[material_name]
    return materials["M_HMI04_Charcoal"]


def import_mesh(record):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": record["fbx"], "destination_path": DEST,
        "destination_name": record["asset_name"], "automated": True,
        "replace_existing": True, "replace_existing_settings": True, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    static = options.get_editor_property("static_mesh_import_data")
    static.set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "generate_lightmap_u_vs": True,
        "auto_generate_collision": True, "remove_degenerates": False,
    })
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST}/{record['asset_name']}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Failed to import static mesh {record['asset_name']}")
    return mesh


def geometry_finish(mesh):
    dynamic = unreal.DynamicMesh()
    from_options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    from_options.set_editor_properties({"apply_build_settings": False, "request_tangents": True, "use_build_scale": True})
    read_lod = unreal.GeometryScriptMeshReadLOD()
    unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(mesh, dynamic, from_options, read_lod)
    before = dynamic.get_mesh_info_string()
    repair = unreal.GeometryScriptDegenerateTriangleOptions()
    repair.set_editor_properties({"min_edge_length": 0.0001, "min_triangle_area": 0.000001, "compact_on_completion": True})
    unreal.GeometryScript_MeshRepair.repair_mesh_degenerate_geometry(dynamic, repair)
    unreal.GeometryScript_MeshRepair.compact_mesh(dynamic)
    normals = unreal.GeometryScriptCalculateNormalsOptions()
    normals.set_editor_properties({"angle_weighted": True, "area_weighted": True})
    unreal.GeometryScript_Normals.recompute_normals(dynamic, normals)
    after = dynamic.get_mesh_info_string()
    to_options = unreal.GeometryScriptCopyMeshToAssetOptions()
    to_options.set_editor_properties({
        "enable_recompute_normals": False, "enable_recompute_tangents": True,
        "enable_remove_degenerates": True, "clean_assigned_materials": False,
        "use_build_scale": True,
    })
    write_lod = unreal.GeometryScriptMeshWriteLOD()
    unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dynamic, mesh, to_options, write_lod, True)
    return before, after


def assign_materials(mesh, materials):
    static_materials = mesh.get_editor_property("static_materials")
    assigned = []
    for slot in static_materials:
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
        material = select_material(slot_name, materials)
        slot.set_editor_property("material_interface", material)
        assigned.append({"slot": slot_name, "material": material.get_path_name()})
    mesh.set_editor_property("static_materials", static_materials)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    return assigned


def spawn_mesh(mesh, label):
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    return actor


def build_map(meshes):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        levels.load_level(MAP)
        for actor in actor_system.get_all_level_actors():
            actor_system.destroy_actor(actor)
    elif not levels.new_level(MAP):
        raise RuntimeError(f"Unable to create {MAP}")
    floor = actor_system.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -6), unreal.Rotator())
    floor.set_actor_label("LB_HMI04_ValidationFloor")
    floor.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
    floor.set_actor_scale3d(unreal.Vector(6, 6, 0.1))
    floor_mat = unreal.load_asset("/Game/LineBoss/Materials/M_LB_FactoryConcrete")
    if floor_mat:
        floor.static_mesh_component.set_material(0, floor_mat)
    for name, mesh in meshes.items():
        spawn_mesh(mesh, "LB_HMI04_" + name)

    sun = actor_system.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(), unreal.Rotator(-42, -32, 0))
    sun.set_actor_label("LB_HMI04_Key")
    sun.get_editor_property("directional_light_component").set_editor_property("intensity", 1.5)
    rect = actor_system.spawn_actor_from_class(unreal.RectLight, unreal.Vector(150, 180, 190), unreal.Rotator())
    rect.set_actor_label("LB_HMI04_Fill")
    rect.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(rect.get_actor_location(), unreal.Vector(0,0,75)), False)
    rect.get_editor_property("rect_light_component").set_editor_properties({"intensity": 650.0, "attenuation_radius": 600.0, "source_width": 160.0, "source_height": 160.0})
    exposure = actor_system.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
    exposure.set_actor_label("LB_HMI04_FixedExposure")
    exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0})
    settings = exposure.get_editor_property("settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True, "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True, "auto_exposure_bias": -1.0,
    })
    exposure.set_editor_property("settings", settings)
    # The FBX conversion places the operator face toward +Y.  Use a modest
    # three-quarter front view so the screen/control panel and cabinet depth
    # are both legible in a release-distance validation shot.
    camera = actor_system.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(145, 225, 125), unreal.Rotator())
    camera.set_actor_label("LB_CAM_HMI04_Front")
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0,0,78)), False)
    camera.camera_component.set_editor_property("field_of_view", 38.0)
    levels.save_current_level()
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
    return camera


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    materials = {name: build_material(name, spec) for name, spec in MATERIALS.items()}
    meshes = {}
    records = []
    for record in manifest["modules"]:
        mesh = import_mesh(record)
        before, after = geometry_finish(mesh)
        assignments = assign_materials(mesh, materials)
        meshes[record["asset_name"]] = mesh
        box = mesh.get_bounding_box()
        records.append({
            "asset": mesh.get_path_name(), "source_bounds_cm": record["bounds"],
            "unreal_bounds_cm": {"min": [box.min.x,box.min.y,box.min.z], "max": [box.max.x,box.max.y,box.max.z]},
            "geometry_before": before, "geometry_after": after, "materials": assignments,
        })
    build_map(meshes)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps({
        "status": "UNREAL_MODELING_CANDIDATE_NOT_PROMOTED", "manifest": str(MANIFEST),
        "destination": DEST, "validation_map": MAP, "module_count": len(records), "modules": records,
    }, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_HMI04_MODELING_PASS modules={len(records)} audit={AUDIT}")


main()
