"""Exact-map authority and lineage audit for the expanded v570 candidate."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundIntegrationCandidate_v570"
SOURCE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
CANDIDATE_FILE = ROOT / "Content/LineBoss/Developer/Validation/LB_PressShop_InboundIntegrationCandidate_v570.umap"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_exact_authority_v571.json"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v570")

counts = {key: 0 for key in ["LB.Vehicle.CoilAGV", "LB.Vehicle.CoilAGV.LiftDeck", "LB.Inventory.InTransfer"]}
modules=[]
controllers={}
for actor in actors.get_all_level_actors():
    tags={str(tag) for tag in actor.tags}
    for key in counts:
        if key in tags:
            counts[key] += 1
    if "LB.Inbound.DirectV438.v570" in tags and isinstance(actor, unreal.StaticMeshActor):
        modules.append(actor.get_actor_label())
    cls=actor.get_class().get_name()
    if cls in ("LBCoilAGVController", "LBInboundDeliveryController", "LBPressShopBuildAuthority"):
        controllers[cls]=controllers.get(cls,0)+1

source_hash=hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest().upper()
candidate_hash=hashlib.sha256(CANDIDATE_FILE.read_bytes()).hexdigest().upper()
checks={
    "protected_v438_unchanged": source_hash == EXPECTED,
    "one_coil_agv": counts["LB.Vehicle.CoilAGV"] == 1,
    "one_lift_deck": counts["LB.Vehicle.CoilAGV.LiftDeck"] == 1,
    "one_in_transfer_coil": counts["LB.Inventory.InTransfer"] == 1,
    "one_coil_agv_controller": controllers.get("LBCoilAGVController",0) == 1,
    "one_build_authority": controllers.get("LBPressShopBuildAuthority",0) == 1,
    "thirteen_inbound_modules": len(modules) == 13,
}
status="PASS" if all(checks.values()) else "FAIL"
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"status":status,"map":MAP,"checks":checks,"tag_counts":counts,
                           "controller_counts":controllers,"inbound_modules":sorted(modules),
                           "protected_v438_sha256":source_hash,"candidate_sha256":candidate_hash,
                           "promotion_authorized":False},indent=2),encoding="utf-8")
if status != "PASS":
    raise RuntimeError(f"v571 authority audit failed: {checks}")
unreal.log("LINE_BOSS_INBOUND_EXACT_AUTHORITY_V571_PASS")
