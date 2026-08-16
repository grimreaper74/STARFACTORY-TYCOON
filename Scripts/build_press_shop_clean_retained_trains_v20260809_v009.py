"""Install only tagged retained complete Train A-D actors into a fresh clean-map child.

The rejected whole-shop maps are never opened.  Each isolated train donor is read into
plain records, then reconstructed on the approved clean inbound/storage parent.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundStorageFit_v20260809_v005"
TARGET = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundRetainedTrains_v20260809_v011"
OUT = ROOT / "Saved/Audits/PressShopIntegration/clean_retained_trains_build_v20260809_v011.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
DONORS = {
    "A": "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeP0_v694",
    "B": "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainB_CompleteVariant_v696",
    "C": "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainC_CompleteVariant_v696",
    "D": "/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainD_CompleteVariant_v696",
}
# Rows preserve the fixed perimeter walkway.  Donor +Y is process flow; yaw -90 maps it to world +X.
DATUMS = {"A": (4000.0, -3300.0, 95.0), "B": (4000.0, -1100.0, 95.0),
          "C": (4000.0, 1100.0, 95.0), "D": (4000.0, 3300.0, 95.0)}
SPECS = {
    "A": ("SMOT / SMOTR / ROOF OUTER", (0.235, 0.455, 0.620)),
    "B": ("FLOORS / UNDERBODY", (0.302, 0.545, 0.290)),
    "C": ("CLOSURES", (0.784, 0.482, 0.176)),
    "D": ("REINFORCEMENTS / SMALL PANELS", (0.459, 0.341, 0.749)),
}

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
before = sha(PROTECTED)
if before != EXPECTED or lib.does_asset_exist(TARGET) or OUT.exists():
    raise RuntimeError("fresh/protected invariant failed")

records = {}
for letter, donor in DONORS.items():
    if not levels.load_level(donor): raise RuntimeError(f"Could not load {donor}")
    scope = f"LB.PressTrain.Installed.TRAIN_{letter}"
    members = [a for a in api.get_all_level_actors() if scope in {str(t) for t in a.tags}]
    statics = []
    authority = [a for a in members if isinstance(a, unreal.LBPressTrainAStation)]
    for actor in members:
        if isinstance(actor, unreal.LBPressTrainAStation): continue
        if not isinstance(actor, unreal.StaticMeshActor):
            raise RuntimeError(f"Unexpected installed actor class {actor.get_class().get_path_name()}")
        comp = actor.static_mesh_component
        mesh = comp.get_editor_property("static_mesh")
        if not mesh: raise RuntimeError(f"Missing mesh on {actor.get_actor_label()}")
        mats=[]
        for i in range(comp.get_num_materials()):
            mat=comp.get_material(i); mats.append(mat.get_path_name() if mat else None)
        loc=actor.get_actor_location(); rot=actor.get_actor_rotation(); scale=actor.get_actor_scale3d()
        statics.append({"label":actor.get_actor_label(),"tags":[str(t) for t in actor.tags],
                        "loc":[loc.x,loc.y,loc.z],"rot":[rot.pitch,rot.yaw,rot.roll],
                        "scale":[scale.x,scale.y,scale.z],"mesh":mesh.get_path_name(),"materials":mats,
                        "collision":str(comp.get_collision_enabled()),
                        "nav":bool(comp.get_editor_property("can_ever_affect_navigation"))})
    if len(members)!=182 or len(statics)!=181 or len(authority)!=1:
        raise RuntimeError(f"Train {letter} donor scope invalid: {len(members)}/{len(statics)}/{len(authority)}")
    records[letter]=statics

if not levels.new_level_from_template(TARGET, SOURCE): raise RuntimeError("Could not create clean child")
reports={}
for letter in "ABCD":
    dx,dy,dz=DATUMS[letter]
    spawned=[]
    for row in records[letter]:
        x,y,z=row["loc"]
        # yaw -90: local +Y -> world +X, local +X -> world -Y.
        world=unreal.Vector(dx+y, dy-x, dz+z)
        p,yaw,r=row["rot"]
        actor=api.spawn_actor_from_class(unreal.StaticMeshActor,world,unreal.Rotator(pitch=p,yaw=yaw-90.0,roll=r))
        actor.set_actor_label(f"CLEAN_{letter}_{row['label']}")
        actor.tags=[unreal.Name(t) for t in row["tags"]]+[unreal.Name("LB.CleanRebuild.RetainedTrain.v20260809.v009")]
        actor.set_actor_scale3d(unreal.Vector(*row["scale"]))
        comp=actor.static_mesh_component; comp.set_static_mesh(lib.load_asset(row["mesh"]))
        for i,path in enumerate(row["materials"]):
            if path: comp.set_material(i,lib.load_asset(path))
        comp.set_editor_property("can_ever_affect_navigation",row["nav"])
        spawned.append(actor)
    family,colour=SPECS[letter]
    auth=api.spawn_actor_from_class(unreal.LBPressTrainAStation,unreal.Vector(dx,dy,dz),unreal.Rotator(pitch=0,yaw=-90,roll=0))
    auth.set_actor_label(f"CLEAN_CA_MW_PressTrain{letter}_Authority_v009")
    auth.tags=[unreal.Name(f"LB.PressTrain.Installed.TRAIN_{letter}"),unreal.Name("LB.CleanRebuild.RetainedTrain.v20260809.v009")]
    if not auth.configure_train_variant(unreal.Name(f"TRAIN_{letter}"),f"TRAIN {letter}",family,unreal.LinearColor(*colour,1.0)):
        raise RuntimeError(f"Train {letter} authority configuration failed")
    spawned.append(auth)
    # Validate physical presentation envelope only.  The native authority deliberately
    # owns a large invisible protected placement envelope and must not be counted as art.
    lo=[float("inf")]*3; hi=[float("-inf")]*3
    for actor in spawned[:-1]:
        o,e=actor.get_actor_bounds(False,False)
        for i,(v,d) in enumerate(zip(o.to_tuple(),e.to_tuple())):
            lo[i]=min(lo[i],v-d); hi[i]=max(hi[i],v+d)
    reports[letter]={"datum_cm":DATUMS[letter],"yaw_deg":-90,"installed_actor_count":len(spawned),
                     "bounds_min_cm":lo,"bounds_max_cm":hi,"process_flow":"S01_WEST_TO_S07_EAST__LOCAL_POSITIVE_Y_TO_WORLD_POSITIVE_X"}
    if len(spawned)!=182 or lo[0] < -11000 or hi[0] > 11000 or lo[1] < -4425 or hi[1] > 4425 or lo[2] < -2:
        raise RuntimeError(f"Train {letter} envelope failed: {reports[letter]}")

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level(): raise RuntimeError("Could not save target")
after=sha(PROTECTED)
if after!=before: raise RuntimeError("Protected map changed")
map_file=ROOT/"Content/LineBoss/Maps/LB_PressShop_CleanInboundRetainedTrains_v20260809_v011.umap"
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"$schema":"cairnwell/audit/clean-retained-trains-v009/v1",
    "generated_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS__FRESH_CLEAN_CHILD__ONLY_TAGGED_RETAINED_TRAINS_A_D__VISUAL_REVIEW_PENDING",
    "source_clean_map":SOURCE,"target":TARGET,"donors":DONORS,"reports":reports,
    "installed_total":sum(v["installed_actor_count"] for v in reports.values()),
    "rejected_whole_shop_maps_opened":False,"meshy_credits_used":0,"map_sha256":sha(map_file),
    "protected_v438_before":before,"protected_v438_after":after,"promotion_authorized":False},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_RETAINED_TRAINS_V011_PASS")
unreal.SystemLibrary.quit_editor()
