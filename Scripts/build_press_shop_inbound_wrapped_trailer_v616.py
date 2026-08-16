"""Fresh v597 child: modular lorry with four exact retained wrapped PR003 coils.

This never edits v597.  The former combined lorry is converted to the empty
chassis and four independently movable MasterCoil Candidate_v005 actors are
authored for the visible unload sequence.
"""
from pathlib import Path
import hashlib
import json
import unreal

BASE = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v597"
MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundWrappedTrailerCandidate_v616"
CHASSIS = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/AnimatedLorryCandidate_v001/SM_CA_MW_Inbound_LorryChassis_v001"
COIL = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/inbound_wrapped_trailer_build_v616.json"

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

base_file = ROOT / "Content/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v597.umap"
base_before = digest(base_file)
if OUT.exists():
    raise RuntimeError(f"Refusing to overwrite retained PASS candidate: {MAP}")
if not lib.does_asset_exist(MAP) or not levels.load_level(MAP):
    raise RuntimeError("Clean isolated v616 snapshot is missing or could not be loaded")

chassis_mesh = lib.load_asset(CHASSIS)
coil_mesh = lib.load_asset(COIL)
if not isinstance(chassis_mesh, unreal.StaticMesh) or not isinstance(coil_mesh, unreal.StaticMesh):
    raise RuntimeError("Retained chassis or exact wrapped master coil is missing")

by_label = {a.get_actor_label(): a for a in actors_api.get_all_level_actors()}
lorry = by_label.get("LB_INBOUND_V570_LorryFourCoil")
controller = by_label.get("LB_INBOUND_V577_DeliveryAuthority")
required = {
    "bridge": by_label.get("LB_INBOUND_V570_CraneBridge"),
    "trolley": by_label.get("LB_INBOUND_V570_CraneTrolley"),
    "hoist": by_label.get("LB_INBOUND_V570_HoistBlock"),
    "hook": by_label.get("LB_INBOUND_V570_PoweredCHook"),
    "saddle": by_label.get("LB_INBOUND_V570_ReceivingSaddle"),
}
if not lorry or not controller or not all(required.values()):
    raise RuntimeError("Exact v597 inbound actor set is incomplete")

dock = unreal.Vector(-14200.0, -2000.0, 0.0)
approach = unreal.Vector(-15400.0, -2000.0, 0.0)
lorry.static_mesh_component.set_static_mesh(chassis_mesh)
lorry.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
lorry.set_actor_label("LB_INBOUND_V616_LorryChassis")
lorry.set_actor_location(approach, False, False)
lorry.tags = [unreal.Name(x) for x in (
    "LB.Inbound.Visual.Lorry", "LB.Inbound.ReverseOnly", "LB.Asset.CandidateNotPromoted")]

# The exact same mesh/material slots used by the retained PR003 packaged store.
# Coil axis faces the operator aisle; the four centres follow the trailer length.
coil_actors = []
for index, offset_x in enumerate((-360.0, -120.0, 120.0, 360.0), 1):
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(approach.x + offset_x, approach.y, 152.0),
        unreal.Rotator(0.0, 0.0, 90.0))
    actor.set_actor_label(f"LB_INBOUND_V616_TrailerWrappedCoil_{index:02d}")
    actor.static_mesh_component.set_static_mesh(coil_mesh)
    actor.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    actor.tags = [unreal.Name(x) for x in (
        f"LB.Inbound.Visual.TrailerCoil.{index:02d}",
        "LB.Inbound.TrailerLoad", "LB.Material.PackagedCoil",
        "LB.Asset.CandidateNotPromoted")]
    coil_actors.append(actor)

for key, tag in (("bridge", "CraneBridge"), ("trolley", "CraneTrolley"),
                 ("hoist", "Hoist"), ("hook", "Hook"), ("saddle", "Saddle")):
    actor = required[key]
    actor.tags = list(actor.tags) + [unreal.Name(f"LB.Inbound.Visual.{tag}")]
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component and key != "saddle":
        component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

controller.set_editor_property("auto_discover_visual_sequence", True)
controller.set_editor_property("authored_lorry_approach_point", approach)
controller.set_editor_property("authored_lorry_dock_point", dock)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Candidate save failed")
base_after = digest(base_file)
if base_before != base_after:
    raise RuntimeError("Immutable v597 parent changed")

payload = {
    "status": "PASS__ISOLATED_NOT_PROMOTED",
    "map": MAP,
    "parent": BASE,
    "parent_hash_preserved": True,
    "trailer_coil_count": len(coil_actors),
    "trailer_coil_mesh": COIL,
    "matches_retained_pr003_packaged_coil": True,
    "simple_dark_imported_coils_used_in_map": False,
    "lorry_motion": "reverse_from_approach_to_dock",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LB_INBOUND_WRAPPED_TRAILER_V616_BUILD_PASS::{json.dumps(payload)}")
