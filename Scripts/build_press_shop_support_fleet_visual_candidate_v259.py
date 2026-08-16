"""Build v259 directly from v255 with corrected open-front dock orientation."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_support_fleet_visual_candidate_v258.py")
code = source.read_text(encoding="utf-8").replace("v258", "v259").replace("V258", "V259")
needle = '''        dock.static_mesh_component.set_static_mesh(mesh)
        dock.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)'''
replacement = '''        dock.static_mesh_component.set_static_mesh(mesh)
        # Imported source forward is opposite the retained rear-first berth CFR.
        # Turn only the non-authoritative visual so its open portal faces the aisle;
        # validated robot roots, charging contacts, and collision proxies stay fixed.
        dock.set_actor_rotation(unreal.Rotator(0.0, 0.0, 180.0), False)
        dock.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)'''
if needle not in code:
    raise RuntimeError("Could not patch v259 dock visual orientation")
code = code.replace(needle, replacement)
code = code.replace(
    '"geometry_or_authority_changed": False,',
    '"geometry_or_authority_changed": False,\n'
    '    "dock_visual_yaw_correction_deg": 180.0,\n'
    '    "runtime_robot_contact_or_collision_transform_changed": False,'
)
exec(compile(code, str(source) + "::v259-open-front-orientation", "exec"), globals(), globals())
