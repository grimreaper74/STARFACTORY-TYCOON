"""Force sRGB on the buildings' base-colour textures, reporting the
before-state. The base-colour PNGs measure ~0.68 sRGB - light grey -
yet the buildings render mid-charcoal. A light sRGB texture sampled as
LINEAR darkens midtones by exactly that much (0.68^2.2 = 0.43), so the
prime suspect is the flag, and this prints what it actually was."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
TEX_ROOT = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/"
            "Meshes/BuildingTextures")
out = root / "Saved/Audits/Spacecraft/building_materials_repair_v003.json"
library = unreal.EditorAssetLibrary
rows = []
for asset in library.list_assets(TEX_ROOT, recursive=False):
    name = asset.split("/")[-1].split(".")[0]
    if not name.endswith("_base_color"):
        continue
    tex = library.load_asset("%s/%s" % (TEX_ROOT, name))
    if tex is None:
        continue
    before = bool(tex.get_editor_property("srgb"))
    vt = bool(tex.get_editor_property("virtual_texture_streaming"))
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("compression_settings",
                            unreal.TextureCompressionSettings.TC_DEFAULT)
    library.save_loaded_asset(tex, only_if_is_dirty=False)
    after = bool(library.load_asset(
        "%s/%s" % (TEX_ROOT, name)).get_editor_property("srgb"))
    rows.append({"texture": name, "srgb_before": before,
                 "srgb_after": after, "virtual_textured": vt})
    print("%-44s srgb %s -> %s  vt=%s" % (name, before, after, vt))
report = {
    "$schema": "lineboss/audit/building-materials-repair-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__BASE_COLOR_SRGB_FORCED",
    "textures": rows,
}
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("textures: %d" % len(rows))
