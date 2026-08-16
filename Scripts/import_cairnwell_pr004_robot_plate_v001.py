"""Import the deterministic Cairnwell PR-004 robot plate and build its material."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Brand/Cairnwell/RobotPlates/T_Cairnwell_PR004_RobotPlate_v001.png"
MANIFEST = ROOT / "SourceAssets/Brand/Cairnwell/RobotPlates/cairnwell_pr004_robot_plate_v001_manifest.json"
DEST = "/Game/LineBoss/Brand/Cairnwell/Candidate_v005/RobotPlate"
AUDIT = ROOT / "Saved/Audits/cairnwell_pr004_robot_plate_unreal_v001.json"
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
texture_path = DEST + "/T_Cairnwell_PR004_RobotPlate_v001"
texture = lib.load_asset(texture_path)
if texture is None:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE), "destination_path": DEST,
        "destination_name": "T_Cairnwell_PR004_RobotPlate_v001",
        "automated": True, "replace_existing": False, "save": True,
    })
    tools.import_asset_tasks([task])
    texture = lib.load_asset(texture_path)
if not isinstance(texture, unreal.Texture2D):
    raise RuntimeError("PR-004 robot plate texture import failed")
texture.set_editor_properties({
    "srgb": True,
    "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT,
    "mip_gen_settings": unreal.TextureMipGenSettings.TMGS_SHARPEN2,
    "never_stream": False,
})
lib.save_loaded_asset(texture, only_if_is_dirty=False)

material_path = DEST + "/M_Cairnwell_PR004_RobotPlate_v001"
material = lib.load_asset(material_path)
if material is None:
    material = tools.create_asset(
        "M_Cairnwell_PR004_RobotPlate_v001", DEST,
        unreal.Material, unreal.MaterialFactoryNew(),
    )
    sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -350, -40)
    sample.set_editor_property("texture", texture)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -350, 160)
    rough.set_editor_property("r", 0.5)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -350, 240)
    metal.set_editor_property("r", 0.04)
    mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    material.set_editor_properties({"two_sided": True, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})
    mel.recompile_material(material)
    lib.save_loaded_asset(material, only_if_is_dirty=False)

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
payload = {
    "$schema": "line-boss/audit/cairnwell-pr004-robot-plate-unreal/v1",
    "status": "UNREAL_PLATE_ASSET_CANDIDATE_NOT_PROMOTED",
    "source": str(SOURCE),
    "manifest": str(MANIFEST),
    "source_sha256": manifest["sha256"],
    "texture": texture.get_path_name(),
    "texture_size_px": [texture.blueprint_get_size_x(), texture.blueprint_get_size_y()],
    "material": material.get_path_name(),
    "internal_project_use_gate": "CLEARED_BY_USER_CONFIRMATION",
    "map_placements": 0,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_CAIRNWELL_PR004_ROBOT_PLATE_V001_PASS audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
