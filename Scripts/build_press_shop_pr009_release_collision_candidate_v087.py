"""Build isolated PR-009 v087 with deterministic simple release collision."""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from press_shop_pr009_release_collision_v087_config import PARENT_MAP, TARGET_MAP, STATIC_DEST, MOVING_DEST

root = Path(unreal.Paths.project_dir())
source_audit_path = root / "Saved/Audits/PR009_InMap_v087/source_collision_evidence.json"
out = root / "Saved/Audits/PR009_InMap_v087/release_collision_build.json"
source = json.loads(source_audit_path.read_text(encoding="utf-8"))
if source.get("supplied_ucx_count") != 12 or source.get("missing_source_objects"):
    raise RuntimeError("Source collision evidence is incomplete")

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

created_map = False
if not lib.does_asset_exist(TARGET_MAP):
    if not lib.duplicate_asset(PARENT_MAP, TARGET_MAP):
        raise RuntimeError(f"Could not duplicate immutable parent {PARENT_MAP}")
    if not lib.save_asset(TARGET_MAP, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save duplicated target {TARGET_MAP}")
    created_map = True
if created_map:
    unreal.log("PR009_V087_MAP_DUPLICATED__RERUN_FOR_COLLISION_AUTHORING")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(f"Could not load {TARGET_MAP}")

STATIC_KEYS = sorted(source["static_groups"])
UCX = {row["name"]: row for row in source["supplied_ucx_candidates"]}

def source_to_unreal_box(row, source_name):
    rotation = row.get("rotation_euler_degrees", [0.0, 0.0, 0.0])
    if any(abs(value) > 0.01 for value in rotation[:2]):
        raise RuntimeError(f"Unsupported non-upright source collision object {source_name}: {rotation}")
    return {
        "source": source_name,
        "center_cm": [row["location_m"][0] * 100.0, -row["location_m"][1] * 100.0, row["location_m"][2] * 100.0],
        "dimensions_cm": [value * 100.0 for value in row["dimensions_m"]],
        "rotation_degrees": [0.0, -rotation[2], 0.0],
    }

def selected(asset, predicate):
    return [source_to_unreal_box(row, row["name"]) for row in source["static_groups"][asset] if predicate(row)]

plan = {}
plan["SM_CA_MW_PR009_BaseFrame_01"] = selected(
    "SM_CA_MW_PR009_BaseFrame_01", lambda row: row["semantic"] in {"gantry_column", "cable_tray", "machine_foot"})

carrier_rows = [row for row in source["static_groups"]["SM_CA_MW_PR009_Carrier_01"] if row["semantic"] == "blank_stack"]
carrier_min = [min(row["bounds_min_m"][axis] for row in carrier_rows) for axis in range(3)]
carrier_max = [max(row["bounds_max_m"][axis] for row in carrier_rows) for axis in range(3)]
carrier_row = {"location_m": [(carrier_min[i] + carrier_max[i]) * 0.5 for i in range(3)],
               "dimensions_m": [carrier_max[i] - carrier_min[i] for i in range(3)],
               "rotation_euler_degrees": [0.0, 0.0, 0.0]}
plan["SM_CA_MW_PR009_Carrier_01"] = [source_to_unreal_box(carrier_row, "AUTHORED_UNION_PR009_BlankStack")]
plan["SM_CA_MW_PR009_ElectricalCabinet_01"] = [source_to_unreal_box(UCX["UCX_PR009_Cabinet_01"], "UCX_PR009_Cabinet_01")]

guard_boxes = [source_to_unreal_box(UCX[name], name) for name in (
    "UCX_PR009_GuardOperator_01", "UCX_PR009_GuardServiceA_01",
    "UCX_PR009_GuardServiceB_01", "UCX_PR009_GuardServiceC_01")]
guard_boxes += selected("SM_CA_MW_PR009_GuardSet_01", lambda row:
    row["semantic"] == "guard_frame" and any(token in row["name"] for token in (
        "Guard_InfeedLeft_", "Guard_InfeedRight_", "Guard_OutfeedLeft_", "Guard_OutfeedRight_")))
plan["SM_CA_MW_PR009_GuardSet_01"] = guard_boxes
plan["SM_CA_MW_PR009_HMI_01"] = [source_to_unreal_box(UCX["UCX_PR009_HMI_01"], "UCX_PR009_HMI_01")]
plan["SM_CA_MW_PR009_InspectionHardware_01"] = selected(
    "SM_CA_MW_PR009_InspectionHardware_01", lambda row: row["semantic"] == "sensor" and row["name"].endswith("_Body"))
plan["SM_CA_MW_PR009_InteractionHardware_01"] = selected(
    "SM_CA_MW_PR009_InteractionHardware_01", lambda row: row["semantic"] in {"loto_cabinet", "estop_housing"})
plan["SM_CA_MW_PR009_ServiceSystems_01"] = selected(
    "SM_CA_MW_PR009_ServiceSystems_01", lambda row: row["semantic"] in {"cable_trunking", "field_io_box"})
plan["SM_CA_MW_PR009_TracePortal_01"] = selected(
    "SM_CA_MW_PR009_TracePortal_01", lambda row: row["semantic"] in {"trace_portal_beam", "trace_portal_post"})
plan["SM_CA_MW_PR009_VisionCentre_01"] = selected(
    "SM_CA_MW_PR009_VisionCentre_01", lambda row: row["semantic"] in {"frame_rail", "vision_beam"})

expected_counts = {"SM_CA_MW_PR009_BaseFrame_01": 15, "SM_CA_MW_PR009_Carrier_01": 1,
                   "SM_CA_MW_PR009_ElectricalCabinet_01": 1, "SM_CA_MW_PR009_GuardSet_01": 20,
                   "SM_CA_MW_PR009_HMI_01": 1, "SM_CA_MW_PR009_InspectionHardware_01": 3,
                   "SM_CA_MW_PR009_InteractionHardware_01": 4, "SM_CA_MW_PR009_ServiceSystems_01": 7,
                   "SM_CA_MW_PR009_TracePortal_01": 3, "SM_CA_MW_PR009_VisionCentre_01": 3}
actual_counts = {key: len(value) for key, value in plan.items()}
if actual_counts != expected_counts:
    raise RuntimeError(f"Deterministic collision plan count mismatch: {actual_counts}")

query_only = {"SM_CA_MW_PR009_Carrier_01", "SM_CA_MW_PR009_InspectionHardware_01",
              "SM_CA_MW_PR009_InteractionHardware_01", "SM_CA_MW_PR009_ServiceSystems_01"}
nav_relevant = set(STATIC_KEYS) - query_only

def collision_counts(mesh):
    body = mesh.get_editor_property("body_setup")
    agg = body.get_editor_property("agg_geom")
    counts = {"box": len(agg.get_editor_property("box_elems")),
              "sphere": len(agg.get_editor_property("sphere_elems")),
              "capsule": len(agg.get_editor_property("sphyl_elems")),
              "convex": len(agg.get_editor_property("convex_elems"))}
    counts["total"] = sum(counts.values())
    return counts

def apply_boxes(mesh, boxes):
    body = mesh.get_editor_property("body_setup")
    agg = unreal.KAggregateGeom()
    elements = []
    for spec in boxes:
        elem = unreal.KBoxElem()
        elem.set_editor_property("center", unreal.Vector(*spec["center_cm"]))
        elem.set_editor_property("rotation", unreal.Rotator(*spec["rotation_degrees"]))
        elem.set_editor_property("x", spec["dimensions_cm"][0])
        elem.set_editor_property("y", spec["dimensions_cm"][1])
        elem.set_editor_property("z", spec["dimensions_cm"][2])
        elements.append(elem)
    agg.set_editor_property("box_elems", elements)
    body.set_editor_property("agg_geom", agg)
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    body.modify()
    mesh.modify()
    lib.save_loaded_asset(mesh, only_if_is_dirty=False)
    counts = collision_counts(mesh)
    if counts != {"box": len(boxes), "sphere": 0, "capsule": 0, "convex": 0, "total": len(boxes)}:
        raise RuntimeError(f"Collision persistence mismatch for {mesh.get_path_name()}: {counts}")
    return counts

def key_from_mesh(mesh):
    name = mesh.get_name()
    for key in STATIC_KEYS:
        if key in name:
            return key
    return None

static_rows = []
static_actors = [actor for actor in actors_api.get_all_level_actors() if unreal.Name("LB.Structure.PR009") in actor.tags]
if len(static_actors) != 10:
    raise RuntimeError(f"Expected ten v086 static groups in duplicated map, found {len(static_actors)}")
for actor in static_actors:
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    old_mesh = component.get_editor_property("static_mesh")
    key = key_from_mesh(old_mesh)
    if key is None:
        raise RuntimeError(f"Unknown PR-009 static mesh {old_mesh.get_path_name()}")
    dest_path = f"{STATIC_DEST}/{key}_v087"
    new_mesh = lib.load_asset(dest_path)
    if new_mesh is None:
        if not lib.duplicate_asset(old_mesh.get_path_name().split(".")[0], dest_path):
            raise RuntimeError(f"Could not duplicate {old_mesh.get_path_name()} to {dest_path}")
        new_mesh = lib.load_asset(dest_path)
    counts = apply_boxes(new_mesh, plan[key])
    component.set_static_mesh(new_mesh)
    if key in query_only:
        component.set_collision_profile_name(unreal.Name("OverlapAll"))
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    else:
        component.set_collision_profile_name(unreal.Name("BlockAll"))
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_editor_property("can_ever_affect_navigation", key in nav_relevant)
    label = actor.get_actor_label().replace("LB_PR009_V086_", "LB_PR009_V087_")
    actor.set_actor_label(label)
    actor.tags = [unreal.Name(str(tag).replace("v086", "v087")) for tag in actor.tags] + [unreal.Name("LB.Collision.ReleaseCandidate.v087")]
    static_rows.append({"group": key, "actor": label,
                        "source_asset": f"/Game/LineBoss/Candidates/PressShop/PR009/v003/Static/{key}.{key}",
                        "release_asset": new_mesh.get_path_name(), "simple_collision": counts,
                        "collision_profile": str(component.get_collision_profile_name()),
                        "collision_enabled": str(component.get_editor_property("body_instance").get_editor_property("collision_enabled")),
                        "nav_relevant": key in nav_relevant, "primitives": plan[key]})

def moving_role(label):
    patterns = {
        "infeed_roll": r"MOD_PR009_M01_InfeedRoll_", "gantry_bridge": r"MOD_PR009_M02_GantryBridge_01$",
        "gantry_cross_slide": r"MOD_PR009_M03_GantryCrossSlide_01$", "gantry_z": r"MOD_PR009_M04_GantryZ_Carriage_01$",
        "lift": r"MOD_PR009_M05_LiftTable_01$", "side_jogger": r"MOD_PR009_M06_SideJogger_",
        "end_jogger": r"MOD_PR009_M07_EndJogger_01$", "separator_picker": r"MOD_PR009_M08_SeparatorPicker_01$",
        "output_roll": r"MOD_PR009_08_OutputRoll_",
    }
    for role, pattern in patterns.items():
        if re.search(pattern, label):
            return role
    return None

moving_rows = []
moving_assets = {}
for actor in actors_api.get_all_level_actors():
    old_label = actor.get_actor_label()
    if old_label.startswith("LB_PR009_V086_"):
        actor.set_actor_label(old_label.replace("LB_PR009_V086_", "LB_PR009_V087_"))
        actor.tags = [unreal.Name(str(tag).replace("v086", "v087")) for tag in actor.tags]
    role = moving_role(actor.get_actor_label())
    if role is None:
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    old_mesh = component.get_editor_property("static_mesh") if component else None
    if old_mesh is None:
        raise RuntimeError(f"Selected mover has no static mesh: {actor.get_actor_label()}")
    old_asset_path = old_mesh.get_path_name().split(".")[0]
    if old_asset_path not in moving_assets:
        dest_path = old_asset_path if old_asset_path.startswith(MOVING_DEST + "/") else f"{MOVING_DEST}/{old_mesh.get_name()}_v087"
        new_mesh = lib.load_asset(dest_path)
        if new_mesh is None:
            if not lib.duplicate_asset(old_asset_path, dest_path):
                raise RuntimeError(f"Could not duplicate moving mesh {old_asset_path}")
            new_mesh = lib.load_asset(dest_path)
        box = new_mesh.get_bounding_box()
        spec = {"source": "AUTHORED_FROM_UNREAL_RENDER_BOUNDS", "center_cm": [
                    (box.min.x + box.max.x) * 0.5, (box.min.y + box.max.y) * 0.5, (box.min.z + box.max.z) * 0.5],
                "dimensions_cm": [box.max.x - box.min.x, box.max.y - box.min.y, box.max.z - box.min.z],
                "rotation_degrees": [0.0, 0.0, 0.0]}
        counts = apply_boxes(new_mesh, [spec])
        moving_assets[old_asset_path] = (new_mesh, counts, spec)
    new_mesh, counts, spec = moving_assets[old_asset_path]
    component.set_static_mesh(new_mesh)
    component.set_collision_profile_name(unreal.Name("OverlapAllDynamic"))
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    component.set_editor_property("can_ever_affect_navigation", False)
    actor.tags = list(actor.tags) + [unreal.Name("LB.Collision.SelectiveMover.v087")]
    moving_rows.append({"actor": actor.get_actor_label(), "role": role, "source_asset": old_mesh.get_path_name(),
                        "release_asset": new_mesh.get_path_name(), "simple_collision": counts,
                        "collision_profile": str(component.get_collision_profile_name()), "nav_relevant": False,
                        "primitive": spec})

def fixed_chassis_role(label):
    patterns = {
        "gantry_rail": r"MOD_PR009_03_GantryLongRail_", "drive_gearbox": r"MOD_PR009_(01|08)_DRIVE_Gearbox$",
        "drive_motor": r"MOD_PR009_(01|08)_DRIVE_MotorBody$", "drive_guard": r"MOD_PR009_(01|08)_DriveChainGuard$",
        "infeed_frame": r"MOD_PR009_01_Infeed_FrameRail_", "lift_pit_frame": r"MOD_PR009_04_LiftPitFrame$",
        "output_frame": r"MOD_PR009_08_Output_FrameRail_", "separator_base": r"MOD_PR009_06_SeparatorBase$",
    }
    for role, pattern in patterns.items():
        if re.search(pattern, label):
            return role
    return None

fixed_rows = []
fixed_assets = {}
for actor in actors_api.get_all_level_actors():
    role = fixed_chassis_role(actor.get_actor_label())
    if role is None:
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    old_mesh = component.get_editor_property("static_mesh") if component else None
    if old_mesh is None:
        raise RuntimeError(f"Selected fixed chassis actor has no mesh: {actor.get_actor_label()}")
    old_asset_path = old_mesh.get_path_name().split(".")[0]
    if old_asset_path not in fixed_assets:
        dest_path = old_asset_path if old_asset_path.startswith(MOVING_DEST + "/") else f"{MOVING_DEST}/{old_mesh.get_name()}_v087"
        new_mesh = lib.load_asset(dest_path)
        if new_mesh is None:
            if not lib.duplicate_asset(old_asset_path, dest_path):
                raise RuntimeError(f"Could not duplicate fixed chassis mesh {old_asset_path}")
            new_mesh = lib.load_asset(dest_path)
        box = new_mesh.get_bounding_box()
        spec = {"source": "AUTHORED_FROM_UNREAL_RENDER_BOUNDS", "center_cm": [
                    (box.min.x + box.max.x) * 0.5, (box.min.y + box.max.y) * 0.5, (box.min.z + box.max.z) * 0.5],
                "dimensions_cm": [box.max.x - box.min.x, box.max.y - box.min.y, box.max.z - box.min.z],
                "rotation_degrees": [0.0, 0.0, 0.0]}
        counts = apply_boxes(new_mesh, [spec])
        fixed_assets[old_asset_path] = (new_mesh, counts, spec)
    new_mesh, counts, spec = fixed_assets[old_asset_path]
    component.set_static_mesh(new_mesh)
    component.set_collision_profile_name(unreal.Name("BlockAll"))
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_editor_property("can_ever_affect_navigation", True)
    actor.tags = list(actor.tags) + [unreal.Name("LB.Collision.FixedChassis.v087")]
    fixed_rows.append({"actor": actor.get_actor_label(), "role": role, "source_asset": old_mesh.get_path_name(),
                       "release_asset": new_mesh.get_path_name(), "simple_collision": counts,
                       "collision_profile": str(component.get_collision_profile_name()), "nav_relevant": True,
                       "primitive": spec})
if len(fixed_rows) != 14:
    raise RuntimeError(f"Expected 14 substantial fixed-chassis collision actors, found {len(fixed_rows)}")

# Confirm all visual/material/camera objects are inherited, while v087 authoring
# is restricted to collision assets, collision settings, labels and metadata.
camera_count = len([actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.CameraActor)
                    and unreal.Name("LB.Camera.Validation") in actor.tags])
