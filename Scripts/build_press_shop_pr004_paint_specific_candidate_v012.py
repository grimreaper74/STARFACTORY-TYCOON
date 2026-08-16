"""Build PR-004 v012 with chroma-faithful paint and exact detail slots only.

The accepted v006 map is the template. Existing non-target material bindings,
geometry, transforms and pivots remain untouched. The paint master deliberately
does not multiply Cairnwell RAL 1023 by a vendor base-colour texture.
"""
from datetime import datetime,timezone
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
BASE="/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
DEST="/Game/LineBoss/Maps/LB_PressShop_PR004PaintSpecificCandidate_v012"
MAT_ROOT="/Game/LineBoss/Stations/Press/PR004/Candidate_v012/PaintSpecificMaterials"
PREFIX="LB_INT_PR004_V009_robot_v002_"
IMPORT=ROOT/"Saved/Audits/pr004_unreal_import_candidate_v003.json"
AUDIT=ROOT/"Saved/Audits/press_shop_pr004_paint_specific_candidate_v012.json"
NORMAL_PATH="/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_Metalbeam01_N.T_Metalbeam01_N"
ORM_PATH="/Game/LineBoss/Vendor/FactoryEnvironment/Textures/T_Metalbeam01_ORM.T_Metalbeam01_ORM"
lib=unreal.EditorAssetLibrary; tools=unreal.AssetToolsHelpers.get_asset_tools(); mel=unreal.MaterialEditingLibrary

def expr(mat,klass,x,y): return mel.create_material_expression(mat,klass,x,y)

