"""v102 exact-map extension of the retained v100/v101 static authority gates."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_shop_pr010_release_art_static_v100.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v100",
    "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v102")
code = code.replace(
    "Saved/Audits/PR010_ReleaseArt_v100/pr010_release_art_static_gate_v100.json",
    "Saved/Audits/PR010_ReleaseArt_v102/pr010_release_art_static_gate_v102.json")
code = code.replace("if len(proxies) != 24:", "if len(proxies) != 52:")
code = code.replace("expected 24 retained collision proxies", "expected 52 retained, legacy-pylon and v102 service collision proxies")
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

v102_service = [actor for actor in scope if any(tag.startswith("LB.PR010.ServiceDeck.") for tag in {str(value) for value in actor.tags})]
v102_pylons = [actor for actor in scope if "LB.PR010.LaneIdentity.Detailed" in {str(value) for value in actor.tags}]
v102_pylon_text = [actor for actor in texts if "LB.PR010.LaneIdentity.Text" in {str(value) for value in actor.tags}]
v102_stack_text = [actor for actor in texts if "LB.PR010.StackPositionID" in {str(value) for value in actor.tags}]
v102_proxies = [actor for actor in proxies if "LB.Asset.Candidate.v102" in {str(value) for value in actor.tags}]
if len(v102_service) != 16:
    failures.append(f"expected sixteen v102 service-deck visuals, found {len(v102_service)}")
if len(v102_proxies) != 20:
    failures.append(f"expected twenty v102 service collision proxies, found {len(v102_proxies)}")
if len(v102_pylons) != 4:
    failures.append(f"expected four detailed v102 lane pylons, found {len(v102_pylons)}")
elif any(any(abs(value - expected) > 1.0 for value, expected in zip(world_size(actor), (35, 35, 220))) for actor in v102_pylons):
    failures.append("one or more detailed v102 lane pylons have incorrect world dimensions")
if len(v102_pylon_text) != 8:
    failures.append(f"expected eight v102 pylon texts, found {len(v102_pylon_text)}")
if len(v102_stack_text) != 9:
    failures.append(f"expected nine v102 stack IDs, found {len(v102_stack_text)}")
v102_missing_assets = [name for name in (
    "SM_CA_MW_PR010_UpperServiceHousingSection_v102",
    "SM_CA_MW_PR010_ServiceWalkwayRailSection_v102",
    "SM_CA_MW_PR010_RoofDrivePod_v102",
    "SM_CA_MW_PR010_RoofUtilityRoute_v102",
    "SM_CA_MW_PR010_IDPylonDetailed_v102")
    if not library.does_asset_exist(f"/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v102/{name}")]
if v102_missing_assets:
    failures.append(f"missing v102 imported assets: {v102_missing_assets}")
'''
code = code.replace("missing_assets = [name for name in (", injection + "\nmissing_assets = [name for name in (")
code = code.replace("pr010-release-art-static-v100", "pr010-release-art-static-v102")
code = code.replace(
    "PASS__PR010_V100_IMPORT_AUTHORITY_DIMENSIONS_OPEN_GUARDS_HMI_BRANDING__RUNTIME_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "PASS__PR010_V102_SERVICE_DECK_PYLONS_TRACEABILITY_LIVE_HMI_IMPORT_AUTHORITY__RUNTIME_VISUAL_GATES_REQUIRED__NOT_PROMOTED")
code = code.replace("FAIL__PR010_V100_STATIC__NOT_PROMOTED", "FAIL__PR010_V102_STATIC__NOT_PROMOTED")
exec(compile(code, str(base) + "::v102", "exec"), globals(), globals())
