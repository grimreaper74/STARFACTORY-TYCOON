"""Create v013 from v012 with restrained orientation-aware dust on paint."""
from datetime import datetime,timezone
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Maps/LB_PressShop_PR004PaintSpecificCandidate_v012";DEST="/Game/LineBoss/Maps/LB_PressShop_PR004AgedDustCandidate_v013";MAT_ROOT="/Game/LineBoss/Stations/Press/PR004/Candidate_v013/AgedPaint";PREFIX="LB_INT_PR004_V009_robot_v002_";IMPORT=ROOT/"Saved/Audits/pr004_unreal_import_candidate_v003.json";AUDIT=ROOT/"Saved/Audits/press_shop_pr004_aged_dust_candidate_v013.json"
BC="/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_Metalbeam01_BC.T_Metalbeam01_BC";N="/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_Metalbeam01_N.T_Metalbeam01_N";ORM="/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_Metalbeam01_ORM.T_Metalbeam01_ORM"
lib=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
def e(m,k,x,y):return mel.create_material_expression(m,k,x,y)
def build():
 name="M_LB_PR004_AgedDustSafetyPaint_Master_v013";m=tools.create_asset(name,MAT_ROOT,unreal.Material,unreal.MaterialFactoryNew());m.set_editor_properties({"two_sided":False,"blend_mode":unreal.BlendMode.BLEND_OPAQUE})
 paint=e(m,unreal.MaterialExpressionVectorParameter,-900,-260);paint.set_editor_properties({"parameter_name":"AgedPaintColour","default_value":unreal.LinearColor(.62,.31,.003,1)})
 dust=e(m,unreal.MaterialExpressionVectorParameter,-900,-150);dust.set_editor_properties({"parameter_name":"DustColour","default_value":unreal.LinearColor(.13,.10,.065,1)})
 uv=e(m,unreal.MaterialExpressionTextureCoordinate,-1100,100);scale=e(m,unreal.MaterialExpressionScalarParameter,-1100,210);scale.set_editor_properties({"parameter_name":"TextureScale","default_value":8.0});uvm=e(m,unreal.MaterialExpressionMultiply,-900,100);mel.connect_material_expressions(uv,"",uvm,"A");mel.connect_material_expressions(scale,"",uvm,"B")
 masktex=e(m,unreal.MaterialExpressionTextureSample,-680,-30);masktex.set_editor_property("texture",unreal.load_asset(BC));mel.connect_material_expressions(uvm,"",masktex,"UVs")
 normalws=e(m,unreal.MaterialExpressionVertexNormalWS,-680,-150);up=e(m,unreal.MaterialExpressionConstant3Vector,-680,-250);up.set_editor_property("constant",unreal.LinearColor(0,0,1,1));dot=e(m,unreal.MaterialExpressionDotProduct,-470,-180);mel.connect_material_expressions(normalws,"",dot,"A");mel.connect_material_expressions(up,"",dot,"B")
 amount=e(m,unreal.MaterialExpressionScalarParameter,-470,-50);amount.set_editor_properties({"parameter_name":"DustAmount","default_value":.13});maskmul=e(m,unreal.MaterialExpressionMultiply,-260,-100);mel.connect_material_expressions(masktex,"R",maskmul,"A");mel.connect_material_expressions(dot,"",maskmul,"B");maskfinal=e(m,unreal.MaterialExpressionMultiply,-70,-100);mel.connect_material_expressions(maskmul,"",maskfinal,"A");mel.connect_material_expressions(amount,"",maskfinal,"B")
 colour=e(m,unreal.MaterialExpressionLinearInterpolate,140,-180);mel.connect_material_expressions(paint,"",colour,"A");mel.connect_material_expressions(dust,"",colour,"B");mel.connect_material_expressions(maskfinal,"",colour,"Alpha");mel.connect_material_property(colour,"",unreal.MaterialProperty.MP_BASE_COLOR)
 normal=e(m,unreal.MaterialExpressionTextureSample,-680,300);normal.set_editor_properties({"texture":unreal.load_asset(N),"sampler_type":unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL});mel.connect_material_expressions(uvm,"",normal,"UVs");flat=e(m,unreal.MaterialExpressionConstant3Vector,-680,430);flat.set_editor_property("constant",unreal.LinearColor(.5,.5,1,1));ns=e(m,unreal.MaterialExpressionScalarParameter,-470,430);ns.set_editor_properties({"parameter_name":"NormalStrength","default_value":.18});nl=e(m,unreal.MaterialExpressionLinearInterpolate,-260,350);mel.connect_material_expressions(flat,"",nl,"A");mel.connect_material_expressions(normal,"RGB",nl,"B");mel.connect_material_expressions(ns,"",nl,"Alpha");mel.connect_material_property(nl,"",unreal.MaterialProperty.MP_NORMAL)
 orm=e(m,unreal.MaterialExpressionTextureSample,-680,650);orm.set_editor_properties({"texture":unreal.load_asset(ORM),"sampler_type":unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR});mel.connect_material_expressions(uvm,"",orm,"UVs");r=e(m,unreal.MaterialExpressionScalarParameter,-470,740);r.set_editor_properties({"parameter_name":"BaseRoughness","default_value":.74});ri=e(m,unreal.MaterialExpressionScalarParameter,-470,840);ri.set_editor_properties({"parameter_name":"RoughnessVariation","default_value":.18});rl=e(m,unreal.MaterialExpressionLinearInterpolate,-260,700);mel.connect_material_expressions(r,"",rl,"A");mel.connect_material_expressions(orm,"G",rl,"B");mel.connect_material_expressions(ri,"",rl,"Alpha");mel.connect_material_property(rl,"",unreal.MaterialProperty.MP_ROUGHNESS);zero=e(m,unreal.MaterialExpressionConstant,-260,850);zero.set_editor_property("r",0.0);mel.connect_material_property(zero,"",unreal.MaterialProperty.MP_METALLIC);mel.connect_material_property(orm,"R",unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
 mel.recompile_material(m);lib.save_loaded_asset(m,only_if_is_dirty=False);return m
if lib.does_asset_exist(DEST):raise RuntimeError(f"Refusing overwrite {DEST}")
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.new_level_from_template(DEST,BASE):raise RuntimeError("Could not clone v012")
mat=build();source=json.loads(IMPORT.read_text(encoding="utf-8"));recs={i["asset"].rsplit("/",1)[-1].split(".",1)[0]:i for i in source["imported_assets"] if i["family"]=="robot_v002"};rows=[];count=0
for a in actors.get_all_level_actors():
 if not a.get_actor_label().startswith(PREFIX):continue
 c=a.get_component_by_class(unreal.StaticMeshComponent);rec=recs.get(c.static_mesh.get_name());slots=[]
 for i,x in enumerate(rec["opaque_material_assignments"]):
  if "SafetyOchre" in x["slot"] or "SafetyYellow" in x["slot"]:c.set_material(i,mat);slots.append(i);count+=1
 rows.append({"actor":a.get_actor_label(),"safety_slots":slots})
if len(rows)!=28 or count!=13:raise RuntimeError(f"Gate failed {len(rows)} {count}")
if not levels.save_current_level():raise RuntimeError("Save failed")
AUDIT.write_text(json.dumps({"$schema":"line-boss/audit/pr004-aged-dust-v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"AGED_DUST_CANDIDATE_NOT_PROMOTED","lineage":["v006 accepted baseline","v012 paint-chroma proof","v013 condition experiment"],"map":DEST,"modules":len(rows),"safety_slots":count,"material":mat.get_path_name(),"dust":{"orientation":"VertexNormalWS dot world up","mask":"licensed metal texture red channel","amount":.13},"geometry_layout_pivots_modified":False,"visual_gate":"PENDING","promotion_authorized":False},indent=2),encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_AGED_DUST_V013_PASS modules={len(rows)} slots={count}");unreal.SystemLibrary.quit_editor()
