"""Balanced-lighting successor of v002; never overwrite prior evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();SRC="/Game/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v002";MAP="/Game/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v003";OUT=ROOT/"Saved/Audits/PressShopIntegration/clean_shell_lighting_build_v20260809_v003.json";P=ROOT/"Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap";E="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("fresh/protected invariant")
if not levels.new_level_from_template(MAP,SRC):raise RuntimeError("copy failed")
rc=0
for a in actors.get_all_level_actors():
 c=a.get_component_by_class(unreal.RectLightComponent)
 if c:c.set_editor_property("intensity",18000.0);rc+=1
 s=a.get_component_by_class(unreal.SkyLightComponent)
 if s:s.set_editor_property("intensity",0.60)
 d=a.get_component_by_class(unreal.DirectionalLightComponent)
 if d:d.set_editor_property("intensity",0.30)
if not levels.save_current_level():raise RuntimeError("save")
after=sha(P)
if after!=before:raise RuntimeError("protected changed")
mf=ROOT/"Content/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v003.umap";OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"$schema":"cairnwell/audit/clean-shell-lighting-v3","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__BALANCED_LIGHTING_BUILD__VISUAL_REVIEW_REQUIRED","source":SRC,"map":MAP,"map_sha256":sha(mf),"rect_lights":rc,"rect_intensity":18000.0,"skylight":0.6,"directional":0.3,"protected_v438_before":before,"protected_v438_after":after,"production_actor_count":0},indent=2),encoding="utf-8");unreal.log("LINE_BOSS_CLEAN_SHELL_LIGHTING_V003_PASS")
