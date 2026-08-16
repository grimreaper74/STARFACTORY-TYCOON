"""Exact static collision and route-segregation gate for coil AGV v135."""

from datetime import datetime, timezone
from pathlib import Path
import json
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVRuntimeCandidate_v135"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr003_pr004_coil_agv_collision_segregation_v135.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

actors = actors_api.get_all_level_actors()
failures = []


def tags(actor):
    return {str(tag) for tag in actor.tags}


def primitive(actor):
    return actor.get_component_by_class(unreal.PrimitiveComponent)


def component_row(actor):
    comp = primitive(actor)
    mesh = actor.static_mesh_component.static_mesh if isinstance(actor,unreal.StaticMeshActor) else None
    body = mesh.get_editor_property("body_setup") if mesh else None
    aggregate = body.get_editor_property("agg_geom") if body else None
    simple = sum(len(aggregate.get_editor_property(field)) for field in ("box_elems","sphere_elems","sphyl_elems","convex_elems")) if aggregate else None
    origin, extent = actor.get_actor_bounds(False,False)
    return {
        "label": actor.get_actor_label(),
        "collision_enabled": str(comp.get_editor_property("body_instance").get_editor_property("collision_enabled")) if comp else None,
        "collision_profile": str(comp.get_collision_profile_name()) if comp else None,
        "can_ever_affect_navigation": bool(comp.get_editor_property("can_ever_affect_navigation")) if comp else None,
        "mobility": str(comp.get_editor_property("mobility")) if comp else None,
        "simple_collision_count": simple,
        "bounds_min_cm": [origin.x-extent.x,origin.y-extent.y,origin.z-extent.z],
        "bounds_max_cm": [origin.x+extent.x,origin.y+extent.y,origin.z+extent.z]
    }


chassis = [a for a in actors if "LB.Vehicle.CoilAGV" in tags(a) and "LB.Vehicle.CoilAGV.LiftDeck" not in tags(a)]
decks = [a for a in actors if "LB.Vehicle.CoilAGV.LiftDeck" in tags(a)]
loads = [a for a in actors if "LB.Inventory.InTransfer" in tags(a)]
route = [a for a in actors if "LB.Route.CoilAGV.TBC" in tags(a) and "DockStop" not in a.get_actor_label()]
dock_stops = [a for a in actors if "LB.Route.CoilAGV.TBC" in tags(a) and "DockStop" in a.get_actor_label()]
walkways = [a for a in actors if any("walkway" in tag.lower() or "pedestrian" in tag.lower() for tag in tags(a))]

if len(chassis)!=1: failures.append(f"expected one chassis, found {len(chassis)}")
if len(decks)!=1: failures.append(f"expected one deck, found {len(decks)}")
if len(loads)!=1: failures.append(f"expected one transferred load, found {len(loads)}")
if len(route)<10: failures.append(f"expected marked AGV route actors, found {len(route)}")

vehicle_rows = [component_row(a) for a in chassis+decks+loads]
for row in vehicle_rows:
    if primitive(next(a for a in chassis+decks+loads if a.get_actor_label()==row["label"])).get_editor_property("mobility") != unreal.ComponentMobility.MOVABLE:
        failures.append(f"vehicle/load actor is not movable: {row['label']}={row['mobility']}")
    if primitive(next(a for a in chassis+decks+loads if a.get_actor_label()==row["label"])).get_editor_property("body_instance").get_editor_property("collision_enabled") == unreal.CollisionEnabled.NO_COLLISION:
        failures.append(f"vehicle/load actor has no collision: {row['label']}")
    if (row["simple_collision_count"] or 0) <= 0:
        failures.append(f"vehicle/load mesh has no simple collision: {row['label']}")

route_rows = [component_row(a) for a in route]
for row in route_rows:
    actor = next(a for a in route if a.get_actor_label()==row["label"])
    if primitive(actor).get_editor_property("body_instance").get_editor_property("collision_enabled") != unreal.CollisionEnabled.NO_COLLISION:
        failures.append(f"route marking collides: {row['label']}={row['collision_enabled']}")
    if row["can_ever_affect_navigation"]:
        failures.append(f"route marking affects navigation: {row['label']}")

