"""Exact static gate for Train A sightline candidate v013."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
TARGET_VERSION = os.environ.get("LB_PTA_SIGHTLINE_TARGET_VERSION", "v013")
ROBOT_PAINT_MODE = os.environ.get("LB_PTA_ROBOT_PAINT_MODE", "legacy_orange").lower()
MAP = os.environ.get("LB_PTA_SIGHTLINE_TARGET_MAP", "/Game/LineBoss/Maps/LB_PressTrainASightlineCandidate_v013")
SOURCE_MAP = os.environ.get("LB_PTA_SIGHTLINE_SOURCE_MAP", "/Game/LineBoss/Maps/LB_PressTrainAMotionCandidate_v012")
OUT = ROOT / f"Saved/Audits/PressTrains/press_train_a_sightline_static_{TARGET_VERSION}.json"
MAP_FILE = ROOT / "Content/LineBoss/Maps" / (MAP.rsplit("/", 1)[-1] + ".umap")
SOURCE_MAP_FILE = ROOT / "Content/LineBoss/Maps" / (SOURCE_MAP.rsplit("/", 1)[-1] + ".umap")
PROTECTED = {
    "v010": (ROOT / "Content/LineBoss/Maps/LB_PressTrainARuntimeCandidate_v010.umap",
             "8CA5F44D54F3D47E160AF54D92C6D8307BC74CAF0778711FA3A71E1C76E81DD2"),
    "v107": (ROOT / "Content/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107.umap",
             "E6851D041D3D566B2FE32560F331725CBB1FE84B034E7B86DA9B0D33191ECF77"),
    "v213": (ROOT / "Content/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v213.umap",
             "1790B48ABF75762A474C6F3FDB91B2ABD3AD9088B5430D08DC1905154CDF6554"),
}
EXPECTED_SOURCE = os.environ.get("LB_PTA_SIGHTLINE_EXPECTED_SOURCE_SHA256",
                                 "E51F2EDE5D8D2C71FC7E096E79535A6389E4FEC5EADBF373842268E32C22F688")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = actors_api.get_all_level_actors()


def tags(actor):
    return {str(value) for value in actor.tags}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


failures = []
authorities = [actor for actor in actors if isinstance(actor, unreal.LBPressTrainAStation)]
if len(authorities) != 1:
    failures.append(f"Expected one native authority, found {len(authorities)}")
presentation = [actor for actor in actors if any(value.startswith("LB.PressTrain.Role.") for value in tags(actor))]
if len(presentation) != 336:
    failures.append(f"Expected 336 presentation actors, found {len(presentation)}")
scoped = [actor for actor in actors if f"LB.PressTrain.TrainA.Sightline.{TARGET_VERSION}" in tags(actor)
          or f"LB.Asset.Candidate.{TARGET_VERSION}" in tags(actor)]
scope_missing = [actor.get_actor_label() for actor in scoped
                 if "LB.Asset.CandidateNotPromoted" not in tags(actor)
                 or "LB.Authority.WorldPlacement.TBCNotInvented" not in tags(actor)]
if scope_missing:
    failures.append(f"{TARGET_VERSION} scope tags missing: {scope_missing}")

binding_counts = {
    "destack": sum("LB.PressTrain.Role.destack_lift" in tags(actor) for actor in actors),
    "transfer": sum("LB.PressTrain.Role.transfer_crossbar" in tags(actor)
                    or "LB.PressTrain.Role.transfer_gripper" in tags(actor) for actor in actors),
    "moving_slides": sum("LB.PressTrain.Role.moving_press_slide" in tags(actor) for actor in actors),
    "moving_upper_dies": sum("LB.PressTrain.Role.moving_upper_die" in tags(actor) for actor in actors),
    "carried_workpieces": sum("LB.PressTrain.Role.carried_workpiece_state" in tags(actor) for actor in actors),
    "unload_robot_shoulder": sum("LB.PressTrain.Role.unload_robot_shoulder_runtime" in tags(actor) for actor in actors),
    "formed_panel": sum("LB.PressTrain.Role.visible_formed_panel" in tags(actor)
                        or "LB.PressTrain.Role.formed_panel_positive_y_discharge" in tags(actor) for actor in actors),
    "red_beacons": sum("LB.PressTrain.Role.state_beacon_red" in tags(actor) for actor in actors),
    "amber_beacons": sum("LB.PressTrain.Role.state_beacon_amber" in tags(actor) for actor in actors),
    "green_beacons": sum("LB.PressTrain.Role.state_beacon_green" in tags(actor) for actor in actors),
}
expected = {"destack": 3, "transfer": 25, "moving_slides": 5, "moving_upper_dies": 5,
            "carried_workpieces": 5, "unload_robot_shoulder": 1, "formed_panel": 2,
            "red_beacons": 5, "amber_beacons": 5, "green_beacons": 5}
if binding_counts != expected:
    failures.append(f"Binding-role mismatch: {binding_counts}")

hmi = [actor for actor in actors if "LB.HMI.PressTrainA.LiveState" in tags(actor)]
hmi_bound = len(hmi) == 1 and isinstance(hmi[0], unreal.TextRenderActor) \
    and f"LB.HMI.PressTrainA.BoundToAuthoredScreen.{TARGET_VERSION}" in tags(hmi[0])
if not hmi_bound:
    failures.append(f"Live HMI is not uniquely bound to authored {TARGET_VERSION} screen")
hmi_location_cm = None
if hmi:
    loc = hmi[0].get_actor_location()
    hmi_location_cm = [round(loc.x, 3), round(loc.y, 3), round(loc.z, 3)]
    if max(abs(a - b) for a, b in zip(hmi_location_cm, [644.0, 4150.0, 260.0])) > .5:
        failures.append(f"Live HMI transform does not match authored screen: {hmi_location_cm}")

glass_actors = [actor for actor in actors if "LB.PressTrain.Role.operator_inspection_window" in tags(actor)]
glass_materials = []
for actor in glass_actors:
    material = actor.static_mesh_component.get_material(0)
    mode = str(material.get_editor_property("blend_mode")) if material else "MISSING"
    glass_materials.append({"actor": actor.get_actor_label(), "material": material.get_path_name() if material else None,
                            "blend_mode": mode})
if len(glass_actors) != 5 or any("TRANSLUCENT" not in row["blend_mode"].upper() for row in glass_materials):
    failures.append(f"Expected five translucent inspection glazing actors: {glass_materials}")
heavy_throats = [actor for actor in actors if actor.get_actor_label().startswith((
    "PTA_S02_HeavyFrame_", "PTA_S03_HeavyFrame_", "PTA_S04_HeavyFrame_",
    "PTA_S05_HeavyFrame_", "PTA_S06_HeavyFrame_"))]
if len(heavy_throats) != 5:
    failures.append(f"Expected five v007 heavy-frame throat actors, found {len(heavy_throats)}")
true_frames = [actor for actor in actors if "LB.PressTrain.Role.operator_inspection_window_bezel" in tags(actor)]
if len(true_frames) != 5:
    failures.append(f"Expected five true window frames, found {len(true_frames)}")

hierarchy_roles = {"unload_robot_shoulder_runtime", "unload_robot_upper_arm_runtime",
                   "unload_robot_elbow_runtime", "unload_robot_forearm_runtime",
                   "unload_robot_wrist_runtime", "unload_robot_gripper_runtime", "unload_robot_tool_runtime"}
hierarchy = [actor for actor in actors
             if any(f"LB.PressTrain.Role.{role}" in tags(actor) for role in hierarchy_roles)]
edges = [{"child": actor.get_actor_label(), "parent": actor.get_attach_parent_actor().get_actor_label()}
         for actor in hierarchy if actor.get_attach_parent_actor()]
if len(hierarchy) != 8 or len(edges) != 8:
    failures.append(f"Robot hierarchy mismatch actors={len(hierarchy)} edges={len(edges)}")

portal_braces = [actor for actor in actors if "LB.PressTrain.Role.inspection_cantilever_brace" in tags(actor)]
portal_leds = [actor for actor in actors if "LB.PressTrain.Role.inspection_cantilever_led" in tags(actor)]
if TARGET_VERSION != "v013" and (len(portal_braces) != 2 or len(portal_leds) != 2):
    failures.append(f"Open robot-side portal mismatch: braces={len(portal_braces)} leds={len(portal_leds)}")
robot_paint = []
for actor in actors:
    if not any(f"LB.PressTrain.Role.{role}" in tags(actor) for role in
               ("unload_robot_shoulder_runtime", "unload_robot_upper_arm_runtime", "unload_robot_forearm_runtime")):
        continue
    paths = []
    for index in range(len(actor.static_mesh_component.get_materials())):
        material = actor.static_mesh_component.get_material(index)
        if material:
            paths.append(material.get_path_name())
    robot_paint.append({"actor": actor.get_actor_label(), "materials": paths})
if TARGET_VERSION != "v013":
    if ROBOT_PAINT_MODE == "family_charcoal_orange":
        family_charcoal = len(robot_paint) == 3 and all(
            any("Charcoal" in path for path in row["materials"]) for row in robot_paint
        )
        family_accent = any(
            "RobotSafetyYellow" in path for row in robot_paint for path in row["materials"]
        )
        if not family_charcoal or not family_accent:
            failures.append(f"Cairnwell family charcoal/orange paint mismatch: {robot_paint}")
    elif len(robot_paint) != 3 or any(
        not any("RobotSafetyYellow" in path for path in row["materials"])
        for row in robot_paint
    ):
        failures.append(f"Dedicated retained robot paint mismatch: {robot_paint}")

source_hash = sha(SOURCE_MAP_FILE)
if source_hash != EXPECTED_SOURCE:
    failures.append(f"Protected source map changed: {source_hash}")
protected_hashes = {}
for key, (path, expected_hash) in PROTECTED.items():
    actual = sha(path)
    protected_hashes[key] = actual
    if actual != expected_hash:
        failures.append(f"Protected {key} changed: {actual}")

pass_status = ("PASS__V013_NATIVE_AUTHORITY_EXACT_MOTION_TRUE_THROATS_TRANSLUCENT_GLAZING_AUTHORED_HMI_LINEAGE_SAVE_GATE__RUNTIME_VISUAL_RELEASE_OPEN__NOT_PROMOTED"
               if TARGET_VERSION == "v013" else
               f"PASS__{TARGET_VERSION.upper()}_NATIVE_AUTHORITY_EXACT_MOTION_OPEN_S07_ROBOT_SIDE_RESTRAINED_ROBOT_PAINT_TRUE_THROATS_TRANSLUCENT_GLAZING_AUTHORED_HMI_LINEAGE_SAVE_GATE__RUNTIME_VISUAL_RELEASE_OPEN__NOT_PROMOTED")
report = {"$schema": f"cairnwell/audit/press-train-a-sightline-static-{TARGET_VERSION}/v1",
          "generated_utc": datetime.now(timezone.utc).isoformat(),
          "status": pass_status if not failures else f"FAIL__{TARGET_VERSION.upper()}_SIGHTLINE_STATIC_GATE__NOT_PROMOTED",
          "map": MAP, "map_sha256": sha(MAP_FILE), "source_map": SOURCE_MAP,
          "source_map_sha256": source_hash, "native_authority_count": len(authorities),
          "presentation_actor_count": len(presentation), "binding_role_counts": binding_counts,
          "sightline_scoped_actor_count": len(scoped), "scope_missing": scope_missing,
          "live_hmi_count": len(hmi), "hmi_bound_to_authored_screen": hmi_bound,
          "hmi_location_cm": hmi_location_cm, "translucent_glazing": glass_materials,
          "heavy_frame_throat_actor_count": len(heavy_throats), "true_window_frame_count": len(true_frames),
          "robot_hierarchy_edges": edges, "open_robot_side_portal_brace_count": len(portal_braces),
          "open_robot_side_portal_led_count": len(portal_leds), "robot_paint_mode": ROBOT_PAINT_MODE,
          "robot_paint": robot_paint,
          "save_root_format": 11,
          "protected_map_hashes": protected_hashes, "world_placement": "TBC_NOT_INVENTED",
          "failures": failures, "production_map_changed": False, "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
