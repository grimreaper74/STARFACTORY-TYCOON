# Line Boss: Car Factory — Brand Identity Authority

Status: approved internal design authority and user-authorized for use in Line Boss. Formal external trademark registration, exclusivity and territory conflict review are separate release/business matters.

Source pack: `SourceAssets/ReferencePacks/CAIRNWELL_AUTOMOTIVE_BRAND_IDENTITY_PACK_v1.0/`

## Approved names

- Corporation: **CAIRNWELL AUTOMOTIVE**
- Factory/site: **MOORCROSS WORKS**
- Vehicle platform: **U-SERIES**
- Initial campaign: **THE RESTART**
- Game title: **LINE BOSS: CAR FACTORY**

These names supersede the provisional `Alder Forge Automotive` and `Greyford Works` names. Do not use those provisional names in new assets.

## Authoritative palette

| Token | Hex | Approximate RAL | Intended use |
|---|---:|---|---|
| Cairnwell Green | `#1F4B44` | RAL 6004 | Corporate signs, ownership marks and restored certification accents |
| Foundry Charcoal | `#202428` | RAL 7021 | Primary housings, signs and dark UI surfaces |
| Steel Grey | `#70777C` | RAL 7043 | Secondary equipment and neutral industrial surfaces |
| Warm White | `#F3F1E9` | RAL 9002 | Text, light sign fields and contrast |
| Safety Yellow | `#F2C300` | RAL 1023 | Functional safety marking only |
| Signal Red | `#C7352C` | RAL 3020 | Stops, hazards and alarm states only |

Safety Yellow and Signal Red remain functional safety colours. They must not be repurposed as general corporate decoration.

## Typography

- Display: Inter Display ExtraBold
- Supporting text: Inter Regular / SemiBold
- Use a licensed bundled font or a deterministic approved fallback in packaged builds.
- Convert externally supplied SVG text to outlines, or render it through the controlled game font pipeline, before producing final decals.

## Application rules

- The Cairnwell mark identifies corporate ownership; the functional asset ID remains the dominant maintenance identifier.
- Use `MOORCROSS WORKS` on site entrances and major building signs.
- Use stable functional IDs such as `PR005-DC01`, `HMI-PR005-01`, `CR01-001`, `MR01-001` and `CRANE-40T-01` on equipment.
- Mothballed and restored states share geometry. Express condition through materials, decals, certification plates and replaceable service parts.
- Do not bake branding into shared base geometry. Use material instances, decals, signs or replaceable plates.
- Keep warning labels, emergency controls and statutory signage distinct from brand graphics.

## Controlled implementation order

1. Shared HMI cabinet identity plate and PR-005 asset plate.
2. One CR01/MR01 shared-platform ownership-mark test.
3. Moorcross Works Press Shop entrance sign.
4. Review fresh fixed-camera Unreal screenshots.
5. Roll the approved treatment out to remaining equipment and vehicles.

No branding candidate is promoted solely because it imports or renders correctly. Promotion requires readable scale, correct placement and visual approval in fresh Unreal evidence.

## Legal gate

The user confirmed on 2026-08-03 that Cairnwell is a fictional identity created with Pro for this game and authorized its use in Line Boss. The internal project-use gate is therefore cleared. This confirmation does not claim trademark registration or exclusivity; complete any desired external name, trademark and design-conflict review before public marketing or release in intended sales territories.
