"""PIE traces for guard perimeter, fixed chassis footprints and material corridor."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from press_shop_pr009_release_collision_v087_config import TARGET_MAP

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
root = Path(unreal.Paths.project_dir())
audit_dir = root / "Saved/Audits/PR009_InMap_v087"
out = audit_dir / "physical_collision_pie_audit.json"
build = json.loads((audit_dir / "release_collision_build.json").read_text(encoding="utf-8"))
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(TARGET_MAP): raise RuntimeError(f"Could not load {TARGET_MAP}")
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic(); handle = None

def hit_actor(result):
    try: return result.to_tuple()[9]
    except Exception: return None

def trace(world,start,end,ignored=None):
    result = unreal.SystemLibrary.line_trace_single(world,unreal.Vector(*start),unreal.Vector(*end),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignored or [],unreal.DrawDebugTrace.NONE,True)
    if result is None:
        return {"start_cm":start,"end_cm":end,"hit":False,"hit_actor":None,"impact_point_cm":None}
    fields = result.to_tuple(); hit = bool(fields[0])
    actor = hit_actor(result) if hit else None
    return {"start_cm":start,"end_cm":end,"hit":bool(hit),"hit_actor":actor.get_actor_label() if actor else None,
            "impact_point_cm":[fields[5].x,fields[5].y,fields[5].z] if hit else None}

def box_trace(world,start,end,half):
    result = unreal.SystemLibrary.box_trace_single(world,unreal.Vector(*start),unreal.Vector(*end),unreal.Vector(*half),
        unreal.Rotator(),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,True)
    if result is None:
        return {"start_cm":start,"end_cm":end,"half_extent_cm":half,"blocked":False,
                "hit_actor":None,"impact_point_cm":None}
    fields = result.to_tuple(); hit = bool(fields[0])
    actor = hit_actor(result) if hit else None
    return {"start_cm":start,"end_cm":end,"half_extent_cm":half,"blocked":bool(hit),
            "hit_actor":actor.get_actor_label() if actor else None,
            "impact_point_cm":[fields[5].x,fields[5].y,fields[5].z] if hit else None}

def finish(payload,failures):
    global handle
    if handle is not None: unreal.unregister_slate_post_tick_callback(handle); handle=None
    payload.update({"$schema":"cairnwell/audit/pr009-physical-collision-pie-v087/v1",
                    "generated_utc":datetime.now(timezone.utc).isoformat(),"target_map":TARGET_MAP,
                    "status":"PASS__PHYSICAL_AND_MATERIAL_PATH_TRACES__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
                    "failures":failures,"promotion_authorized":False})
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    unreal.log(f"PR009_V087_PHYSICAL_COLLISION_{'PASS' if not failures else 'FAIL'} output={out}")
    unreal.EditorLevelLibrary.editor_end_play(); unreal.EditorPythonScripting.set_keep_python_script_alive(False); unreal.SystemLibrary.quit_editor()

def tick_impl(_delta):
    if time.monotonic()-started < 4.0: return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None: return
    all_actors = unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
    by_label = {actor.get_actor_label():actor for actor in all_actors}
    failures=[]
    guard_actor=next((actor for actor in all_actors if unreal.Name("LB.Structure.PR009") in actor.tags and "GuardSet" in actor.get_actor_label()),None)
    guard_rows={}
    if guard_actor is None:
        failures.append("missing GuardSet actor")
    else:
        loc=guard_actor.get_actor_location()
        guard_record=next(row for row in build["static_groups"] if row["group"]=="SM_CA_MW_PR009_GuardSet_01")
        for primitive in guard_record["primitives"]:
            cx,cy,cz=primitive["center_cm"]; dx,dy,dz=primitive["dimensions_cm"]
            wc=(loc.x+cy,loc.y-cx,loc.z+cz)
            # Source X maps to world -Y and source Y maps to world +X at the fixed -90 degree station yaw.
            if dx <= dy:
                points=((wc[0],wc[1]+dx*.5+20,wc[2]),(wc[0],wc[1]-dx*.5-20,wc[2]))
            else:
                points=((wc[0]+dy*.5+20,wc[1],wc[2]),(wc[0]-dy*.5-20,wc[1],wc[2]))
            guard_rows[primitive["source"]]=trace(world,*points,[actor for actor in all_actors if actor != guard_actor])
    for name,row in guard_rows.items():
        if not row["hit"] or "GuardSet" not in (row["hit_actor"] or ""): failures.append(f"guard perimeter trace failed {name}: {row}")
    material_apertures={
        "infeed_centre_opening":trace(world,(1030,-2000,115),(920,-2000,115)),
        "outfeed_centre_opening":trace(world,(170,-2000,115),(280,-2000,115)),
    }
    for name,row in material_apertures.items():
        if row["hit"]: failures.append(f"intended material aperture blocked {name}: {row}")
    corridor_line=trace(world,(1050,-2000,115),(150,-2000,115))
    carrier_actor=next((actor for actor in all_actors if unreal.Name("LB.Structure.PR009") in actor.tags and "Carrier" in actor.get_actor_label()),None)
    if carrier_actor is None:
        measured_half=[0,0,0]; failures.append("missing carrier group for authoritative envelope")
    else:
        carrier_origin,carrier_extent=carrier_actor.get_actor_bounds(False,False)
        measured_half=[carrier_extent.x,carrier_extent.y,carrier_extent.z]
    # Pro Sheet 02 lists the maximum blank as 2600 x 1800 mm.  The pack's
    # coordinate authority defines local +Y as material flow and local +X as
    # across strip/lane.  With station yaw -90, local flow maps to world X and
    # across-strip maps to world Y, so the world half extents are 130 x 90 cm.
    pro_max_half=[130.0,90.0,0.8]
    # The combined Carrier static group includes its four locator posts.  Those
    # are receiving fixtures, not part of a transferred blank and must not be
    # swept through the upstream conveyor guides.  Use the Pro blank envelope
    # exactly; carrier/locator clearance is covered at the stack station.
    authoritative_half=list(pro_max_half)
    blank_sweep=box_trace(world,(1050,-2000,105),(150,-2000,105),authoritative_half)
    if corridor_line["hit"]: failures.append(f"material centreline blocked: {corridor_line}")
    if blank_sweep["blocked"]: failures.append(f"transferred blank swept envelope blocked: {blank_sweep}")
    fixed_rows=[]
    for record in build["fixed_chassis_collision_actors"]:
        actor=by_label.get(record["actor"])
        if actor is None: failures.append(f"missing fixed chassis actor {record['actor']}"); continue
        origin,extent=actor.get_actor_bounds(False,False)
        row=trace(world,(origin.x,origin.y,origin.z+extent.z+25),(origin.x,origin.y,origin.z-extent.z-25),
                  [other for other in all_actors if other != actor])
        row.update({"expected_actor":record["actor"],"role":record["role"]})
        if not row["hit"] or row["hit_actor"]!=record["actor"]: failures.append(f"fixed chassis physical trace failed {record['actor']}: {row}")
        fixed_rows.append(row)
    base_actor=next((actor for actor in all_actors if unreal.Name("LB.Structure.PR009") in actor.tags and "BaseFrame" in actor.get_actor_label()),None)
    base_rows=[]
    if base_actor is None: failures.append("missing BaseFrame actor")
    else:
        loc=base_actor.get_actor_location()
        base_record=next(row for row in build["static_groups"] if row["group"]=="SM_CA_MW_PR009_BaseFrame_01")
        for primitive in base_record["primitives"]:
            cx,cy,cz=primitive["center_cm"]; dx,dy,dz=primitive["dimensions_cm"]
            world_center=(loc.x+cy,loc.y-cx,loc.z+cz)
            row=trace(world,(world_center[0],world_center[1],world_center[2]+dz*.5+20),(world_center[0],world_center[1],world_center[2]-dz*.5-20),
                      [other for other in all_actors if other != base_actor])
            row.update({"source_primitive":primitive["source"],"expected_actor":base_actor.get_actor_label()})
            if not row["hit"] or row["hit_actor"]!=base_actor.get_actor_label(): failures.append(f"BaseFrame primitive trace failed {primitive['source']}: {row}")
            base_rows.append(row)
    mover_rows=[]
    for record in build["moving_collision_actors"]:
        actor=by_label.get(record["actor"]); component=actor.get_component_by_class(unreal.StaticMeshComponent) if actor else None
        world_static_response=str(component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC)) if component else None
        row={"actor":record["actor"],"role":record["role"],"present":actor is not None,
             "profile":str(component.get_collision_profile_name()) if component else None,
             "collision_enabled":str(component.get_editor_property("body_instance").get_editor_property("collision_enabled")) if component else None,
             "world_static_response":world_static_response,
             "physically_blocking":bool(world_static_response and "BLOCK" in world_static_response.upper())}
        if not actor or row["physically_blocking"] or "QUERY_ONLY" not in (row["collision_enabled"] or "").upper(): failures.append(f"mover sensing/blocking distinction failed {row}")
        mover_rows.append(row)
    finish({"guard_perimeter_traces":guard_rows,"intended_material_aperture_traces":material_apertures,
            "material_centreline_trace":corridor_line,
            "transferred_blank_envelope_authority":{"measured_v087_carrier_half_extent_cm":measured_half,
                "pro_max_blank_dimensions_mm_flow_by_across":[2600,1800],"pro_max_world_half_extent_cm":pro_max_half,
                "tested_world_half_extent_cm":authoritative_half,
                "carrier_bounds_excluded_from_transferred_blank_reason":"Carrier locators and accumulated stack height are receiving fixtures, not the transferred blank envelope"},
            "transferred_blank_box_sweep":blank_sweep,"fixed_chassis_vertical_traces":fixed_rows,
            "baseframe_primitive_traces":base_rows,"query_only_mover_evidence":mover_rows,
            "query_only_movers_are_physical_blockers":False},failures)

def tick(_delta):
    try:
        tick_impl(_delta)
    except Exception as exc:
        unreal.log_error(f"PR009_V087_PHYSICAL_COLLISION_VALIDATOR_EXCEPTION: {exc!r}")
        finish({"validator_exception":{"type":type(exc).__name__,"message":str(exc)}},
               [f"validator exception: {type(exc).__name__}: {exc}"])

handle=unreal.register_slate_post_tick_callback(tick)
