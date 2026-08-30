"""Set the NANITE and INSTANCED-STATIC-MESH usage flags the game needs.

Owner, 2026-08-28, looking at a launched game: "the mesh its lost all
the detail, its on epic in settings". The meshes are fine. Every one of
them is being drawn with the ENGINE DEFAULT MATERIAL, and the engine
says why in its own words, 23 times:

    Material .../MI_LB_AssemblyBay missing usage flag Nanite!
    Default Material will be used in game.

A material must declare the ways it will be used. Ours never declared
Nanite or instanced static meshes, and every mesh we import is Nanite.

WHY THIS WAS INVISIBLE UNTIL A REAL PLAY SESSION: in the EDITOR Unreal
notices the missing flag, sets it on the fly and saves the material, so
everything looks right. A -game run cannot do that - it has no authority
to modify content - so it falls back to the default material instead.
Every screenshot taken in-editor looked correct while the game the owner
actually launched did not, which is exactly the trap the project's own
release-gate rule warns about: editor evidence proves the editor.

Usage flags live on the BASE MATERIAL, never on an instance, so each
instance in the log is resolved to its parent before the flag is set.

Fail-closed like every other lane here: refuses to rerun over its own
receipt, and READS EVERY FLAG BACK off the saved asset rather than
trusting the setter.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/material_usage_flags_v001.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v002.")

# Exactly the materials the ENGINE named, not every material in the
# project: setting a usage flag recompiles that material's shaders, and
# this project decides on measurement rather than on a broad sweep.
NANITE = [
    "/Game/Materials/MI_FactoryConcreteFloor01",
    "/Game/LineBoss/Materials/Surfaces/MI_LB_Surface_PalePanel",
    "/Game/LineBoss/Materials/Surfaces/MI_LB_Surface_Graphite",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/M_LB_Site_Trim",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/M_LB_Track_Accent",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/M_LB_Track_AccentBlue",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/M_LB_Track_Glow",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/M_LB_Track_Panel",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/M_LB_Track_Trim",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/MI_LB_AssemblyBay",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/MI_LB_ChargingDock",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/MI_LB_DroneAssembly",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/MI_LB_DroneCargoLift",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/MI_LB_DroneSpray",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/MI_LB_DroneWinch",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/MI_LB_HoverPad",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes/BuildingTextures/MI_SM_LB_ST_ShipFactoryHall_v002",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes/BuildingTextures/MI_SM_LB_ST_StorageSilo_v001",
]
INSTANCED = [
    "/Game/Materials/MI_Background1",
    "/Game/Materials/MI_Background2",
    "/Game/LineBoss/Materials/Surfaces/MI_LB_Surface_PalePanel",
    "/Game/LineBoss/Materials/Surfaces/MI_LB_Surface_Graphite",
    "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/M_LB_Site_Trim",
]

# Everything the palette master feeds wears the master's flags, so the
# master is repaired even though the engine only named its instances.
EXTRA_BASES = ["/Game/LineBoss/Materials/Surfaces/M_LB_Surface_Master"]

library = unreal.EditorAssetLibrary
failures = []
rows = []


def base_material(path):
    """The BASE material behind a path - usage flags live only there."""
    asset = library.load_asset(path)
    if asset is None:
        return None, "asset missing"
    seen = 0
    while isinstance(asset, unreal.MaterialInstance) and seen < 8:
        parent = asset.get_editor_property("parent")
        if parent is None:
            return None, "instance has no parent"
        asset = parent
        seen += 1
    if not isinstance(asset, unreal.Material):
        return None, "did not resolve to a Material"
    return asset, None


wanted = {}
for path in NANITE:
    wanted.setdefault(path, set()).add("used_with_nanite")
for path in INSTANCED:
    wanted.setdefault(path, set()).add("used_with_instanced_static_meshes")
for path in EXTRA_BASES:
    wanted.setdefault(path, set()).update(
        ["used_with_nanite", "used_with_instanced_static_meshes"])

# Instances collapse onto shared parents; repair each parent once.
by_base = {}
for path, flags in sorted(wanted.items()):
    material, why = base_material(path)
    if material is None:
        failures.append("%s: %s" % (path, why))
        continue
    entry = by_base.setdefault(material.get_path_name(),
                               {"material": material, "flags": set(),
                                "asked_for": []})
    entry["flags"].update(flags)
    entry["asked_for"].append(path.split("/")[-1])

for base_path, entry in sorted(by_base.items()):
    material = entry["material"]
    for flag in sorted(entry["flags"]):
        try:
            material.set_editor_property(flag, True)
        except Exception as exc:  # noqa: BLE001
            failures.append("%s could not take %s: %s"
                            % (base_path, flag, exc))
    library.save_loaded_asset(material, only_if_is_dirty=False)
    # READ BACK off the saved asset: a setter that silently did nothing
    # is exactly the failure this whole lane exists to catch.
    reloaded = library.load_asset(base_path.split(".")[0])
    verified = {}
    for flag in sorted(entry["flags"]):
        try:
            verified[flag] = bool(reloaded.get_editor_property(flag))
        except Exception:  # noqa: BLE001
            verified[flag] = None
        if verified[flag] is not True:
            failures.append("%s did not keep %s" % (base_path, flag))
    rows.append({
        "base_material": base_path,
        "repaired_for": sorted(entry["asked_for"]),
        "flags": verified,
    })

report = {
    "$schema": "lineboss/audit/material-usage-flags-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__MATERIAL_USAGE_FLAGS_SET" if not failures
               else "FAIL_CLOSED__MATERIAL_USAGE_FLAGS"),
    "why": ("Owner 2026-08-28 launched the game and reported the meshes "
            "had lost all detail. The engine had already said why, 23 "
            "times: materials missing the Nanite usage flag are replaced "
            "by the DEFAULT MATERIAL in a -game run. The editor sets the "
            "flag on the fly and saves it, so editor evidence looked "
            "correct while the launched game did not."),
    "base_materials": rows,
    "failures": failures,
    "not_proven": [
        "Nobody has relaunched and looked yet. The flags are set and "
        "read back; whether the factory now READS right is the owner's "
        "call, not this receipt's.",
        "Only the materials the engine actually named were touched. Any "
        "material not yet used on a Nanite mesh will warn the same way "
        "the first time it is, and should be added to a v002 rather "
        "than the project being swept blindly.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"],
                  "base_materials": len(rows),
                  "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
