"""Install route R02 and correct decorative floor-mark collision in v265."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_support_fleet_runtime_candidate_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v265").replace("V263", "V265")
code = code.replace('"route_revision": 1', '"route_revision": 2')
needle = '''controller.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v265",
    "LB.Asset.CandidateNotPromoted",
    "LB.Runtime.Authority.SupportFleet",
    "LB.SupportRobot.CertifiedRoutes.R01",
)]
'''
replacement = needle.replace("R01", "R02") + '''
floor_mark_collision_corrections = []
for actor in ACTORS.get_all_level_actors():
    role_tags = [str(tag) for tag in actor.tags
                 if ".Role." in str(tag) and str(tag).endswith("Mark")]
    if not role_tags:
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        continue
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    actor.tags = list(actor.tags) + [unreal.Name("LB.Collision.VisualFloorMark.NoCollision.v265")]
    floor_mark_collision_corrections.append({
        "actor": actor.get_actor_label(), "role_tags": role_tags})
'''
if needle not in code:
    raise RuntimeError("Could not inject v265 floor-mark collision correction")
code = code.replace(needle, replacement)
code = code.replace(
    '"collision_policy_changes": 0,',
    '"collision_policy_changes": len(floor_mark_collision_corrections),\n'
    '    "floor_mark_collision_corrections": floor_mark_collision_corrections,')
exec(compile(code, str(source) + "::v265-r02-floor-mark-collision", "exec"), globals(), globals())
