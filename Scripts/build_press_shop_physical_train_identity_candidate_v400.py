"""Fresh direct-v386 physical identity successor correcting v398 visual failures."""

import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
BASE="/Game/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386"
BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386.umap"
BASE_SHA="057F2D9F382EB34DAC7E8727E3E58FEA4194C99E16F339F016116533B8377038"
MAP="/Game/LineBoss/Maps/LB_PressShop_PhysicalTrainIdentityCorrectedCandidate_v400"
MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_PhysicalTrainIdentityCorrectedCandidate_v400.umap"
DEST="/Game/LineBoss/Candidates/PressShop/TrainIdentity/PhysicalSigns_v397"
MATROOT="/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials"
OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_physical_train_identity_corrected_build_v400.json"
ROWS={"A":-4300.0,"B":-2100.0,"C":100.0,"D":2300.0}

def sha(path):
 d=hashlib.sha256()
 with path.open("rb") as stream:
  for chunk in iter(lambda:stream.read(1048576),b""):d.update(chunk)
 return d.hexdigest().upper()

lib=unreal.EditorAssetLibrary
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha(BASE_FILE)!=BASE_SHA:raise RuntimeError("protected v386 base drift")
if lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("refusing to overwrite v400")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("fresh direct-v386 child failed")

materials=[
 lib.load_asset(MATROOT+"/M_CA_MW_PR009_LayeredCairnwellGreen_v086"),
 lib.load_asset(MATROOT+"/M_CA_MW_PR009_LayeredFoundryCharcoal_v086"),
 lib.load_asset(MATROOT+"/M_CA_MW_PR009_LayeredSafetyYellow_v086"),
 lib.load_asset(MATROOT+"/M_CA_MW_PR009_LabelWhite_v086"),
]
if not all(isinstance(m,unreal.MaterialInterface) for m in materials):raise RuntimeError("retained PBR sign materials missing")

added=[]
for train,y in ROWS.items():
 asset=f"{DEST}/SM_CA_MW_PressTrainIdentity_{train}_v396"
 mesh=lib.load_asset(asset)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(f"missing {asset}")
 label=f"LB_V400_PRESS_TRAIN_{train}_PHYSICAL_IDENTITY_WEST"
 actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(1115.0,y,850.0),unreal.Rotator(yaw=180.0))
 if actor is None:raise RuntimeError(label)
 actor.set_actor_label(label);actor.static_mesh_component.set_static_mesh(mesh);actor.set_actor_scale3d(unreal.Vector(100,100,100))
 comp=actor.static_mesh_component
 for index,material in enumerate(materials):comp.set_material(index,material)
 comp.set_collision_profile_name("NoCollision");comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
 comp.set_editor_property("generate_overlap_events",False);comp.set_editor_property("can_ever_affect_navigation",False)
 actor.tags=[unreal.Name(v) for v in (f"LB.PressTrain.Identity.Train{train}",f"LB.PressTrain.DisplayDesignation.{train}","LB.PressTrain.Identity.AllocatedAutomatically","LB.PressTrain.Stations.S01-S07","LB.FactoryBuilder.ReusableModule","LB.Identity.PhysicalMesh","LB.Identity.VisualOnly.NoRuntimeAuthority","LB.Collision.NoCollision.VisualOnly","LB.Navigation.None","LB.Asset.Candidate.v400","LB.Asset.CandidateNotPromoted")]
 origin,extent=actor.get_actor_bounds(False)
 added.append({"label":label,"train":train,"asset":asset,"location_cm":[1115.0,y,850.0],"rotation_yaw":180.0,"world_size_cm":[extent.x*2,extent.y*2,extent.z*2],"material_assets":[m.get_path_name() for m in materials]})

counts={k:sum(1 for a in actors.get_all_level_actors() if f"LB.PressTrain.Installed.TRAIN_{k}" in {str(t) for t in a.tags}) for k in "ABCD"}
fail=[]
if len(added)!=4:fail.append(f"sign count {len(added)}")
if counts!={"A":338,"B":338,"C":338,"D":338}:fail.append(f"train counts {counts}")
if not levels.save_current_level():fail.append("save failed")
if sha(BASE_FILE)!=BASE_SHA:fail.append("protected v386 changed")
payload={"$schema":"cairnwell/audit/press-shop-physical-train-identity-corrected-build-v400/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__V398_BACKFACE_AND_MATERIAL_FAILURES_CORRECTED__FRESH_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__V400_NOT_A_PARENT","base":BASE,"base_sha256":BASE_SHA,"map":MAP,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"v398_status":"VISUALLY_REJECTED__NEVER_PARENT","corrections":["180 degree physical mesh orientation correction","explicit retained semantic PBR material overrides"],"added_physical_identity":added,"train_actor_counts":counts,"factory_builder_contract":{"automatic_designation":"A..Z stable allocation","station_ids":"<designation>-S01..S07","persistent_guid":"required","runtime_allocator":"OPEN_NOT_CLAIMED"},"promotion_authorized":False,"failures":fail}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8");print(json.dumps(payload,indent=2))
if fail:raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
