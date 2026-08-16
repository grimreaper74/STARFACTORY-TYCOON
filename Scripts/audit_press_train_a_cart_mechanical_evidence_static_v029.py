"""Exact-map static, branding, cart-pairing and authority gate for Train A v029."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_release_detail_static_v023.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAReleaseDetailCandidate_v023", "LB_PressTrainACartMechanicalEvidenceCandidate_v029")
code = code.replace("press_train_a_release_detail_static_v023.json", "press_train_a_cart_mechanical_evidence_static_v029.json")
code = code.replace("release-detail-static-v023", "cart-mechanical-evidence-static-v029")
code = code.replace("PRESS_TRAIN_A_V023", "PRESS_TRAIN_A_V029")
code = code.replace("LB.Asset.Candidate.v023", "LB.Asset.Candidate.v029")
code = code.replace(
    'release_fixed = [actor for actor in presentation if "LB.PressTrain.Fixed.ReleaseDetail" in tags(actor)]',
    'release_fixed = [actor for actor in presentation if "LB.PressTrain.Fixed.ReleaseDetail" in tags(actor)]\n'
    'exterior = [actor for actor in presentation if "LB.PressTrain.Fixed.ExteriorDetail" in tags(actor)]\n'
    'overhead = [actor for actor in scope if "LB.Validation.ReleaseOverheadLighting" in tags(actor)]')
code = code.replace(
    'release_texts = [actor for actor in texts if "LB.PressTrain.ReleaseDetail.Text" in tags(actor)]',
    'release_texts = [actor for actor in texts if "LB.PressTrain.ReleaseDetail.Text" in tags(actor)]\n'
    'cart_plates = [actor for actor in texts if "LB.PressTrain.ReleaseDetail.CartIdentityPlate" in tags(actor)]')
code = code.replace('"presentation": (len(presentation), 96)', '"presentation": (len(presentation), 110)')
code = code.replace(
    '"installed": (len(installed), 21), "release_fixed": (len(release_fixed), 22),',
    '"installed": (len(installed), 21), "release_fixed": (len(release_fixed), 22), '
    '"exterior": (len(exterior), 14), "overhead": (len(overhead), 4),')
code = code.replace('"cameras": (len(cameras), 4)', '"cameras": (len(cameras), 5)')
code = code.replace('"texts": (len(texts), 20)', '"texts": (len(texts), 13)')
code = code.replace(
    '"release_texts": (len(release_texts), 12)',
    '"release_texts": (len(release_texts), 0), "cart_plates": (len(cart_plates), 5)')
code = code.replace("if len(scope) != 145:", "if len(scope) != 157:")
code = code.replace("expected 145 scoped actors", "expected 157 scoped actors")
code = code.replace(
    'text_values = [str(actor.text_render.get_editor_property("text")) for actor in texts]',
    'text_values = [str(actor.text_render.get_editor_property("text")) for actor in texts]\n'
    'for stage_index in range(2, 7):\n'
    '    stage = f"S{stage_index:02d}"\n'
    '    cart = next((actor for actor in release_carts if actor.get_actor_label() == f"CA_MW_PTA_{stage}_DieCart"), None)\n'
    '    load = next((actor for actor in tooling_loads if actor.get_actor_label() == f"CA_MW_PTA_{stage}_DieCartToolingLoad"), None)\n'
    '    if cart is None or load is None or abs(cart.get_actor_location().z - 120.0) > 0.1 or abs(load.get_actor_location().z - 120.0) > 0.1:\n'
    '        failures.append(f"{stage} cart/tooling corrected ride-height pair missing")')
code = code.replace(
    "missing_assets = [path for path in required_assets if not library.does_asset_exist(path)]",
    'required_assets += [f"/Game/LineBoss/Candidates/PressTrains/Shared/ExteriorDetail_v002/{name}" for name in (\n'
    '    "SM_CA_MW_PT_CrownDriveDress_v002", "SM_CA_MW_PT_ServiceDoorVentPack_v002",\n'
    '    "SM_CA_MW_PT_AccessPlatformLadder_v002", "SM_CA_MW_PT_S01FeederDress_v002",\n'
    '    "SM_CA_MW_PT_S07InspectionStillageDress_v002")]\n'
    'missing_assets = [path for path in required_assets if not library.does_asset_exist(path)]')
exec(compile(code, str(base) + "::v029", "exec"), globals(), globals())