def paint_master():
 name="M_LB_PR004_AgedSafetyPaint_Master_v012"; path=f"{MAT_ROOT}/{name}"
 mat=lib.load_asset(path) or tools.create_asset(name,MAT_ROOT,unreal.Material,unreal.MaterialFactoryNew())
 mel.delete_all_material_expressions(mat); mat.set_editor_properties({"two_sided":False,"blend_mode":unreal.BlendMode.BLEND_OPAQUE})
 colour=expr(mat,unreal.MaterialExpressionVectorParameter,-650,-220); colour.set_editor_properties({"parameter_name":"PaintColour","default_value":unreal.LinearColor(0.8879,0.5457,0.0040,1)})
 mel.connect_material_property(colour,"",unreal.MaterialProperty.MP_BASE_COLOR)
 uv=expr(mat,unreal.MaterialExpressionTextureCoordinate,-900,100); scale=expr(mat,unreal.MaterialExpressionScalarParameter,-900,210); scale.set_editor_properties({"parameter_name":"TextureScale","default_value":7.0})
 mul=expr(mat,unreal.MaterialExpressionMultiply,-700,120); mel.connect_material_expressions(uv,"",mul,"A");mel.connect_material_expressions(scale,"",mul,"B")
 normal=expr(mat,unreal.MaterialExpressionTextureSample,-480,80); normal.set_editor_properties({"texture":unreal.load_asset(NORMAL_PATH),"sampler_type":unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL});mel.connect_material_expressions(mul,"",normal,"UVs")
 flat=expr(mat,unreal.MaterialExpressionConstant3Vector,-480,230);flat.set_editor_property("constant",unreal.LinearColor(.5,.5,1,1))
 nstrength=expr(mat,unreal.MaterialExpressionScalarParameter,-480,330);nstrength.set_editor_properties({"parameter_name":"NormalStrength","default_value":.20})
 nlerp=expr(mat,unreal.MaterialExpressionLinearInterpolate,-240,160);mel.connect_material_expressions(flat,"",nlerp,"A");mel.connect_material_expressions(normal,"RGB",nlerp,"B");mel.connect_material_expressions(nstrength,"",nlerp,"Alpha");mel.connect_material_property(nlerp,"",unreal.MaterialProperty.MP_NORMAL)
 orm=expr(mat,unreal.MaterialExpressionTextureSample,-480,500);orm.set_editor_properties({"texture":unreal.load_asset(ORM_PATH),"sampler_type":unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR});mel.connect_material_expressions(mul,"",orm,"UVs")
 rough=expr(mat,unreal.MaterialExpressionScalarParameter,-480,650);rough.set_editor_properties({"parameter_name":"BaseRoughness","default_value":.61})
 rinfluence=expr(mat,unreal.MaterialExpressionScalarParameter,-480,750);rinfluence.set_editor_properties({"parameter_name":"RoughnessVariation","default_value":.28})
 rlerp=expr(mat,unreal.MaterialExpressionLinearInterpolate,-240,570);mel.connect_material_expressions(rough,"",rlerp,"A");mel.connect_material_expressions(orm,"G",rlerp,"B");mel.connect_material_expressions(rinfluence,"",rlerp,"Alpha");mel.connect_material_property(rlerp,"",unreal.MaterialProperty.MP_ROUGHNESS)
 metal=expr(mat,unreal.MaterialExpressionConstant,-240,760);metal.set_editor_property("r",0.0);mel.connect_material_property(metal,"",unreal.MaterialProperty.MP_METALLIC)
 mel.connect_material_property(orm,"R",unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
 mel.recompile_material(mat);lib.save_loaded_asset(mat,only_if_is_dirty=False);return mat

def direct_material(key,colour,roughness,metallic):
 name=f"M_LB_PR004_{key}_Direct_v012";path=f"{MAT_ROOT}/{name}"
 mat=lib.load_asset(path) or tools.create_asset(name,MAT_ROOT,unreal.Material,unreal.MaterialFactoryNew())
 mel.delete_all_material_expressions(mat);mat.set_editor_properties({"two_sided":False,"blend_mode":unreal.BlendMode.BLEND_OPAQUE})
 c=expr(mat,unreal.MaterialExpressionConstant3Vector,-300,-80);c.set_editor_property("constant",unreal.LinearColor(*colour,1));r=expr(mat,unreal.MaterialExpressionConstant,-300,80);r.set_editor_property("r",roughness);m=expr(mat,unreal.MaterialExpressionConstant,-300,160);m.set_editor_property("r",metallic)
 mel.connect_material_property(c,"",unreal.MaterialProperty.MP_BASE_COLOR);mel.connect_material_property(r,"",unreal.MaterialProperty.MP_ROUGHNESS);mel.connect_material_property(m,"",unreal.MaterialProperty.MP_METALLIC)
 mel.recompile_material(mat);lib.save_loaded_asset(mat,only_if_is_dirty=False);return mat

if lib.does_asset_exist(DEST):raise RuntimeError(f"Refusing to overwrite preserved candidate {DEST}")
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.new_level_from_template(DEST,BASE):raise RuntimeError("Could not clone populated v006 map")
paint=paint_master();details={
 "EdgeWear":direct_material("EdgeWear",(.12,.045,.010),.76,.72),
 "GreaseResidue":direct_material("GreaseResidue",(.008,.004,.0015),.24,0.0),
 "HydraulicIDBlue":direct_material("HydraulicIDBlue",(.006,.050,.18),.58,0.0),
 "ServiceLabel":direct_material("ServiceLabel",(.34,.35,.32),.70,0.0),
 "WarningLabel":direct_material("WarningLabel",(.42,.040,.007),.66,0.0),
}
source=json.loads(IMPORT.read_text(encoding="utf-8"));mesh_records={i["asset"].rsplit("/",1)[-1].split(".",1)[0]:i for i in source["imported_assets"] if i["family"]=="robot_v002"}
rows=[];paint_count=0;detail_count=0
for actor in actors.get_all_level_actors():
 if not actor.get_actor_label().startswith(PREFIX):continue
 comp=actor.get_component_by_class(unreal.StaticMeshComponent);rec=mesh_records.get(comp.static_mesh.get_name()) if comp and comp.static_mesh else None
 if rec is None:raise RuntimeError(f"Unaudited robot actor {actor.get_actor_label()}")
 changes=[]
 for index,a in enumerate(rec["opaque_material_assignments"]):
  slot=a["slot"]
  if "SafetyOchre" in slot or "SafetyYellow" in slot:
   comp.set_material(index,paint);changes.append({"index":index,"source_slot":slot,"layer":"SafetyPaint","material":paint.get_path_name()});paint_count+=1
  else:
   key=next((key for key in details if key in slot),None)
   if key:
    comp.set_material(index,details[key]);changes.append({"index":index,"source_slot":slot,"layer":key,"material":details[key].get_path_name()});detail_count+=1
 rows.append({"actor":actor.get_actor_label(),"mesh":comp.static_mesh.get_path_name(),"overrides":changes})
if len(rows)!=28 or paint_count!=13:raise RuntimeError(f"Gate failed modules={len(rows)} safety_slots={paint_count}")

# Wider evidence camera: complete robot, pedestal and immediate process context.
label="LB_AUDIT_PR004_RobotComplete_v012";camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(-6100,-650,900));camera.set_actor_label(label);camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(-4750,-2050,180)),False);camera.camera_component.set_editor_property("field_of_view",52.0)
if not levels.save_current_level():raise RuntimeError("Could not save v012")
payload={"$schema":"line-boss/audit/press-shop-pr004-paint-specific/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PAINT_SPECIFIC_CANDIDATE_NOT_PROMOTED","base_map":BASE,"candidate_map":DEST,"design":{"paint_colour_srgb":"#F2C300","base_colour_path":"direct_parameter_no_vendor_base_colour_multiplication","licensed_inputs":{"normal":NORMAL_PATH,"orm":ORM_PATH},"non_target_v006_materials_preserved":True},"geometry_layout_pivots_modified":False,"robot_module_count":len(rows),"safety_paint_slot_count":paint_count,"authored_detail_slot_count":detail_count,"paint_material":paint.get_path_name(),"detail_materials":{k:v.get_path_name() for k,v in details.items()},"actors":rows,"camera":label,"collision_gate":"OPEN","runtime_gate":"OPEN_NATIVE_TOOLCHAIN_AND_INTERLOCKS","visual_gate":"PENDING_FRESH_FIXED_CAMERA_REVIEW","promotion_authorized":False}
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_PAINT_V012_PASS modules={len(rows)} safety={paint_count} details={detail_count}")
unreal.SystemLibrary.quit_editor()
