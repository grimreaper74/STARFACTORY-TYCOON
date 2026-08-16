"""Read-only v084 PR-009 actor, binding, collision and PR-010 exclusion audit."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from press_shop_pr009_in_map_validation_config import TARGET_MAP


ROOT = Path(unreal.Paths.project_dir())
MATCH = re.search(r"_v(\d+)$", TARGET_MAP, re.IGNORECASE)
if not MATCH:
    raise RuntimeError(f"TARGET_MAP has no version suffix: {TARGET_MAP}")
VERSION = f"v{MATCH.group(1)}"
PREFIX = f"LB_PR009_V{MATCH.group(1)}_"
OUT_DIR = ROOT / "Saved" / "Audits" / f"PR009_InMap_{VERSION}"
OUT = OUT_DIR / "static_map_audit.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(f"Could not load {TARGET_MAP}")

actors = list(actors_api.get_all_level_actors())
pr008 = [actor for actor in actors if isinstance(actor, unreal.LBPR008Station)]
pr009 = [actor for actor in actors if isinstance(actor, unreal.LBPR009Station)]
flows = [actor for actor in actors if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
failures = []


def actor_ref(actor):
    return None if actor is None else {
        "label": actor.get_actor_label(),
        "name": actor.get_name(),
        "class": actor.get_class().get_name(),
        "path": actor.get_path_name(),
    }


if len(pr008) != 1:
    failures.append(f"Expected exactly one native ALBPR008Station; found {len(pr008)}")
if len(pr009) != 1:
    failures.append(f"Expected exactly one native ALBPR009Station; found {len(pr009)}")
if len(flows) != 1:
    failures.append(f"Expected exactly one ALBPressShopMaterialFlowController; found {len(flows)}")

binding = {"property_accessible": False, "pr008_matches": False, "pr009_matches": False}
if len(flows) == 1:
    try:
        bound_pr008 = flows[0].get_editor_property("pr008_station")
        bound_pr009 = flows[0].get_editor_property("pr009_station")
        binding = {
            "property_accessible": True,
            "bound_pr008": actor_ref(bound_pr008),
            "bound_pr009": actor_ref(bound_pr009),
            "pr008_matches": len(pr008) == 1 and bound_pr008 == pr008[0],
            "pr009_matches": len(pr009) == 1 and bound_pr009 == pr009[0],
        }
    except Exception as exc:
        binding["error"] = str(exc)
if not binding["pr008_matches"] or not binding["pr009_matches"]:
    failures.append("Material-flow controller editor binding does not match the unique PR-008/PR-009 actors")


def collision_row(actor):
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        return {"actor": actor.get_actor_label(), "error": "no StaticMeshComponent"}
    mesh = component.get_editor_property("static_mesh")
    enabled = component.get_editor_property("body_instance").get_editor_property("collision_enabled")
    trace = None
    simple_elements = None
    if mesh is not None:
        try:
            body = mesh.get_editor_property("body_setup")
            trace = str(body.get_editor_property("collision_trace_flag"))
            agg = body.get_editor_property("agg_geom")
            simple_elements = sum(len(agg.get_editor_property(name)) for name in (
                "box_elems", "sphere_elems", "sphyl_elems", "convex_elems", "tapered_capsule_elems"))
        except Exception as exc:
            trace = f"UNAVAILABLE:{exc}"
    return {
        "actor": actor.get_actor_label(),
        "asset": mesh.get_path_name() if mesh else None,
        "collision_enabled": str(enabled),
        "collision_profile": str(component.get_collision_profile_name()),
        "has_collision": enabled != unreal.CollisionEnabled.NO_COLLISION,
        "can_ever_affect_navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
        "collision_trace_flag": trace,
        "simple_collision_element_count": simple_elements,
    }


station_static = [actor for actor in actors if unreal.Name("LB.Structure.PR009") in actor.tags]
modular = [actor for actor in actors if actor.get_actor_label().startswith(PREFIX + "MOD_")]
interface = [actor for actor in actors if unreal.Name("LB.Interface.PR008.PR009") in actor.tags]
static_collision = [collision_row(actor) for actor in station_static]
modular_collision = [collision_row(actor) for actor in modular]
interface_collision = [collision_row(actor) for actor in interface]

if len(station_static) != 10:
    failures.append(f"Expected 10 combined static PR-009 support actors; found {len(station_static)}")
if len(modular) != 158:
    failures.append(f"Expected 158 modular PR-009 presentation actors; found {len(modular)}")
if not interface:
    failures.append("No PR-008/PR-009 supported-interface actors found")
for row in static_collision:
    if not row.get("has_collision") or "BLOCKALL" not in row.get("collision_profile", "").upper():
        failures.append(f"Station static collision missing or not BlockAll: {row.get('actor')}")
if any(row.get("has_collision") for row in modular_collision):
    failures.append("One or more native-bound modular presentation meshes unexpectedly collide")
if not any(row.get("has_collision") for row in interface_collision):
    failures.append("Supported PR-008/PR-009 interface has no blocking collision coverage")

complex_as_simple = [row for row in static_collision + interface_collision
                     if "COMPLEX_AS_SIMPLE" in (row.get("collision_trace_flag") or "").upper()]
release_collision_ready = not complex_as_simple and all(
    (not row.get("has_collision")) or (row.get("simple_collision_element_count") or 0) > 0
    for row in static_collision + interface_collision)

pr010_actor_rows = []
for actor in actors:
    text = "|".join([actor.get_actor_label(), actor.get_name(), actor.get_class().get_name()]
                    + [str(tag) for tag in actor.tags])
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component and component.get_editor_property("static_mesh"):
        text += "|" + component.get_editor_property("static_mesh").get_path_name()
    if "PR010" in text.upper() or "PR-010" in text.upper():
        pr010_actor_rows.append(actor_ref(actor))
if pr010_actor_rows:
    failures.append(f"PR-010 actor/asset references exist in target map: {len(pr010_actor_rows)}")

payload = {
    "$schema": "cairnwell/audit/press-shop-pr009-in-map-static/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "target_map": TARGET_MAP,
    "target_version": VERSION,
    "status": "PASS_WITH_TEMPORARY_COLLISION__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "native_cardinality": {
        "pr008_count": len(pr008), "pr009_count": len(pr009), "material_flow_count": len(flows),
        "pr008": [actor_ref(actor) for actor in pr008],
        "pr009": [actor_ref(actor) for actor in pr009],
        "material_flow": [actor_ref(actor) for actor in flows],
    },
    "material_flow_binding": binding,
    "actor_inventory": {
        "map_actor_count": len(actors),
        "pr009_static_actor_count": len(station_static),
        "pr009_modular_presentation_count": len(modular),
        "pr008_pr009_interface_actor_count": len(interface),
    },
    "collision": {
        "station_static": static_collision,
        "modular_presentation": modular_collision,
        "supported_interface": interface_collision,
        "complex_as_simple_actor_count": len(complex_as_simple),
        "complex_as_simple_actors": [row["actor"] for row in complex_as_simple],
        "technical_coverage_present": not any("collision" in failure.lower() for failure in failures),
        "release_collision_ready": release_collision_ready,
        "release_collision_policy": "Complex-as-simple is accepted only as temporary candidate coverage; release requires authored simple/convex collision and swept-volume validation.",
    },
    "pr010_actor_or_asset_references": pr010_actor_rows,
    "failures": failures,
    "map_saved_or_modified_by_validator": False,
    "promotion_authorized": False,
}
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"CAIRNWELL_PR009_IN_MAP_STATIC_{'PASS' if not failures else 'FAIL'} output={OUT}")
unreal.SystemLibrary.quit_editor()
if failures:
    raise RuntimeError(f"PR-009 static in-map audit failed: {failures}")
