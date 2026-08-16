"""Isolated embedded-GLB PBR intake for corrected PR009 and PR010."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();MAP='/Game/LineBoss/Maps/LB_PressShop_PR009_PR010_OriginalGLB_Isolated_v881';DEST='/Game/LineBoss/Candidates/PressShop/PR009_PR010_OriginalGLB_v881';SRC=Path(r'C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressShop')
FILES={'PR009':SRC/r'PR009\UserMeshy_v20260809_v859\UnrealStaging_OriginalGLB_v880\SM_CA_MW_PR009_OriginalHighPoly_v880.glb','PR010':SRC/r'PR010\UserMeshy_v20260809_v860\UnrealStaging_OriginalGLB_v880\SM_CA_MW_PR010_OriginalHighPoly_v880.glb'}
OUT=ROOT/r'Saved\Audits\PressShopIntegration\pr009_pr010_original_glb_isolated_intake_v881.json';P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or unreal.EditorAssetLibrary.does_asset_exist(MAP) or OUT.exists():raise RuntimeError('fresh/protected invariant')
lib=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);rows={}
for station,src in FILES.items():
 folder=f'{DEST}/{station}';task=unreal.AssetImportTask();task.set_editor_properties({'filename':str(src),'destination_path':folder,'automated':True,'replace_existing':True,'replace_existing_settings':True,'save':True});tools.import_asset_tasks([task]);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
 paths=list(task.get_editor_property('imported_object_paths'));assets=[lib.load_asset(p) for p in paths];meshes=[a for a in assets if isinstance(a,unreal.StaticMesh)]
 if len(meshes)!=1:raise RuntimeError(f'{station} expected one mesh, imported {paths}')
 mesh=meshes[0];d=mesh.get_bounds().box_extent*2;target={'PR009':[520,760,425],'PR010':[1400,840,360]}[station];delta=max(abs(v-e) for v,e in zip((d.x,d.y,d.z),target));rows[station]={'source':str(src),'imported_paths':paths,'mesh':mesh.get_path_name(),'bounds_cm':[d.x,d.y,d.z],'target_cm':target,'bounds_pass':delta<2.0,'material_slots':mesh.get_num_sections(0)}
 if delta>=2.0:raise RuntimeError(f'{station} bounds {rows[station]}')
if not levels.new_level(MAP):raise RuntimeError('map create')
for station,loc in {'PR009':(-650,0,0),'PR010':(650,0,0)}.items():
 mesh=lib.load_asset(rows[station]['mesh']);a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(f'LB_{station}_EmbeddedGLB_Visual_v876');a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);a.tags=[unreal.Name(f'LB.Station.{station}'),unreal.Name('LB.Asset.NewApproved'),unreal.Name('LB.IsolatedValidation.v876'),unreal.Name('LB.Material.EmbeddedGLB')]
if not levels.save_current_level():raise RuntimeError('save')
after=sha(P)
if after!=before:raise RuntimeError('protected changed')
mapfile=ROOT/r'Content\LineBoss\Maps\LB_PressShop_PR009_PR010_OriginalGLB_Isolated_v881.umap';payload={'status':'PASS_ORIGINAL_GLB_IMPORT_AND_BOUNDS__PBR_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'map':MAP,'map_sha256':sha(mapfile),'records':rows,'protected_v438_before':before,'protected_v438_after':after,'meshy_credits_used':0};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');unreal.log('LINE_BOSS_PR009_PR010_ORIGINAL_GLB_V881_PASS')
