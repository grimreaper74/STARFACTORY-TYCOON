"""Record scale and material evidence for vendor assets considered for PR-001--004.

This is read-only apart from its JSON report. It deliberately does not place,
rename or modify any pack content.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
AUDIT = ROOT / "Saved/Audits/front_end_vendor_asset_dimensions_v001.json"
ASSETS = {
    "fence": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Fence_01",
    "fence_part": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_FencePart_01",
    "lamp": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Lamp01",
    "motor": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/Crane/SM_ElectricMotor01",
    "cables": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Cables01",
    "cable_set": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_CableSet_01",
    "electrical_cable": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_ElectricalCable_01",
    "platform": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_IndustrialPlatform01",
    "railing": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_PlatformRailing_01",
    "pipe_long": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Pipe_round_long",
    "pipe_corner": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Pipe_round_corner1",
    "beam": "/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_MetalBeam01",
}


records = []
for role, path in ASSETS.items():
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing curated vendor mesh {path}")
    bounds = mesh.get_bounding_box()
    body = mesh.get_editor_property("body_setup")
    aggregate = body.get_editor_property("agg_geom") if body is not None else None
    collision = {}
    if aggregate is not None:
        for property_name in ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems"):
            collision[property_name] = len(aggregate.get_editor_property(property_name))
    records.append({
        "role": role,
        "asset": mesh.get_path_name(),
        "bounds_cm": {
            "min": list(bounds.min.to_tuple()),
            "max": list(bounds.max.to_tuple()),
            "size": [
                bounds.max.x - bounds.min.x,
                bounds.max.y - bounds.min.y,
                bounds.max.z - bounds.min.z,
            ],
        },
        "materials": [
            {
                "slot": str(slot.get_editor_property("material_slot_name")),
                "material": (
                    slot.get_editor_property("material_interface").get_path_name()
                    if slot.get_editor_property("material_interface") is not None else None
                ),
            }
            for slot in mesh.get_editor_property("static_materials")
        ],
        "collision_primitives": collision,
    })

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "status": "READ_ONLY_AUDIT_PASS",
    "policy": "Curated vendor candidates remain unpromoted until placed and visually reviewed.",
    "records": records,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_FRONT_END_VENDOR_AUDIT_PASS assets={len(records)} path={AUDIT}")
