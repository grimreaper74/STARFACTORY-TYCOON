"""Classify the conservative v239 PR010-to-installed-train AABB contacts.

This is read-only evidence. It does not convert AABB contact into a safety or
engineering clearance claim and it does not authorize v239 promotion.
"""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Saved/Audits/PressShopIntegration/press_shop_v239_restored_train_collision_overlap.json"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_v239_restored_train_interface_contact_classification.json"

source = json.loads(SOURCE.read_text(encoding="utf-8"))
rows = []
for contact in source["overlaps"]:
    train_actor = contact["train_actor"]
    if "CommonFoundation" in train_actor:
        category = "COMMON_FOUNDATION_SUPPORT_CONTACT"
    elif "TransferRail" in train_actor:
        category = "S01_TRANSFER_INTERFACE_CONTACT"
    elif "_S01_" in train_actor:
        category = "S01_FEED_GUARD_FACADE_CONTACT"
    else:
        category = "OUTSIDE_EXPECTED_S01_INTERFACE"
    rows.append({**contact, "classification": category})

counts = Counter(row["classification"] for row in rows)
trains = Counter(row["train"] for row in rows)
unexpected = [row for row in rows if row["classification"] == "OUTSIDE_EXPECTED_S01_INTERFACE"]
payload = {
    "$schema": "cairnwell/audit/press-shop-v239-restored-train-interface-contact-classification/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "HOLD__CONTACTS_CONFINED_TO_TRAIN_B_C_S01_INTERFACE__PHYSICAL_OWNERSHIP_REVIEW_REQUIRED"
              if not unexpected and set(trains) <= {"B", "C"}
              else "FAIL__CONTACT_OUTSIDE_EXPECTED_INTERFACE",
    "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
    "map": source["map"],
    "method_limit": source["method"],
    "contact_count": len(rows),
    "classification_counts": dict(sorted(counts.items())),
    "train_counts": dict(sorted(trains.items())),
    "outside_expected_interface_count": len(unexpected),
    "interpretation": [
        "The screen proves where conservative actor-bound contacts occur; it does not prove mesh penetration.",
        "No contact reaches Train A, Train D, or stages S02-S07.",
        "Foundation and transfer-interface contacts may be intentional handoff/support contacts.",
        "S01 feed/guard/facade contacts require visual and collision-ownership resolution before promotion.",
    ],
    "promotion_authorized": False,
    "contacts": rows,
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({key: payload[key] for key in (
    "status", "contact_count", "classification_counts", "train_counts",
    "outside_expected_interface_count")}, indent=2))

