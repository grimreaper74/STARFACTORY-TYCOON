"""Restore AGV atlas textures and scanner authored palette after modular FBX intake."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir()).resolve(); MAP="/Game/LineBoss/Maps/LB_PressShop_PR002_AGV_IsolatedValidation_v853"
AGV="/Game/LineBoss/Candidates/PressShop/Inbound_v853/AGV_C01"; SCN="/Game/LineBoss/Candidates/PressShop/Inbound_v853/PR002Scanner"; MAT="/Game/LineBoss/Candidates/PressShop/Inbound_v853/Materials"
STAGE=Path(r"C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressShop\InboundCoilDelivery\CoilAGV_UserApproved_v20260809_v851\UnrealStaging_v852")
OUT=ROOT/r"Saved\Audits\PressShopIntegration\pr002_agv_material_repair_v855.json"
P=ROOT/r"Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap"; E="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"; sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper(); before=sha(P)
if before!=E or OUT.exists(): raise RuntimeError("fresh/protected invariant")
lib=unreal.EditorAssetLibrary; tools=unreal.AssetToolsHelpers.get_asset_tools(); mel=unreal.MaterialEditingLibrary

def import_texture(filename,name):
 t=unreal.AssetImportTask(); t.set_editor_properties({"filename":str(STAGE/filename),"destination_path":MAT,"destination_name":name,"automated":True,"replace_existing":True,"replace_existing_settings":True,"save":True}); tools.import_asset_tasks([t]); tex=lib.load_asset(f"{MAT}/{name}")
 if not isinstance(tex,unreal.Texture2D):raise RuntimeError(name)
 return tex
base=import_texture("T_AGV_C01_BaseColor_v855.jpg","T_AGV_C01_BaseColor_v855"); normal=import_texture("T_AGV_C01_Normal_v855.jpg","T_AGV_C01_Normal_v855")
normal.set_editor_properties({"srgb":False,"compression_settings":unreal.TextureCompressionSettings.TC_NORMALMAP}); lib.save_loaded_asset(normal,False)

def material(name,color=None,rough=.45,metal=.1,base_tex=None,normal_tex=None):
 path=f"{MAT}/{name}"; m=lib.load_asset(path)
 if m is None:m=tools.create_asset(name,MAT,unreal.Material,unreal.MaterialFactoryNew())
 if base_tex:
  b=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-420,-80); b.texture=base_tex; mel.connect_material_property(b,"RGB",unreal.MaterialProperty.MP_BASE_COLOR)
 else:
  b=mel.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-420,-80); b.constant=unreal.LinearColor(*color,1); mel.connect_material_property(b,"",unreal.MaterialProperty.MP_BASE_COLOR)
 if normal_tex:
  n=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-420,100); n.texture=normal_tex; n.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL; mel.connect_material_property(n,"RGB",unreal.MaterialProperty.MP_NORMAL)
 r=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-180,160);r.r=rough;mel.connect_material_property(r,"",unreal.MaterialProperty.MP_ROUGHNESS)
 mt=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-180,240);mt.r=metal;mel.connect_material_property(mt,"",unreal.MaterialProperty.MP_METALLIC)
 mel.recompile_material(m);lib.save_loaded_asset(m,False);return m

m_agv=material("M_AGV_C01_Atlas_v855",rough=.38,metal=.28,base_tex=base,normal_tex=normal)
palette={
 "green":material("M_PR002_CairnwellGreen_v855",(0.012,0.105,0.070),.32,.32),
 "charcoal":material("M_PR002_Charcoal_v855",(0.018,0.024,0.030),.44,.35),
 "yellow":material("M_PR002_SafetyYellow_v855",(0.92,0.48,0.01),.34,.12),
 "grey":material("M_PR002_CabinetGrey_v855",(0.48,0.52,0.55),.38,.25),
 "black":material("M_PR002_CableBlack_v855",(0.008,0.010,0.012),.62,.0),
 "blue":material("M_PR002_ScannerBlue_v855",(0.015,0.18,0.48),.30,.20),
 "white":material("M_PR002_WrappedCoilWhite_v855",(0.82,0.84,0.86),.58,.05),
}

assigned={"agv":[],"scanner":[]}
for path in lib.list_assets(AGV,recursive=True,include_folder=False):
 mesh=lib.load_asset(path)
 if isinstance(mesh,unreal.StaticMesh):mesh.set_material(0,m_agv);lib.save_loaded_asset(mesh,False);assigned["agv"].append(path)
for path in lib.list_assets(SCN,recursive=True,include_folder=False):
 mesh=lib.load_asset(path)
 if not isinstance(mesh,unreal.StaticMesh):continue
 n=mesh.get_name()
 key="charcoal"
 if "SafetyPost" in n:key="yellow"
 elif "Gantry" in n or "Crossbeam" in n:key="green"
 elif "Cabinet" in n or "Console" in n:key="grey"
 elif "ServiceCable" in n:key="black"
 elif "ScannerHead" in n:key="blue"
 elif "WrappedCoil" in n:key="white"
 mesh.set_material(0,palette[key]);lib.save_loaded_asset(mesh,False);assigned["scanner"].append({"asset":path,"material":key})
after=sha(P)
if after!=before:raise RuntimeError("protected changed")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"status":"PASS_MATERIAL_BINDING__UNREAL_RECAPTURE_REQUIRED","generated_utc":datetime.now(timezone.utc).isoformat(),"map":MAP,"agv_texture_atlas":str(base.get_path_name()),"agv_normal":str(normal.get_path_name()),"assigned":assigned,"protected_v438_before":before,"protected_v438_after":after,"meshy_credits_used":0},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_PR002_AGV_MATERIALS_V855_PASS")
