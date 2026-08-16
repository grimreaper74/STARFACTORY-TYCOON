"""Import and exact-audit the installed PR005 service-bay Unreal derivative."""

from pathlib import Path


source = Path(__file__).with_name("import_audit_pr005_service_logistics_v007.py")
code = source.read_text(encoding="utf-8")
replacements = {
    'ServiceLogistics_UnrealDerived_v007': 'ServiceBayInstalled_UnrealDerived_v009',
    'PR005_SERVICE_LOGISTICS_UNREAL_DERIVED_MANIFEST_v007.json': 'PR005_SERVICE_BAY_INSTALLED_UNREAL_DERIVED_MANIFEST_v009.json',
    '/Game/LineBoss/Candidates/PressShop/PR005/ServiceLogistics_v007/Meshes': '/Game/LineBoss/Candidates/PressShop/PR005/ServiceBayInstalled_v009/Meshes',
    'press_shop_pr005_service_logistics_unreal_intake_v007.json': 'press_shop_pr005_service_bay_installed_unreal_intake_v009.json',
    'press-shop-pr005-service-logistics-unreal-intake-v007': 'press-shop-pr005-service-bay-installed-unreal-intake-v009',
    'SIX_V053_STATIC_LOGISTICS_BLOCKOUT_ACTORS_ONLY': 'SIX_V053_LOGISTICS_BLOCKOUT_ACTORS_PLUS_PRESENTATION_ONLY_BAY_CONTEXT',
    'LINE_BOSS_PR005_SERVICE_LOGISTICS_V007_INTAKE_PASS': 'LINE_BOSS_PR005_SERVICE_BAY_INSTALLED_V009_INTAKE_PASS',
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"installed-bay intake replacement source missing: {before}")
    code = code.replace(before, after)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
