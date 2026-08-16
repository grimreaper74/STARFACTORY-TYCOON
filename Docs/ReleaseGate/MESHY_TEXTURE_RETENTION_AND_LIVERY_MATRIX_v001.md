# Meshy Texture Retention and Cairnwell Livery Matrix

**Baseline:** 2026-08-13  
**Applies to:** the existing Meshy source library only.  
**Status:** implementation authority for candidate visual derivatives; it does not promote any source into runtime by itself.

## Core decision

We are **not** stripping Meshy models back to flat colour.  For every retained role-matched Meshy asset:

- keep its **normal**, **roughness/metallic (ORM)**, **ambient/detail**, **decals**, **labels**, **screen/UI**, **cable/hose**, **rubber**, **steel**, **fastener**, **vent/louvre** and **wear** information;
- retain the complete base-colour atlas when it contains semantic controls, labels, status lenses or mixed materials that cannot safely be recoloured globally;
- recolour only deliberate broad fabricated-paint surfaces in a new derived material or separately identified material slot/mask;
- never multiply an entire mixed Meshy atlas by a green/white tint: that would corrupt safety controls, screens, labels and exposed metal.

The engineering source and every original Meshy source remain immutable.  All retinting is done in a newly named Unreal material/derivative.

## Approved Cairnwell colour roles

| Role | Colour | Use |
| --- | --- | --- |
| Fabricated enclosure body | Warm White `#F3F1E9` | Main panels, doors, roofs, cabinet bodies |
| Structure / motor / gearbox | Foundry Charcoal `#202428` | Bases, frames, motors, gearboxes, guards where dark is mechanically credible |
| Secondary equipment | Steel Grey `#70777C` | Secondary fabricated equipment, non-brand neutral structure |
| Service/ownership panel | Cairnwell Green `#1F4B44` | A restrained door, service strip, access panel, ID surround or ownership plate |
| Functional safety | Safety Yellow `#F2C300` | Guard rails, pinch-zone hardware, hazard edges and real safety devices only |
| Stop/fault | Signal Red `#C7352C` | E-stops, fault/alarm lenses only |
| Process contact | Existing brushed/bare steel maps | Mandrels, rolls, shafts, bearings, press contacts and tooling |
| Flexible service | Existing black rubber/cable maps | Hoses, cable conduits, gaskets and glands |

## Texture selection by asset family

