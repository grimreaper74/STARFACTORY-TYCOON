"""v088 adapter for the established PR-009 process/motion/save/authority PIE validator."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr009_in_map_pie.py")
code = base.read_text(encoding="utf-8").replace(
    "from press_shop_pr009_in_map_validation_config import TARGET_MAP",
    "from press_shop_pr009_trace_portal_clearance_v088_config import TARGET_MAP")
token = "motion_max_rotation_delta_degrees = {key: 0.0 for key in MOTION}\n"
injection = token + "motion_world_swept_bounds_cm = {key: {'min': [float('inf')]*3, 'max': [float('-inf')]*3} for key in MOTION}\n" + \
    "motion_collision_behavior = {}\n"
if token not in code: raise RuntimeError("v088 motion-bounds injection token missing")
code = code.replace(token, injection, 1)
token = "        current = transform_row(by_label[label])\n"
injection = "        motion_actor = by_label[label]\n" + token + \
    "        bounds_origin, bounds_extent = motion_actor.get_actor_bounds(False, False)\n" + \
    "        for axis, (centre, extent) in enumerate(zip((bounds_origin.x,bounds_origin.y,bounds_origin.z),(bounds_extent.x,bounds_extent.y,bounds_extent.z))):\n" + \
    "            motion_world_swept_bounds_cm[key]['min'][axis] = min(motion_world_swept_bounds_cm[key]['min'][axis], centre-extent)\n" + \
    "            motion_world_swept_bounds_cm[key]['max'][axis] = max(motion_world_swept_bounds_cm[key]['max'][axis], centre+extent)\n" + \
    "        collision_component = motion_actor.get_component_by_class(unreal.StaticMeshComponent)\n" + \
    "        if collision_component:\n" + \
    "            motion_collision_behavior[key] = {'profile': str(collision_component.get_collision_profile_name()), 'enabled': str(collision_component.get_editor_property('body_instance').get_editor_property('collision_enabled')), 'world_static_response': str(collision_component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC))}\n"
if token not in code: raise RuntimeError("v088 motion sampling injection token missing")
code = code.replace(token, injection, 1)
token = '        "motion_checks": motion_checks,\n'
injection = token + '        "motion_world_swept_bounds_cm": motion_world_swept_bounds_cm,\n        "motion_collision_behavior": motion_collision_behavior,\n'
if token not in code: raise RuntimeError("v088 payload injection token missing")
code = code.replace(token, injection, 1)
exec(compile(code, str(base) + "::v088-release-collision", "exec"), globals(), globals())
