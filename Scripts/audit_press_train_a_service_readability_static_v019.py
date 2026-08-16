"""v019 exact-map static audit adapter."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_task_fixture_static_v018.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainATaskFixtureCandidate_v018", "LB_PressTrainAServiceReadabilityCandidate_v019")
code = code.replace("press_train_a_task_fixture_static_v018.json", "press_train_a_service_readability_static_v019.json")
code = code.replace("task-fixture-static-v018", "service-readability-static-v019")
code = code.replace("PRESS_TRAIN_A_V018", "PRESS_TRAIN_A_V019")
code = code.replace("LB.Asset.Candidate.v018", "LB.Asset.Candidate.v019")
code = code.replace("v018 candidate tag", "v019 candidate tag")
exec(compile(code, str(base) + "::v019", "exec"), globals(), globals())
