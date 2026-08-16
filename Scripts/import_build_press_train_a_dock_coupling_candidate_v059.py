"""Build isolated Train A v059 from retained v053 with low-profile coupling v002."""

from pathlib import Path


base = Path(__file__).with_name("import_build_press_train_a_dock_coupling_candidate_v056.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v056", "Candidate_v059")
code = code.replace("evidence_v056", "evidence_v059")
code = code.replace("candidate-v056", "candidate-v059")
code = code.replace("LB.Asset.Candidate.v056", "LB.Asset.Candidate.v059")
code = code.replace("PRESS_TRAIN_A_V056", "PRESS_TRAIN_A_V059")
code = code.replace("V056", "V059").replace("v056", "v059")
code = code.replace("DockCouplingEvidence_v001", "DockCouplingEvidence_v002")
code = code.replace("MANIFEST_v001", "MANIFEST_v002")
code = code.replace("source_audit_v001", "source_audit_v002")
code = code.replace("DockCouplingEngaged_v001", "DockCouplingEngaged_v002")
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
exec(compile(code, str(base) + "::v059", "exec"), globals(), globals())
