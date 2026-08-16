"""Import the reusable master-coil candidate and bind controlled materials."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/IndustrialKit/MasterCoil/SM_LB_MasterCoil_Candidate_v002.fbx"
DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil"
NAME = "SM_LB_MasterCoil_Candidate_v002"
AUDIT = ROOT / "Saved/Audits/master_coil_candidate_v002.json"

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(SOURCE), "destination_path": DEST, "destination_name": NAME,
    "automated": True, "replace_existing": True,
    "replace_existing_settings": True, "save": True,
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
    "auto_generate_collision": True, "remove_degenerates": True,
})
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST}/{NAME}")
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("Master coil did not import as a StaticMesh")

def controlled_material(name, colour, metallic, roughness, two_sided=False):
    asset_path = f"{DEST}/{name}"
    material = unreal.load_asset(asset_path)
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Controlled coil material is not editable: {asset_path}")
    mel = unreal.MaterialEditingLibrary
    # Rebuild even an existing candidate material.  An earlier renderer test
    # could leave its blend mode or graph in a translucent/fallback state; the
    # delivered coil must always be solid in every gameplay view.
    mel.delete_all_material_expressions(material)
    material.set_editor_properties({
        "blend_mode": unreal.BlendMode.BLEND_OPAQUE,
        "two_sided": two_sided,
    })
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -450, -80)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -450, 80)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -450, 210)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


coil_steel = controlled_material(
    "M_LB_MasterCoil_SilverWrap_v002", (0.42, 0.45, 0.49), 0.08, 0.72,
    two_sided=True,
)
wound_edge = controlled_material(
    "M_LB_MasterCoil_WoundEdge_v002", (0.025, 0.032, 0.040), 0.42, 0.62,
    two_sided=True,
)
dark = controlled_material("M_LB_MasterCoil_Strap_v002", (0.006, 0.009, 0.012), 0.12, 0.66)
cardboard = controlled_material("M_LB_MasterCoil_Cardboard_v002", (0.24, 0.12, 0.035), 0.0, 0.88)

assignments = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    name = str(slot.get_editor_property("imported_material_slot_name") or
               slot.get_editor_property("material_slot_name"))
    lowered = name.lower()
    selected = (
        cardboard if ("cardboard" in lowered or "protector" in lowered)
        else dark if ("band" in lowered or "strap" in lowered)
        else wound_edge if "edge" in lowered
        else coil_steel
    )
    mesh.set_material(index, selected)
    assignments.append({"slot": name, "material": selected.get_path_name()})
unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

box = mesh.get_bounding_box()
result = {
    "status": "CANDIDATE_NOT_PROMOTED",
    "source": str(SOURCE),
    "asset": mesh.get_path_name(),
    "dimensions_mm": {"width": 1500, "outer_diameter": 1900, "bore": 610},
    "nominal_mass_kg": 27500,
    "bounds_cm": {
        "min": list(box.min.to_tuple()), "max": list(box.max.to_tuple()),
        "size": [box.max.x-box.min.x, box.max.y-box.min.y, box.max.z-box.min.z],
    },
    "materials": assignments,
    "material_render_contract": {
        material.get_name(): {
            "blend_mode": str(material.get_editor_property("blend_mode")),
            "two_sided": bool(material.get_editor_property("two_sided")),
        }
        for material in (coil_steel, wound_edge, dark, cardboard)
    },
}
for material_name, contract in result["material_render_contract"].items():
    if "OPAQUE" not in contract["blend_mode"].upper():
        raise RuntimeError(f"Master-coil material is not opaque: {material_name} {contract}")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_MASTER_COIL_IMPORT_PASS asset={result['asset']} audit={AUDIT}")
