from pathlib import Path
import hashlib, json, unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();P=ROOT/r"Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap";E="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8";sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
MAT="/Game/LineBoss/Candidates/PressShop/Inbound_v853/Materials/M_AGV_C01_Atlas_v855";TEX="/Game/LineBoss/Candidates/PressShop/Inbound_v853/Materials/T_AGV_C01_BaseColor_v855";OUT=ROOT/r"Saved\Audits\PressShopIntegration\agv_flatten_bad_normal_v858.json"
if before!=E or OUT.exists():raise RuntimeError("fresh/protected invariant")
lib=unreal.EditorAssetLibrary;mel=unreal.MaterialEditingLibrary;m=lib.load_asset(MAT);t=lib.load_asset(TEX)
mel.delete_all_material_expressions(m)
b=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-400,-80);b.texture=t;mel.connect_material_property(b,"RGB",unreal.MaterialProperty.MP_BASE_COLOR)
r=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-180,80);r.r=.62;mel.connect_material_property(r,"",unreal.MaterialProperty.MP_ROUGHNESS)
mt=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-180,160);mt.r=.08;mel.connect_material_property(mt,"",unreal.MaterialProperty.MP_METALLIC)
mel.recompile_material(m);lib.save_loaded_asset(m,False)
after=sha(P)
if after!=before:raise RuntimeError("protected changed")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"status":"PASS_REMOVED_TRIANGLE_AMPLIFYING_NORMAL__RECAPTURE_REQUIRED","material":MAT,"base_color":TEX,"normal_disconnected":True,"roughness":.62,"metallic":.08,"protected_v438_before":before,"protected_v438_after":after,"meshy_credits_used":0},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_AGV_FLAT_NORMAL_V858_PASS")
