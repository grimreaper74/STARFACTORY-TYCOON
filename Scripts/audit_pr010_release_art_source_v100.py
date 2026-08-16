import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets" / "PR010" / "FourLaneBuffer" / "ReleaseArt_v100"
MANIFEST = SOURCE / "PR010_RELEASE_ART_MANIFEST_v100.json"
AUDIT_DIR = ROOT / "Saved" / "Audits" / "PR010_ReleaseArt_v100"
AUDIT = AUDIT_DIR / "pr010_release_art_source_audit_v100.json"

EXPECTED = {
    "SM_CA_MW_PR010_GuardPanel_OpenMesh_v100": ([2700, 80, 1200], {"CA_MW_SafetyYellow", "CA_MW_WorkedSteel"}),
    "SM_CA_MW_PR010_InfeedTransferCradle_v100": ([2400, 800, 180], {"CA_MW_SafetyYellow", "CA_MW_FoundryCharcoal", "CA_MW_WorkedSteel"}),
    "SM_CA_MW_PR010_RemoteHMIHousing_v100": ([760, 500, 1650], {"CA_MW_FoundryCharcoal", "CA_MW_ServiceGrey", "CA_MW_ScreenOnline", "CA_MW_CairnwellGreen", "CA_MW_SafetyYellow", "CA_MW_SensorGlass"}),
    "SM_CA_MW_PR010_SafetyScanner_v100": ([220, 220, 240], {"CA_MW_FoundryCharcoal", "CA_MW_SafetyYellow", "CA_MW_SensorGlass"}),
    "SM_CA_MW_PR010_TowPoint_v100": ([240, 180, 340], {"CA_MW_FoundryCharcoal", "CA_MW_SafetyYellow"}),
}


def main():
    failures = []
    data = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    assets = {entry.get("asset"): entry for entry in data.get("assets", [])}

    if not (SOURCE / "CA_MW_PR010_ReleaseArt_v100.blend").is_file():
        failures.append("missing source blend")
    if set(assets) != set(EXPECTED):
        failures.append(f"asset set mismatch: {sorted(assets)}")

    results = []
    for name, (expected_dims, required_slots) in EXPECTED.items():
        entry = assets.get(name, {})
        fbx = SOURCE / entry.get("file", "missing")
        measured = entry.get("measured_dimensions_mm", [])
        dimensions_ok = len(measured) == 3 and all(abs(float(a) - float(b)) <= 0.5 for a, b in zip(measured, expected_dims))
        slots = set(entry.get("material_slots", []))
        item = {
            "asset": name,
            "fbx_exists": fbx.is_file(),
            "fbx_bytes": fbx.stat().st_size if fbx.is_file() else 0,
            "measured_dimensions_mm": measured,
            "expected_dimensions_mm": expected_dims,
            "dimensions_within_0_5mm": dimensions_ok,
            "required_material_slots_present": required_slots.issubset(slots),
        }
        if not item["fbx_exists"] or item["fbx_bytes"] < 1024:
            failures.append(f"{name}: missing or empty FBX")
        if not dimensions_ok:
            failures.append(f"{name}: dimensions {measured} != {expected_dims}")
        if not item["required_material_slots_present"]:
            failures.append(f"{name}: missing material slots {sorted(required_slots - slots)}")
        results.append(item)

    forbidden = [path.name for path in SOURCE.rglob("*") if "lineboss" in path.name.lower() or "line_boss" in path.name.lower()]
    if forbidden:
        failures.append(f"forbidden in-world brand naming: {forbidden}")

    report = {
        "status": "PASS__PR010_V100_SOURCE_DIMENSIONS_MATERIAL_SLOTS_BRANDING__UNREAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V100_SOURCE_AUDIT__NOT_PROMOTED",
        "authority": "Pro Sheet 03 plus accepted v099 technical contracts",
        "assets": results,
        "forbidden_brand_names": forbidden,
        "failures": failures,
        "promotion_authorized": False,
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
