# Original spray-booth runtime v001 — frozen source and import gate

Status: **SUPERSEDED BY THE ORIGINAL-PROCEDURAL V002 TWO-LOD AUTHORITY**  
Date: 2026-08-15  
Reserved fresh-only destination:
`/Game/LineBoss/Candidates/PaintShop/SprayBoothRuntime_v001`

## Accepted authority

Only these original procedural files are eligible:

| File | Bytes | SHA-256 |
|---|---:|---|
| `SourceAssets/Candidate/PaintShop/SprayBoothRuntime_v001/Authority/generate_LB_PaintSprayBooth_Runtime_v001.py` | 25,508 | `A2C5ED68C267AC6F7A2898D9D6C6B180FC4E8EE1A0F9418971EAED5462C6505A` |
| `SourceAssets/Candidate/PaintShop/SprayBoothRuntime_v001/Authority/LB_PaintSprayBooth_Runtime_v001.blend` | 140,537 | `9B8706A16B0E3599EC7DF6FF153C28C98840F4F2FCBDB787622F9AB02A89902E` |
| `SourceAssets/Candidate/PaintShop/SprayBoothRuntime_v001/Authority/LB_PaintSprayBooth_Runtime_v001.glb` | 317,028 | `CE2D76BDDB0B2CBDE475F4339179104BE725FE651C57AD14AB3C25499640DEE8` |

The generator creates fresh cubes/cylinders only and declares no imported
topology. The GLB contains 81 meshes, 82 nodes and exactly these six material
names: `M_LB_Panel_OffWhite`, `M_LB_Frame_Graphite`,
`M_LB_Cairnwell_Green`, `M_LB_Safety_Yellow`, `M_LB_Rail_Steel`, and
`M_LB_Extraction_Gray`.

Frozen design contract: 1200 × 500 × 450 cm overall bounds; 430 × 335 cm clear
open portals at both short ends; six solid panel modules on each long side;
zero windows, personnel doors, side vehicle openings, internal spray robots,
armatures or animation; three roof extraction housings and collars; twin
continuous floor rails. The Unreal candidate must have controlled UV/lightmap
channels, authored simple collision that leaves both portals clear, Nanite
disabled, exactly two source LODs, and independent technical and screenshot
receipts before promotion.

## Hard LOD gate

The audited v001 authority contains only one source LOD and remains unchanged.
The required separate Blender-primitive LOD1 now exists in the v002 successor
authority; engine auto-reduction and every Meshy source remain forbidden.
See `SPRAY_BOOTH_RUNTIME_V002_UNREAL_LANE.md` for the frozen lane.

## ED oven provenance decision

Safe to reuse as validation-only original procedural blockout packages:

- `EDLineRuntime_Candidate_v001/Exports/SM_LB_EDLine_OvenEntryModule_Blockout_v001.fbx`
  — `9974B468AEA1C71B84364F6FFF540E592B4706B147CD66A0BDCB9B269D01625F`
- `...OvenProcessModule...fbx` —
  `5759D2D03775EA6FF596D17ABFAA31AA76FB42EBD716A488B1A0F4C6ADCDEA7A`
- `...OvenExitModule...fbx` —
  `584FC4E5DBEBC8B5ACE0E8ED7E46C6EA94DB5CA429910341FBF14CE631BE5537`
- `...OvenFanAssembly...fbx` —
  `7130FD4E70FB752399649352803B85AAFEF8F9E9DA4FB0502B0BD4CFB19B4D9E`
- `...OvenServiceDoor...fbx` —
  `C453A6F950F445BB2615845DEFE4B8FF96A86F372EB1AC3020D6F5B142A17C93`
- `...OvenServiceLight...fbx` —
  `C1D1481048A5817173F7245334A1D4BF647C4E13EA57D17C6582A7065EF8677E`

Their authority chain is `EDLineAssembly/Build/build_ed_line.py` → combined
GLB → modular exporter. That build explicitly authors low-poly primitives,
keeps the Meshy tank/oven siblings as disabled reference-only empties, and
exports only tagged procedural objects.

Blocked: every file under `EDCuringOven/Authorities` and the corresponding
standalone EDCuringOven audited package, because the authorities are named
`Meshy_AI_*`; also block `EDLineMeshyReview_v002`. Neither may seed topology,
LOD, materials or collision for this seam.

## Future one-shot

The v001 namespace remains blocked. Use only the v002 successor lane documented
in `SPRAY_BOOTH_RUNTIME_V002_UNREAL_LANE.md`.