| Family / chosen source | Keep untouched | Retint / override only in derivative | Explicitly do not do |
| --- | --- | --- | --- |
| **PR005 detailed operator HMI** — `SourceAssets/Shared/FactoryAssetLibrary/MeshyCabinetHMI_v632/SM_CA_Factory_OperatorHMI_MeshyMaster_v632.glb` | Full packed PBR atlas: base colour, ORM, normal and emission. Keep screen, buttons, E-stop, labels, cabling and metal detail intact. | No global tint. Add a small separate Cairnwell-green ownership/ID plate or a physically separate service panel only after runtime screenshot review. | Do not use the v026 embedded copy: its null material slots can turn the HMI flat/grey. Do not treat static Meshy emission as working status lights. |
| **PR005 detailed electrical cabinet** — `.../SM_CA_Factory_ElectricalCabinet_MeshyMaster_v632.glb` | Full PBR atlas, electrical labels, door hardware, vents, glands and cable detail. | After isolated validation, retint only an identified broad cabinet-body material or add a separate warm-white/green outer panel. | Do not recolour UI, warning plates, gland strips, vents or safety hardware. Not part of first PR005 runtime change. |
| **PR005 matched exterior skins** — the B/C/D/E + roof Meshy sources and `ArtSkin_v009_MeshyFullSkinColoured` | High-frequency normal/roughness detail for folded edges, hinges, latches, vents, brackets, rails and service details. Keep all exposed steel/black cable/safety parts semantically distinct. | Broad enclosure panels: Warm White; structural beams/base: Charcoal; one or two access/service panels: Green; true guard/rail faces: Yellow. | Do not hide mandrel, pinch rolls, threader, strip path or moving components. Do not make all panels green/yellow. |
| **PR006 / PR007 dedicated ReleaseDetail overlays** | Existing roll/shaft/motor/valve/hose/door/vent detail; all bare metal and black service materials. | Fixed exterior access panels and utility housings use Warm White/Steel Grey; drive racks/frames Charcoal; selected service access panels Green. | Do not recolour or attach detail to roll cassette, gap cylinders, strip path, moving guards, wash/lube process surfaces. |
| **PR008 10 station-specific detailed modules** | Rollers, knife/shear surfaces, drive motors, cable/hose, HMI screen/button detail, station labels and safety components. | Fixed enclosures/cabinets Warm White; fixed frames/HPU Charcoal; selected service doors Green; guards genuinely Yellow. | Do not replace detailed PR008 HMI/cabinets with stretched generic Meshy models. Do not globally tint mixed panels. |
| **PR009 production source / blank stacker** | Existing texture detail, inspection hardware, cable/service systems, guard mesh, labels and panel/stack detail. | Only separated fixed paint shells may become Warm White/Green; structure/movers stay Charcoal/steel. | Do not treat `v087/ReleaseCollision` as a visual texture authority. Do not bake colour into collision donor meshes. |
| **PR010 four-lane supermarket / feed** — engineering core plus `Meshy_AI_Cairnwell_Roller_Conv_0808165030_texture.blend` and `Meshy_AI_Industrial_Adjustable_0812070022_texture.blend` | Conveyor roller, chain/drive, bare steel, black cable, stillage hardware and existing labels. | Conveyor/stillage fixed side frames: Charcoal or Steel Grey; controlled access/cabinet: Warm White; limited Green service/ownership strip; true guards Yellow. | Do not call a generic Meshy asset a supermarket; do not repaint the four-lane engineering core without a new authorized derivative. |
| **Inbound lorry / coil AGVs / coil handler** | Complete PBR texture sets, coil steel, tyres, labels, warning stripes, lights and mechanical hardware. | Only approved body-panel livery/material instances; preserve visual condition/detail and safety markings. | Do not replace readable approved Coil AGV texture with the rejected softer v919 bake. |
| **Conveyors / stillages** | Full PBR surface detail: rollers, chains, bolts, mesh, forks, steel and labels. | Broad fixed frames may use Charcoal/Steel Grey; safety rails/edges Yellow where functionally correct. | Do not flatten them to one grey material or use cargo racks as machine cores. |
| **Body Weld robots, fixture, vision gate and EOAT** | Robot joints, cabling, tools, steel jigs, suction cups, lenses, labels and detailed PBR maps. Retain role-correct clean robot paint where it reads correctly in the reference. | Fixed fixture enclosure/support: Warm White/Charcoal; carefully selected static service panels Green; genuinely protective rails Yellow. | Do not recolour welded tooling or the BIW as branding; do not overwrite robot/tool PBR with a single flat colour; raw source remains too high-poly for direct runtime. |
| **Factory envelope / doors / bays** | Concrete, glazing, shutter mechanism, door hardware, wall-panel normals/roughness and grime at a restrained level. | Doors Green, wall panels light neutral, structure Charcoal, safety zones Yellow as route/safety authority allows. | Do not turn the factory dark, overly glossy, or use yellow as wall decoration. |
| **Cairnwell vehicle / panels** | Existing painted vehicle panel, glass, lamps, tyres and metal textures as source evidence only. | Later vehicle-specific derivative only after press/Body Weld gates. | Do not use vehicle texture sources as generic factory materials. |

## Material implementation rule

For an asset with a single mixed Meshy material atlas, use one of these safe routes:

1. **Keep the atlas unchanged** and add a separate branded/painted overlay element; or
2. create an explicit material derivative that multiplies only a proven broad-paint mask/slot while preserving the original normal/ORM/emission channels; or
3. separate only known fixed body material regions in a derivative, then assign role-specific Cairnwell materials.

Never use a blanket colour parameter on a mixed UI/mechanical atlas.  This is the source of the flat, toy-like and safety-colour regressions we are avoiding.

## First applied choice: PR005 HMI

The first PR005 candidate retains the HMI v632 **entire texture set**, unchanged, because its atlas combines the white cabinet, screen, controls, E-stop, labels and lensed details.  The Cairnwell identity treatment will be a small separate green ID/ownership plate after the intact HMI has passed material, scale, placement and real player-camera checks.

This keeps the detailed model looking like a real industrial console while allowing the machine around it to carry the Cairnwell palette.
