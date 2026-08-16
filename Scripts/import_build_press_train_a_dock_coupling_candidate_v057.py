"""Build isolated Train A v057 directly from retained v053.

This is the technical successor to failed v056. It keeps the warning-clean
v003 endpoints, fits the engaged coupling evidence inside the verified 15 m
train envelope, and uses the established world-placement authority tag.
"""

from pathlib import Path


base = Path(__file__).with_name("import_build_press_train_a_dock_coupling_candidate_v056.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v056", "Candidate_v057")
code = code.replace("evidence_v056", "evidence_v057")
code = code.replace("candidate-v056", "candidate-v057")
code = code.replace("LB.Asset.Candidate.v056", "LB.Asset.Candidate.v057")
code = code.replace("PRESS_TRAIN_A_V056", "PRESS_TRAIN_A_V057")
code = code.replace("V056", "V057").replace("v056", "v057")
code = code.replace(
    'actor.set_actor_transform(cart.get_actor_transform(), False, True)',
    'actor.set_actor_transform(cart.get_actor_transform(), False, True)\n'
    '    fit_location = actor.get_actor_location()\n'
    '    fit_location.x -= 62.1\n'
    '    actor.set_actor_location(fit_location, False, False)',
)
code = code.replace(
    'unreal.Name("LB.Authority.WorldPlacement.TBC_NOT_INVENTED")',
    'unreal.Name("LB.Authority.WorldPlacement.TBCNotInvented")',
)
exec(compile(code, str(base) + "::v057", "exec"), globals(), globals())
