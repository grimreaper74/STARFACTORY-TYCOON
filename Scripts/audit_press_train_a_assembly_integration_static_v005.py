"""Exact-map import/static/collision/navigation/performance/branding gate for Train A v005."""

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v005"
DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v005"
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v001"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v001.json"
AUTHORED_RECEIPT_PATH = ROOT / "Saved/Audits/PressTrains/press_train_a_assembly_instance_staging_v005.json"
BUILD_PATH = ROOT / "Saved/Audits/PressTrains/press_train_a_assembly_integration_build_v005.json"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_assembly_integration_static_v005.json"
FAILURES_OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_assembly_integration_failed_scale_history_v001_v004.json"
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
authored_receipt = json.loads(AUTHORED_RECEIPT_PATH.read_text(encoding="utf-8"))
build = json.loads(BUILD_PATH.read_text(encoding="utf-8"))
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = list(actors_api.get_all_level_actors())


def tags(actor):
    return {str(value) for value in actor.tags}


def slot_names(mesh):
    return [str(row.get_editor_property("material_slot_name")) for row in mesh.get_editor_property("static_materials")]


scope = [actor for actor in actors if "LB.PressTrain.TrainA.AssemblyIntegration.v005" in tags(actor)]
presentation = [actor for actor in scope if isinstance(actor, unreal.StaticMeshActor)
                and any(value.startswith("LB.PressTrain.Role.") for value in tags(actor))]
by_source_name = {actor.get_actor_label()[:-7]: actor for actor in presentation if actor.get_actor_label().endswith("_UEv005")}
failures = []
transform_errors = []
material_errors = []
collision_errors = []
for record in manifest["instances"]:
    actor = by_source_name.get(record["name"])
    if actor is None:
        transform_errors.append({"object": record["name"], "error": "missing"})
        continue
    loc = actor.get_actor_location(); rot = actor.get_actor_rotation(); scale = actor.get_actor_scale3d()
    actual_loc = [loc.x * 10, loc.y * 10, loc.z * 10]
    actual_rot = [rot.roll, rot.pitch, rot.yaw]
    if any(abs(a-b) > 0.05 for a,b in zip(actual_loc, record["location_mm"])) or any(abs(a-b) > 0.05 for a,b in zip(actual_rot, record["rotation_deg"])) or any(abs(a-b) > 1e-5 for a,b in zip((scale.x,scale.y,scale.z),record["scale"])):
        transform_errors.append({"object": record["name"], "location_mm": actual_loc, "rotation_deg_xyz": actual_rot})
    comp = actor.static_mesh_component
    if comp.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION or comp.get_editor_property("can_ever_affect_navigation"):
        collision_errors.append(actor.get_actor_label())
    for index, _slot in enumerate(comp.get_material_slot_names()):
        material = comp.get_material(index)
        if material is None or not material.get_path_name().startswith(DEST + "/Materials/"):
            material_errors.append({"actor": actor.get_actor_label(), "index": index,
                                    "material": material.get_path_name() if material else None})
if len(presentation) != 163:
    failures.append(f"expected 163 presentation actors, found {len(presentation)}")
if transform_errors:
    failures.append(f"manifest transform mismatches: {len(transform_errors)}")
if material_errors:
    failures.append(f"material assignment mismatches: {len(material_errors)}")
if collision_errors:
    failures.append(f"visual collision policy mismatches: {len(collision_errors)}")

minimum = unreal.Vector(1e12,1e12,1e12); maximum = unreal.Vector(-1e12,-1e12,-1e12)
for actor in presentation:
    origin, extent = actor.get_actor_bounds(False, False)
    minimum.x=min(minimum.x,origin.x-extent.x); minimum.y=min(minimum.y,origin.y-extent.y); minimum.z=min(minimum.z,origin.z-extent.z)
    maximum.x=max(maximum.x,origin.x+extent.x); maximum.y=max(maximum.y,origin.y+extent.y); maximum.z=max(maximum.z,origin.z+extent.z)
