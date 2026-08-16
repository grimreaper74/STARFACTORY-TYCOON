"""Import the verified Cairnwell logo derivative and build reusable materials."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
SOURCE=ROOT/"SourceAssets/Brand/Cairnwell/Textures/T_Cairnwell_PrimaryLogo_2400x640.png"
MANIFEST=ROOT/"SourceAssets/Brand/Cairnwell/cairnwell_primary_logo_candidate_v001_manifest.json"
DEST="/Game/LineBoss/Brand/Cairnwell/Candidate_v002"
AUDIT=ROOT/"Saved/Audits/cairnwell_primary_logo_unreal_candidate_v002.json"
lib=unreal.EditorAssetLibrary; tools=unreal.AssetToolsHelpers.get_asset_tools(); mel=unreal.MaterialEditingLibrary
if not SOURCE.is_file() or not MANIFEST.is_file(): raise RuntimeError("Verified Cairnwell source/manifest missing")
texture_path=f"{DEST}/T_Cairnwell_PrimaryLogo_v002"
texture=lib.load_asset(texture_path)
if texture is None:
    task=unreal.AssetImportTask(); task.set_editor_properties({"filename":str(SOURCE),"destination_path":DEST,"destination_name":"T_Cairnwell_PrimaryLogo_v002","automated":True,"replace_existing":False,"save":True})
    tools.import_asset_tasks([task]); texture=lib.load_asset(texture_path)
if not isinstance(texture,unreal.Texture2D): raise RuntimeError("Cairnwell texture import failed")
texture.set_editor_properties({"srgb":True,"compression_settings":unreal.TextureCompressionSettings.TC_EDITOR_ICON,"mip_gen_settings":unreal.TextureMipGenSettings.TMGS_SHARPEN2,"never_stream":False})
lib.save_loaded_asset(texture,only_if_is_dirty=False)

def build_material(name,masked,roughness,metallic):
    path=f"{DEST}/{name}"; mat=lib.load_asset(path) or tools.create_asset(name,DEST,unreal.Material,unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    sample=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-350,-40); sample.set_editor_property("texture",texture)
    rough=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-350,170); rough.set_editor_property("r",roughness)
    metal=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-350,250); metal.set_editor_property("r",metallic)
    mel.connect_material_property(sample,"RGB",unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal,"",unreal.MaterialProperty.MP_METALLIC)
    if masked:
        mat.set_editor_property("blend_mode",unreal.BlendMode.BLEND_MASKED)
        mat.set_editor_property("opacity_mask_clip_value",0.25)
        mel.connect_material_property(sample,"A",unreal.MaterialProperty.MP_OPACITY_MASK)
    else: mat.set_editor_property("blend_mode",unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_properties({"two_sided":True,"use_material_attributes":False})
    mel.recompile_material(mat); lib.save_loaded_asset(mat,only_if_is_dirty=False); return mat

surface=build_material("M_Cairnwell_PrimaryLogo_Surface_v002",False,0.42,0.08)
decal=build_material("M_Cairnwell_PrimaryLogo_Masked_v002",True,0.48,0.0)
size=[texture.blueprint_get_size_x(),texture.blueprint_get_size_y()]
payload={"$schema":"line-boss/audit/cairnwell-primary-logo-unreal-candidate/v1","status":"UNREAL_ASSET_CANDIDATE_NOT_PROMOTED","source":str(SOURCE),"manifest":str(MANIFEST),"texture":texture.get_path_name(),"texture_size_px":size,"srgb":bool(texture.get_editor_property("srgb")),"compression":str(texture.get_editor_property("compression_settings")),"materials":[surface.get_path_name(),decal.get_path_name()],"map_placements":0,"promotion_authorized":False,"legal_clearance":"PENDING"}
AUDIT.parent.mkdir(parents=True,exist_ok=True); AUDIT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
unreal.log(f"LINE_BOSS_CAIRNWELL_LOGO_V002_PASS size={size}")
unreal.SystemLibrary.quit_editor()
