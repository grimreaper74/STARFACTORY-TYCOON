"""Corrected cumulative build after v212 exposed collision getter API mismatch."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_cumulative_release_candidate_v211.py")
code = source.read_text(encoding="utf-8").replace("v211", "v213").replace("V211", "V213")

replacements = {
    'rows = [serialize_actor(actor) for actor in actors if actor.get_actor_label().startswith(prefix)]':
        'rows = [serialize_actor(actor) for actor in actors if actor.get_actor_label().startswith(prefix) or (station == "PR005" and actor.get_actor_label() == INFILL)]',
    'expected_counts = {"PR005": 3,': 'expected_counts = {"PR005": 4,',
    'record["collision_enabled"] = prop(component, "collision_enabled")':
        'record["collision_enabled"] = component.get_collision_enabled()',
    'record["collision_profile_name"] = prop(component, "collision_profile_name")':
        'record["collision_profile_name"] = component.get_collision_profile_name()',
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"v213 replacement source missing: {before}")
    code = code.replace(before, after)

before_target_infill = '''infill_rows = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == INFILL]
if len(infill_rows) != 1 or infill_materials is None:
    raise RuntimeError("target PR005 infill/material donor mismatch")
infill_component = infill_rows[0].static_mesh_component
for index, material_path in enumerate(infill_materials):
    if material_path:
        material = library.load_asset(material_path)
        if material is None:
            raise RuntimeError(f"missing donor infill material {material_path}")
        infill_component.set_material(index, material)
infill_rows[0].tags = list(infill_rows[0].tags) + [unreal.Name("LB.Merge.Cumulative.v213")]

'''
if before_target_infill not in code:
    raise RuntimeError("v213 target-infill replacement source missing")
code = code.replace(before_target_infill, "")

exec(compile(code, str(source) + "::v213", "exec"), {"__name__": "__main__", "__file__": str(source)})
