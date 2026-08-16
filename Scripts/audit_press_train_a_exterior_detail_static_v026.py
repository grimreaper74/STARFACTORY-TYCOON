"""Exact-map static audit adapter for exterior-detail v026."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_release_detail_static_v023.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAReleaseDetailCandidate_v023", "LB_PressTrainAExteriorDetailCandidate_v026")
code = code.replace("press_train_a_release_detail_static_v023.json", "press_train_a_exterior_detail_static_v026.json")
code = code.replace("release-detail-static-v023", "exterior-detail-static-v026")
code = code.replace("PRESS_TRAIN_A_V023", "PRESS_TRAIN_A_V026")
code = code.replace("LB.Asset.Candidate.v023", "LB.Asset.Candidate.v026")
code = code.replace(
    'release_fixed = [actor for actor in presentation if "LB.PressTrain.Fixed.ReleaseDetail" in tags(actor)]',
    'release_fixed = [actor for actor in presentation if "LB.PressTrain.Fixed.ReleaseDetail" in tags(actor)]\nexterior = [actor for actor in presentation if "LB.PressTrain.Fixed.ExteriorDetail" in tags(actor)]')
code = code.replace('"presentation": (len(presentation), 96)', '"presentation": (len(presentation), 110)')
code = code.replace(
    '"installed": (len(installed), 21), "release_fixed": (len(release_fixed), 22),',
    '"installed": (len(installed), 21), "release_fixed": (len(release_fixed), 22), "exterior": (len(exterior), 14),')
code = code.replace('"texts": (len(texts), 20)', '"texts": (len(texts), 8)')
code = code.replace('"release_texts": (len(release_texts), 12)', '"release_texts": (len(release_texts), 0)')
code = code.replace("if len(scope) != 145:", "if len(scope) != 147:")
code = code.replace("expected 145 scoped actors", "expected 147 scoped actors")
code = code.replace(
    "missing_assets = [path for path in required_assets if not library.does_asset_exist(path)]",
    'required_assets += [f"/Game/LineBoss/Candidates/PressTrains/Shared/ExteriorDetail_v002/{name}" for name in (\n'
    '    "SM_CA_MW_PT_CrownDriveDress_v002", "SM_CA_MW_PT_ServiceDoorVentPack_v002",\n'
    '    "SM_CA_MW_PT_AccessPlatformLadder_v002", "SM_CA_MW_PT_S01FeederDress_v002",\n'
    '    "SM_CA_MW_PT_S07InspectionStillageDress_v002")]\n'
    'missing_assets = [path for path in required_assets if not library.does_asset_exist(path)]')
exec(compile(code, str(base) + "::v026", "exec"), globals(), globals())
