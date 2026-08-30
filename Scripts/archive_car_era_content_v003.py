"""Third archive pass: the orphan trees that were BREAKING THE COOK.

Found by trying to fix the standalone game executable, which will not
launch at all. Its cooked data is stale and its Zen backing is gone, so
the fix is a re-cook - and the cook CRASHES, on an array bounds
assertion during garbage collection, immediately after pages of:

  Package /Game/Materials/Mi_3ColorsMaskBase_UniqueForward has a
  dependency on package /Game/Textures/T_AssemblyLineRoll01_BC which
  does not exist.

That is damage from the FIRST two archive passes. They moved
/Game/Textures out and restored only the one package the dependency walk
needed - correctly - but nothing checked what was left pointing AT the
moved textures. /Game/Materials was never in any move list, so 430
car-era materials stayed behind with their textures gone.

The lesson worth keeping: archiving by dependency walk tells you what
the game NEEDS. It does not tell you what is left DANGLING, and a
dangling reference is quiet until something walks the whole content tree
- which a cook does.

WHAT MOVES, decided by the walk and not by name:
    /Game/Materials   430 files, 49 MB, 0 packages needed
    /Game/Fx           20 files, 17 MB, 0 packages needed

WHAT DOES NOT MOVE, though the walk does not name it either:

    /Game/Localization

Localization data is loaded BY CULTURE at runtime, not referenced by
package, so a dependency walk structurally cannot see it. Moving it
because the walk stayed silent would quietly break the translated build
the owner requires - and it would break it in a way that only shows up
in another language. The walk's blind spot matters more here than its
answer.

Empty directories (Audio, Collections, Developers) are left alone: they
cost nothing and removing them is churn, not cleanup.

MOVED, NOT DELETED, and the receipt reads backwards as an undo.
Fail-closed: refuses to rerun over its receipt, and refuses outright if
the keep set turns out to need anything in a tree it was about to move.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = root / "Saved/Audits/Spacecraft/car_era_archive_v003.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v004.")

walk = root / "Saved/Audits/Spacecraft/spacecraft_keep_packages_v002.json"
if not walk.exists():
    raise RuntimeError("Refusing to move anything without the file-level walk.")
keep = set(json.loads(walk.read_text(encoding="utf-8"))["packages"])

content = root / "Content"
archive = root / "ArchivedCarEraContent" / "Content"

MOVE = ["Materials", "Fx"]
# Named so the reason is in the receipt, not only in this docstring.
KEPT_DESPITE_WALK = {
    "Localization": ("loaded by culture at runtime, not by package "
                     "reference, so the dependency walk cannot see it; "
                     "the game ships translated"),
}

failures = []
moved = []
for relative in MOVE:
    source = content / relative
    if not source.exists():
        continue
    package_root = "/Game/" + relative
    needed = [p for p in keep if p.startswith(package_root + "/")]
    if needed:
        failures.append("REFUSED - the keep set needs %d package(s) in %s"
                        % (len(needed), package_root))
        continue
    destination = archive / relative
    if destination.exists():
        failures.append("archive already holds %s" % relative)
        continue
    size = round(sum(f.stat().st_size for f in source.rglob("*")
                     if f.is_file()) / (1024 * 1024))
    files = sum(1 for f in source.rglob("*") if f.is_file())
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(source), str(destination))
    except Exception as exc:  # noqa: BLE001
        failures.append("%s: %s" % (relative, exc))
        continue
    moved.append({"from": "Content/" + relative,
                  "to": "ArchivedCarEraContent/Content/" + relative,
                  "files": files, "megabytes": size})

report = {
    "$schema": "lineboss/audit/car-era-archive-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__ORPHAN_TREES_ARCHIVED" if not failures
               else "PARTIAL__ORPHAN_TREES_ARCHIVE"),
    "why": ("The standalone game executable cannot launch and needs a "
            "re-cook; the cook CRASHED on an array bounds assertion "
            "after pages of dangling-dependency spam from car-era "
            "materials whose textures the first two archive passes had "
            "moved. Archiving by dependency walk says what the game "
            "needs; it does not say what is left dangling, and a "
            "dangling reference stays quiet until something walks the "
            "whole content tree."),
    "moved": moved,
    "megabytes_moved": sum(m["megabytes"] for m in moved),
    "kept_despite_walk": KEPT_DESPITE_WALK,
    "failures": failures,
    "not_proven": [
        "THE COOK HAS NOT BEEN RERUN. This addresses the dangling "
        "references the crash log was full of; it is not proof that the "
        "crash is gone. The cook is the check.",
        "Only trees with ZERO needed packages were moved. A tree the "
        "walk partly needs would require the move-then-restore handling "
        "pass two used, and none qualified here.",
        "Reversible: the archive mirrors the source tree, so every move "
        "reads backwards as an undo.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"],
                  "moved": moved,
                  "megabytes": report["megabytes_moved"],
                  "failures": failures}, indent=2))
