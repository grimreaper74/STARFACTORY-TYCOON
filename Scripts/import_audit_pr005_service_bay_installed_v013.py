"""Import and exact-audit the camera-readable PR005 service bay."""

from pathlib import Path

source = Path(__file__).with_name("import_audit_pr005_service_bay_installed_v009.py")
code = source.read_text(encoding="utf-8").replace("v009", "v013").replace("V009", "V013")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
