"""Isolated Unreal intake for the approved PR002 scanner and user AGV; never touches v438/v791."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
MAP="/Game/LineBoss/Maps/LB_PressShop_PR002_AGV_IsolatedValidation_v853"
DEST_AGV="/Game/LineBoss/Candidates/PressShop/Inbound_v853/AGV_C01"
DEST_SCN="/Game/LineBoss/Candidates/PressShop/Inbound_v853/PR002Scanner"
SRCROOT=Path(r"C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressShop")
AGV_DIR=SRCROOT/r"InboundCoilDelivery\CoilAGV_UserApproved_v20260809_v851\UnrealStaging_v852"
SCN_DIR=SRCROOT/r"PR002\UserScanner_v20260809_v839"
SCN_FBX_DIR=SCN_DIR/"UnrealStaging_v849"
AGV_MAN=AGV_DIR/"AGV_USERAPPROVED_UNREAL_STAGING_MANIFEST_v852.json"
SCN_MAN=SCN_DIR/"PR002_UNREAL_STAGING_MANIFEST_v849.json"
OUT=ROOT/r"Saved\Audits\PressShopIntegration\pr002_agv_isolated_intake_v853.json"
PROTECTED=ROOT/r"Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
before=sha(PROTECTED)
if before!=EXPECTED or unreal.EditorAssetLibrary.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("fresh/protected invariant")

agv=json.loads(AGV_MAN.read_text(encoding="utf-8")); scn=json.loads(SCN_MAN.read_text(encoding="utf-8"))
lib=unreal.EditorAssetLibrary; tools=unreal.AssetToolsHelpers.get_asset_tools()
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")

def import_manifest(manifest, srcdir, dest):
    tasks=[]; expected={}
    for rec in manifest["assets"]:
        src=srcdir/rec["fbx"]
        if not src.is_file(): raise RuntimeError(f"missing staged FBX {src}")
        name=src.stem
        t=unreal.AssetImportTask(); t.set_editor_properties({"filename":str(src),"destination_path":dest,"destination_name":name,"automated":True,"replace_existing":True,"replace_existing_settings":True,"save":True})
        o=unreal.FbxImportUI(); o.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":True,"import_textures":True,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,"automated_import_should_detect_type":False})
        o.static_mesh_import_data.set_editor_properties({"combine_meshes":True,"generate_lightmap_u_vs":True,"auto_generate_collision":False,"import_uniform_scale":100.0})
        t.options=o; tasks.append(t); expected[name]=rec
    tools.import_asset_tasks(tasks); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    result=[]
    for name,rec in expected.items():
        path=f"{dest}/{name}"; mesh=lib.load_asset(path)
        if not isinstance(mesh,unreal.StaticMesh): raise RuntimeError(f"failed import {path}")
        d=mesh.get_bounds().box_extent*2
        result.append({"asset":path,"bounds_cm":[d.x,d.y,d.z],"materials":mesh.get_num_sections(0)})
    return result

agv_assets=import_manifest(agv,AGV_DIR,DEST_AGV)
scn_assets=import_manifest(scn,SCN_FBX_DIR,DEST_SCN)
if not levels.new_level(MAP): raise RuntimeError("could not create isolated map")

def spawn_group(rows, origin, tag, movable=False):
    spawned=[]
    for i,row in enumerate(rows):
        mesh=lib.load_asset(row["asset"])
        a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*origin),unreal.Rotator())
        a.set_actor_label(f"{tag}_{i+1:02d}_{mesh.get_name()}")
        a.static_mesh_component.set_static_mesh(mesh)
        a.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC)
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        a.tags=[unreal.Name("LB.Asset.NewApproved"),unreal.Name("LB.IsolatedValidation.v853"),unreal.Name(tag)]
        spawned.append(a)
    return spawned

spawn_group(scn_assets,(-300.0,0.0,0.0),"LB.PR002.Scanner",False)
spawn_group(agv_assets,(350.0,0.0,0.0),"LB.AGV.C01",True)

# Simple gameplay collision proxies kept separate from high-detail Meshy visuals.
def proxy(label,loc,scale,tag):
    a=actors.spawn_actor_from_class(unreal.BlockingVolume,unreal.Vector(*loc),unreal.Rotator())
    a.set_actor_label(label); a.set_actor_scale3d(unreal.Vector(*scale)); a.tags=[unreal.Name("LB.Collision.Proxy"),unreal.Name(tag)]; return a
proxy("LB_AGV_C01_CollisionProxy",(350,0,37.5),(0.85,1.10,0.375),"LB.AGV.C01")
proxy("LB_PR002_BaseCollisionProxy",(-300,0,25),(1.79,1.85,0.25),"LB.PR002.Scanner")

if not levels.save_current_level(): raise RuntimeError("save failed")
after=sha(PROTECTED)
if after!=before: raise RuntimeError("protected map changed")
map_file=ROOT/r"Content\LineBoss\Maps\LB_PressShop_PR002_AGV_IsolatedValidation_v853.umap"
payload={"status":"PASS_IMPORT_AND_SCALE__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED","generated_utc":datetime.now(timezone.utc).isoformat(),"map":MAP,"map_sha256":sha(map_file),"agv_assets":agv_assets,"scanner_assets":scn_assets,"agv_parts":len(agv_assets),"scanner_parts":len(scn_assets),"agv_expected_envelope_cm":[170,220,75],"protected_v438_before":before,"protected_v438_after":after,"meshy_credits_used":0}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_PR002_AGV_ISOLATED_V853_PASS")
