import bpy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
blend = root / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v013/CA_MW_PressTrainA_AssemblyStudy_v013.blend"
bpy.ops.wm.open_mainfile(filepath=str(blend))
collection = bpy.data.collections["TRAIN_A_ASSEMBLY"]
roles = {
    "heavy_press_frame", "operator_side_enclosure", "moving_press_slide",
    "fixed_press_bolster", "stage_specific_exterior_mechanics",
    "draw_hydraulic_accumulator", "draw_hydraulic_feed", "frame_service_fixing"
}
rows = []
for obj in collection.all_objects:
    if obj.type != "MESH" or obj.get("role") not in roles:
        continue
    rows.append({
        "name": obj.name,
        "stage": obj.get("stage"),
        "role": obj.get("role"),
        "location_m": [round(float(x), 4) for x in obj.location],
        "dimensions_m": [round(float(x), 4) for x in obj.dimensions],
        "rotation_rad": [round(float(x), 5) for x in obj.rotation_euler],
        "collision_intent": obj.get("collision_intent"),
    })
print("LB_V014_INVENTORY_BEGIN")
print(json.dumps(sorted(rows, key=lambda x: (str(x["stage"]), x["role"], x["name"])), indent=2))
print("LB_V014_INVENTORY_END")
