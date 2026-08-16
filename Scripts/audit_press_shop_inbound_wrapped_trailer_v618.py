"""Read-only exact-map audit of isolated wrapped-trailer v616."""
from pathlib import Path
import json
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundWrappedTrailerCandidate_v616"
COIL = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005"
CHASSIS = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/AnimatedLorryCandidate_v001/SM_CA_MW_Inbound_LorryChassis_v001"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_wrapped_trailer_exact_map_v618.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load v616")

actors = actors_api.get_all_level_actors()
coils = []
for actor in actors:
    tags = {str(t) for t in actor.tags}
    ordered = [t for t in tags if t.startswith("LB.Inbound.Visual.TrailerCoil.")]
    if ordered:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        mesh = comp.get_editor_property("static_mesh") if comp else None
        body = mesh.get_editor_property("body_setup") if mesh else None
        agg = body.get_editor_property("agg_geom") if body else None
        collision_count = sum(len(agg.get_editor_property(name)) for name in
                              ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems")) if agg else 0
        coils.append({
            "label": actor.get_actor_label(),
            "tag": ordered[0],
            "mesh": mesh.get_path_name().split(".")[0] if mesh else None,
            "materials": [m.get_path_name() if m else None for m in comp.get_materials()] if comp else [],
            "mobility": str(comp.get_editor_property("mobility")) if comp else None,
            "simple_collision_shapes": collision_count,
            "location_cm": list(actor.get_actor_location().to_tuple()),
        })

def tagged(tag):
    return [a for a in actors if a.actor_has_tag(unreal.Name(tag))]

lorry = tagged("LB.Inbound.Visual.Lorry")
controller = next((a for a in actors if a.get_class().get_name() == "LBInboundDeliveryController"), None)
bindings = {name: len(tagged("LB.Inbound.Visual." + name)) for name in
            ("CraneBridge", "CraneTrolley", "Hoist", "Hook", "Saddle")}
expected_tags = [f"LB.Inbound.Visual.TrailerCoil.{i:02d}" for i in range(1, 5)]
errors = []
if len(coils) != 4: errors.append(f"Expected four trailer coils, got {len(coils)}")
if sorted(c["tag"] for c in coils) != expected_tags: errors.append("Ordered trailer tags are incomplete or duplicated")
if any(c["mesh"] != COIL for c in coils): errors.append("A trailer coil does not use exact retained MasterCoil v005")
if any(len(c["materials"]) != 10 for c in coils): errors.append("A trailer coil does not expose all ten retained material slots")
if any(c["simple_collision_shapes"] < 1 for c in coils): errors.append("A trailer coil has no simple collision")
if any("MOVABLE" not in c["mobility"].upper() for c in coils): errors.append("A trailer coil is not movable")
if len(lorry) != 1: errors.append("Exactly one tagged lorry is required")
elif lorry[0].static_mesh_component.static_mesh.get_path_name().split(".")[0] != CHASSIS: errors.append("Lorry is not modular empty chassis")
if any(value != 1 for value in bindings.values()): errors.append("Crane/hook/saddle visual tags are incomplete or duplicated")
if controller is None: errors.append("Inbound delivery controller missing")
else:
    approach = controller.get_editor_property("authored_lorry_approach_point")
    dock = controller.get_editor_property("authored_lorry_dock_point")
    if (approach - dock).length() <= 1.0: errors.append("Lorry approach and dock points are identical")
    if not controller.get_editor_property("auto_discover_visual_sequence"): errors.append("Runtime visual auto-discovery disabled")

payload = {
    "status": "PASS__EXACT_MAP_NOT_PROMOTED" if not errors else "FAIL",
    "map": MAP,
    "coil_count": len(coils),
    "coils": sorted(coils, key=lambda c: c["tag"]),
    "binding_tag_counts": bindings,
    "errors": errors,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if errors: raise RuntimeError("; ".join(errors))
unreal.log(f"LB_INBOUND_WRAPPED_TRAILER_V618_AUDIT_PASS::{json.dumps(payload)}")
