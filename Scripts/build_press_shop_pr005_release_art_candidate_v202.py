"""Build PR005 v202 from retained v198 with an anchored service-return bay.

v199-v201 are preserved dark/isolated visual rejects and are never parents.
The v202 change is presentation-only: it preserves the inherited production
route, runtime authority, collision/navigation roles and physical gate hold.
"""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr005_release_art_candidate_v199.py")
code = source.read_text(encoding="utf-8").replace("v199", "v202").replace("V199", "V202")

# Keep the material response physically restrained but camera-readable.  These
# are local PR005 overrides only; the PR003 coil materials are not in scope.
replacements = {
    "(0.008, 0.028, 0.068), (0.025, 0.085, 0.18)": "(0.045, 0.120, 0.240), (0.100, 0.235, 0.420)",
    "(0.15, 0.035, 0.003), (0.40, 0.12, 0.008)": "(0.260, 0.060, 0.006), (0.520, 0.190, 0.018)",
    "(0.006, 0.009, 0.010), (0.035, 0.042, 0.044)": "(0.020, 0.028, 0.032), (0.075, 0.090, 0.098)",
    "(0.24, 0.10, 0.001), (0.58, 0.28, 0.005)": "(0.340, 0.145, 0.002), (0.680, 0.330, 0.010)",
    "(0.12, 0.14, 0.15), (0.34, 0.37, 0.38)": "(0.240, 0.275, 0.295), (0.480, 0.525, 0.545)",
    "(0.42, 0.44, 0.42), (0.72, 0.74, 0.70)": "(0.620, 0.640, 0.600), (0.840, 0.860, 0.820)",
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"v202 material replacement source missing: {before}")
    code = code.replace(before, after)

lighting_start = code.index("# Restrained local bay fill; no new global hall lighting policy.")
save_start = code.index("if not levels.save_current_level():", lighting_start)
service_bay = r'''# Installed service-return bay: presentation-only floor dressing at the
# inherited v053 logistics datum.  It does not claim or change production flow.
pad_material = layered_surface(
    "M_CA_MW_PR005_ServiceBayConcrete_v202",
    (0.105, 0.115, 0.118), (0.190, 0.205, 0.208), 0.02, 0.90, 0.76, 0.06)
boundary_material = layered_surface(
    "M_CA_MW_PR005_ServiceBayBoundary_v202",
    (0.380, 0.170, 0.002), (0.760, 0.410, 0.012), 0.05, 0.70, 0.52, 0.08)
fixture_material = layered_surface(
    "M_CA_MW_PR005_ServiceBayFixture_v202",
    (0.300, 0.340, 0.350), (0.700, 0.760, 0.780), 0.58, 0.40, 0.24, 0.10)
cube = lib.load_asset("/Engine/BasicShapes/Cube.Cube")
if not isinstance(cube, unreal.StaticMesh):
    raise RuntimeError("Engine cube unavailable")


def spawn_dressing_cube(label, location, scale, material, role):
    actor = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    mesh_component = actor.static_mesh_component
    mesh_component.set_static_mesh(cube)
    mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
    mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    mesh_component.set_editor_property("can_ever_affect_navigation", False)
    mesh_component.set_material(0, material)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v202", "LB.Asset.CandidateNotPromoted",
        "LB.Station.PR-005", "LB.PR005.ReleaseArt",
        "LB.Logistics.StaticDressing", role,
        "LB.Authority.ProductionFlowUnchanged")]
    return actor


# 4.5 m x 2.0 m sealed-concrete inset at the retained logistics datum.
spawn_dressing_cube(
    "LB_PR005_V202_ServiceReturnBay_Pad",
    (-2950.0, -3340.0, 1.0), (4.50, 2.00, 0.02), pad_material,
    "LB.Logistics.ServiceBayPad")

# Restrained 50 mm yellow perimeter.  The camera-side edge is deliberately
# broken to read as an open service entrance rather than a fenced process lane.
for label, location, scale in (
    ("North", (-2950.0, -3437.5, 2.6), (4.50, 0.05, 0.012)),
    ("South", (-2950.0, -3242.5, 2.6), (4.50, 0.05, 0.012)),
    ("West", (-3172.5, -3340.0, 2.6), (0.05, 2.00, 0.012)),
    ("EastUpper", (-2727.5, -3388.0, 2.6), (0.05, 1.04, 0.012)),
    ("EastLower", (-2727.5, -3292.0, 2.6), (0.05, 1.04, 0.012)),
):
    spawn_dressing_cube(
        f"LB_PR005_V202_ServiceReturnBay_Boundary_{label}",
        location, scale, boundary_material, "LB.Logistics.ServiceBayBoundary")

# Two slim ceiling-level fixture witnesses plus point lights.  The inherited
# rect-light trials were directionally ineffective; point sources are used so
# the service kit receives local fill without changing the hall policy.
for index, x in enumerate((-3060.0, -2840.0), 1):
    spawn_dressing_cube(
        f"LB_PR005_V202_ServiceReturnBay_LED_{index:02d}",
        (x, -3340.0, 545.0), (1.45, 0.10, 0.045), fixture_material,
        "LB.Lighting.PR005.LocalBayFixture")
    light = actors_api.spawn_actor_from_class(
        unreal.PointLight, unreal.Vector(x, -3340.0, 525.0), unreal.Rotator())
    light.set_actor_label(f"LB_PR005_V202_LocalBayPoint_{index:02d}")
    component = light.get_component_by_class(unreal.PointLightComponent)
    component.set_editor_properties({
        "intensity": 1650.0,
        "attenuation_radius": 640.0,
        "cast_shadows": False,
        "light_color": unreal.Color(205, 220, 224, 255),
    })
    light.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v202", "LB.Lighting.PR005.LocalBay",
        "LB.Authority.ProductionFlowUnchanged")]

'''
code = code[:lighting_start] + service_bay + code[save_start:]

# Extend the build record without broadening its authority claim.
code = code.replace(
    '"local_bay_lights": 2,',
    '"local_bay_lights": 2,\n'
    '    "service_return_bay": {"sealed_concrete_pad": 1, "open_boundary_segments": 5, '
    '"fixture_witnesses": 2, "collision": "NoCollision", "navigation": False, '
    '"datum": "INHERITED_V053_LOGISTICS_POSITION"},')

exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
