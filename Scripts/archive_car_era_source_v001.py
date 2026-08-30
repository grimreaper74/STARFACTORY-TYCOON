"""Move the car game's C++ out of the module, by include closure.

Owner, 2026-08-28: "can you delete all the old car factory game stuff".
The content half is done - 18 GB down to 3 GB. This is the source half.

The car content going left a real breakage behind it: the car-era
LBGameMode hard-references a maintenance-robot Blueprint in its CDO
constructor, and that Blueprint is now archived, so every launch logs

    Error: CDO Constructor (LBGameMode): Failed to find
    /Game/LineBoss/Robots/Maintenance/MR01/.../BP_LB_MR01_MaintenanceAMR

The spacecraft game runs through it, but a permanent error in the log is
exactly the kind of noise that hides the next real one.

WHAT STAYS is computed, not listed: the transitive INCLUDE CLOSURE of
the roots below. Anything no root reaches - directly or through another
header - is car-era by construction and moves.

  roots: every LBSpacecraft* file, the module entry point, the
         developer automation bridge, and the game user settings.

The bridge is the awkward one and the reason this is a closure rather
than a name match. It pulls in fifteen car-era headers for verbs that no
longer have a game behind them - place_machine, coil_agv, support_robot,
its 328-line CaptureState. Gutting a working 1,673-line file by hand is
the riskier option, so its dependencies stay for now and the bridge gets
superseded later by a spacecraft-only one - which is this project's own
convention anyway: supersede, keep the superseded thing as evidence.

For every header kept, its .cpp is kept too: a UCLASS whose translation
unit went missing links no better than a missing header compiles.

MOVED, NOT DELETED - though unlike the content, Source IS in git (350
files tracked), so this half really is recoverable either way.

Fail-closed: refuses to rerun over its receipt, and refuses outright if
the closure would move a spacecraft file.
"""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = root / "Saved/Audits/Spacecraft/car_era_source_archive_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")

source = root / "Source/LineBossCarFactory"
archive = root / "ArchivedCarEraSource/LineBossCarFactory"

everything = {f.name: f for f in source.iterdir()
              if f.suffix in (".cpp", ".h")}

roots = [name for name in everything if name.startswith("LBSpacecraft")]
roots += [name for name in ("LineBossCarFactory.cpp",
                            "LBDeveloperAutomationBridge.cpp",
                            "LBDeveloperAutomationBridge.h",
                            "LBGameUserSettings.cpp",
                            "LBGameUserSettings.h")
          if name in everything]

include_pattern = re.compile(r'#include\s+"([^"]+)"')
keep = set()
frontier = list(roots)
while frontier:
    name = frontier.pop()
    if name in keep or name not in everything:
        continue
    keep.add(name)
    # A header and its translation unit travel together.
    stem = Path(name).stem
    for sibling in ("%s.h" % stem, "%s.cpp" % stem):
        if sibling in everything and sibling not in keep:
            frontier.append(sibling)
    try:
        text = everything[name].read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        continue
    for included in include_pattern.findall(text):
        included = included.split("/")[-1]
        if included.endswith(".generated.h"):
            continue
        if included in everything:
            frontier.append(included)

move = sorted(name for name in everything if name not in keep)
failures = []
for name in move:
    if name.startswith("LBSpacecraft"):
        failures.append("REFUSED - closure would move a spacecraft file: %s"
                        % name)
if failures:
    raise RuntimeError("; ".join(failures))

archive.mkdir(parents=True, exist_ok=True)
moved = []
for name in move:
    try:
        shutil.move(str(everything[name]), str(archive / name))
        moved.append(name)
    except Exception as exc:  # noqa: BLE001
        failures.append("%s: %s" % (name, exc))

kept_lines = 0
for name in sorted(keep):
    path = source / name
    if path.exists():
        kept_lines += len(path.read_text(encoding="utf-8",
                                         errors="replace").splitlines())

report = {
    "$schema": "lineboss/audit/car-era-source-archive-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__CAR_ERA_SOURCE_ARCHIVED" if not failures
               else "PARTIAL__CAR_ERA_SOURCE_ARCHIVE"),
    "why": ("The car content is archived and its code hard-references "
            "assets that are gone, so every launch logs a CDO error. "
            "What stays is the include closure of the spacecraft files, "
            "the module entry point, the automation bridge and the game "
            "user settings - computed, not listed."),
    "kept_files": len(keep),
    "kept_lines": kept_lines,
    "moved_files": len(moved),
    "moved": moved,
    "failures": failures,
    "not_proven": [
        "IT HAS NOT BEEN COMPILED. An include closure is not a link "
        "closure: a symbol referenced without its header being included "
        "would not appear here. The build is the check.",
        "The car-era automation bridge verbs (place_machine, coil_agv, "
        "support_robot, CaptureState) still exist and still pull their "
        "car-era headers in, so this closure keeps more than the "
        "spacecraft game strictly needs. A spacecraft-only bridge would "
        "let the rest go.",
        "Reversible twice over: moved rather than deleted, and Source is "
        "tracked in git.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"],
                  "kept_files": len(keep), "kept_lines": kept_lines,
                  "moved_files": len(moved),
                  "failures": failures[:5]}, indent=2))
