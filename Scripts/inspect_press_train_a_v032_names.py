import bpy
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v032/CA_MW_PressTrainA_ModularAssembly_v032.blend"
bpy.ops.wm.open_mainfile(filepath=str(src))
for obj in bpy.data.objects:
    name = obj.name.lower()
    if any(token in name for token in ("identity", "badge", "label", "s03", "cairnwell")):
        print(obj.name, obj.type, tuple(round(v, 3) for v in obj.location), obj.get("station_id"), obj.get("assembly_role"))
