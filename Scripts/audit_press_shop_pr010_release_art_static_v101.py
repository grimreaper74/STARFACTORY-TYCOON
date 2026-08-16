"""v101 exact-map extension of the retained v100 static authority gate."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_shop_pr010_release_art_static_v100.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v100",
    "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v101")
code = code.replace(
    "Saved/Audits/PR010_ReleaseArt_v100/pr010_release_art_static_gate_v100.json",
    "Saved/Audits/PR010_ReleaseArt_v101/pr010_release_art_static_gate_v101.json")
code = code.replace("if len(proxies) != 24:", "if len(proxies) != 28:")
code = code.replace("expected 24 retained collision proxies", "expected 28 retained guard/fascia collision proxies")
injection = '''
v101_carriers = [actor for actor in scope if "LB.PR010.ReleaseArt.CarrierPallet" in {str(tag) for tag in actor.tags}]
v101_stacks = [actor for actor in scope if "LB.PR010.ReleaseArt.LayeredStack" in {str(tag) for tag in actor.tags}]
v101_fascia = [actor for actor in scope if "LB.PR010.ReleaseArt.OpenFascia" in {str(tag) for tag in actor.tags}]
v101_texts = [actor for actor in texts if actor.get_actor_label().startswith("LB_PR010_V101_TEXT_")]
v101_lights = [actor for actor in scope if "LB.PR010.Lighting.v101" in {str(tag) for tag in actor.tags}]
if len(v101_carriers) != 8 or any("CarrierPallet_v101" not in mesh_path(actor) for actor in v101_carriers):
    failures.append("eight v101 detailed carrier pallets not installed")
if len(v101_stacks) != 9 or any("BlankStack_Layered_v101" not in mesh_path(actor) for actor in v101_stacks):
    failures.append("nine v101 layered stacks not installed")
if len(v101_fascia) != 4 or any("FasciaLouvered_v101" not in mesh_path(actor) for actor in v101_fascia):
    failures.append("four v101 open fascia visuals not installed")
if len(v101_texts) != 5:
    failures.append(f"expected five v101 HMI text actors, found {len(v101_texts)}")
if any(abs(abs(actor.get_actor_rotation().yaw) - 180.0) > 0.01 for actor in v101_texts):
    failures.append("v101 HMI text is not camera-facing at 180 degrees")
if len(v101_lights) != 4:
    failures.append(f"expected four corrected v101 task lights, found {len(v101_lights)}")
v101_missing_assets = [name for name in (
    "SM_CA_MW_PR010_CarrierPallet_v101", "SM_CA_MW_PR010_BlankStack_Layered_v101",
    "SM_CA_MW_PR010_FasciaLouvered_v101") if not library.does_asset_exist(f"/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v101/{name}")]
if v101_missing_assets:
    failures.append(f"missing v101 imported assets: {v101_missing_assets}")
'''
code = code.replace("missing_assets = [name for name in (", injection + "\nmissing_assets = [name for name in (")
code = code.replace("pr010-release-art-static-v100", "pr010-release-art-static-v101")
code = code.replace(
    "PASS__PR010_V100_IMPORT_AUTHORITY_DIMENSIONS_OPEN_GUARDS_HMI_BRANDING__RUNTIME_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "PASS__PR010_V101_IMPORT_AUTHORITY_CARRIERS_STACKS_OPEN_GUARDS_FASCIA_HMI_BRANDING__RUNTIME_VISUAL_GATES_REQUIRED__NOT_PROMOTED")
code = code.replace("FAIL__PR010_V100_STATIC__NOT_PROMOTED", "FAIL__PR010_V101_STATIC__NOT_PROMOTED")
exec(compile(code, str(base) + "::v101", "exec"), globals(), globals())
