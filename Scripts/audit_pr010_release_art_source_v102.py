import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v102"
MANIFEST = SOURCE / "PR010_RELEASE_ART_MANIFEST_v102.json"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v102/pr010_release_art_source_audit_v102.json"
EXPECTED = {
    "SM_CA_MW_PR010_UpperServiceHousingSection_v102": [2900, 1240, 900],
    "SM_CA_MW_PR010_ServiceWalkwayRailSection_v102": [2900, 900, 1208],
    "SM_CA_MW_PR010_RoofDrivePod_v102": [1200, 800, 400],
    "SM_CA_MW_PR010_RoofUtilityRoute_v102": [2900, 500, 250],
    "SM_CA_MW_PR010_IDPylonDetailed_v102": [350, 350, 2200],
}
data = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {}
rows = {row.get("asset"): row for row in data.get("assets", [])}
failures, results = [], []
if set(rows) != set(EXPECTED): failures.append(f"asset set mismatch: {sorted(rows)}")
if not (SOURCE / "CA_MW_PR010_ReleaseArt_v102.blend").is_file(): failures.append("missing Blender source")
for name, expected in EXPECTED.items():
    row = rows.get(name, {}); measured = row.get("measured_dimensions_mm", [])
    dim_ok = len(measured) == 3 and all(abs(float(a)-float(b)) <= 0.5 for a, b in zip(measured, expected))
    fbx = SOURCE / row.get("file", "missing")
    authority = str(row.get("authority", "")); slots = row.get("material_slots", [])
    result = {"asset": name, "measured_dimensions_mm": measured, "expected_dimensions_mm": expected,
        "dimensions_within_0_5mm": dim_ok, "fbx_exists": fbx.is_file(), "fbx_bytes": fbx.stat().st_size if fbx.is_file() else 0,
        "material_slot_count": len(slots), "authority": authority}
    results.append(result)
    if not dim_ok: failures.append(f"{name}: dimension mismatch {measured}")
    if not fbx.is_file() or fbx.stat().st_size < 1024: failures.append(f"{name}: missing/empty FBX")
    if not slots: failures.append(f"{name}: no material slots")
    if not authority: failures.append(f"{name}: missing authority classification")
forbidden = [path.name for path in SOURCE.rglob("*") if "lineboss" in path.name.lower() or "line_boss" in path.name.lower()]
if forbidden: failures.append(f"forbidden in-world brand naming: {forbidden}")
report = {"status": "PASS__PR010_V102_SERVICE_DECK_SOURCE_DIMENSIONS_MATERIALS_AUTHORITY_BRANDING__UNREAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V102_SOURCE__NOT_PROMOTED",
    "authority": "Pro Sheet 03 plus retained v101 technical contracts", "assets": results,
    "forbidden_brand_names": forbidden, "failures": failures, "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2)); raise SystemExit(1 if failures else 0)
