"""Create a non-overwriting readable-lighting successor of clean shell v001."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();SRC="/Game/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v001";MAP="/Game/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v002"
OUT=ROOT/"Saved/Audits/PressShopIntegration/clean_shell_lighting_build_v20260809_v002.json";PROTECTED=ROOT/"Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap";EXPECTED="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
before=sha(PROTECTED)
if before!=EXPECTED or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("fresh/protected invariant")
if not levels.new_level_from_template(MAP,SRC):raise RuntimeError("copy failed")
cube=unreal.load_asset("/Engine/BasicShapes/Cube.Cube");white=unreal.load_asset("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v001/Materials/M_LB_CleanShell_WarmWhite_v001")
roof=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,1675),unreal.Rotator());roof.set_actor_label("LB_CLEAN_RoofLiner_v002");roof.tags=[unreal.Name("LB.CleanShell.v20260809.v002"),unreal.Name("LB.Asset.NewAuthored"),unreal.Name("LB.Environment.RoofLiner")]
roof.static_mesh_component.set_static_mesh(cube);roof.static_mesh_component.set_world_scale3d(unreal.Vector(220,120,.5));roof.static_mesh_component.set_material(0,white);roof.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS);roof.static_mesh_component.set_editor_property("can_ever_affect_navigation",False)
rect_count=0
for a in actors.get_all_level_actors():
 c=a.get_component_by_class(unreal.RectLightComponent)
 if c:
  c.set_editor_properties({"intensity":75000.0,"source_width":1000.0,"source_height":220.0});rect_count+=1
 s=a.get_component_by_class(unreal.SkyLightComponent)
 if s:s.set_editor_property("intensity",1.25)
 d=a.get_component_by_class(unreal.DirectionalLightComponent)
 if d:d.set_editor_property("intensity",1.0)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError("save failed")
after=sha(PROTECTED)
if after!=before:raise RuntimeError("protected changed")
mf=ROOT/"Content/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v002.umap"
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"$schema":"cairnwell/audit/clean-shell-lighting-v2","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__NONOVERWRITING_ROOF_LINER_AND_HIGH_BAY_LIGHTING__VISUAL_REVIEW_REQUIRED","source":SRC,"map":MAP,"map_sha256":sha(mf),"rect_lights":rect_count,"rect_intensity":75000.0,"roof_liner":True,"protected_v438_before":before,"protected_v438_after":after,"production_actor_count":0},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_SHELL_LIGHTING_V002_PASS")
