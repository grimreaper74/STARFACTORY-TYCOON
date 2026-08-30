"""Read-only transform/material record for the selected v001 seed actors."""

import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_seed_transforms_v053.json"
LABELS = (
    "MESHY | S02 Draw / form | reused press asset",
    "MESHY | S03 Trim | reused press asset",
    "MESHY | S04 Pierce | reused press asset",
    "MESHY | S05 Flange / hem | reused press asset",
    "MESHY | S06 Vision / outfeed | reused press asset",
    "MESHY | S01 Coil feeder | coil-free repair",
    "S00 | approved bare master coil",
    "S00 | approved wrapped master coil",
    "ROBOT | S01 | laser tend robot",
    "ROBOT | S02 | draw quality robot",
    "ROBOT | S04 | pierce handling robot",
    "ROBOT | S06 | vision stack robot",
)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
rows = []
for label in LABELS:
    actor = actors.get(label)
    if actor is None:
        rows.append({"label":label, "status":"MISSING"})
        continue
    location, rotation, scale = actor.get_actor_location(), actor.get_actor_rotation(), actor.get_actor_scale3d()
    row = {"label":label, "class":actor.get_class().get_name(), "location_cm":[location.x,location.y,location.z], "rotation":[rotation.pitch,rotation.yaw,rotation.roll], "scale":[scale.x,scale.y,scale.z]}
    if isinstance(actor, unreal.StaticMeshActor):
        component=actor.static_mesh_component
        mesh=component.get_editor_property("static_mesh")
        row["mesh"]=mesh.get_path_name() if mesh else None
        row["materials"]=[component.get_material(index).get_path_name() if component.get_material(index) else None for index in range(component.get_num_materials())]
        row["visible"] = component.is_visible()
    rows.append(row)
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"status":"PASS__READ_ONLY_SEED_ACTOR_TRANSFORM_AUDIT", "actors":rows, "map_saved":False}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_SEED_TRANSFORM_AUDIT_V053_PASS")
