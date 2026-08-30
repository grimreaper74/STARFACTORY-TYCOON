"""Second archive pass: the trees that needed the file-level answer.

The first pass moved the seventeen unambiguous car-era trees (4.1 GB).
This one takes the trees that could not be judged by name because the
spacecraft game needs a HANDFUL of files inside them:

    /Game/Textures          6.1 GB, needs exactly ONE package
    /Game/LineBoss/Vendor   760 MB, needs THREE

and the trees the file-level walk proved need nothing at all:

    /Game/Meshes, LineBoss/Maps, LineBoss/Developer,
    LineBoss/Shared, LineBoss/Runtime, LineBoss/Candidates/Site

HOW THE PARTIAL ONES ARE HANDLED: move the whole tree out, then move the
needed packages back to exactly where they were. That is deliberately
cruder than picking files out one at a time, and safer for it - the
keepers end up in their original paths by construction rather than by a
path-rebuilding routine that could get one wrong, and a mistake shows up
as a missing asset the moment the game runs rather than as a subtly
wrong one.

The keep list is the file-level dependency walk
(spacecraft_keep_packages_v002.json), never folder names. Folder names
have over-reached twice in this project already.

Every .uasset carries sidecars the mover must not leave behind, so a
package is moved as "every file whose name matches its stem".

Fail-closed: refuses to run without the walk, refuses to rerun over its
receipt, and records every move so it reads backwards as an undo.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = root / "Saved/Audits/Spacecraft/car_era_archive_v002.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v003.")

walk = root / "Saved/Audits/Spacecraft/spacecraft_keep_packages_v002.json"
if not walk.exists():
    raise RuntimeError(
        "Refusing to move anything without the file-level walk.")
keep = set(json.loads(walk.read_text(encoding="utf-8"))["packages"])

content = root / "Content"
archive = root / "ArchivedCarEraContent" / "Content"

# Nothing under these is needed - the walk says so at file level.
WHOLE = ["Meshes", "LineBoss/Maps", "LineBoss/Developer",
         "LineBoss/Shared", "LineBoss/Runtime", "LineBoss/Candidates/Site"]
# These hold a few keepers; the tree goes and the keepers come back.
PARTIAL = ["Textures", "LineBoss/Vendor"]

failures = []
moved = []


def megabytes(path):
    if not path.exists():
        return 0
    return round(sum(f.stat().st_size for f in path.rglob("*")
                     if f.is_file()) / (1024 * 1024))


def move_tree(relative):
    source = content / relative
    if not source.exists():
        return 0
    size = megabytes(source)
    destination = archive / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        failures.append("archive already holds %s" % relative)
        return 0
    shutil.move(str(source), str(destination))
    moved.append({"tree": "Content/" + relative, "megabytes": size})
    return size


total = 0
for relative in WHOLE:
    # Guard: never move a tree the walk needs, whatever this list says.
    package_root = "/Game/" + relative
    if any(package.startswith(package_root + "/") for package in keep):
        failures.append("REFUSED - the keep set needs something in %s"
                        % package_root)
        continue
    total += move_tree(relative)

restored = []
for relative in PARTIAL:
    package_root = "/Game/" + relative
    keepers = [p for p in keep if p.startswith(package_root + "/")]
    total += move_tree(relative)
    # Bring the keepers home, into the paths they came from.
    for package in keepers:
        stem = package.split("/")[-1]
        relative_dir = package[len("/Game/"):].rsplit("/", 1)[0]
        source_dir = archive / relative_dir
        target_dir = content / relative_dir
        if not source_dir.exists():
            failures.append("cannot restore %s - %s missing"
                            % (package, source_dir))
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        found = False
        for f in source_dir.iterdir():
            if f.is_file() and f.stem == stem:
                shutil.move(str(f), str(target_dir / f.name))
                found = True
        if not found:
            failures.append("cannot restore %s - no file for it" % package)
        else:
            restored.append(package)

report = {
    "$schema": "lineboss/audit/car-era-archive-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__CAR_ERA_ARCHIVED_PASS_TWO" if not failures
               else "PARTIAL__CAR_ERA_ARCHIVE_PASS_TWO"),
    "why": ("The trees the first pass could not judge by name. Textures "
            "is 6.1 GB and the game needs one package of it; Vendor is "
            "760 MB and needs three. The rest of these trees the "
            "file-level walk proved need nothing at all."),
    "moved_trees": moved,
    "restored_packages": sorted(restored),
    "megabytes_moved": total,
    "failures": failures,
    "not_proven": [
        "NOBODY HAS LAUNCHED THE GAME SINCE. The walk is static and "
        "cannot see a path built at runtime from strings, which is most "
        "of how this presenter loads meshes - so build, run and look is "
        "the check, not this receipt.",
        "Reversible: the archive mirrors the source tree, so every move "
        "here reads backwards as an undo.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"],
                  "megabytes": total,
                  "trees": len(moved),
                  "restored": len(restored),
                  "failures": failures}, indent=2))
