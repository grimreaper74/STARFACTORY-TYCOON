import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v101"
MANIFEST = SOURCE / "PR010_RELEASE_ART_MANIFEST_v101.json"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v101/pr010_release_art_source_audit_v101.json"
EXPECTED = {
    "SM_CA_MW_PR010_CarrierPallet_v101": ([2400, 1900, 180], {"CA_MW_SafetyYellow", "CA_MW_FoundryCharcoal", "CA_MW_WorkedSteel"}),
    "SM_CA_MW_PR010_BlankStack_Layered_v101": ([2200, 1700, 500], {"CA_MW_BlankSteel", "CA_MW_FoundryCharcoal", "CA_MW_White"}),
    "SM_CA_MW_PR010_FasciaLouvered_v101": ([2900, 80, 750], {"CA_MW_CairnwellGreen", "CA_MW_WorkedSteel"}),
}

data = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {}
rows = {row.get("asset"): row for row in data.get("assets", [])}
failures, assets = [], []
if set(rows) != set(EXPECTED): failures.append(f"asset set mismatch: {sorted(rows)}")
if not (SOURCE / "CA_MW_PR010_ReleaseArt_v101.blend").is_file(): failures.append("missing source blend")
for name, (dims, slots) in EXPECTED.items():
    row = rows.get(name, {})
    measured = row.get("measured_dimensions_mm", [])
    dim_ok = len(measured) == 3 and all(abs(float(a)-float(b)) <= 0.5 for a, b in zip(measured, dims))
    fbx = SOURCE / row.get("file", "missing")
    slot_ok = slots.issubset(set(row.get("material_slots", [])))
    assets.append({"asset": name, "dimensions_ok": dim_ok, "fbx_exists": fbx.is_file(), "fbx_bytes": fbx.stat().st_size if fbx.is_file() else 0, "material_slots_ok": slot_ok})
    if not dim_ok: failures.append(f"{name}: dimension mismatch {measured}")
    if not fbx.is_file() or fbx.stat().st_size < 1024: failures.append(f"{name}: missing/empty FBX")
    if not slot_ok: failures.append(f"{name}: material-slot mismatch")
forbidden = [path.name for path in SOURCE.rglob("*") if "lineboss" in path.name.lower() or "line_boss" in path.name.lower()]
if forbidden: failures.append(f"forbidden brand naming: {forbidden}")
report = {"status": "PASS__PR010_V101_SOURCE_DIMENSIONS_MATERIALS_BRANDING__UNREAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V101_SOURCE__NOT_PROMOTED", "assets": assets, "forbidden_brand_names": forbidden, "failures": failures, "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(1 if failures else 0)
