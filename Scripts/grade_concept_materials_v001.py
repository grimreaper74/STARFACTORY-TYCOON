"""Palette-grade the concept batch (2026-09-01).

The TRELLIS imports carry their baked base-color textures, which read
near-black under the factory lighting and are not palette-graded. The
standing rule (BRAND_PALETTE_ADOPTION_v001): art is GRADED to the
palette rather than picked by eye. This lane builds one master material
that regrades any baked texture onto the adopted world albedo -

    dark  -> Structure.Graphite  #4A4D50
    light -> Machine.Housing.Pale #D6D2CB

by luminance, while a saturation mask lets the concept's own accents
(amber trim, blue indicators) punch through at boosted brightness. One
MaterialInstance per mesh binds that mesh's baked texture; every slot
on the mesh gets the instance.

Runs INSIDE the editor. Receipt-guarded like every lane.
"""
import json
import os
import unreal

RECEIPT_NAME = "concept_material_grade_v001.json"
PROPS_ROOT = "/Game/Spacecraft/Props"
MASTER_PATH = PROPS_ROOT + "/M_LB_ConceptGraded_v001"

MESHES = [
    "line_station_v001", "kit_dolly_v001", "gantry_crane_v001",
    "lifter_drone_v001", "cargo_drone_v001", "assembly_drone_v001",
    "scout_option3_hull_v001", "delivery_dock_v001",
    "power_station_v001", "fabricator_cell_v003", "charging_dock_v002",
]

# sRGB -> linear approximations of the adopted palette.
GRAPHITE = (0.069, 0.077, 0.084)
HOUSING_PALE = (0.68, 0.65, 0.60)


def build_master():
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    lib = unreal.MaterialEditingLibrary
    factory = unreal.MaterialFactoryNew()
    mat = tools.create_asset("M_LB_ConceptGraded_v001", PROPS_ROOT,
                             unreal.Material, factory)

    def node(cls, x, y):
        return lib.create_material_expression(mat, cls, x, y)

    tex = node(unreal.MaterialExpressionTextureSampleParameter2D,
               -1200, 0)
    tex.set_editor_property("parameter_name", "BaseTex")

    desat = node(unreal.MaterialExpressionDesaturation, -900, -100)
    lib.connect_material_expressions(tex, "RGB", desat, "")

    # Luminance lift so shadowed bakes still read as lit surfaces.
    lift = node(unreal.MaterialExpressionMultiply, -700, -100)
    lift.set_editor_property("const_b", 1.6)
    lib.connect_material_expressions(desat, "", lift, "A")
    lift_sat = node(unreal.MaterialExpressionSaturate, -560, -100)
    lib.connect_material_expressions(lift, "", lift_sat, "")

    graphite = node(unreal.MaterialExpressionConstant3Vector, -700, 120)
    graphite.set_editor_property(
        "constant", unreal.LinearColor(*GRAPHITE, 1.0))
    pale = node(unreal.MaterialExpressionConstant3Vector, -700, 260)
    pale.set_editor_property(
        "constant", unreal.LinearColor(*HOUSING_PALE, 1.0))

    two_tone = node(unreal.MaterialExpressionLinearInterpolate, -400, 0)
    lib.connect_material_expressions(graphite, "", two_tone, "A")
    lib.connect_material_expressions(pale, "", two_tone, "B")
    lib.connect_material_expressions(lift_sat, "", two_tone, "Alpha")

    # Saturation mask: max(rgb)-min(rgb), widened - lets the concept's
    # amber/blue accents keep their hue instead of being flattened.
    mask_r = node(unreal.MaterialExpressionComponentMask, -900, 420)
    mask_r.set_editor_property("r", True)
    mask_r.set_editor_property("g", False)
    mask_r.set_editor_property("b", False)
    lib.connect_material_expressions(tex, "RGB", mask_r, "")
    mask_g = node(unreal.MaterialExpressionComponentMask, -900, 500)
    mask_g.set_editor_property("r", False)
    mask_g.set_editor_property("g", True)
    mask_g.set_editor_property("b", False)
    lib.connect_material_expressions(tex, "RGB", mask_g, "")
    mask_b = node(unreal.MaterialExpressionComponentMask, -900, 580)
    mask_b.set_editor_property("r", False)
    mask_b.set_editor_property("g", False)
    mask_b.set_editor_property("b", True)
    lib.connect_material_expressions(tex, "RGB", mask_b, "")

    max_rg = node(unreal.MaterialExpressionMax, -740, 440)
    lib.connect_material_expressions(mask_r, "", max_rg, "A")
    lib.connect_material_expressions(mask_g, "", max_rg, "B")
    max_rgb = node(unreal.MaterialExpressionMax, -620, 460)
    lib.connect_material_expressions(max_rg, "", max_rgb, "A")
    lib.connect_material_expressions(mask_b, "", max_rgb, "B")

    min_rg = node(unreal.MaterialExpressionMin, -740, 560)
    lib.connect_material_expressions(mask_r, "", min_rg, "A")
    lib.connect_material_expressions(mask_g, "", min_rg, "B")
    min_rgb = node(unreal.MaterialExpressionMin, -620, 580)
    lib.connect_material_expressions(min_rg, "", min_rgb, "A")
    lib.connect_material_expressions(mask_b, "", min_rgb, "B")

    sat_diff = node(unreal.MaterialExpressionSubtract, -500, 500)
    lib.connect_material_expressions(max_rgb, "", sat_diff, "A")
    lib.connect_material_expressions(min_rgb, "", sat_diff, "B")
    sat_wide = node(unreal.MaterialExpressionMultiply, -380, 500)
    sat_wide.set_editor_property("const_b", 4.0)
    lib.connect_material_expressions(sat_diff, "", sat_wide, "A")
    sat_mask = node(unreal.MaterialExpressionSaturate, -260, 500)
    lib.connect_material_expressions(sat_wide, "", sat_mask, "")

    accent = node(unreal.MaterialExpressionMultiply, -400, 300)
    accent.set_editor_property("const_b", 1.5)
    lib.connect_material_expressions(tex, "RGB", accent, "A")

    final = node(unreal.MaterialExpressionLinearInterpolate, -120, 100)
    lib.connect_material_expressions(two_tone, "", final, "A")
    lib.connect_material_expressions(accent, "", final, "B")
    lib.connect_material_expressions(sat_mask, "", final, "Alpha")
    lib.connect_material_property(
        final, "", unreal.MaterialProperty.MP_BASE_COLOR)

    rough = node(unreal.MaterialExpressionScalarParameter, -400, 700)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.55)
    lib.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def find_base_texture(folder):
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_path(folder, recursive=True)
    for data in assets:
        if data.asset_class_path.asset_name == "Texture2D":
            return unreal.load_asset(str(data.package_name))
    return None


