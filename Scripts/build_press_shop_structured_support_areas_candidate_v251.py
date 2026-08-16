"""Build a structured support-area successor directly from retained v249.

The rejected v250 map is never loaded or used as a parent. Its build script is
reused only as a deterministic recipe for existing props, then extended with
physical bay structure, identity and local task lighting before the v251 save.
"""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_support_areas_candidate_v250.py")
code = source.read_text(encoding="utf-8").replace("v250", "v251").replace("V250", "V251")
code = code.replace(
    '"crate": "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics/Meshes/SM_AssemblyLineCrate01",\n}',
    '"crate": "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics/Meshes/SM_AssemblyLineCrate01",\n'
    '    "cube": "/Engine/BasicShapes/Cube",\n'
    '    "lamp": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Lamp01",\n}'
)

enhancements = r'''

# Structured bay successor: complete department reading without inventing
# ratings, machine capacities or a new world datum.
materials = {
    "charcoal": library.load_asset("/Game/LineBoss/Materials/M_LB_ShellCharcoal"),
    "steel": library.load_asset("/Game/LineBoss/Materials/M_LB_StructureSteel"),
    "yellow": library.load_asset("/Game/LineBoss/Materials/M_LB_SafetyYellow"),
    "support": library.load_asset("/Game/LineBoss/Materials/M_LB_Zone_PRESS_SUPPORT"),
    "tooling": library.load_asset("/Game/LineBoss/Materials/M_LB_Zone_PRESS_TOOLING"),
}
if any(value is None for value in materials.values()):
    failures.append("missing structured support material")


def block(area, role, x, y, z, sx, sy, sz, material_name, collision=True):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z), unreal.Rotator())
    if actor is None:
        failures.append(f"block spawn failed {area}/{role}")
        return None
    label = f"LB_WHOLE_V251_{area}_{role}_{len(added)+1:03d}"
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    component = actor.static_mesh_component
    component.set_static_mesh(loaded["cube"])
    component.set_material(0, materials[material_name])
    component.set_mobility(unreal.ComponentMobility.STATIC)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    if collision:
        component.set_collision_profile_name(unreal.Name("BlockAll"))
    component.set_editor_property("can_ever_affect_navigation", collision)
    actor.tags = [unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.SupportArea.AuthoritativeAnchor.EST-P"),
                  unreal.Name(f"LB.SupportArea.{area}"), unreal.Name(f"LB.SupportArea.Role.{role}"),
                  unreal.Name("LB.Placement.TBC")]
    added.append({"label": label, "area": area, "role": role, "mesh": "cube",
                  "location_cm": [x, y, z], "size_cm": [sx, sy, sz], "collision": collision})
    return actor


def task_light(area, index, x, y, z, target_x, target_y):
    lamp = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z), unreal.Rotator())
    lamp_label = f"LB_WHOLE_V251_{area}_TaskLuminaire_{index:02d}"
    lamp.set_actor_label(lamp_label)
    lamp.static_mesh_component.set_static_mesh(loaded["lamp"])
    lamp.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    lamp.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    lamp.tags = [unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name(f"LB.SupportArea.{area}"),
                 unreal.Name("LB.Lighting.IndustrialLED.Task"), unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority")]
    added.append({"label": lamp_label, "area": area, "role": "TaskLuminaire", "mesh": "lamp", "location_cm": [x, y, z]})
    light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, y, z - 12.0), unreal.Rotator())
    light_label = f"LB_WHOLE_V251_{area}_TaskLight_{index:02d}"
    light.set_actor_label(light_label)
    light.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(light.get_actor_location(), unreal.Vector(target_x, target_y, 40.0)), False)
    light.rect_light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.rect_light_component.set_editor_properties({"intensity": 900.0, "attenuation_radius": 1200.0,
        "source_width": 340.0, "source_height": 180.0, "light_color": unreal.Color(205, 220, 225, 255), "cast_shadows": True})
    light.tags = [unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name(f"LB.SupportArea.{area}"),
                  unreal.Name("LB.Lighting.IndustrialLED.Task"), unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority")]
    added.append({"label": light_label, "area": area, "role": "TaskLight", "class": "RectLight", "location_cm": [x, y, z]})


def identity(area, body, x, y, z, yaw):
    actor = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(x, y, z), unreal.Rotator(yaw=yaw))
    label = f"LB_WHOLE_V251_{area}_Identity"
    actor.set_actor_label(label)
    component = actor.text_render
    component.set_text(body)
    component.set_world_size(32.0)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_text_render_color(unreal.Color(215, 235, 220, 255))
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    actor.tags = [unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name(f"LB.SupportArea.{area}"),
                  unreal.Name("LB.Identity.Cairnwell.Moorcross"), unreal.Name("LB.Placement.TBC")]
    added.append({"label": label, "area": area, "role": "Identity", "class": "TextRenderActor", "location_cm": [x, y, z]})


def north_bay(area, body, x, width, depth=1800.0):
    y = 4500.0
    block(area, "BayFloor", x, y, 2.0, width, depth, 4.0, "support", False)
    block(area, "BackWall", x, 5480.0, 170.0, width, 18.0, 340.0, "charcoal", True)
    block(area, "WestDivider", x - width / 2.0, 4680.0, 110.0, 18.0, 1600.0, 220.0, "steel", True)
    block(area, "EastDivider", x + width / 2.0, 4680.0, 110.0, 18.0, 1600.0, 220.0, "steel", True)
    block(area, "Header", x, 5480.0, 390.0, width, 24.0, 35.0, "yellow", False)
    for i, lx in enumerate((x - width * 0.23, x + width * 0.23), 1):
        task_light(area, i, lx, 4550.0, 620.0, lx, 4550.0)
    identity(area, body, x, 5465.0, 310.0, -90.0)
    # Open-front yellow corners communicate a bay without fencing automation routes.
    block(area, "FrontWestMark", x - width / 2.0 + 15.0, 3685.0, 3.0, 30.0, 260.0, 3.0, "yellow", False)
    block(area, "FrontEastMark", x + width / 2.0 - 15.0, 3685.0, 3.0, 30.0, 260.0, 3.0, "yellow", False)


def east_bay(area, body, x, y, width=1150.0, depth=1050.0):
    block(area, "BayFloor", x, y, 2.0, width, depth, 4.0, "tooling", False)
    for px in (x - width / 2.0, x + width / 2.0):
        for py in (y - depth / 2.0, y + depth / 2.0):
            block(area, "CornerPost", px, py, 130.0, 16.0, 16.0, 260.0, "yellow", True)
    block(area, "NorthHeader", x, y + depth / 2.0, 270.0, width, 18.0, 28.0, "steel", False)
    block(area, "SouthHeader", x, y - depth / 2.0, 270.0, width, 18.0, 28.0, "steel", False)
    task_light(area, 1, x, y, 650.0, x, y)
    identity(area, body, x + width / 2.0 - 20.0, y, 220.0, 180.0)


north_bay("PR041", "PR-041  SCRAP RECOVERY | TBC", -8800.0, 1350.0)
north_bay("MAINT", "MAINTENANCE WORKSHOP | TBC", -5800.0, 1900.0)
north_bay("UTIL", "UTILITIES MONITORING | TBC", -900.0, 1700.0)
north_bay("QLAB", "QUALITY LAB | TBC", 4100.0, 1700.0)

east_bay("PR039", "PR-039 FIRST-OFF SCAN | TBC", 9900.0, -4600.0)
east_bay("PR040", "PR-040 QUARANTINE | TBC", 9900.0, -3200.0)
east_bay("PR042", "PR-042 DIE SERVICES | TBC", 7800.0, -2000.0, 1350.0, 1350.0)
east_bay("PR043", "PR-043 STILLAGE MARSHALLING | TBC", 9900.0, -800.0)
east_bay("PR044", "PR-044 DISPATCH HANDOFF | TBC", 9900.0, 2000.0, 1200.0, 1300.0)

'''

code = code.replace(
    'if len(added) != 45:\n    failures.append(f"expected 45 support actors, added {len(added)}")',
    enhancements + '\nexpected_added = 45 + 48 + 50\nif len(added) != expected_added:\n    failures.append(f"expected {expected_added} structured support actors, added {len(added)}")'
)
code = code.replace("support_areas_build_v251.json", "structured_support_areas_build_v251.json")
code = code.replace("support-areas-build-v251", "structured-support-areas-build-v251")
code = code.replace(
    "PASS__AUTHORITATIVE_EST_P_SUPPORT_ANCHORS_POPULATED_WITH_EXISTING_ASSETS__TBC_PLACEMENT__FRESH_VISUAL_COLLISION_NAV_RUNTIME_GATES_REQUIRED__NOT_PROMOTED",
    "PASS__STRUCTURED_SUPPORT_BAYS_ADDED_DIRECTLY_FROM_V249__TBC_PLACEMENT__FRESH_VISUAL_COLLISION_NAV_RUNTIME_GATES_REQUIRED__NOT_PROMOTED"
)
exec(compile(code, str(source) + "::v251", "exec"), globals(), globals())
