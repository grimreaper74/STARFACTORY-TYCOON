import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "Saved/Automation/PR010_V101_Final"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v101/automation_regression_v101.json"
TESTS = {
    "PR010_RuntimeAndSave": "LineBoss.PressShop.PR010.RuntimeAndSave",
    "PR009_RuntimeAndSave": "LineBoss.PressShop.PR009.RuntimeAndSave",
    "PR008_RuntimeAndSave": "LineBoss.PressShop.PR008.RuntimeAndSave",
    "PR008ToPR009TraceableBlankHandoff": "LineBoss.PressShop.MaterialFlow.PR008ToPR009TraceableBlankHandoff",
}
rows, failures = {}, []
for folder, expected in TESTS.items():
    path = BASE / folder / "index.json"
    if not path.is_file():
        failures.append(f"missing {path}"); continue
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    tests = data.get("tests", [])
    test = next((row for row in tests if row.get("fullTestPath") == expected), None)
    row = {"path": str(path.relative_to(ROOT)), "succeeded": data.get("succeeded"), "succeeded_with_warnings": data.get("succeededWithWarnings"), "failed": data.get("failed"), "test_state": test.get("state") if test else None, "warnings": test.get("warnings") if test else None, "errors": test.get("errors") if test else None}
    rows[folder] = row
    if not test or data.get("succeeded") != 1 or data.get("failed") != 0 or data.get("succeededWithWarnings") != 0 or test.get("state") != "Success" or test.get("warnings") != 0 or test.get("errors") != 0:
        failures.append(f"automation failed: {folder}: {row}")
report = {"status": "PASS__PR010_V101_NATIVE_AUTOMATION_AND_PR008_PR009_FLOW_REGRESSIONS__ZERO_WARNINGS_ERRORS__NOT_PROMOTED" if not failures else "FAIL__PR010_V101_AUTOMATION__NOT_PROMOTED", "tests": rows, "failures": failures, "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2)); raise SystemExit(1 if failures else 0)
