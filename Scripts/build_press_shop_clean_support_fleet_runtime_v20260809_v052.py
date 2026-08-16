"""Install configurable clean-layout support-fleet runtime authority in v049."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE="/Game/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNavFleetFix_v20260809_v049"
MAP="/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetRuntime_v20260809_v056"
OUT=ROOT/"Saved/Audits/PressShopIntegration/clean_support_fleet_runtime_build_v20260809_v056.json"
PROTECTED=ROOT/"Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
before=sha(PROTECTED)
lib=unreal.EditorAssetLibrary; levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if before!=EXPECTED or lib.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError("fresh/protected invariant")
if not levels.new_level_from_template(MAP,SOURCE): raise RuntimeError("map child failed")
identity={"LB_CLEAN_Robot_CR01_01":("LB-CR01-01","LB-CR01"),"LB_CLEAN_Robot_CR01_02":("LB-CR01-02","LB-CR01"),"LB_CLEAN_Robot_MR01_01":("LB-MR01-01","LB-MR01"),"LB_CLEAN_Robot_MR01_02":("LB-MR01-02","LB-MR01")}
configured=[]
for actor in actors.get_all_level_actors():
    if actor.get_class().get_name()=="LBPressShopSupportFleetController": raise RuntimeError("unexpected inherited fleet controller")
    if actor.get_actor_label() in identity:
        unit,variant=identity[actor.get_actor_label()]
        if not actor.configure_identity(unreal.Name(unit),unreal.Name(variant)): raise RuntimeError("identity rejected "+actor.get_actor_label())
        configured.append({"actor":actor.get_actor_label(),"unit_id":unit,"variant_id":variant})
if len(configured)!=4: raise RuntimeError("expected four configured identities")
controller=actors.spawn_actor_from_class(unreal.LBPressShopSupportFleetController,unreal.Vector(0,-3500,20),unreal.Rotator())
controller.set_actor_label("LB_CLEAN_SUPPORT_FLEET_RuntimeAuthority_v056")
controller.set_editor_property("auto_load_campaign_fleet",False)
controller.set_editor_property("use_installed_actor_transforms",True)
controller.set_editor_property("installed_layout_service_aisle_y",-3500.0)
controller.set_editor_property("installed_layout_standby_point",unreal.Vector(0,-3500,0))
controller.tags=[unreal.Name("LB.CleanRebuild.v20260809.v056"),unreal.Name("LB.Runtime.Authority.SupportFleet"),unreal.Name("LB.Asset.NewAuthored")]
if not levels.save_current_level(): raise RuntimeError("save failed")
after=sha(PROTECTED)
if after!=before: raise RuntimeError("protected changed")
map_file=ROOT/"Content/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetRuntime_v20260809_v056.umap"
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"status":"PASS_BUILD__FOUR_EXPLICIT_RUNTIME_IDENTITIES__CLEAN_INSTALLED_TRANSFORM_FLEET_AUTHORITY__PIE_DISPATCH_RETURN_REQUIRED__NOT_PROMOTED","generated_utc":datetime.now(timezone.utc).isoformat(),"source":SOURCE,"map":MAP,"map_sha256":sha(map_file),"controller":controller.get_actor_label(),"configured_identities":configured,"use_installed_actor_transforms":True,"auto_load_campaign_fleet":False,"standby_cm":[0,-3500,0],"meshy_credits_used":0,"protected_v438_before":before,"protected_v438_after":after},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_SUPPORT_FLEET_RUNTIME_V056_PASS")
