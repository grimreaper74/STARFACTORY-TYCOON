"""v096 adapter for the established PR-009 runtime/save/authority validator."""
from pathlib import Path

adapter = Path(__file__).with_name("validate_press_shop_pr009_in_map_pie_v089.py")
code = adapter.read_text(encoding="utf-8").replace(
    "press_shop_pr009_transfer_guide_collision_v089_config",
    "press_shop_pr009_flow_axis_correction_v096_config")
token = 'exec(compile(code, str(base) + "::v089-release-collision", "exec"), globals(), globals())'
injection = r'''code = code.replace(
    "motion_world_swept_bounds_cm = {key: {'min': [float('inf')]*3, 'max': [float('-inf')]*3} for key in MOTION}\n",
    "motion_world_swept_bounds_cm = {key: {'min': [float('inf')]*3, 'max': [float('-inf')]*3} for key in MOTION}\nmotion_world_sample_bounds_cm = {key: [] for key in MOTION}\n")
code = code.replace(
    "        collision_component = motion_actor.get_component_by_class(unreal.StaticMeshComponent)\n",
    "        motion_world_sample_bounds_cm[key].append({'min': [bounds_origin.x-bounds_extent.x,bounds_origin.y-bounds_extent.y,bounds_origin.z-bounds_extent.z], 'max': [bounds_origin.x+bounds_extent.x,bounds_origin.y+bounds_extent.y,bounds_origin.z+bounds_extent.z]})\n        collision_component = motion_actor.get_component_by_class(unreal.StaticMeshComponent)\n")
code = code.replace(
    '        "motion_world_swept_bounds_cm": motion_world_swept_bounds_cm,\n',
    '        "motion_world_swept_bounds_cm": motion_world_swept_bounds_cm,\n        "motion_world_sample_bounds_cm": motion_world_sample_bounds_cm,\n')
''' + token
if token not in code:
    raise RuntimeError("v096 runtime sample-bounds injection token missing")
code = code.replace(token, injection, 1)
exec(compile(code, str(adapter) + "::v096-flow-axis", "exec"), globals(), globals())
