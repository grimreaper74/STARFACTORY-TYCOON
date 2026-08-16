"""Build corrected support-fleet v255 directly from protected v253."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_support_fleet_candidate_v254.py")
code = source.read_text(encoding="utf-8").replace("v254", "v255").replace("V254", "V255")
code = code.replace(
    'for mesh_component in child.get_components_by_class(unreal.StaticMeshComponent):\n        name = mesh_component.get_name()',
    'for mesh_component in child.get_components_by_class(unreal.PrimitiveComponent):\n'
    '        mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)\n'
    '        mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))\n'
    '        mesh_component.set_editor_property("can_ever_affect_navigation", False)\n'
    '        name = mesh_component.get_name()'
)
code = code.replace(
    'dock.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)\n'
    '    dock.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)',
    'dock.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)\n'
    '    dock.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))\n'
    '    dock.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)'
)
code = code.replace(
    '"collision_strategy": "Retained dock visual has no consolidated intake collision; three hidden open-portal BlockAll proxies per berth are provisional and navigation-affecting.",',
    '"collision_strategy": "Dock visuals and CR01 presentation children are explicitly NoCollision; parent robot authority plus three hidden open-portal BlockAll proxies per berth carry collision/navigation.",'
)
exec(compile(code, str(source) + "::v255-corrected-direct-v253", "exec"), globals(), globals())
