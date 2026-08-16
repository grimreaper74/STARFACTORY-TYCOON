"""Build corrected-front-end cumulative successor from retained v190.

The existing v211 merge implementation is replayed with the same v213 fixes,
but the immutable corrected PR-003/PR-004 v190 map is the fresh parent.  Donor
maps and every retained predecessor remain read-only.
"""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_cumulative_release_candidate_v211.py")
code = source.read_text(encoding="utf-8").replace("v211", "v214").replace("V211", "V214")

replacements = {
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107"':
        'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190"',
    'rows = [serialize_actor(actor) for actor in actors if actor.get_actor_label().startswith(prefix)]':
        'rows = [serialize_actor(actor) for actor in actors if actor.get_actor_label().startswith(prefix) or (station == "PR005" and actor.get_actor_label() == INFILL)]',
    'expected_counts = {"PR005": 3,': 'expected_counts = {"PR005": 4,',
    'record["collision_enabled"] = prop(component, "collision_enabled")':
        'record["collision_enabled"] = component.get_collision_enabled()',
    'record["collision_profile_name"] = prop(component, "collision_profile_name")':
        'record["collision_profile_name"] = component.get_collision_profile_name()',
    '''for label in sorted(PR005_OLD):
    actor = by_label.get(label)
    if actor is None or not actors_api.destroy_actor(actor):
        raise RuntimeError(f"could not remove inherited PR005 logistics actor {label}")
    removed_pr005.append(label)''':
        '''for label in sorted(PR005_OLD):
    actor = by_label.get(label)
    if actor is None:
        continue
    if not actors_api.destroy_actor(actor):
        raise RuntimeError(f"could not remove inherited PR005 logistics actor {label}")
    removed_pr005.append(label)''',
    '''if len(old_anchor_actors) != 48:
    raise RuntimeError(f"expected 48 generic PR008 anchors in fresh v107 child, got {len(old_anchor_actors)}")''':
        '''if len(old_anchor_actors) not in (0, 48):
    raise RuntimeError(f"expected zero or 48 generic PR008 anchors in corrected-front-end child, got {len(old_anchor_actors)}")''',
    '''return {
        "tags": [str(value) for value in actor.tags],
        "properties": {name: prop(component, name) for name in (
            "intensity", "attenuation_radius", "inner_cone_angle", "outer_cone_angle",
            "source_radius", "soft_source_radius", "cast_shadows", "light_color")},
    }''':
        '''return {
        "label": actor.get_actor_label(),
        "location": vec(actor.get_actor_location()),
        "rotation": rot(actor.get_actor_rotation()),
        "scale": vec(actor.get_actor_scale3d()),
        "tags": [str(value) for value in actor.tags],
        "properties": {name: prop(component, name) for name in (
            "intensity", "attenuation_radius", "inner_cone_angle", "outer_cone_angle",
            "source_radius", "soft_source_radius", "cast_shadows", "light_color")},
    }''',
    '''for label, donor in spot_overrides.items():
    actor = target_by_label.get(label)
    if not isinstance(actor, unreal.SpotLight):
        raise RuntimeError(f"missing target inherited light {label}")
    actor.spot_light_component.set_editor_properties({
        key: value for key, value in donor["properties"].items() if value is not None})
    actor.tags = [unreal.Name(value) for value in donor["tags"]] + [unreal.Name("LB.Merge.Cumulative.v214")]''':
        '''for label, donor in spot_overrides.items():
    actor = target_by_label.get(label)
    if actor is None:
        rotation = unreal.Rotator()
        rotation.set_editor_properties({
            "pitch": donor["rotation"][0], "yaw": donor["rotation"][1], "roll": donor["rotation"][2]})
        actor = actors_api.spawn_actor_from_class(unreal.SpotLight, unreal.Vector(*donor["location"]), rotation)
        if actor is None:
            raise RuntimeError(f"could not spawn inherited light {label}")
        actor.set_actor_label(label)
        actor.set_actor_scale3d(unreal.Vector(*donor["scale"]))
    elif not isinstance(actor, unreal.SpotLight):
        raise RuntimeError(f"target inherited light has wrong class {label}")
    actor.spot_light_component.set_editor_properties({
        key: value for key, value in donor["properties"].items() if value is not None})
    actor.tags = [unreal.Name(value) for value in donor["tags"]] + [unreal.Name("LB.Merge.Cumulative.v214")]''',
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"v214 replacement source missing: {before}")
    code = code.replace(before, after)

target_infill = '''infill_rows = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == INFILL]
if len(infill_rows) != 1 or infill_materials is None:
    raise RuntimeError("target PR005 infill/material donor mismatch")
infill_component = infill_rows[0].static_mesh_component
for index, material_path in enumerate(infill_materials):
    if material_path:
        material = library.load_asset(material_path)
        if material is None:
            raise RuntimeError(f"missing donor infill material {material_path}")
        infill_component.set_material(index, material)
infill_rows[0].tags = list(infill_rows[0].tags) + [unreal.Name("LB.Merge.Cumulative.v214")]

'''
if target_infill not in code:
    raise RuntimeError("v214 target-infill removal source missing")
code = code.replace(target_infill, "")

exec(compile(code, str(source) + "::corrected-front-end-v214", "exec"), {
    "__name__": "__main__",
    "__file__": str(source),
})
