"""Read-only source mesh/LOD/material-slot audit for the approved master coil."""
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
ASSET = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "master_coil_asset_v002.json"

mesh = unreal.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("approved master coil asset missing")
slots = []
for index, static_material in enumerate(mesh.get_editor_property("static_materials")):
    material = static_material.material_interface
    slots.append({
        "index": index,
        "slot_name": str(static_material.material_slot_name),
        "imported_slot_name": str(static_material.get_editor_property("imported_material_slot_name")),
        "source_material": material.get_path_name() if material else None,
    })
nanite = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_nanite_settings(mesh)
lod_count = int(mesh.get_num_lods())
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS_READ_ONLY",
    "asset": mesh.get_path_name(),
    "lod_count": lod_count,
    "triangles_by_lod": [int(mesh.get_num_triangles(index)) for index in range(lod_count)],
    "nanite_enabled": bool(nanite.enabled),
    "nanite_keep_percent_triangles": float(nanite.keep_percent_triangles),
    "nanite_fallback_percent_triangles": float(nanite.fallback_percent_triangles),
    "material_slots": slots,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_MASTER_COIL_ASSET_AUDIT_PASS output=" + str(OUT))
unreal.SystemLibrary.quit_editor()
