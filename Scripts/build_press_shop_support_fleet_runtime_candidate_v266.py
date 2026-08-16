"""Install route R02 and correct visual floor-detail collision in v266."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_support_fleet_runtime_candidate_v263.py")
code = source.read_text(encoding="utf-8").replace("v263", "v266").replace("V263", "V266")
code = code.replace('"route_revision": 1', '"route_revision": 2')
needle = '''controller.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v266",
    "LB.Asset.CandidateNotPromoted",
    "LB.Runtime.Authority.SupportFleet",
    "LB.SupportRobot.CertifiedRoutes.R01",
)]
'''
replacement = needle.replace("R01", "R02") + '''
floor_detail_collision_corrections = []
for actor in ACTORS.get_all_level_actors():
    actor_tags = [str(tag) for tag in actor.tags]
    role_tags = [tag for tag in actor_tags if ".Role." in tag and tag.endswith("Mark")]
    sawcut_tags = [tag for tag in actor_tags if tag == "LB.Environment.Floor.SawCutJoint"]
    if not role_tags and not sawcut_tags:
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        continue
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    actor.tags = list(actor.tags) + [unreal.Name("LB.Collision.VisualFloorDetail.NoCollision.v266")]
    floor_detail_collision_corrections.append({
        "actor": actor.get_actor_label(), "role_tags": role_tags,
        "sawcut_tags": sawcut_tags})
'''
if needle not in code:
    raise RuntimeError("Could not inject v266 floor-detail collision correction")
code = code.replace(needle, replacement)
code = code.replace(
    '"collision_policy_changes": 0,',
    '"collision_policy_changes": len(floor_detail_collision_corrections),\n'
    '    "floor_detail_collision_corrections": floor_detail_collision_corrections,')
exec(compile(code, str(source) + "::v266-r02-floor-detail-collision", "exec"), globals(), globals())