dock_stop_rows = [component_row(a) for a in dock_stops]
if len(dock_stop_rows) != 2:
    failures.append(f"expected two physical dock stops, found {len(dock_stop_rows)}")
for row in dock_stop_rows:
    actor = next(a for a in dock_stops if a.get_actor_label()==row["label"])
    if primitive(actor).get_editor_property("body_instance").get_editor_property("collision_enabled") == unreal.CollisionEnabled.NO_COLLISION:
        failures.append(f"physical dock stop has no collision: {row['label']}")

# Authored route is 320 cm wide and imported chassis is 222 cm wide.
# This proves geometric fit only; operational lateral clearance remains TBC.
route_width_cm = 320.0
chassis_width_cm = vehicle_rows[0]["bounds_max_cm"][1]-vehicle_rows[0]["bounds_min_cm"][1] if vehicle_rows else None
lateral_margin_each_side_cm = (route_width_cm-chassis_width_cm)/2.0 if chassis_width_cm is not None else None
if lateral_margin_each_side_cm is None or lateral_margin_each_side_cm <= 0:
    failures.append(f"chassis does not fit route envelope: margin={lateral_margin_each_side_cm}")

walkway_rows = [component_row(a) for a in walkways]
# The south straight route occupies y[-2860,-2540]. Record the nearest marked
# pedestrian/walkway surface but do not claim a regulatory clearance.
route_south_y = -2860.0
separations = []
for row in walkway_rows:
    minimum_y, maximum_y = row["bounds_min_cm"][1],row["bounds_max_cm"][1]
    if maximum_y <= route_south_y:
        separations.append(route_south_y-maximum_y)
    elif minimum_y >= -2540.0:
        separations.append(minimum_y-(-2540.0))
    else:
        separations.append(-min(maximum_y-route_south_y,-2540.0-minimum_y))
minimum_marked_walkway_separation_cm = min(separations) if separations else None
if minimum_marked_walkway_separation_cm is not None and minimum_marked_walkway_separation_cm < 0:
    failures.append(f"marked pedestrian/walkway surface overlaps AGV route: {minimum_marked_walkway_separation_cm} cm")

result = {
    "$schema":"cairnwell/audit/press-shop-pr003-pr004-coil-agv-collision-segregation-v135/v1",
    "generated_utc":datetime.now(timezone.utc).isoformat(),
    "map":MAP,
    "status":"COLLISION_AND_MARKED_ROUTE_SEGREGATION_PASS__OPERATIONAL_CLEARANCES_TBC__NOT_PROMOTED" if not failures else "COLLISION_OR_ROUTE_SEGREGATION_FAIL__NOT_PROMOTED",
    "vehicle_and_load":vehicle_rows,
    "route_marking_count":len(route_rows),
    "route_markings":route_rows,
    "physical_dock_stops":dock_stop_rows,
    "route_width_cm":route_width_cm,
    "route_width_status":"TBC",
    "chassis_width_cm":chassis_width_cm,
    "geometric_lateral_margin_each_side_cm":lateral_margin_each_side_cm,
    "lateral_margin_authority":"GEOMETRIC_FIT_ONLY__OPERATIONAL_CLEARANCE_TBC",
    "marked_walkway_count":len(walkway_rows),
    "marked_walkways":walkway_rows,
    "minimum_marked_walkway_separation_cm":minimum_marked_walkway_separation_cm,
    "failures":failures,
    "promotion_authorized":False
}
OUT.write_text(json.dumps(result,indent=2),encoding="utf-8")
if failures:
    raise RuntimeError(str(failures))
print(json.dumps({"status":result["status"],"lateral_margin_each_side_cm":lateral_margin_each_side_cm,"walkway_separation_cm":minimum_marked_walkway_separation_cm},indent=2))
