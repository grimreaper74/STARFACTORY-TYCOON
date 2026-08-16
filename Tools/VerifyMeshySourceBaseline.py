"""Read-only SHA-256 verification of the full original Meshy intake baseline."""
import csv
import hashlib
import json
import os
import sys


def digest(path):
    value = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest().upper()


baseline_path, output_path = sys.argv[1], sys.argv[2]
with open(baseline_path, encoding="cp1252") as handle:
    lines = [line.rstrip("\r\n").replace("`t", "\t") for line in handle]
    rows = list(csv.DictReader(lines, delimiter="\t"))
details = []
for row in rows:
    path = row["source"]
    entry = {"source": path, "expected_sha256": row["sha256"], "expected_size": int(row["size"])}
    if not os.path.exists(path):
        entry["result"] = "missing"
    else:
        entry["actual_size"] = os.path.getsize(path)
        entry["actual_sha256"] = digest(path)
        entry["result"] = "matched" if entry["actual_size"] == entry["expected_size"] and entry["actual_sha256"] == entry["expected_sha256"] else "mismatch"
    details.append(entry)
summary = {result: sum(1 for entry in details if entry["result"] == result) for result in ("matched", "missing", "mismatch")}
output = {"purpose": "Full Meshy source intake integrity verification; read-only.", "baseline": baseline_path, "summary": summary, "details": details}
with open(output_path, "w", encoding="utf-8") as handle:
    json.dump(output, handle, indent=2)
    handle.write("\n")
print(json.dumps(summary))