def main():
    project = unreal.SystemLibrary.get_project_directory()
    audit_dir = os.path.join(project, "Saved", "Audits", "Spacecraft")
    os.makedirs(audit_dir, exist_ok=True)
    receipt_path = os.path.join(audit_dir, RECEIPT_NAME)
    if os.path.exists(receipt_path):
        unreal.log_error("RECEIPT EXISTS: %s - author v002." %
                         receipt_path)
        return

    master = build_master()
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    lib = unreal.MaterialEditingLibrary
    results = []
    failures = 0
    for name in MESHES:
        entry = {"asset": name}
        folder = "%s/%s" % (PROPS_ROOT, name)
        mesh_path = "%s/%s" % (folder, name)
        mesh = unreal.load_asset(mesh_path)
        if not isinstance(mesh, unreal.StaticMesh):
            entry["status"] = "FAIL_CLOSED__MESH_MISSING"
            failures += 1
            results.append(entry)
            continue

        mi_factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = tools.create_asset("MI_%s_Graded" % name, folder,
                                unreal.MaterialInstanceConstant,
                                mi_factory)
        lib.set_material_instance_parent(mi, master)
        texture = find_base_texture(folder)
        if texture is not None:
            lib.set_material_instance_texture_parameter_value(
                mi, "BaseTex", texture)
            entry["texture"] = texture.get_path_name()
        else:
            entry["texture"] = "NONE - master defaults apply"
        unreal.EditorAssetLibrary.save_loaded_asset(mi)

        slots = mesh.get_num_sections(0)
        materials = mesh.get_editor_property("static_materials")
        for index in range(len(materials)):
            mesh.set_material(index, mi)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        entry["slots"] = len(materials)
        entry["status"] = "PASS__GRADED"
        results.append(entry)
        unreal.log("GRADED %s (%d slots)" % (name, len(materials)))

    receipt = {
        "$schema": "lineboss/audit/concept-material-grade/v1",
        "status": ("PASS__ALL_GRADED" if failures == 0
                   else "FAIL_CLOSED__%d_FAILURES" % failures),
        "master": MASTER_PATH,
        "assets": results,
    }
    with open(receipt_path, "w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
    unreal.log("MATERIAL GRADE COMPLETE: %s" % receipt["status"])


main()
