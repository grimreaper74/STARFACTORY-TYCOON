"""Append visual-review records only; never alter source Meshy files."""
import json
import os


ROOT = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8"
LEDGER = os.path.join(ROOT, "SourceAssets", "Shared", "CairnwellIndustrialDetailLibrary_v001", "split_source_visual_review_v001.json")
RENDER = r"Saved\ValidationScreenshots\IndustrialDetailLibrary_Intake\StandaloneMasters"

records = [
    ("C:\\Users\\greg_\\Downloads\\Meshy_AI__0808180312_part-segmentation.blend", "Split_Unreviewed_0808180312.png", "industrial robot arm with dedicated end tool", "excluded-shared-library", "Robot arm and tooling are role-specific; retain for its robot workstream only. No library extraction.", []),
    ("C:\\Users\\greg_\\Downloads\\Meshy_AI__0809081545_part-segmentation.blend", "Split_Unreviewed_0809081545.png", "coil-handling AGV base platform", "role-specific-master", "Dedicated inbound coil AGV source. Preserve intact for coil logistics; do not use as PR005 dressing.", ["bumper", "lamp housing", "service hatch"]),
    ("C:\\Users\\greg_\\Downloads\\Meshy_AI__0811171413_part-segmentation.blend", "Split_Unreviewed_0811171413.png", "unrenderable/extreme-scale fragment", "excluded-shared-library", "The source bounds are 91.67m x 16.06m x 0.60m and the neutral render is not legible. Do not extract or reuse without a separately authorised recovery review.", []),
    ("C:\\Users\\greg_\\Downloads\\Meshy_AI__0812064711_part-segmentation.blend", "Split_Unreviewed_0812064711.png", "vehicle chassis/underbody segmentation", "excluded-shared-library", "Vehicle workstream only; no factory or PR005 reuse.", []),
    ("C:\\Users\\greg_\\Downloads\\Meshy_AI__0812064813_part-segmentation.blend", "Split_Unreviewed_0812064813.png", "vehicle chassis/underbody segmentation variant", "excluded-shared-library", "Vehicle workstream only; no factory or PR005 reuse.", []),
    ("C:\\Users\\greg_\\Downloads\\Meshy_AI__0812065058_part-segmentation.blend", "Split_Unreviewed_0812065058.png", "industrial vision/quality gate", "role-specific-master", "Retain intact for the Body Weld vision-gate role only. Cabinet/conduit parts require a separate component inspection before any library extraction.", ["cabinet", "conduit", "stack-light mount"]),
    ("C:\\Users\\greg_\\Downloads\\Meshy_AI__0812065500_part-segmentation.blend", "Split_Unreviewed_0812065500.png", "vacuum panel pick end-of-arm tool", "excluded-shared-library", "Role-specific process tooling; no generic machine or PR005 use.", []),
    ("C:\\Users\\greg_\\Downloads\\Meshy_AI__0812065910_part-segmentation.blend", "Split_Unreviewed_0812065910.png", "three-high panel stillage", "role-specific-master", "Retain intact for panel-stillage logistics only. Do not mine for generic PR005 details without a later isolated part validation.", ["lifting eye", "locator block", "fabricated foot"]),
]

with open(LEDGER, encoding="utf-8") as handle:
    document = json.load(handle)
seen = {record.get("source") for record in document["reviewed_sources"]}
for source, render, role, status, decision, candidates in records:
    if source not in seen:
        document["reviewed_sources"].append({
            "source": source,
            "render": os.path.join(RENDER, render),
            "observed_role": role,
            "status": status,
            "shared_library_decision": decision,
            "reusable_candidate_classes": candidates,
        })
document["reviewed_sources"].sort(key=lambda item: item["source"])
with open(LEDGER, "w", encoding="utf-8") as handle:
    json.dump(document, handle, indent=2)
    handle.write("\n")
print("REVIEWED_SOURCES|{}".format(len(document["reviewed_sources"])))
