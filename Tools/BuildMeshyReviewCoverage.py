"""Read-only cross-reference of the Meshy source inventory against review ledgers."""
import json
import os
import re
import sys
from collections import Counter


def stamp(value):
    match = re.search(r"(?<!\d)(\d{10})(?!\d)", value or "")
    return match.group(1) if match else None


def records(document):
    for key in ("sources", "entries", "models", "items", "excluded_sources", "reviewed_sources", "reviewed_masters", "families"):
        value = document.get(key)
        if isinstance(value, list):
            return value
    return []


def main():
    library_root = sys.argv[1]
    names = {
        "inventory": "all_meshy_source_catalogue_v001.json",
        "split": "split_source_visual_review_v001.json",
        "whole": "whole_module_visual_review_v002.json",
        "excluded": "vehicle_and_companion_exclusion_ledger_v001.json",
    }
    documents = {}
    for key, name in names.items():
        with open(os.path.join(library_root, name), encoding="utf-8") as handle:
            documents[key] = json.load(handle)

    reviewed = {}
    for kind in ("split", "whole", "excluded"):
        for record in records(documents[kind]):
            path = record.get("source_path") or record.get("path") or record.get("source") or ""
            key = record.get("timestamp") or stamp(path) or stamp(record.get("name", ""))
            if key:
                reviewed.setdefault(key, []).append(kind)

    coverage = []
    for record in records(documents["inventory"]):
        path = record.get("source_path") or record.get("path") or record.get("source") or ""
        filename = os.path.basename(path)
        key = stamp(path)
        family_reviews = reviewed.get(key, []) if key else []
        # Internal library copies and the manually named v632 assets have their own manifests.
        if "CairnwellIndustrialDetailLibrary" in path:
            disposition = "library-derivative-not-a-source-authority"
        elif "MeshyCabinetHMI_v632" in path:
            disposition = "whole-review-manual-v632"
        elif family_reviews:
            disposition = "+".join(sorted(set(family_reviews)))
        elif "\\PR005\\ArtSkin_v0" in path:
            disposition = "derived-pr005-skin-history-reviewed-through-v012"
        elif "\\PressTrains\\TrainA\\" in path:
            disposition = "derived-press-train-evaluation; role-specific; not-detail-library"
        elif "PoweredConveyor_v001" in path:
            disposition = "derived-powered-conveyor-authority; role-specific"
        elif "CompactForkliftAGV" in path:
            disposition = "derived-compact-forklift-authority; logistics-only"
        elif "FinishedPanelStillage" in path:
            disposition = "derived-panel-stillage-authority; logistics-only"
        elif "EDLineMeshyReview_v002" in path:
            disposition = "derived-ed-line-assembly; ED-only"
        elif "MissingEquipmentProMeshyPack" in path:
            disposition = "derived-pr004-reference-pack; PR004-only"
        elif "PlasticFilmCompactor_v20260810" in path:
            disposition = "derived-pr004-compactor-appearance; PR004-only"
        else:
            disposition = "unmatched"
        coverage.append({
            "source_path": path,
            "filename": filename,
            "timestamp_family": key,
            "file_kind": record.get("file_kind"),
            "review_disposition": disposition,
        })

    summary = Counter(item["review_disposition"] for item in coverage)
    output = {
        "purpose": "Maps every catalogued Meshy path to its visual review or exclusion evidence. No source files changed.",
        "inventory_count": len(coverage),
        "summary": dict(sorted(summary.items())),
        "unmatched": [item for item in coverage if item["review_disposition"] == "unmatched"],
        "coverage": coverage,
    }
    with open(os.path.join(library_root, "meshy_review_coverage_v001.json"), "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"inventory_count": len(coverage), "summary": output["summary"], "unmatched_count": len(output["unmatched"])}, indent=2))


if __name__ == "__main__":
    main()
