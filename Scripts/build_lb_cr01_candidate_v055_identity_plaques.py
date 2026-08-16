"""Add reusable, correctly seated Cairnwell/Moorcross identity plaques to CR01."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v054/Blueprints/BP_LB_CR01_CleaningAMR_v054"
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v055/Blueprints/BP_LB_CR01_CleaningAMR_v055"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v055_identity_plaques_build.json"

assets = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary


def require(path, cls=None):
    asset = assets.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


if assets.does_directory_exist("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v055"):
    raise RuntimeError("Refusing to overwrite preserved CR01 Candidate v055")
if not assets.duplicate_asset(SOURCE_BP, BP_PATH):
    raise RuntimeError(f"Could not duplicate {SOURCE_BP} -> {BP_PATH}")
blueprint = require(BP_PATH, unreal.Blueprint)


def gather():
    handles = {}
    objects = {}
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        name = str(data_library.get_variable_name(data))
        if name and name != "None" and name not in handles:
            handles[name] = handle
            objects[name] = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
    return handles, objects


def add_component(parent_handle, component_class, name):
    result = subsystem.add_new_subobject(params=unreal.AddNewSubobjectParams(
        parent_handle=parent_handle,
        new_class=component_class,
        blueprint_context=blueprint,
        conform_transform_to_parent=False,
        skip_mark_blueprint_modified=False,
    ))
    handle = result[0]
    if not data_library.is_handle_valid(handle):
        raise RuntimeError(f"Could not add {name}: {result[1] if len(result) > 1 else ''}")
    subsystem.rename_subobject(handle=handle, new_name=unreal.Text(name))
    data = subsystem.k2_find_subobject_data_from_handle(handle)
    component = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
    if component is None:
        raise RuntimeError(f"Could not resolve component template {name}")
    return component


handles, existing = gather()
parent_handle = handles.get("CR01PayloadFrame")
if parent_handle is None:
    raise RuntimeError("Missing CR01PayloadFrame identity parent")
cube = require("/Engine/BasicShapes/Cube.Cube", unreal.StaticMesh)
green = require("/Game/LineBoss/Robots/Shared/Materials/Candidate_v003/MI_LB_Robot_CairnwellGreen_Mothballed_v003", unreal.MaterialInterface)

source_authority = {
    "carrier_blender_location_m": [0.4907, 0.11, 0.735],
    "carrier_blender_dimensions_m": [0.001, 0.34, 0.17],
    "wordmark_blender_location_m": [0.49145, 0.11, 0.78],
    "asset_id_blender_location_m": [0.49145, 0.11, 0.71],
    "conversion": "UE_X=-BLENDER_Y*100; UE_Y=BLENDER_X*100; UE_Z=BLENDER_Z*100",
}

rows = []
for side, y, yaw in (("R", 49.55, 90.0), ("L", -49.55, -90.0)):
    plate_name = f"IdentityPlate_Cairnwell_{side}"
    plate = add_component(parent_handle, unreal.StaticMeshComponent, plate_name)
    plate.set_static_mesh(cube)
    plate.set_material(0, green)
    plate.set_editor_property("relative_location", unreal.Vector(-11.0, y, 73.5))
    plate.set_editor_property("relative_scale3d", unreal.Vector(0.34, 0.0025, 0.17))
    plate.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    plate.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    plate.set_editor_property("can_ever_affect_navigation", False)
    plate.set_editor_property("component_tags", [
        unreal.Name("LB.Brand.CairnwellAutomotive"),
        unreal.Name("LB.Site.MoorcrossWorks"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ])
    rows.append({"component": plate_name, "type": "physical_plate", "location_cm": [-11.0, y, 73.5], "dimensions_cm": [34.0, 0.25, 17.0]})

    for suffix, text, z, size, colour, tag in (
        ("Wordmark", "CAIRNWELL", 78.2, 6.2, unreal.Color(238, 230, 202, 255), "LB.Brand.CairnwellAutomotive"),
        ("AssetId", "CR-01 001", 71.2, 4.4, unreal.Color(235, 178, 28, 255), "LB.Asset.Identity.CR01-001"),
        ("Site", "MOORCROSS WORKS", 66.5, 2.5, unreal.Color(196, 205, 202, 255), "LB.Site.MoorcrossWorks"),
    ):
        name = f"IdentityText_{suffix}_{side}"
        component = add_component(parent_handle, unreal.TextRenderComponent, name)
        component.set_text(text)
        component.set_world_size(size)
        component.set_text_render_color(colour)
        component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
        component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
        component.set_editor_property("relative_location", unreal.Vector(-11.0, y + (0.22 if y > 0 else -0.22), z))
        component.set_editor_property("relative_rotation", unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
        component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        component.set_editor_property("cast_shadow", False)
        component.set_editor_property("component_tags", [unreal.Name(tag), unreal.Name("LB.Asset.CandidateNotPromoted")])
        rows.append({"component": name, "type": "diegetic_text", "text": text, "location_cm": [-11.0, y + (0.22 if y > 0 else -0.22), z], "yaw_deg": yaw, "world_size_cm": size})

bp_library.compile_blueprint(blueprint)
generated_class = bp_library.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("CR01 v055 generated class missing")
unreal.get_default_object(generated_class).set_editor_property("tags", [
    unreal.Name("LB.SupportRobot.LB-CR01"),
    unreal.Name("LB.Asset.Candidate.v055"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.RP01.ParentCandidate.v003"),
    unreal.Name("LB.Brand.CairnwellAutomotive"),
    unreal.Name("LB.Site.MoorcrossWorks"),
    unreal.Name("LB.Safety.FaultLatched"),
])
bp_library.compile_blueprint(blueprint)
if not assets.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {BP_PATH}")

result = {
    "$schema": "line-boss/audit/lb-cr01-candidate-v055-identity-plaques-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_SEATED_TWO_SIDED_DIEGETIC_IDENTITY_BUILT__FRESH_RELOAD_AND_CAMERA_GATES_REQUIRED__NOT_PROMOTED",
    "source_blueprint_preserved": SOURCE_BP,
    "candidate_blueprint": BP_PATH,
    "source_coordinate_authority": source_authority,
    "component_count": len(rows),
    "components": rows,
    "branding": ["Cairnwell Automotive", "CR-01 001", "Moorcross Works"],
    "line_boss_in_world_branding_added": False,
    "collision_changed": False,
    "navigation_changed": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V055_IDENTITY_BUILD_PASS components={len(rows)} audit={AUDIT}")
