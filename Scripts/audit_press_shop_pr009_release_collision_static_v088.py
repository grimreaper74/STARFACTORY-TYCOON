"""Read-only v088 static/simple collision, binding and isolation audit."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from press_shop_pr009_trace_portal_clearance_v088_config import TARGET_MAP, STATIC_DEST, MOVING_DEST

root = Path(unreal.Paths.project_dir())
audit_dir = root / "Saved/Audits/PR009_InMap_v088"
out = audit_dir / "release_collision_static_audit.json"
build = json.loads((audit_dir / "release_collision_build.json").read_text(encoding="utf-8"))
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary
if not levels.load_level(TARGET_MAP): raise RuntimeError(f"Could not load {TARGET_MAP}")
actors = list(actors_api.get_all_level_actors())
failures = []

def counts(mesh):
    body = mesh.get_editor_property("body_setup")
    agg = body.get_editor_property("agg_geom")
    row = {"box": len(agg.get_editor_property("box_elems")), "sphere": len(agg.get_editor_property("sphere_elems")),
           "capsule": len(agg.get_editor_property("sphyl_elems")), "convex": len(agg.get_editor_property("convex_elems"))}
    row["total"] = sum(row.values())
    return row, str(body.get_editor_property("collision_trace_flag"))

def component_row(actor):
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = component.get_editor_property("static_mesh") if component else None
    primitive, trace = counts(mesh) if mesh else ({"box":0,"sphere":0,"capsule":0,"convex":0,"total":0}, None)
    return {"actor": actor.get_actor_label(), "asset": mesh.get_path_name() if mesh else None,
            "primitives": primitive, "trace_flag": trace,
            "collision_enabled": str(component.get_editor_property("body_instance").get_editor_property("collision_enabled")) if component else None,
            "profile": str(component.get_collision_profile_name()) if component else None,
            "nav_relevant": bool(component.get_editor_property("can_ever_affect_navigation")) if component else None,
            "world_static_response": str(component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC)) if component else None}

static = [actor for actor in actors if unreal.Name("LB.Structure.PR009") in actor.tags]
fixed = [actor for actor in actors if unreal.Name("LB.Collision.FixedChassis.v088") in actor.tags]
movers = [actor for actor in actors if unreal.Name("LB.Collision.SelectiveMover.v088") in actor.tags]
modular = [actor for actor in actors if actor.get_actor_label().startswith("LB_PR009_V088_MOD_")]
interface = [actor for actor in actors if unreal.Name("LB.Interface.PR008.PR009") in actor.tags]
static_rows, fixed_rows, mover_rows = map(lambda group: [component_row(actor) for actor in group], (static, fixed, movers))
nonselected_rows = [component_row(actor) for actor in modular if actor not in fixed and actor not in movers]
interface_rows = [component_row(actor) for actor in interface]

if len(static) != 10: failures.append(f"static group count {len(static)} != 10")
if len(fixed) != 14: failures.append(f"fixed chassis count {len(fixed)} != 14")
if len(movers) != 26: failures.append(f"selective mover count {len(movers)} != 26")
if len(modular) != 158: failures.append(f"modular presentation count {len(modular)} != 158")
for row in static_rows:
    if row["primitives"]["total"] <= 0 or "COMPLEX_AS_SIMPLE" in row["trace_flag"].upper(): failures.append(f"invalid static collision {row['actor']}")
for row in fixed_rows:
    if row["primitives"]["total"] != 1 or "BLOCKALL" not in row["profile"].upper() or "QUERY_AND_PHYSICS" not in row["collision_enabled"].upper(): failures.append(f"invalid fixed chassis collision {row['actor']}")
for row in mover_rows:
    if row["primitives"]["total"] != 1 or "OVERLAP" not in row["profile"].upper() or "QUERY_ONLY" not in row["collision_enabled"].upper() or row["nav_relevant"]: failures.append(f"invalid mover query collision {row['actor']}")
if any("COMPLEX_AS_SIMPLE" in (row["trace_flag"] or "").upper() for row in static_rows + fixed_rows + mover_rows + interface_rows):
    failures.append("complex-as-simple remains in v088 release scope")
if any("NO_COLLISION" not in (row["collision_enabled"] or "").upper() for row in nonselected_rows):
    failures.append("non-selected cosmetic modular visual unexpectedly collides")

visual_asset_proofs = []
for build_row in build["static_groups"]:
    source_mesh = lib.load_asset(f"/Game/LineBoss/Candidates/PressShop/PR009/v003/Static/{build_row['group']}")
    release_mesh = lib.load_asset(build_row["release_asset"].split(".")[0])
    source_box, release_box = source_mesh.get_bounding_box(), release_mesh.get_bounding_box()
    source_slots = [str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
                    for slot in source_mesh.get_editor_property("static_materials")]
    release_slots = [str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
                     for slot in release_mesh.get_editor_property("static_materials")]
    proof = {"group": build_row["group"],
             "vertices_match": source_mesh.get_num_vertices(0) == release_mesh.get_num_vertices(0),
             "triangles_match": source_mesh.get_num_triangles(0) == release_mesh.get_num_triangles(0),
             "bounds_match": all(abs(a-b) <= 0.01 for a,b in zip(
                 [source_box.min.x,source_box.min.y,source_box.min.z,source_box.max.x,source_box.max.y,source_box.max.z],
                 [release_box.min.x,release_box.min.y,release_box.min.z,release_box.max.x,release_box.max.y,release_box.max.z])),
             "materials_match": [material.get_path_name() if material else None for material in [source_mesh.get_material(i) for i in range(len(source_mesh.get_editor_property("static_materials")))]] ==
                                [material.get_path_name() if material else None for material in [release_mesh.get_material(i) for i in range(len(release_mesh.get_editor_property("static_materials")))]],
             "material_slot_names_match": source_slots == release_slots,
             "simple_collision": build_row["simple_collision"]}
    if build_row["group"] == "SM_CA_MW_PR009_TracePortal_01":
        expected_bounds = [-157.2308, -335.5, 55.0, 157.2308, -294.5, 326.0]
        actual_bounds = [release_box.min.x, release_box.min.y, release_box.min.z,
                         release_box.max.x, release_box.max.y, release_box.max.z]
        proof["approved_dimensioned_geometry_change"] = True
        proof["expected_derived_bounds_cm"] = expected_bounds
        proof["derived_bounds_match"] = all(abs(a-b) <= 0.15 for a,b in zip(actual_bounds, expected_bounds))
        proof["identity_requirements"] = {
            "clear_opening_mm": build_row.get("derived_clear_opening_mm"),
            "source_y_envelope_m": build_row.get("derived_source_y_envelope_m"),
        }
        if not all(proof[key] for key in ("vertices_match", "triangles_match", "material_slot_names_match", "derived_bounds_match")):
            failures.append(f"derived trace-portal asset mismatch {proof}")
    elif not all(proof[key] for key in ("vertices_match","triangles_match","bounds_match","materials_match")):
        failures.append(f"visual duplicate mismatch {build_row['group']}")
    visual_asset_proofs.append(proof)

pr008 = [actor for actor in actors if isinstance(actor, unreal.LBPR008Station)]
pr009 = [actor for actor in actors if isinstance(actor, unreal.LBPR009Station)]
flows = [actor for actor in actors if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
binding_ok = len(pr008)==len(pr009)==len(flows)==1 and flows[0].get_editor_property("pr008_station")==pr008[0] and flows[0].get_editor_property("pr009_station")==pr009[0]
if not binding_ok: failures.append("native authority cardinality/binding changed")
pr010 = [actor.get_actor_label() for actor in actors if "PR010" in (actor.get_actor_label()+"|"+"|".join(str(tag) for tag in actor.tags)).upper()]
if pr010: failures.append(f"PR010 actors found {pr010}")

payload = {"$schema":"cairnwell/audit/pr009-release-collision-static-v088/v1","generated_utc":datetime.now(timezone.utc).isoformat(),
           "status":"PASS__ASSET_COLLISION_READY__RUNTIME_SWEEP_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
           "target_map":TARGET_MAP,"static_groups":static_rows,"fixed_chassis":fixed_rows,"selective_query_movers":mover_rows,
           "intentionally_no_collision_modular_visuals":nonselected_rows,"supported_interface":interface_rows,
           "visual_asset_identity_proofs":visual_asset_proofs,"authority_binding_preserved":binding_ok,
           "simple_primitive_total":sum(row["primitives"]["total"] for row in static_rows+fixed_rows+mover_rows),
           "convex_primitive_total":sum(row["primitives"]["convex"] for row in static_rows+fixed_rows+mover_rows),
           "complex_as_simple_count":sum("COMPLEX_AS_SIMPLE" in (row["trace_flag"] or "").upper() for row in static_rows+fixed_rows+mover_rows+interface_rows),
           "asset_collision_ready":not failures,"release_collision_ready":False,"release_collision_ready_reason":"Runtime sweeps, navigation and full regression suite not yet consolidated",
           "pr010_actors":pr010,"failures":failures,"promotion_authorized":False}
out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2),encoding="utf-8")
unreal.log(f"PR009_V088_STATIC_COLLISION_{'PASS' if not failures else 'FAIL'} output={out}")
unreal.SystemLibrary.quit_editor()
if failures: raise RuntimeError(str(failures))