flows = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
pr008 = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR008Station)]
pr009 = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR009Station)]
if len(flows) != 1 or len(pr008) != 1 or len(pr009) != 1:
    raise RuntimeError(f"Authority cardinality changed: flow={len(flows)} PR008={len(pr008)} PR009={len(pr009)}")
flows[0].bind_blank_stations(pr008[0], pr009[0])

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {TARGET_MAP}")
lib.save_directory(STATIC_DEST, only_if_is_dirty=False, recursive=True)
lib.save_directory(MOVING_DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "cairnwell/audit/pr009-release-collision-build-v087/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "V087_SIMPLE_COLLISION_AUTHORED__FULL_RUNTIME_AND_SWEEP_GATES_REQUIRED__NOT_PROMOTED",
    "parent_map": PARENT_MAP, "target_map": TARGET_MAP,
    "source_collision_evidence": source_audit_path.relative_to(root).as_posix(),
    "supplied_ucx_assessment": source["assessment"],
    "static_groups": sorted(static_rows, key=lambda row: row["group"]),
    "static_group_count": len(static_rows),
    "static_simple_primitive_total": sum(row["simple_collision"]["total"] for row in static_rows),
    "moving_collision_actors": sorted(moving_rows, key=lambda row: row["actor"]),
    "moving_collision_actor_count": len(moving_rows),
    "moving_unique_asset_count": len(moving_assets),
    "fixed_chassis_collision_actors": sorted(fixed_rows, key=lambda row: row["actor"]),
    "fixed_chassis_collision_actor_count": len(fixed_rows),
    "fixed_chassis_unique_asset_count": len(fixed_assets),
    "intentionally_non_colliding_visual_policy": [
        "fasteners, cable glands, cables/hoses and sensor lenses remain NoCollision",
        "individual blank/separator sheet visuals remain NoCollision; carrier/blank clearance is validated by swept envelope",
        "non-selected cosmetic modular presentation parts remain NoCollision",
    ],
    "validation_camera_count": camera_count,
    "visual_mesh_geometry_changed": False, "materials_changed": False, "lighting_changed": False, "cameras_changed": False,
    "collision_behavior_distinction": {
        "fixed_static_and_chassis": "BlockAll QueryAndPhysics; physical service/robot/drone obstruction",
        "selected_movers": "OverlapAllDynamic QueryOnly; sensing/inspection envelopes and never physical blockers",
    },
    "singleton_flow_authority_preserved": True, "pr010_started": False, "promotion_authorized": False,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"PR009_V087_RELEASE_COLLISION_BUILD_PASS static={len(static_rows)} fixed_chassis={len(fixed_rows)} movers={len(moving_rows)} output={out}")
unreal.SystemLibrary.quit_editor()
