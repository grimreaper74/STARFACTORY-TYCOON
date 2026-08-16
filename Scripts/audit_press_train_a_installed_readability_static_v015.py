"""v015 exact-map static audit adapter."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_cctv_material_static_v014.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACCTVMaterialCandidate_v014", "LB_PressTrainAInstalledReadabilityCandidate_v015")
code = code.replace("press_train_a_cctv_material_static_v014.json", "press_train_a_installed_readability_static_v015.json")
code = code.replace("cctv-material-static-v014", "installed-readability-static-v015")
code = code.replace("PRESS_TRAIN_A_V014", "PRESS_TRAIN_A_V015")
code = code.replace("LB.Asset.Candidate.v014", "LB.Asset.Candidate.v015")
code = code.replace("candidate_v014", "candidate_v015")
code = code.replace("v014 candidate tag", "v015 candidate tag")
exec(compile(code, str(base) + "::v015", "exec"), globals(), globals())
