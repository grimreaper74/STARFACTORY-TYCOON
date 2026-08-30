"""Move the car game's content out of Content/, reversibly.

Owner, 2026-08-28: "just put the car content in a different folder" -
after being told that Content/ is gitignored and a delete would have no
undo. Moving is the right answer: everything survives, and Unreal simply
stops seeing it because it is no longer under Content/.

WHAT DECIDES WHAT MOVES: a dependency walk, not folder names. The
spacecraft game needs 474 packages out of 18,055 - established by
Scripts scan (receipt: spacecraft_keep_set_v001.json) walking the
playable map plus every soft-path root the C++ loads. Folder names are
exactly the wrong tool for this and this project has proved it twice
already: the fixing split and the palette sweep both over-reached by
matching on names.

STAGED ON PURPOSE. This first pass moves only the UNAMBIGUOUS car-era
trees - press shop, weld shop, paint shop, the Cairnwell vehicles, the
OneFactory floor and their robots. The genuinely ambiguous ones
(/Game/Textures at 6.1 GB, /Game/Meshes, LineBoss/Maps, Developer,
Shared, Vendor) are left for a second pass once this one is verified by
actually launching the game - because a static dependency walk cannot
see a path built at runtime from strings, and the only honest check is
to run it.

REVERSIBLE BY CONSTRUCTION: every move is recorded in the receipt as a
from/to pair, and the destination mirrors the source tree exactly, so
putting it back is the same list read backwards.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = root / "Saved/Audits/Spacecraft/car_era_archive_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")

content = root / "Content"
archive = root / "ArchivedCarEraContent" / "Content"

keep_receipt = root / "Saved/Audits/Spacecraft/spacecraft_keep_set_v001.json"
if not keep_receipt.exists():
    raise RuntimeError(
        "Refusing to move anything without the dependency walk. "
        "Run the keep-set scan first.")
keep = json.loads(keep_receipt.read_text(encoding="utf-8"))
needed_folders = set(keep.get("folders_needed", {}))

# Unambiguous car-era trees, relative to Content/.
MOVE = [
    "LineBoss/Candidates/PressShop",
    "LineBoss/Candidates/PressTrains",
    "LineBoss/Candidates/WeldShop",
    "LineBoss/Candidates/PaintShop",
    "LineBoss/Candidates/AssemblyShop",
    "LineBoss/Candidates/Vehicles",
    "LineBoss/Candidates/ControlRoom",
    "LineBoss/Candidates/Architecture",
    "LineBoss/Factory",
    "LineBoss/Stations",
    "LineBoss/PressTrains",
    "LineBoss/IndustrialKit",
    "LineBoss/Equipment",
    "LineBoss/Robots",
    "LineBoss/SupportRobots",
    "LineBoss/Brand",
    "LineBoss/Native",
]

failures = []
moves = []
for relative in MOVE:
    source = content / relative
    if not source.exists():
        continue
    # LAST-DITCH GUARD: never move a tree the dependency walk said the
    # spacecraft game needs, whatever this list claims.
    package_root = "/Game/" + relative
    if any(folder.startswith(package_root) or package_root.startswith(folder)
           for folder in needed_folders
           if folder.count("/") >= package_root.count("/")):
        failures.append("REFUSED - the keep set needs %s" % package_root)
        continue
    destination = archive / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    size_mb = sum(f.stat().st_size for f in source.rglob("*") if f.is_file())
    size_mb = round(size_mb / (1024 * 1024))
    try:
        shutil.move(str(source), str(destination))
    except Exception as exc:  # noqa: BLE001
        failures.append("%s: %s" % (relative, exc))
        continue
    moves.append({"from": "Content/" + relative,
                  "to": "ArchivedCarEraContent/Content/" + relative,
                  "megabytes": size_mb})

report = {
    "$schema": "lineboss/audit/car-era-archive-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__CAR_ERA_ARCHIVED" if not failures
               else "PARTIAL__CAR_ERA_ARCHIVE"),
    "why": ("Owner asked for the car content moved rather than deleted, "
            "because Content/ is gitignored and a delete would have had "
            "no undo. What moves is decided by a dependency walk of the "
            "spacecraft game (474 packages of 18,055), never by folder "
            "names."),
    "archive_root": str(archive),
    "moved": moves,
    "megabytes_moved": sum(m["megabytes"] for m in moves),
    "failures": failures,
    "not_proven": [
        "NOBODY HAS LAUNCHED THE GAME SINCE. A static dependency walk "
        "cannot see a path built at runtime from strings, so the only "
        "honest check is to build, run and look - which is the next "
        "step, not a claim this receipt gets to make.",
        "This is the FIRST of two passes. /Game/Textures (6.1 GB), "
        "/Game/Meshes, LineBoss/Maps, Developer, Shared and Vendor are "
        "deliberately untouched until this pass is verified.",
        "Fully reversible: every move is a from/to pair here and the "
        "destination mirrors the source tree exactly.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"],
                  "moved": len(moves),
                  "megabytes": report["megabytes_moved"],
                  "failures": failures}, indent=2))
