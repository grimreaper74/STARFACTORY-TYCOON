"""Add isolated CR01 v052 blocking and cleaning-query collision proxies."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v052/Blueprints/BP_LB_CR01_CleaningAMR_v052"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v052_collision_build.json"

asset_library = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data_library = unreal.SubobjectDataBlueprintFunctionLibrary


def handles_and_objects(blueprint):
    handles = {}
    objects = {}
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        name = str(data_library.get_variable_name(data))
        if name and name != "None" and name not in handles:
            handles[name] = handle
            objects[name] = data_library.get_object_for_blueprint(data, blueprint) or data_library.get_object(data)
    return handles, objects


def add_component(blueprint, parent_handle, component_class, name):
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
        raise RuntimeError(f"Could not resolve template {name}")
    return component


def configure(component, location, profile, nav, tags):
    component.set_editor_property("relative_location", unreal.Vector(*location))
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    component.set_collision_profile_name(unreal.Name(profile))
    component.set_collision_enabled(
        unreal.CollisionEnabled.QUERY_AND_PHYSICS if profile == "BlockAllDynamic" else unreal.CollisionEnabled.QUERY_ONLY
    )
    component.set_editor_property("generate_overlap_events", profile != "BlockAllDynamic")
    component.set_editor_property("can_ever_affect_navigation", nav)
    component.set_editor_property("component_tags", [unreal.Name(tag) for tag in tags] + [unreal.Name("LB.Asset.CandidateNotPromoted")])


blueprint = asset_library.load_asset(BP_PATH)
if not isinstance(blueprint, unreal.Blueprint):
    raise RuntimeError(f"Missing isolated cleaner Blueprint {BP_PATH}")
handles, existing = handles_and_objects(blueprint)

specs = [
    ("Collision_CR01_Base", "CR01PayloadFrame", unreal.BoxComponent, (0.0, 0.0, 19.25), (75.5, 49.23, 19.25), "BlockAllDynamic", True, ["LB.CR01.Collision.Body", "LB.CR01.Collision.Navigation"]),
    ("Collision_CR01_Upper", "CR01PayloadFrame", unreal.BoxComponent, (-4.0, 0.0, 66.0), (56.0, 45.0, 28.0), "BlockAllDynamic", True, ["LB.CR01.Collision.Body", "LB.CR01.Collision.Navigation"]),
    ("Collision_CR01_Roof", "CR01PayloadFrame", unreal.BoxComponent, (-4.0, 0.0, 103.0), (25.0, 25.0, 9.0), "BlockAllDynamic", True, ["LB.CR01.Collision.Body", "LB.CR01.Collision.Navigation"]),
    ("Query_CR01_FrontBrush", "PVT_FrontBrushSpin", unreal.BoxComponent, (0.0, 0.0, 0.0), (9.1, 41.8, 9.1), "OverlapAllDynamic", False, ["LB.CR01.Query.Cleaning", "LB.CR01.Query.FrontBrush"]),
    ("Query_CR01_SideBrush_L", "PVT_SideBrushSpin_L", unreal.SphereComponent, (0.0, 0.0, 0.0), 17.5, "OverlapAllDynamic", False, ["LB.CR01.Query.Cleaning", "LB.CR01.Query.SideBrush.L"]),
    ("Query_CR01_SideBrush_R", "PVT_SideBrushSpin_R", unreal.SphereComponent, (0.0, 0.0, 0.0), 17.5, "OverlapAllDynamic", False, ["LB.CR01.Query.Cleaning", "LB.CR01.Query.SideBrush.R"]),
    ("Query_CR01_ScrubDeck", "PVT_ScrubDeckLift", unreal.BoxComponent, (0.0, 0.0, 0.0), (34.0, 38.0, 11.5), "OverlapAllDynamic", False, ["LB.CR01.Query.Cleaning", "LB.CR01.Query.ScrubDeck"]),
    ("Query_CR01_Squeegee", "PVT_SqueegeeYaw", unreal.BoxComponent, (0.0, 0.0, 0.0), (8.0, 45.0, 4.5), "OverlapAllDynamic", False, ["LB.CR01.Query.Cleaning", "LB.CR01.Query.Squeegee"]),
]

rows = []
for name, parent_name, component_class, location, shape, profile, nav, tags in specs:
    if name in existing:
        raise RuntimeError(f"Refusing to overwrite existing collision component {name}")
    parent_handle = handles.get(parent_name)
    if parent_handle is None:
        raise RuntimeError(f"Missing collision parent {parent_name}")
    component = add_component(blueprint, parent_handle, component_class, name)
    configure(component, location, profile, nav, tags)
    if isinstance(component, unreal.BoxComponent):
        component.set_box_extent(unreal.Vector(*shape), update_overlaps=False)
        shape_row = {"type": "box", "half_extent_cm": list(shape)}
    else:
        component.set_sphere_radius(shape, update_overlaps=False)
        shape_row = {"type": "sphere", "radius_cm": shape}
    rows.append({
        "component": name, "parent": parent_name, "relative_location_cm": list(location),
        "collision_profile": profile, "navigation_relevant": nav, "tags": tags, **shape_row,
    })

bp_library.compile_blueprint(blueprint)
if not asset_library.save_loaded_asset(blueprint, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save collision-bound cleaner Blueprint {BP_PATH}")

result = {
    "$schema": "line-boss/audit/lb-cr01-candidate-v052-collision-build",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_COLLISION_PROXY_BUILD_PASS__FRESH_RUNTIME_AUDIT_REQUIRED__NOT_PROMOTED",
    "blueprint": BP_PATH,
    "blocking_body_proxy_count": 3,
    "nonblocking_cleaning_query_count": 5,
    "bristles_use_blocking_collision": False,
    "components": rows,
    "source_meshes_modified": False,
    "rp01_parent_modified": False,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V052_COLLISION_BUILD_PASS proxies={len(rows)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
