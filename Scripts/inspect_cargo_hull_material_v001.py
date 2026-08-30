"""What is the Cargo hull material made of, and do Scout maps exist?

The Scout - the craft in every launch - wears WorldGridMaterial, the
engine default. The Cargo wears a real instance. Before building the
Scout one, look at how its sibling is put together and find out what
textures the Scout actually has.
"""
import unreal
library = unreal.EditorAssetLibrary
mat_lib = unreal.MaterialEditingLibrary

MI = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials/"
      "MI_LB_SC_Cargo01_Hull")
inst = library.load_asset(MI)
if inst is None:
    print("HULLPROBE cargo instance missing")
else:
    parent = inst.get_editor_property("parent")
    print("HULLPROBE parent %s" % (parent.get_path_name() if parent else "NONE"))
    for tp in inst.texture_parameter_values:
        tex = tp.parameter_value
        print("HULLPROBE texture %s = %s"
              % (tp.parameter_info.name,
                 tex.get_path_name() if tex else "NONE"))
    for sp in inst.scalar_parameter_values:
        print("HULLPROBE scalar %s = %s"
              % (sp.parameter_info.name, sp.parameter_value))
    for vp in inst.vector_parameter_values:
        print("HULLPROBE vector %s = %s"
              % (vp.parameter_info.name, vp.parameter_value))

# Any texture with Scout in the name, anywhere.
hits = []
for asset in library.list_assets(
        "/Game/LineBoss/Candidates/Spacecraft", recursive=True):
    name = asset.split("/")[-1].split(".")[0]
    if "Scout" in name and ("_base" in name.lower() or "color" in name.lower()
                            or "normal" in name.lower()
                            or name.startswith("T_")):
        hits.append(asset)
print("HULLPROBE scout maps %d" % len(hits))
for h in sorted(hits)[:12]:
    print("HULLPROBE map %s" % h)
