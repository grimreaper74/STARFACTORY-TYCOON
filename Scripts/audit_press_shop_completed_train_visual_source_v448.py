"""Read-only audit of the accepted completed train aggregate and installed material overrides in v438."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
MESH_PATH = "/Game/LineBoss/Candidates/PressTrains/TrainA/ProDetailVisual_v354/SM_CA_MW_PressTrainA_ProDetailUnrealAggregate_v049"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_completed_train_visual_source_v448.json"

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
matches = []
for actor in api.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    comp = actor.static_mesh_component
    mesh = comp.static_mesh
    if mesh and mesh.get_path_name().split(".", 1)[0] == MESH_PATH:
        origin, extent = actor.get_actor_bounds(False)
        matches.append({
            "label": actor.get_actor_label(),
            "location": list(actor.get_actor_location().to_tuple()),
            "rotation": str(actor.get_actor_rotation()),
            "scale": list(actor.get_actor_scale3d().to_tuple()),
            "bounds_origin": list(origin.to_tuple()),
            "bounds_extent": list(extent.to_tuple()),
            "materials": [
                comp.get_material(i).get_path_name() if comp.get_material(i) else None
                for i in range(comp.get_num_materials())
            ],
            "tags": [str(t) for t in actor.tags],
        })

payload = {"map": MAP, "map_saved": False, "mesh": MESH_PATH, "count": len(matches), "instances": matches}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
