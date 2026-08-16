from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetPaint_v20260809_v023'
TARGET='/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetPaintReadable_v20260809_v026'
MAT_DIR='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v026/FloorMaterials'
OUT=ROOT/'Saved/Audits/PressShopIntegration/clean_full_floor_palette_repair_v20260809_v026.json'
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'
EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
before=sha(PROTECTED); assert before==EXPECTED
lib=unreal.EditorAssetLibrary; mel=unreal.MaterialEditingLibrary
tools=unreal.AssetToolsHelpers.get_asset_tools(); levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert not lib.does_asset_exist(TARGET)
assert levels.load_level(SOURCE)
assert lib.duplicate_asset(SOURCE,TARGET)

def make(name, colour, roughness=0.68):
    path=f'{MAT_DIR}/{name}'
    assert not lib.does_asset_exist(path)
    m=tools.create_asset(name,MAT_DIR,unreal.Material,unreal.MaterialFactoryNew())
    base=mel.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-350,0)
    base.set_editor_property('constant',unreal.LinearColor(*colour,1.0))
    rough=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-350,150)
    rough.set_editor_property('r',roughness)
    mel.connect_material_property(base,'',unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(m); lib.save_loaded_asset(m); return m

mats={
 'floor':make('M_LB_PS_SealedFloorMidGrey_v026',(0.255,0.275,0.290),0.74),
 'green':make('M_LB_PS_ProtectedWalkwayGreen_v026',(0.030,0.285,0.105),0.66),
 'yellow':make('M_LB_PS_SafetyYellow_v026',(0.930,0.590,0.010),0.60),
 'blue':make('M_LB_PS_AGVBlue_v026',(0.015,0.230,0.720),0.62),
 'white':make('M_LB_PS_CrossingWhite_v026',(0.920,0.920,0.870),0.64),
 'red':make('M_LB_PS_KeepClearRed_v026',(0.720,0.025,0.018),0.62),
}

counts={k:0 for k in mats}; changed=[]
for actor in actors.get_all_level_actors():
    if not isinstance(actor,unreal.StaticMeshActor): continue
    label=actor.get_actor_label(); tags={str(x) for x in actor.tags}; key=None
    if label=='LB_CLEAN_Floor_220m_x_120m': key='floor'
    elif 'LB.FloorPaint.Walkway' in tags or 'LB.FloorPaint.FixedWalkway' in tags or 'LB.FloorPaint.SupportDockBay' in tags: key='green'
    elif 'LB.FloorPaint.AGVRoute' in tags or 'LB.FloorPaint.AGVHandoff' in tags: key='blue'
    elif 'LB.FloorPaint.PedestrianCrossing' in tags or 'LB.FloorPaint.SupportDockStop' in tags: key='white'
    elif 'LB.FloorPaint.CraneExclusion' in tags or 'LB.FloorPaint.FireKeepClear' in tags: key='red'
    elif ('LB.FloorPaint.SafetyBoundary' in tags or 'LB.FloorPaint.StorageBoundary' in tags or
          'LB.FloorPaint.WalkwayEdge' in tags or 'LB.FloorPaint.FixedSafetyEdge' in tags or
          'LB.FloorPaint.SupportDockEdge' in tags): key='yellow'
    if key:
        actor.static_mesh_component.set_material(0,mats[key]); counts[key]+=1; changed.append(label)

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
map_file=ROOT/'Content/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetPaintReadable_v20260809_v026.umap'
after=sha(PROTECTED); assert after==before
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'status':'PASS_PALETTE_REPAIR__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED','generated_utc':datetime.now(timezone.utc).isoformat(),'source':SOURCE,'map':TARGET,'map_sha256':sha(map_file),'reassigned_counts':counts,'reassigned_actor_count':len(changed),'palette_contract':{'floor':'mid-grey sealed epoxy','walkway':'high-readability green','safety':'Cairnwell yellow','agv':'route blue','crossings':'warm white','keep_clear':'signal red'},'meshy_credits_used':0,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8')
unreal.log('LINE_BOSS_FULL_FLOOR_PALETTE_V026_PASS')
