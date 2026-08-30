"""Restore render visibility for the four reusable robot tender components.

Their actors were deliberately placed and their actor-hidden state is false,
but the audit found every mesh component still had Visibility=False.  This is
an integration-state repair only; mesh, material, scale and transform remain
unchanged.
"""

import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_robot_visibility_restore_v047.json"
TAG = unreal.Name("LB.PressShop.2126.RobotRenderVisibility.v047")
LABELS = (
    "ROBOT | S01 | laser tend robot",
    "ROBOT | S02 | draw quality robot",
    "ROBOT | S04 | pierce handling robot",
    "ROBOT | S06 | vision stack robot",
)


def sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


protected_before = sha256(PROTECTED)
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("Robot visibility repair v047 already applied")

rows = []
for label in LABELS:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("Robot actor missing: " + label)
    component = actor.static_mesh_component
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    mesh = component.get_editor_property("static_mesh")
    material_paths = [component.get_material(index).get_path_name() if component.get_material(index) else None for index in range(component.get_num_materials())]
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("Robot mesh missing: " + label)
    actor.set_actor_hidden_in_game(False)
    actor.set_is_temporarily_hidden_in_editor(False)
    component.set_visibility(True, True)
    component.set_render_in_main_pass(True)
    if not component.is_visible():
        raise RuntimeError("Robot component remained invisible: " + label)
    actor.tags = list(actor.tags) + [TAG, unreal.Name("LB.PressShop.Automation.RenderVisible")]
    rows.append({
        "label": label,
        "mesh": mesh.get_path_name(),
        "component_visible_after": component.is_visible(),
        "location_cm_unchanged": [location.x, location.y, location.z],
        "rotation_unchanged": [rotation.pitch, rotation.yaw, rotation.roll],
        "scale_unchanged": [scale.x, scale.y, scale.z],
        "material_paths_unchanged": material_paths,
    })

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate map")
protected_after = sha256(PROTECTED)
if protected_before != protected_after:
    raise RuntimeError("Protected v438 changed")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__REUSED_ROBOT_TENDERS_RENDER_VISIBLE",
    "robots": rows,
    "new_machine_geometry": False,
    "roof_created": False,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_ROBOT_RENDER_VISIBILITY_V047_PASS")
