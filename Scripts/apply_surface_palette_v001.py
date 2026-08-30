"""Put the project's OWN palette on the generated props.

Owner 2026-08-28: materials are authored in Unreal, not taken from
Meshy. The eleven generated assets currently wear eleven unrelated
Meshy map sets; this points them at the shared palette instead, so the
site has one look tuned in one place.

Structural things take GRAPHITE (the dark framing of the settled
language); everything else takes PALE PANEL. Nothing is deleted - the
Meshy instances stay in the project as evidence of what was tried, and
a mesh can be pointed back at one by changing a line here.

Fail-closed: reads the assignment back off the saved asset, and fails
if any mesh ends up on a material that is not the palette.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/surface_palette_applied_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")

PALETTE = "/Game/LineBoss/Materials/Surfaces"
PALE = "%s/MI_LB_Surface_PalePanel" % PALETTE
GRAPHITE = "%s/MI_LB_Surface_Graphite" % PALETTE
SC = "/Game/LineBoss/Candidates/Spacecraft/SiteScenery_v001"
IN = "/Game/LineBoss/Candidates/Spacecraft/ShipFactoryInterior_v001"

ASSIGN = {
    # Structural steel reads dark in the settled language.
    "%s/SM_LB_SC_FencePanel" % SC: GRAPHITE,
    "%s/SM_LB_SC_LightMast" % SC: GRAPHITE,
    "%s/SM_LB_IN_GantryCrane" % IN: GRAPHITE,
    # Panelled bodies read pale.
    "%s/SM_LB_SC_EntranceGate" % SC: PALE,
    "%s/SM_LB_SC_CargoContainer" % SC: PALE,
    "%s/SM_LB_SC_StorageTank" % SC: PALE,
    "%s/SM_LB_SC_Substation" % SC: PALE,
    "%s/SM_LB_SC_DeliveryHauler" % SC: PALE,
    "%s/SM_LB_IN_StockpileRack" % IN: PALE,
    "%s/SM_LB_IN_HallColumn" % IN: PALE,
    "%s/SM_LB_IN_DispatchDoor" % IN: PALE,
}

library = unreal.EditorAssetLibrary
failures = []
rows = []
for path, material_path in sorted(ASSIGN.items()):
    material = library.load_asset(material_path)
    mesh = library.load_asset(path)
    if material is None:
        failures.append("palette material missing: %s" % material_path)
        continue
    if not isinstance(mesh, unreal.StaticMesh):
        failures.append("mesh missing: %s" % path)
        continue
    before = mesh.get_material(0)
    mesh.set_material(0, material)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    reloaded = library.load_asset(path)
    after = reloaded.get_material(0)
    ok = after is not None and after.get_name() == material.get_name()
    if not ok:
        failures.append("%s did not keep %s"
                        % (path.split("/")[-1], material.get_name()))
    rows.append({
        "mesh": path.split("/")[-1],
        "was": before.get_name() if before else "NONE",
        "now": after.get_name() if after else "NONE",
        "applied": ok,
    })

report = {
    "$schema": "lineboss/audit/surface-palette-applied-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__PALETTE_APPLIED" if not failures
               else "FAIL_CLOSED__PALETTE_APPLY"),
    "why": ("Owner 2026-08-28: materials authored in Unreal, not taken "
            "from Meshy - one look, tuned in one place."),
    "meshes": rows,
    "failures": failures,
    "not_proven": [
        "Nobody has looked at the palette on the site yet. The tints "
        "aim at the owner's COLD STEEL decision but are not agreed.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "meshes": len(rows),
                  "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