bounds = {"min_mm":[round(minimum.x*10,3),round(minimum.y*10,3),round(minimum.z*10,3)],
          "max_mm":[round(maximum.x*10,3),round(maximum.y*10,3),round(maximum.z*10,3)],
          "dimensions_mm":[round((maximum.x-minimum.x)*10,3),round((maximum.y-minimum.y)*10,3),round((maximum.z-minimum.z)*10,3)]}
expected = manifest["measured_assembly_bounds_mm"]
if any(abs(a-b)>1.0 for a,b in zip(bounds["min_mm"],expected["min"])) or any(abs(a-b)>1.0 for a,b in zip(bounds["max_mm"],expected["max"])):
    failures.append(f"aggregate bounds mismatch: {bounds}")

proxies = [actor for actor in scope if "LB.Collision.SimpleProxy" in tags(actor)]
floor = next((actor for actor in scope if "LB.Collision.WalkableFloor" in tags(actor)), None)
nav = [actor for actor in scope if isinstance(actor, unreal.NavMeshBoundsVolume)]
proxy_rows = []
for actor in proxies:
    comp=actor.static_mesh_component
    row={"actor":actor.get_actor_label(),"collision":str(comp.get_collision_enabled()),
         "profile":str(comp.get_collision_profile_name()),"nav_relevant":bool(comp.get_editor_property("can_ever_affect_navigation")),
         "hidden_in_game_authored":True}
    proxy_rows.append(row)
    if comp.get_collision_enabled()!=unreal.CollisionEnabled.QUERY_AND_PHYSICS or not row["nav_relevant"]:
        failures.append(f"simple proxy collision/navigation mismatch: {actor.get_actor_label()}")
if len(proxies)!=7 or floor is None or len(nav)!=1:
    failures.append(f"collision/navigation authoring count mismatch proxies={len(proxies)} floor={floor is not None} nav={len(nav)}")

stage_counts=Counter()
role_counts=Counter()
for actor in presentation:
    for value in tags(actor):
        if value.startswith("LB.PressTrain.Stage."): stage_counts[value.rsplit(".",1)[-1]]+=1
        if value.startswith("LB.PressTrain.Role."): role_counts[value.split("LB.PressTrain.Role.",1)[1]]+=1
stage_process_counts={stage:stage_counts[stage] for stage in manifest["stage_instance_counts"]}
if stage_process_counts!=manifest["stage_instance_counts"]:
    failures.append(f"stage counts differ: {dict(stage_counts)}")

asset_paths=sorted({actor.static_mesh_component.get_editor_property("static_mesh").get_path_name() for actor in presentation})
asset_rows=[]; total_triangles=0; total_vertices=0; estimated_sections=0
for path in asset_paths:
    mesh=library.load_asset(path)
    if not isinstance(mesh,unreal.StaticMesh):
        failures.append(f"missing static mesh reference: {path}"); continue
    tris=mesh.get_num_triangles(0); verts=mesh.get_num_vertices(0); slots=len(slot_names(mesh))
    total_triangles+=tris; total_vertices+=verts
    instances=sum(actor.static_mesh_component.get_editor_property("static_mesh").get_path_name()==path for actor in presentation)
    estimated_sections+=slots*instances
    settings=mesh.get_editor_property("nanite_settings")
    asset_rows.append({"asset":path,"lod_count":mesh.get_num_lods(),"vertices_lod0":verts,"triangles_lod0":tris,
                       "material_slots":slots,"instances":instances,"nanite_enabled":bool(settings.get_editor_property("enabled"))})

moving_tokens=("LongDieChangeCart","LargeOuterPanelLoadedDie")
moving_nanite=[row["asset"] for row in asset_rows if any(token in row["asset"] for token in moving_tokens) and row["nanite_enabled"]]
if moving_nanite:
    failures.append(f"moving-candidate modules incorrectly Nanite-enabled: {moving_nanite}")

texts=[str(actor.text_render.get_editor_property("text")) for actor in scope if isinstance(actor,unreal.TextRenderActor)]
forbidden=[text for text in texts if "LINE BOSS" in text.upper() or "LINEBOSS" in text.upper()]
if forbidden:
    failures.append("forbidden in-world Line Boss wording present")
