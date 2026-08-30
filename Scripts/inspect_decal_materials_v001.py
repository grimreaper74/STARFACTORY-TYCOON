"""inspect_decal_materials_v001.py - READ-ONLY.

The auto-painted bay markings register and clean up correctly but have
never been seen rendering. This rules the material out or in: a decal
whose material is not MD_DeferredDecal is not refused - the renderer
quietly substitutes the engine default decal, so the paint is wrong
rather than absent. Prints the domain, blend mode and parent chain for
every material the paint lane loads.

VERDICT when this was run (2026-08-26): both Fab materials ARE
decal-domain. The materials were never the fault.
"""

import unreal

PATHS = [
    "/Game/Materials/MI_DangerLine_01",
    "/Game/Materials/MI_Decal_FloorTraces1",
]


def describe(path, depth=0):
    pad = "  " * depth
    asset = unreal.load_asset(path)
    if asset is None:
        unreal.log_error("DECALCHK MISSING %s" % path)
        return
    cls = asset.get_class().get_name()
    unreal.log("DECALCHK %s%s -> %s" % (pad, path, cls))
    base = asset
    if isinstance(asset, unreal.MaterialInstance):
        parent = asset.get_editor_property("parent")
        if parent is None:
            unreal.log_error("DECALCHK %s  NO PARENT" % pad)
            return
        base = parent
        unreal.log("DECALCHK %s  parent=%s"
                   % (pad, parent.get_path_name()))
    try:
        domain = base.get_editor_property("material_domain")
        blend = base.get_editor_property("blend_mode")
        unreal.log("DECALCHK %s  domain=%s blend=%s"
                   % (pad, domain, blend))
        # Compare ENUM TO ENUM. An earlier version of this script
        # compared str(domain) against "MaterialDomain.MD_DEFERRED_DECAL"
        # - the repr is "<MaterialDomain.MD_DEFERRED_DECAL: 1>", so the
        # test never matched and it reported perfectly good decal
        # materials as broken. That false verdict cost a diagnosis.
        if domain != unreal.MaterialDomain.MD_DEFERRED_DECAL:
            unreal.log_error(
                "DECALCHK %s  NOT A DECAL MATERIAL - the renderer will "
                "substitute the engine default" % pad)
    except Exception as exc:  # noqa: BLE001 - diagnostic lane
        unreal.log_error("DECALCHK %s  could not read domain: %s"
                         % (pad, exc))


for p in PATHS:
    describe(p)

# What decal-domain materials DOES the project already own?
reg = unreal.AssetRegistryHelpers.get_asset_registry()
found = 0
for data in reg.get_assets_by_path("/Game", recursive=True):
    name = str(data.asset_name)
    if "ecal" not in name:
        continue
    asset = data.get_asset()
    base = asset
    if isinstance(asset, unreal.MaterialInstance):
        base = asset.get_editor_property("parent")
    if base is None or not isinstance(base, unreal.Material):
        continue
    if str(base.get_editor_property("material_domain")) == \
            "MaterialDomain.MD_DEFERRED_DECAL":
        unreal.log("DECALCHK CANDIDATE %s" % data.package_name)
        found += 1
        if found >= 25:
            break
unreal.log("DECALCHK DONE candidates=%d" % found)
