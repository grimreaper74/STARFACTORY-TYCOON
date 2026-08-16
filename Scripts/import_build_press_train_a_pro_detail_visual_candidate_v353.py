"""Fresh v343 child using the transform-baked single-mesh v049 visual aggregate."""
from pathlib import Path

base = Path(__file__).with_name("import_build_press_train_a_pro_detail_visual_candidate_v351.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v046/FBX/SM_CA_MW_PressTrainA_ProDetailModular_v046.fbx",
    "SourceAssets/Candidate/PressTrains/TrainA/ProDetailUnrealAggregate_v049/FBX/SM_CA_MW_PressTrainA_ProDetailUnrealAggregate_v049.fbx")
code = code.replace("6482C68BB53068570B2BE46248B5DAB6F227ABA97F983A3C2888D797E5A28106",
                    "4180BB35E3BEC396D2C545037844D6803F7D9BA4BD5F469A7FCD7FFEF003D15A")
code = code.replace("SM_CA_MW_PressTrainA_ProDetailModular_v046", "SM_CA_MW_PressTrainA_ProDetailUnrealAggregate_v049")
code = code.replace("ProDetailVisual_v351", "ProDetailVisual_v353")
code = code.replace("Candidate_v351", "Candidate_v353")
code = code.replace("candidate.v351", "candidate.v353")
code = code.replace("v351", "v353")
code = code.replace("v046 combined visual mesh", "v049 single-mesh visual aggregate")
exec(compile(code, str(base) + "::v353", "exec"), globals(), globals())
