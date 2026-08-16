"""v016 exact-map static audit adapter."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_installed_readability_static_v015.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAInstalledReadabilityCandidate_v015", "LB_PressTrainAProcessLightCandidate_v016")
code = code.replace("press_train_a_installed_readability_static_v015.json", "press_train_a_process_light_static_v016.json")
code = code.replace("installed-readability-static-v015", "process-light-static-v016")
code = code.replace("PRESS_TRAIN_A_V015", "PRESS_TRAIN_A_V016")
code = code.replace("LB.Asset.Candidate.v015", "LB.Asset.Candidate.v016")
code = code.replace("candidate_v015", "candidate_v016")
code = code.replace("v015 candidate tag", "v016 candidate tag")
exec(compile(code, str(base) + "::v016", "exec"), globals(), globals())
