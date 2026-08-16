"""Build PR005 v203 from retained v198 with authored installed service bay.

v199-v202 are preserved visual rejects and are never parents.  This candidate
uses the exact-intake v009 installed service-bay asset at the inherited v053
logistics datum, without changing production flow or native PR005 authority.
"""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr005_release_art_candidate_v199.py")
code = source.read_text(encoding="utf-8").replace("v199", "v203").replace("V199", "V203")

replacements = {
    '/Game/LineBoss/Candidates/PressShop/PR005/ServiceLogistics_v007/Meshes/SM_CA_MW_PR005_ServiceLogistics_Static_v007':
        '/Game/LineBoss/Candidates/PressShop/PR005/ServiceBayInstalled_v009/Meshes/SM_CA_MW_PR005_ServiceBayInstalled_Static_v009',
    'LB_PR005_V203_ServiceLogistics_Static_v007': 'LB_PR005_V203_ServiceBayInstalled_Static_v009',
    '(0.008, 0.028, 0.068), (0.025, 0.085, 0.18)': '(0.045, 0.120, 0.240), (0.100, 0.235, 0.420)',
    '(0.15, 0.035, 0.003), (0.40, 0.12, 0.008)': '(0.260, 0.060, 0.006), (0.520, 0.190, 0.018)',
    '(0.006, 0.009, 0.010), (0.035, 0.042, 0.044)': '(0.020, 0.028, 0.032), (0.075, 0.090, 0.098)',
    '(0.24, 0.10, 0.001), (0.58, 0.28, 0.005)': '(0.340, 0.145, 0.002), (0.680, 0.330, 0.010)',
    '(0.12, 0.14, 0.15), (0.34, 0.37, 0.38)': '(0.240, 0.275, 0.295), (0.480, 0.525, 0.545)',
    '(0.42, 0.44, 0.42), (0.72, 0.74, 0.70)': '(0.620, 0.640, 0.600), (0.840, 0.860, 0.820)',
    'logistics = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-2950.0, -3340.0, 2.5), rotation)':
        'logistics = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-2950.0, -3340.0, 0.0), rotation)',
    '"collision_boxes": 3': '"collision_boxes": 6',
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"v203 replacement source missing: {before}")
    code = code.replace(before, after)

# Add the two extra material roles authored by the installed-bay source.
material_needle = '    "CA_MW_RubberBlack": layered_surface("M_CA_MW_PR005_LogisticsRubber_v203", (0.002, 0.003, 0.003), (0.010, 0.012, 0.012), 0.01, 0.90, 0.78, 0.04),\n}'
material_replacement = '''    "CA_MW_RubberBlack": layered_surface("M_CA_MW_PR005_LogisticsRubber_v203", (0.002, 0.003, 0.003), (0.010, 0.012, 0.012), 0.01, 0.90, 0.78, 0.04),
    "CA_MW_SealedConcrete": layered_surface("M_CA_MW_PR005_ServiceBayConcrete_v203", (0.080, 0.090, 0.095), (0.145, 0.160, 0.165), 0.01, 0.92, 0.78, 0.05),
    "CA_MW_ServiceMeshGrey": layered_surface("M_CA_MW_PR005_ServiceMeshGrey_v203", (0.040, 0.052, 0.057), (0.120, 0.145, 0.155), 0.52, 0.62, 0.40, 0.08),
}'''
if material_needle not in code:
    raise RuntimeError("v203 material role insertion point missing")
code = code.replace(material_needle, material_replacement)

# Extend the retained logistics collision with authored screen/bollard witnesses.
collision_needle = '''    ((162.0, 0.0, 60.0), (70.0, 94.0, 120.0)),
):'''
collision_replacement = '''    ((162.0, 0.0, 60.0), (70.0, 94.0, 120.0)),
    ((0.0, -94.0, 120.0), (450.0, 8.0, 230.0)),
    ((-205.0, 84.0, 43.5), (18.0, 18.0, 78.0)),
    ((205.0, 84.0, 43.5), (18.0, 18.0, 78.0)),
):'''
if collision_needle not in code:
    raise RuntimeError("v203 collision insertion point missing")
code = code.replace(collision_needle, collision_replacement)

lighting_start = code.index("# Restrained local bay fill; no new global hall lighting policy.")
save_start = code.index("if not levels.save_current_level():", lighting_start)
lighting = r'''# Calibrated fill placed beneath the two authored task-light fixtures.
# It is local to the inherited service bay and does not alter the hall policy.
for index, x in enumerate((-3055.0, -2845.0), 1):
    light = actors_api.spawn_actor_from_class(
        unreal.PointLight, unreal.Vector(x, -3406.0, 221.0), unreal.Rotator())
    light.set_actor_label(f"LB_PR005_V203_LocalTaskPoint_{index:02d}")
    component = light.get_component_by_class(unreal.PointLightComponent)
    component.set_editor_properties({
        "intensity": 185.0,
        "attenuation_radius": 360.0,
        "cast_shadows": False,
        "light_color": unreal.Color(205, 218, 222, 255),
    })
    light.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v203", "LB.Lighting.PR005.LocalBay",
        "LB.Authority.ProductionFlowUnchanged")]

'''
code = code[:lighting_start] + lighting + code[save_start:]
code = code.replace(
    '"local_bay_lights": 2,',
    '"local_bay_lights": 2,\n'
    '    "installed_service_bay": {"source": "ServiceBayInstalled_v008", '
    '"unreal_asset": "ServiceBayInstalled_v009", "dimensions_mm": [4500, 2000, 2740], '
    '"datum": "INHERITED_V053_LOGISTICS_POSITION", "production_flow_authority": False},')

exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
