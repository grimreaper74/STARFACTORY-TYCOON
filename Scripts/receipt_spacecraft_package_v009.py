"""Write the audit receipt for the SpacecraftSlice_v009 package.

Plain stdlib - runs AFTER the UAT package and the packaged journey, and
reads everything it claims from the artifacts themselves: exe sha256
hashed from disk, pak size measured, cook stats parsed from the UAT log,
journey results parsed from the journey's own -abslog. Nothing here is
typed in from memory.

Also on record: v004 and v005 were packaged WITHOUT receipts - their
evidence is their logs (packaged_v004_journey.log,
packaged_v005_journey.log). This lane exists so that gap ends at v009.

Run:  python Scripts/receipt_spacecraft_package_v009.py
"""

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
BUILD = ROOT / "Builds/SpacecraftSlice_v009/Windows"
PKG_LOG = ROOT / "Saved/Logs/package_spacecraft_v009.log"
JOURNEY_LOG = ROOT / "Saved/Logs/packaged_v009_journey.log"
OUT = ROOT / "Saved/Audits/Spacecraft/spacecraft_slice_package_v009.json"

if OUT.exists():
    raise SystemExit("Refusing to rerun: receipt exists. Author v009.")

failures = []

exe = BUILD / "LineBossCarFactory.exe"
if not exe.exists():
    raise SystemExit("No packaged exe at %s - package first." % exe)
exe_sha = hashlib.sha256(exe.read_bytes()).hexdigest().upper()

pak_bytes = sum(f.stat().st_size for f in BUILD.rglob("*")
                if f.suffix in (".pak", ".ucas", ".utoc"))

pkg_text = PKG_LOG.read_text(encoding="utf-8", errors="replace")
cook = {}
m = re.search(r"Cook: Cooked packages (\d+) Packages Skipped .*?(\d+)",
              pkg_text)
cooked = re.search(r"Cooked packages (\d+)", pkg_text)
cook["packages_cooked"] = int(cooked.group(1)) if cooked else None
cook["errors"] = pkg_text.count("Error:")
# The v008 material repair must HOLD: a null shader map means the
# buildings are back on the engine default material, which is the
# fault the owner called "a mess".
cook["null_shadermap_warnings"] = pkg_text.count(
    "doesn't have a valid ShaderMap")
if cook["null_shadermap_warnings"]:
    failures.append(
        "%d materials cooked with null shader maps - the v008 repair "
        "has regressed" % cook["null_shadermap_warnings"])
uat_ok = "BUILD SUCCESSFUL" in pkg_text
if not uat_ok:
    failures.append("UAT log does not say BUILD SUCCESSFUL")

journey = {}
if JOURNEY_LOG.exists():
    jt = JOURNEY_LOG.read_text(encoding="utf-8", errors="replace")
    status = re.findall(
        r"SPACECRAFT STATUS sim=([\d.]+)s stations=(\d+) commissioned=(\d+) "
        r"configured=(\d+) revenue=(\d+) cash=(\d+)", jt)
    if status:
        sim, stations, comm, conf, revenue, cash = status[-1]
        journey = {
            "sim_seconds": float(sim), "stations": int(stations),
            "commissioned": bool(int(comm)), "configured": bool(int(conf)),
            "revenue_pence": int(revenue), "cash_pence": int(cash),
        }
        if int(revenue) < 67500000:
            failures.append(
                "arc journey expected five deliveries (67,500,000); got %s"
                % revenue)
    else:
        failures.append("journey log has no SPACECRAFT STATUS line")
    chain = re.search(r"CHAIN (\d+) machines still owe cycles", jt)
    journey["chain_stuck_machines"] = int(chain.group(1)) if chain else None
    if chain and int(chain.group(1)) != 0:
        failures.append("chain ended with %s stuck machines" % chain.group(1))
    journey["exited_cleanly"] = "LogExit: Exiting." in jt
    if not journey.get("exited_cleanly"):
        failures.append("journey did not exit cleanly")
    journey["log"] = str(JOURNEY_LOG.relative_to(ROOT)).replace("\\", "/")
else:
    failures.append("no packaged journey log - run the journey first")

report = {
    "$schema": "lineboss/audit/spacecraft-slice-package-v009/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__SPACECRAFT_SLICE_v009_PACKAGED_AND_JOURNEY_VERIFIED"
               if not failures
               else "FAIL_CLOSED__SPACECRAFT_SLICE_v009"),
    "configuration": "Development",
    "platform": "Win64",
    "map": ("/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001/"
            "Maps/LB_SpacecraftFactory_v001"),
    "archive": "Builds/SpacecraftSlice_v009/Windows",
    "delta_since_v007": [
        "THE WORLD MAP OPENING: the game starts on the site, the ship "
        "factory is the only thing offered, and it must be placed and "
        "entered before anything can be built inside it.",
        "A 600 m site with three same-scale buildings the player "
        "places, a perimeter ring road with a spur to each door, and "
        "land bought outward from the middle 440 m.",
        "Site and interior dressed with ELEVEN assets we generated "
        "through the Meshy API (300 credits) in the game's own white "
        "futuristic language, plus a district built from the "
        "759-piece industrial kit the project already owned.",
        "Clicking a station opens its own page: drone slots, four "
        "drone kinds to hire with their jobs and prices, the crew "
        "standing there, and the fitting allocation.",
        "INSPECTION BETWEEN STATIONS - the first thing taken from the "
        "settled pulse-line model: a station reworks its own bad work "
        "instead of passing it down the line, when someone competent "
        "is watching.",
    ],
    "cook": cook,
    "uat_log_says_successful": uat_ok,
    "executable_sha256": exe_sha,
    "pak_bytes": pak_bytes,
    "journey": journey,
    "not_proven": [
        "The journey runs -nullrhi: nothing was seen or heard in the "
        "packaged build. Sighted evidence for the panel fix is the "
        "editor-binary LiveProof25/30 captures, not this package.",
        "No human has played this build.",
    ],
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "failures": failures,
                  "journey": journey}, indent=2))
sys.exit(1 if failures else 0)
