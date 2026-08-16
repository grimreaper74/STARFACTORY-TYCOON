"""v021 exact-map static audit adapter with five evidence lights."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_installed_service_static_v017.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAInstalledServiceCandidate_v017", "LB_PressTrainAServiceEvidenceCandidate_v021")
code = code.replace("press_train_a_installed_service_static_v017.json", "press_train_a_service_evidence_static_v021.json")
code = code.replace("installed-service-static-v017", "service-evidence-static-v021")
code = code.replace("PRESS_TRAIN_A_V017", "PRESS_TRAIN_A_V021")
code = code.replace("LB.Asset.Candidate.v017", "LB.Asset.Candidate.v021")
code = code.replace("v017 candidate tag", "v021 candidate tag")
code = code.replace('"cameras": (len(cameras), 3)', '"cameras": (len(cameras), 4)')
code = code.replace(
    'local_lights = [actor for actor in scope if "LB.Validation.LocalTaskLighting" in tags(actor)]',
    'local_lights = [actor for actor in scope if "LB.Validation.LocalTaskLighting" in tags(actor)]\nservice_lights = [actor for actor in scope if "LB.Validation.DieChangeEvidenceLighting" in tags(actor)]',
)
code = code.replace(
    '"cameras": (len(cameras), 4), "texts": (len(texts), 8),',
    '"cameras": (len(cameras), 4), "service_lights": (len(service_lights), 5), "texts": (len(texts), 8),',
)
exec(compile(code, str(base) + "::v021", "exec"), globals(), globals())
