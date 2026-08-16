"""Capture comparable parent/target actor, geometry, material and camera fingerprints."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from press_shop_pr009_release_collision_v087_config import PARENT_MAP, TARGET_MAP

phase = os.environ.get("LB_PR009_V087_INVENTORY_PHASE", "").lower()
if phase not in {"parent", "target"}:
    raise RuntimeError("LB_PR009_V087_INVENTORY_PHASE must be parent or target")
map_path = PARENT_MAP if phase == "parent" else TARGET_MAP
root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/PR009_InMap_v087" / f"visual_invariants_{phase}.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(f"Could not load {map_path}")

def vec(value): return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]
def rot(value): return [round(float(value.pitch), 4), round(float(value.yaw), 4), round(float(value.roll), 4)]
def colour(value): return [int(value.r), int(value.g), int(value.b), int(value.a)]
def normalized(label): return re.sub(r"V0*8[67]", "V###", label, flags=re.IGNORECASE)
def material_path(material): return material.get_path_name() if material else None

rows = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if not (label.startswith("LB_PR009_V086_") or label.startswith("LB_PR009_V087_")):
        continue
    row = {"identity": normalized(label), "class": actor.get_class().get_name(),
           "location_cm": vec(actor.get_actor_location()), "rotation_degrees": rot(actor.get_actor_rotation()),
           "scale": vec(actor.get_actor_scale3d())}
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = component.get_editor_property("static_mesh") if component else None
    if mesh:
        box = mesh.get_bounding_box()
        row["mesh_visual"] = {"lod_count": mesh.get_num_lods(),
                              "vertices": [mesh.get_num_vertices(index) for index in range(mesh.get_num_lods())],
                              "triangles": [mesh.get_num_triangles(index) for index in range(mesh.get_num_lods())],
                              "bounds_min_cm": vec(box.min), "bounds_max_cm": vec(box.max),
                              "asset_materials": [material_path(mesh.get_material(index)) for index in range(len(mesh.get_editor_property("static_materials")))],
                              "override_materials": [material_path(material) for material in component.get_editor_property("override_materials")],
                              "visible": bool(component.get_editor_property("visible"))}
    if isinstance(actor, unreal.CameraActor):
        camera = actor.camera_component
        row["camera"] = {"fov": float(camera.get_editor_property("field_of_view")),
                         "aspect": float(camera.get_editor_property("aspect_ratio")),
                         "constrain": bool(camera.get_editor_property("constrain_aspect_ratio"))}
    if isinstance(actor, unreal.TextRenderActor):
        text = actor.text_render
        row["text"] = {"value": str(text.get_editor_property("text")),
                       "world_size": float(text.get_editor_property("world_size")),
                       "colour_rgba": colour(text.get_editor_property("text_render_color"))}
    rows.append(row)
payload = {"$schema": "cairnwell/audit/pr009-v087-visual-invariants/v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
           "phase": phase, "map": map_path, "actor_count": len(rows), "actors": sorted(rows, key=lambda row: row["identity"]),
           "promotion_authorized": False}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"PR009_V087_VISUAL_INVARIANTS_{phase.upper()} count={len(rows)} output={out}")
unreal.SystemLibrary.quit_editor()
