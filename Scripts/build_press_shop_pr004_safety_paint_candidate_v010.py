"""Restore deterministic safety ochre to integrated PR004 authored body slots."""
from datetime import datetime, timezone
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()); BASE="/Game/LineBoss/Maps/LB_PressShop_PR004AuthoredDetailsCandidate_v009"; DEST="/Game/LineBoss/Maps/LB_PressShop_PR004SafetyPaintCandidate_v010"
MAT_PATH="/Game/LineBoss/Stations/Press/PR004/Candidate_v009/MaterialsAuthoredDetail_v010/M_LB_PR004_AgedSafetyOchre_v010"; PREFIX="LB_INT_PR004_V009_robot_v002_"
lib=unreal.EditorAssetLibrary
if lib.does_asset_exist(DEST): raise RuntimeError("v010 already exists")
if not lib.duplicate_asset(BASE,DEST): raise RuntimeError("duplicate failed")
material=lib.load_asset(MAT_PATH) if lib.does_asset_exist(MAT_PATH) else unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_LB_PR004_AgedSafetyOchre_v010","/Game/LineBoss/Stations/Press/PR004/Candidate_v009/MaterialsAuthoredDetail_v010",unreal.Material,unreal.MaterialFactoryNew())
mel=unreal.MaterialEditingLibrary
mel.delete_all_material_expressions(material)
base=mel.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,-400,-30);base.set_editor_property("constant",unreal.LinearColor(0.52,0.205,0.012,1))
rough=mel.create_material_expression(material,unreal.MaterialExpressionConstant,-400,100);rough.set_editor_property("r",0.58)
metal=mel.create_material_expression(material,unreal.MaterialExpressionConstant,-400,190);metal.set_editor_property("r",0.08)
mel.connect_material_property(base,"",unreal.MaterialProperty.MP_BASE_COLOR);mel.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS);mel.connect_material_property(metal,"",unreal.MaterialProperty.MP_METALLIC);mel.recompile_material(material);lib.save_loaded_asset(material,only_if_is_dirty=False)
source=json.loads((ROOT/"Saved/Audits/pr004_unreal_import_candidate_v003.json").read_text(encoding="utf-8")); records={r["asset"].rsplit("/",1)[-1].split(".",1)[0]:r for r in source["imported_assets"] if r["family"]=="robot_v002"}
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);levels.load_level(DEST);rows=[]
for actor in actors.get_all_level_actors():
    if not actor.get_actor_label().startswith(PREFIX):continue
    c=actor.get_component_by_class(unreal.StaticMeshComponent);record=records[c.static_mesh.get_name()];slots=[]
    for i,a in enumerate(record["opaque_material_assignments"]):
        if "SafetyOchre" in a["slot"] or "SafetyYellow" in a["slot"]:c.set_material(i,material);slots.append(i)
    rows.append({"actor":actor.get_actor_label(),"safety_paint_slots":slots})
levels.save_current_level();out=ROOT/"Saved/Audits/press_shop_pr004_safety_paint_candidate_v010.json";out.write_text(json.dumps({"generated_utc":datetime.now(timezone.utc).isoformat(),"status":"CANDIDATE_NOT_PROMOTED","base_map":BASE,"candidate_map":DEST,"source_geometry_preserved":True,"layout_and_pivots_preserved":True,"material":material.get_path_name(),"painted_slot_count":sum(len(r["safety_paint_slots"]) for r in rows),"actors":rows,"promotion_authorized":False,"visual_gate":"PENDING"},indent=2),encoding="utf-8");unreal.log("LINE_BOSS_PR004_SAFETY_PAINT_V010_PASS");unreal.SystemLibrary.quit_editor()
