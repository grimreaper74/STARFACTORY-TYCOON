"""Prune DirectoriesToAlwaysCook to what the SPACECRAFT game needs.

Owner, 2026-08-28: "can you delete all the old car factory game stuff".
This is the reversible half of that, and the half with the biggest
measurable payoff: the packaged build carries 46 always-cook
directories and only FOUR of them are spacecraft. The rest are
PressShop, WeldShop, PaintShop, BodyShop, Cairnwell 2040 and
OneFactory - the car game. That is the package size, and it costs
nothing but a config edit to stop shipping it.

WHY THIS IS SAFE AND DELETING CONTENT IS NOT: this only changes what
gets COOKED. Every asset stays on disk, in the editor, exactly where it
was. Getting it wrong costs one line in an ini, not an unrecoverable
loss - and Content/ is gitignored, so a wrong deletion has no undo at
all.

IT ALSO ADDS. The list had drifted BEHIND the game as well as ahead of
it: the surface palette, the glass, the conveyor, the landing gear, the
ground drones and the site scenery are all loaded by SOFT PATH from
C++, which the cooker cannot see by reference, and none of them were
listed. A packaged build would have shipped without them and fallen
back - silently, exactly like the Nanite usage flags did. Trimming
without adding would have traded a fat build for a broken one.

Fail-closed: refuses to rerun over its receipt, writes the ini only
after building the whole new list, and records every path kept, dropped
and added.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = root / "Saved/Audits/Spacecraft/cook_set_prune_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")
ini = root / "Config/DefaultGame.ini"

# Anything under these is the CAR GAME and is not shipped.
CAR_MARKERS = (
    "/PressShop", "/WeldShop", "/PaintShop", "/BodyShop",
    "/Cairnwell2040", "/Cairnwell/", "/OneFactory", "/Stations/Press",
    "/Equipment/Robots", "/IndustrialKit", "/ScanKit",
    "/AssemblyShop", "/Architecture/FactoryEnvelopeKit",
    "/Vehicles/",
)
# Loaded by SOFT PATH from spacecraft C++, so the cooker cannot see them
# by reference and they must be named explicitly.
MUST_ADD = [
    "/Game/LineBoss/Materials/Surfaces",
    "/Game/LineBoss/Candidates/Spacecraft/LineHardware_v001",
    "/Game/LineBoss/Candidates/Spacecraft/LandingGear_v001",
    "/Game/LineBoss/Candidates/Spacecraft/GroundDrones_v001",
    "/Game/LineBoss/Candidates/Spacecraft/SiteScenery_v001",
    "/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001",
    "/Game/Materials",
]

text = ini.read_text(encoding="utf-8")
lines = text.splitlines()
kept, dropped, added = [], [], []
out_lines = []
seen_paths = set()

for line in lines:
    match = re.search(r'\+DirectoriesToAlwaysCook=\(Path="([^"]*)"\)', line)
    if match is None:
        out_lines.append(line)
        continue
    path = match.group(1)
    seen_paths.add(path)
    if any(marker in path for marker in CAR_MARKERS):
        dropped.append(path)
        continue          # the car game does not ship
    kept.append(path)
    out_lines.append(line)

# Append the missing spacecraft directories next to the ones that stayed.
anchor = None
for index, line in enumerate(out_lines):
    if "+DirectoriesToAlwaysCook=" in line:
        anchor = index
if anchor is None:
    raise RuntimeError("No DirectoriesToAlwaysCook lines survived - refusing.")
insert = []
for path in MUST_ADD:
    if path in seen_paths:
        continue
    insert.append('+DirectoriesToAlwaysCook=(Path="%s")' % path)
    added.append(path)
out_lines[anchor + 1:anchor + 1] = insert

ini.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

report = {
    "$schema": "lineboss/audit/cook-set-prune-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__COOK_SET_PRUNED",
    "why": ("46 always-cook directories, only four of them spacecraft. "
            "The rest is the car game and is what the packaged build "
            "was carrying. The list had also drifted behind the game: "
            "the palette, glass, conveyor, gear, ground drones and site "
            "scenery are loaded by soft path and were unlisted, so "
            "trimming alone would have shipped a broken build."),
    "before_count": len(kept) + len(dropped),
    "after_count": len(kept) + len(added),
    "kept": sorted(kept),
    "dropped_car_era": sorted(dropped),
    "added_spacecraft": sorted(added),
    "not_proven": [
        "NOBODY HAS PACKAGED THIS YET. The size win and, more "
        "importantly, that nothing is missing are both unmeasured "
        "until a package run and a sighted launch of it.",
        "Nothing was deleted. Every asset is still on disk and in the "
        "editor; this only changes what is cooked, and is reversible "
        "by reverting one config file.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"],
                  "before": report["before_count"],
                  "after": report["after_count"],
                  "dropped": len(dropped), "added": len(added)}, indent=2))
