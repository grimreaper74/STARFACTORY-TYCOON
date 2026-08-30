"""inspect_textures_v001.py - READ-ONLY: source file, size and sRGB
flag of the power-plant texture trio (and its neighbours), to prove
whether the wrong image landed in the BaseColor asset."""
import unreal

TEX_DIR = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Textures"
KEYS = ("PowerPlant", "RollingMill")
lib = unreal.EditorAssetLibrary
for asset_path in sorted(lib.list_assets(TEX_DIR, recursive=False)):
    name = asset_path.split("/")[-1].split(".")[0]
    if not any(k in name for k in KEYS):
        continue
    tex = unreal.load_asset(asset_path)
    if not isinstance(tex, unreal.Texture2D):
        continue
    src = tex.get_editor_property("asset_import_data")
    first = ""
    try:
        files = src.extract_filenames()
        first = files[0] if files else ""
    except Exception:
        first = "?"
    unreal.log("TEXCHK %-34s %dx%d srgb=%s comp=%s src=%s" % (
        name, tex.blueprint_get_size_x(), tex.blueprint_get_size_y(),
        tex.get_editor_property("srgb"),
        str(tex.get_editor_property("compression_settings")).split(".")[-1],
        first.split("\\")[-1]))
unreal.log("TEXCHK DONE")
