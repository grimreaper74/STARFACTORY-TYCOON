"""Import and audit the immutable-source-safe PR-005 Unreal scale derivatives."""

from pathlib import Path


source = Path(__file__).with_name("import_audit_pr005_exterior_enclosure_v002.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    'SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR005/Candidate_v002"',
    'SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR005/UnrealDerived_v003"')
code = code.replace(
    'MANIFEST_PATH = SOURCE / "PR005_EXTERIOR_ENCLOSURE_MANIFEST_v002.json"',
    'MANIFEST_PATH = SOURCE / "PR005_EXTERIOR_ENCLOSURE_UNREAL_DERIVED_MANIFEST_v003.json"')
code = code.replace("ExteriorEnclosure_v002", "ExteriorEnclosure_v003")
code = code.replace("press_shop_pr005_exterior_enclosure_unreal_intake_v002.json", "press_shop_pr005_exterior_enclosure_unreal_intake_v003.json")
code = code.replace("row[\"dimensions_mm\"]", "row[\"expected_dimensions_mm\"]")
code = code.replace("Candidate_v002", "UnrealDerived_v003")
code = code.replace("candidate-v002", "candidate-v003")
code = code.replace("intake-v002", "intake-v003")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
