"""Build v260 directly from v255 with open-front docks and aisle overview."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_support_fleet_visual_candidate_v258.py")
code = source.read_text(encoding="utf-8").replace("v258", "v260").replace("V258", "V260")
needle = '''        dock.static_mesh_component.set_static_mesh(mesh)
        dock.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)'''
replacement = '''        dock.static_mesh_component.set_static_mesh(mesh)
        dock.set_actor_rotation(unreal.Rotator(0.0, 0.0, 180.0), False)
        dock.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)'''
if needle not in code:
    raise RuntimeError("Could not patch v260 dock visual orientation")
code = code.replace(needle, replacement)
code = code.replace(
    '''    (-3300.0, 3500.0, 1120.0),
    (-3300.0, 5160.0, 45.0),
    88.0,''',
    '''    (-7900.0, 4050.0, 680.0),
    (-2500.0, 5180.0, 80.0),
    72.0,''',
)
code = code.replace(
    '"geometry_or_authority_changed": False,',
    '"geometry_or_authority_changed": False,\n'
    '    "dock_visual_yaw_correction_deg": 180.0,\n'
    '    "runtime_robot_contact_or_collision_transform_changed": False,'
)
exec(compile(code, str(source) + "::v260-low-oblique-aisle-overview", "exec"), globals(), globals())
