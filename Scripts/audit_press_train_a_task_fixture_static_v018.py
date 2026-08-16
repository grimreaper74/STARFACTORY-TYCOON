"""v018 exact-map static audit adapter."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_installed_service_static_v017.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAInstalledServiceCandidate_v017", "LB_PressTrainATaskFixtureCandidate_v018")
code = code.replace("press_train_a_installed_service_static_v017.json", "press_train_a_task_fixture_static_v018.json")
code = code.replace("installed-service-static-v017", "task-fixture-static-v018")
code = code.replace("PRESS_TRAIN_A_V017", "PRESS_TRAIN_A_V018")
code = code.replace("LB.Asset.Candidate.v017", "LB.Asset.Candidate.v018")
code = code.replace("v017 candidate tag", "v018 candidate tag")
exec(compile(code, str(base) + "::v018", "exec"), globals(), globals())
