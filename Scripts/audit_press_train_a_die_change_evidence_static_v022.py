"""v022 exact-map static audit adapter with service-side evidence lighting."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_installed_service_static_v017.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAInstalledServiceCandidate_v017", "LB_PressTrainADieChangeEvidenceCandidate_v022")
code = code.replace("press_train_a_installed_service_static_v017.json", "press_train_a_die_change_evidence_static_v022.json")
code = code.replace("installed-service-static-v017", "die-change-evidence-static-v022")
code = code.replace("PRESS_TRAIN_A_V017", "PRESS_TRAIN_A_V022")
code = code.replace("LB.Asset.Candidate.v017", "LB.Asset.Candidate.v022")
code = code.replace("v017 candidate tag", "v022 candidate tag")
code = code.replace('"cameras": (len(cameras), 3)', '"cameras": (len(cameras), 4)')
code = code.replace(
    'local_lights = [actor for actor in scope if "LB.Validation.LocalTaskLighting" in tags(actor)]',
    'local_lights = [actor for actor in scope if "LB.Validation.LocalTaskLighting" in tags(actor)]\nservice_rect_lights = [actor for actor in scope if "LB.Validation.DieChangeEvidenceLighting" in tags(actor)]\nservice_point_lights = [actor for actor in scope if "LB.Validation.DieChangeEvidencePointLighting" in tags(actor)]',
)
code = code.replace(
    '"cameras": (len(cameras), 4), "texts": (len(texts), 8),',
    '"cameras": (len(cameras), 4), "service_rect_lights": (len(service_rect_lights), 5), "service_point_lights": (len(service_point_lights), 5), "texts": (len(texts), 8),',
)
exec(compile(code, str(base) + "::v022", "exec"), globals(), globals())
