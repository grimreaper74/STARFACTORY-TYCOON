"""Build a non-destructive layered PR-004 condition candidate from v006."""
from datetime import datetime,timezone
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
BASE="/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
DEST="/Game/LineBoss/Maps/LB_PressShop_PR004LayeredMaterialCandidate_v011"
MAT_ROOT="/Game/LineBoss/Stations/Press/PR004/Candidate_v011/LayeredMaterials"
MASTER="/Game/LineBoss/Stations/Press/PR004/Candidate_v003/MaterialsPBR_v003"
PREFIX="LB_INT_PR004_V009_robot_v002_"
IMPORT=ROOT/"Saved/Audits/pr004_unreal_import_candidate_v003.json"
AUDIT=ROOT/"Saved/Audits/press_shop_pr004_layered_material_candidate_v011.json"

# Linear-space values. Safety paint is derived from Cairnwell #F2C300 rather
# than the orange legacy constant. Authored detail geometry supplies spatially
# meaningful wear/grease/label layers instead of whole-mesh colour noise.
SURFACES={
 "SafetyYellow":("metal",(0.8879,0.5457,0.0040,1),.30,7.0,.64,.34,0.0,.22),
 "CastIron":("metal",(0.028,0.036,0.044,1),.32,6.5,.72,.38,.82,.24),
 "MachinedSteel":("metal",(0.31,0.36,0.41,1),.20,8.0,.34,.24,1.0,.18),
 "MachineDark":("metal",(0.020,0.026,0.031,1),.30,7.5,.70,.34,.58,.22),
 "Rubber":("nonmetal",(0.008,0.010,0.013,1),.10,9.0,.88,.14,0.0,.10),
 "HoseCable":("nonmetal",(0.010,0.014,0.018,1),.12,9.5,.78,.16,0.0,.12),
 "GreaseResidue":("nonmetal",(0.010,0.006,0.002,1),.26,6.0,.25,.30,0.0,.16),
 "ServiceLabel":("nonmetal",(0.36,0.37,0.34,1),.12,4.0,.74,.16,0.0,.08),
 "WarningRed":("metal",(0.57,0.028,0.020,1),.14,6.0,.58,.18,0.0,.12),
 "ReadyGreen":("metal",(0.014,0.070,0.055,1),.12,6.0,.52,.16,0.0,.10),
 "SensorBlue":("metal",(0.020,0.12,0.26,1),.10,7.0,.40,.12,.18,.08),
 "OpaqueSensorLens":("nonmetal",(0.010,0.032,0.055,1),.05,6.0,.24,.06,0.0,.04),
 "EdgeWear":("metal",(0.16,0.070,0.018,1),.40,8.0,.78,.46,.76,.20),
 "HydraulicIDBlue":("nonmetal",(0.010,0.070,0.20,1),.10,7.0,.62,.12,0.0,.06),
 "WarningLabel":("nonmetal",(0.46,0.055,0.010,1),.12,6.0,.72,.14,0.0,.06),
}

def inst(key,spec):
 kind,tint,tex,scale,rough,roughtex,metal,normal=spec
 parent=unreal.load_asset(f"{MASTER}/M_LB_PR004_{'MetalPBR' if kind=='metal' else 'NonmetalPBR'}_Master_v003")
 if parent is None: raise RuntimeError(f"Missing PBR parent {kind}")
 name=f"MI_LB_PR004_Layered_{key}_v011"; path=f"{MAT_ROOT}/{name}"
 mi=unreal.EditorAssetLibrary.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,MAT_ROOT,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
 mi.set_editor_property("parent",parent); mel=unreal.MaterialEditingLibrary
 mel.set_material_instance_vector_parameter_value(mi,"SurfaceTint",unreal.LinearColor(*tint))
 for p,v in (("TextureInfluence",tex),("TextureScale",scale),("BaseRoughness",rough),("RoughTextureInfluence",roughtex),("Metallic",metal),("NormalStrength",normal)):
  mel.set_material_instance_scalar_parameter_value(mi,p,v)
 mel.update_material_instance(mi); unreal.EditorAssetLibrary.save_loaded_asset(mi,only_if_is_dirty=False); return mi

lib=unreal.EditorAssetLibrary; levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(DEST): raise RuntimeError(f"Refusing to overwrite preserved candidate {DEST}")
if not levels.new_level_from_template(DEST,BASE): raise RuntimeError("Could not create populated v011 template clone")
source=json.loads(IMPORT.read_text(encoding="utf-8")); records={i["asset"].rsplit("/",1)[-1].split(".",1)[0]:i for i in source["imported_assets"] if i["family"]=="robot_v002"}
mats={k:inst(k,v) for k,v in SURFACES.items()}; rows=[]
for actor in actors.get_all_level_actors():
 if not actor.get_actor_label().startswith(PREFIX): continue
 comp=actor.get_component_by_class(unreal.StaticMeshComponent); rec=records.get(comp.static_mesh.get_name()) if comp and comp.static_mesh else None
 if rec is None: raise RuntimeError(f"Unaudited robot module {actor.get_actor_label()}")
 changed=[]
 for index,a in enumerate(rec["opaque_material_assignments"]):
  slot=a["slot"]; key=next((d for d in ("EdgeWear","WarningLabel","HydraulicIDBlue","GreaseResidue","ServiceLabel") if d in slot),a["material_key"])
  if key in mats: comp.set_material(index,mats[key]); changed.append({"index":index,"source_slot":slot,"layer":key,"material":mats[key].get_path_name()})
 rows.append({"actor":actor.get_actor_label(),"mesh":comp.static_mesh.get_path_name(),"overrides":changed})
if len(rows)!=28: raise RuntimeError(f"Expected 28 robot modules, found {len(rows)}")
if not levels.save_current_level(): raise RuntimeError("Could not save PR004 v011 candidate")
payload={"$schema":"line-boss/audit/press-shop-pr004-layered-material-v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"LAYERED_MATERIAL_CANDIDATE_NOT_PROMOTED","base_map":BASE,"candidate_map":DEST,"authority":{"brand":"Docs/BRAND_IDENTITY_AUTHORITY.md","safety_yellow_srgb":"#F2C300","condition":"seven-year mothballed with selective serviced witnesses"},"rejected_candidates_not_promoted":["v007","v008","v009","v010"],"geometry_layout_pivots_modified":False,"robot_module_count":len(rows),"material_override_count":sum(len(r["overrides"]) for r in rows),"materials":{k:v.get_path_name() for k,v in mats.items()},"actors":rows,"collision_gate":"OPEN_COMPLEX_AS_SIMPLE_NOT_RELEASE_ACCEPTABLE","runtime_motion_interlock_gate":"OPEN","visual_gate":"PENDING_FRESH_FIXED_CAMERA_REVIEW","promotion_authorized":False}
AUDIT.parent.mkdir(parents=True,exist_ok=True); AUDIT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_LAYERED_V011_PASS actors={len(rows)} overrides={payload['material_override_count']}")
unreal.SystemLibrary.quit_editor()
