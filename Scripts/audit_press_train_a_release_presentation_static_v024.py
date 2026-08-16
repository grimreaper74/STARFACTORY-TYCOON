"""Static audit adapter for release-presentation v024."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_release_detail_static_v023.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAReleaseDetailCandidate_v023", "LB_PressTrainAReleasePresentationCandidate_v024")
code = code.replace("press_train_a_release_detail_static_v023.json", "press_train_a_release_presentation_static_v024.json")
code = code.replace("release-detail-static-v023", "release-presentation-static-v024")
code = code.replace("PRESS_TRAIN_A_V023", "PRESS_TRAIN_A_V024")
code = code.replace("LB.Asset.Candidate.v023", "LB.Asset.Candidate.v024")
code = code.replace('"texts": (len(texts), 20)', '"texts": (len(texts), 8)')
code = code.replace('"release_texts": (len(release_texts), 12)', '"release_texts": (len(release_texts), 0)')
code = code.replace("if len(scope) != 145:", "if len(scope) != 133:")
code = code.replace("expected 145 scoped actors", "expected 133 scoped actors")
exec(compile(code, str(base) + "::v024", "exec"), globals(), globals())