if not any("CAIRNWELL AUTOMOTIVE" in text.upper() and "MOORCROSS WORKS" in text.upper() for text in texts):
    failures.append("Cairnwell/Moorcross evidence identity missing")
candidate_tags=sum("LB.Asset.Candidate.v005" in tags(actor) for actor in scope)
tbc_tags=sum("LB.Authority.WorldPlacement.TBCNotInvented" in tags(actor) for actor in scope)
if candidate_tags!=len(scope) or tbc_tags!=len(scope):
    failures.append("candidate/TBC tags missing from scoped actors")

fixed_cameras=[actor for actor in scope if isinstance(actor,unreal.CameraActor) and "LB.Camera.Fixed" in tags(actor)]
if len(fixed_cameras)!=7:
    failures.append(f"expected seven fixed cameras, found {len(fixed_cameras)}")

failure_history=[]
for version, expected_dims, reason in (
    ("v001",[150,560,134.25],"Interchange 1/100 scale; build receipt lacked dimension gate"),
    ("v002",[150,560,134.25],"Interchange ignored import_uniform_scale=100"),
    ("v003",[150,560,134.25],"legacy factory still interpreted metre coordinates as centimetres"),
    ("v004",[15000,56000,13425],"aggregate combination distorted Z despite exact staged modules")):
    path=ROOT/f"Saved/Audits/PressTrains/press_train_a_assembly_integration_build_{version}.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    actual=data.get("aggregate_import",{}).get("dimensions_mm")
    failure_history.append({"candidate":version,"map":data.get("map"),"measured_dimensions_mm":actual,
                            "expected_failure_signature_mm":expected_dims,"decision":"REJECT_PRESERVE_EVIDENCE","reason":reason})
FAILURES_OUT.write_text(json.dumps({"generated_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PRESERVED_FAILED_IMPORT_HISTORY_NOT_PARENTS", "candidates":failure_history},indent=2),encoding="utf-8")

status="PASS__EXACT_IMPORT_STATIC_COLLISION_NAV_AUTHORING_PERFORMANCE_BRANDING_GATE__RUNTIME_NAV_ANIMATION_PRO_VISUAL_OPEN__NOT_PROMOTED" if not failures else "FAIL__ASSEMBLY_INTEGRATION_STATIC_V005__NOT_PROMOTED"
report={"generated_utc":datetime.now(timezone.utc).isoformat(),"status":status,"map":MAP,"asset_destination":DEST,
        "scope_actor_count":len(scope),"presentation_actor_count":len(presentation),"fixed_camera_count":len(fixed_cameras),
        "stage_counts":dict(stage_counts),"process_stage_counts":stage_process_counts,"role_counts":dict(role_counts),"aggregate_bounds":bounds,
        "transform_errors":transform_errors,"material_errors":material_errors,
        "collision":{"visual_errors":collision_errors,"simple_proxies":proxy_rows,"walkable_floor":floor.get_actor_label() if floor else None,
                     "nav_bounds":[actor.get_actor_label() for actor in nav],"runtime_path_gate":"NOT_APPLICABLE_NO_AUTHORIZED_GAMEPLAY_ROUTE"},
        "performance":{"unique_mesh_assets":len(asset_rows),"unique_lod0_vertices":total_vertices,"unique_lod0_triangles":total_triangles,
                       "estimated_instanced_material_sections":estimated_sections,"assets":asset_rows,
                       "assessment":"first-study presentation cost only; no runtime animation or production population authority"},
        "branding":{"visible_text":texts,"forbidden_hits":forbidden,"world_placement":"TBC_NOT_INVENTED"},
        "failed_predecessor_evidence":str(FAILURES_OUT.relative_to(ROOT)).replace("\\","/"),
        "failures":failures,"runtime_machine_authority":False,"animation_implemented":False,"promotion_authorized":False}
OUT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"status":status,"bounds":bounds,"scope":len(scope),"presentation":len(presentation),
                  "unique_assets":len(asset_rows),"unique_triangles":total_triangles,"estimated_sections":estimated_sections,"failures":failures},indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
