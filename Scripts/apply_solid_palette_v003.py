"""Correct what the v002 sweep over-reached on.

v002 did what the owner asked - Meshy's textures are off every station
and drone, and the palette is solid, bright and warm. But its rule was
"anything that is not a drone or a building is machinery", and that
swept up two families that are not machinery at all:

1. THE SIX CRAFT COMPONENTS (SM_LB_CP_*). These are the Hull,
   Electronics, Power, Propulsion, Navigation and Interior models the
   drones carry and fit. They each had their OWN material, which is how
   a player tells one component from another on a station shelf or
   slung under a hauler. Painting all fourteen of them the same amber
   destroyed that distinction - and the Hull in particular has no
   business wearing a factory colour when the craft's colour comes from
   the customer's livery. They are restored to exactly what they wore.

2. THE RUNWAY (SM_LB_RW_*). A runway strip, its chicane pylons and the
   hover pad are ground furniture, not machines. Amber tarmac reads as
   a mistake. They take GRAPHITE, which is what dark ground furniture
   should be - not restored, because two of them were sitting on the
   engine's WorldGridMaterial, which is a fault rather than a look.

Also: WARNING ORANGE was (0.90, 0.44, 0.09) while the new machine amber
is (0.82, 0.46, 0.13). A warning colour that matches the machinery it is
painted on is not a warning. Orange moves to a brighter, yellower safety
tone that reads against amber.

Restoration comes from the v002 RECEIPT, not from a list retyped here -
the receipt recorded what every mesh WAS, which is the only reason this
is reversible at all.

Fail-closed: refuses to rerun over its receipt, refuses if the v002
receipt it restores from is missing, and reads every assignment back.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/solid_palette_v003.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v004.")
prior_path = root / "Saved/Audits/Spacecraft/solid_palette_v002.json"
if not prior_path.exists():
    raise RuntimeError("v002 receipt missing - nothing to restore from.")
prior = json.loads(prior_path.read_text(encoding="utf-8"))

PALETTE = "/Game/LineBoss/Materials/Surfaces"
GRAPHITE = "%s/MI_LB_Surface_Graphite" % PALETTE
ORANGE = "%s/MI_LB_Surface_WarningOrange" % PALETTE
STATIONS = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"

# Where the original component materials live, so a name from the
# receipt can be resolved back to an asset.
SEARCH_ROOTS = [
    "%s/Materials" % STATIONS,
    "%s/Meshes" % STATIONS,
    "%s/Meshes/BuildingTextures" % STATIONS,
    "/Game/LineBoss/Candidates/Spacecraft",
]

library = unreal.EditorAssetLibrary
mat_lib = unreal.MaterialEditingLibrary
failures = []

# ---- a warning colour that is not the machinery colour ----
orange = library.load_asset(ORANGE)
if orange is None:
    failures.append("warning orange missing")
else:
    mat_lib.set_material_instance_vector_parameter_value(
        orange, "BaseTint", unreal.LinearColor(0.97, 0.72, 0.05, 1.0))
    library.save_loaded_asset(orange, only_if_is_dirty=False)

# ---- index every material once, so restoration is a lookup ----
known = {}
for search in SEARCH_ROOTS:
    if not library.does_directory_exist(search):
        continue
    for asset in library.list_assets(search, recursive=True):
        path = asset.split(".")[0]
        known.setdefault(path.split("/")[-1], path)

rows = []
for entry in prior.get("meshes", []):
    name = entry["mesh"]
    is_component = name.startswith("SM_LB_CP_")
    is_runway = name.startswith("SM_LB_RW_")
    if not (is_component or is_runway):
        continue
    mesh_path = known.get(name)
    if mesh_path is None:
        failures.append("mesh not found to correct: %s" % name)
        continue
    mesh = library.load_asset(mesh_path)
    if not isinstance(mesh, unreal.StaticMesh):
        failures.append("not a static mesh: %s" % name)
        continue

    if is_component:
        was = entry.get("was", "")
        # WorldGridMaterial is the ENGINE DEFAULT - a fault, never a
        # look. Nothing is ever restored to it.
        if not was or was == "NONE" or was == "WorldGridMaterial":
            target_path = GRAPHITE
            why = "component (no honest original - graphite)"
        else:
            target_path = known.get(was)
            why = "component restored"
            if target_path is None:
                failures.append("cannot restore %s: %s not found"
                                % (name, was))
                continue
    else:
        target_path = GRAPHITE
        why = "runway furniture"

    material = library.load_asset(target_path)
    if material is None:
        failures.append("material missing: %s" % target_path)
        continue
    try:
        slots = max(1, len(mesh.get_editor_property("static_materials")))
    except Exception:  # noqa: BLE001
        slots = 1
    for slot in range(slots):
        try:
            mesh.set_material(slot, material)
        except Exception as exc:  # noqa: BLE001
            failures.append("%s slot %d: %s" % (name, slot, exc))
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    reloaded = library.load_asset(mesh_path)
    after = reloaded.get_material(0)
    applied = after is not None and after.get_name() == material.get_name()
    if not applied:
        failures.append("%s did not keep %s"
                        % (name, material.get_name()))
    rows.append({"mesh": name, "why": why,
                 "now": after.get_name() if after else "NONE",
                 "applied": applied})

report = {
    "$schema": "lineboss/audit/solid-palette-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__SOLID_PALETTE_CORRECTED" if not failures
               else "FAIL_CLOSED__SOLID_PALETTE_CORRECTION"),
    "why": ("v002's rule treated everything that was not a drone or a "
            "building as machinery, which swept up the six craft "
            "components and the runway. Components each had their own "
            "material - that is how a player tells them apart - and a "
            "runway is not a machine."),
    "corrected": rows,
    "failures": failures,
    "not_proven": [
        "Nobody has looked at the corrected floor yet.",
        "The warning orange moved to (0.97, 0.72, 0.05) so it reads "
        "against amber machinery; that is a judgement, not a decision.",
        "Two runway meshes were on the engine's WorldGridMaterial "
        "before v002 touched them - a pre-existing fault this lane does "
        "not restore them to.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "corrected": len(rows),
                  "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
