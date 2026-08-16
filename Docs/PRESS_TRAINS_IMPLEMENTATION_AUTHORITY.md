# Cairnwell Press Trains A-D - Unreal implementation authority

Status: active authority for isolated shared-kit and Train A construction.

This document combines the owner decisions in
`Docs/MACHINE_ENCLOSURE_DESIGN_AUTHORITY.md` with the existing Pro pack at
`SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/`.
It does not authorize placement at invented world coordinates.

## Player and presentation model

- The factory is fully automated; no production-worker simulation is required.
- The player operates from the Moorcross Works control room through fixed CCTV,
  drone views and remote HMI commands.
- Each press train must look, sound and report as if it works. It does not need a
  physically complete internal press mechanism or real-time sheet deformation.
- A truthful gameplay cycle is: reserved blank arrives from PR-010, guarded
  destack/load, staged transfer, visible press-slide events, synchronized spatial
  sound/vibration/state lighting, formed-panel mesh/state replacement, final
  inspection, stillage output and saveable production state.
- Enclosures are intentional release geometry, not covers for unfinished assets.
  Provide service doors, windows or camera portals, access platforms, utility
  routing and sufficient close-drone detail to make the machinery believable.

## Coordinate and placement rule

- Station-local axes are `+X` across the train, `+Y` material flow and `+Z` up.
- Build the shared kit and Train A at an isolated local origin using these axes.
- Train A-D global Unreal datums and rotations remain `TBC_NOT_INVENTED` in the
  authoritative pack. Do not place production instances into the accepted Press
  Shop map until an authoritative master-plan transform is available.
- The missing global datums are a placement authority gap, not a machinery design
  gap. No new Pro exterior redesign is required.

## Shared train envelope and access

- Single train envelope: `56,000 L x 15,000 W x 11,500 H mm` EST.
- Stage pitch: `7,500 mm` EST.
- Operator/HMI service side: `1,500 mm` clear RECOMMENDED.
- Die-change/service corridor: `2,500 mm` clear RECOMMENDED.
- Overhead crane hook clearance: `8,000 mm` minimum RECOMMENDED.
- Guarding uses interlocked press enclosures and approved open-mesh access zones;
  do not create an unnecessary full perimeter cage.

## Seven reusable stages

| ID | Function | Local Y centre (mm) | Envelope W x L x H (mm) |
|---|---|---:|---:|
| S01 | Destack and blank load | 0 | 6,500 x 11,000 x 6,500 |
| S02 | Draw press | 7,500 | 7,000 x 12,000 x 11,000 |
| S03 | Secondary form/restrike | 15,000 | 6,500 x 11,000 x 9,500 |
| S04 | Trim press and underfloor scrap | 22,500 | 6,500 x 11,000 x 9,000 |
| S05 | Pierce press and slug collection | 30,000 | 6,500 x 11,000 x 8,500 |
| S06 | Flange/final restrike | 37,500 | 6,500 x 11,000 x 9,000 |
| S07 | Robotic unload/inspect/stillage | 45,000 | 9,000 x 13,000 x 7,000 |

The stage envelopes are game implementation authority. Final real-world press
force, die-bed and civil/foundation values remain engineering estimates and must
not be presented as construction-approved data.

## Required reusable modules

- Common platform/foundation and underfloor service/scrap interfaces.
- Reusable press frame family with draw, form, trim, pierce and flange variants.
- Enclosure panels, fixed lower guards, access doors and inspection windows.
- Transfer rails, pitch motion and interchangeable crossbar/gripper presentation.
- Moving bolster, modular die set, die cart and die-change/service interface.
- Stage HMI/status panel, E-stop/isolation station and train identity module.
- Utility spine: electrical, controls/network, air, hydraulic, lubrication and
  cooling presentation, with believable supported drops.
- S01 destack/load equipment and S07 unload/inspection/stillage equipment.
- Independent collision and safety/no-go volumes for stages, slides, transfer,
  die carts, scrap pits and access gates.

Static frames may use Nanite after validation. Moving slides, bolsters, transfer
parts, dies, robots and doors remain separate components with authored pivots.

## Minimum visible motion and feedback

- Press slide/ram: local Z, `300-800 mm` recipe stroke, safe at top dead centre.
- Moving bolster: local X, `0-3,500 mm`, safe in press.
- Die cart: local X/Y recipe motion, safe in service bay.
- Transfer lift: local Z, `0-600 mm`, raised safe.
- Transfer pitch: local Y, `0-7,500 mm`, stage home.
- Crossbar grippers: recipe rotary/linear motion, open safe.
- Destack lift: local Z, `0-1,200 mm`, lowered safe.
- Unload robots: limited visible six-axis poses, parked safe.

The runtime may use authored curves and state-driven mesh replacement. It must
still prove controlled stop, interlocked access, isolation/zero-energy evidence,
fault recovery, safe save restoration and deterministic resumption.

## Train variants

| Train | Part family | Nominal rate EST | Accent | Distinguishing presentation |
|---|---|---:|---|---|
| A | Large outer panels | 8-12 spm | Blue `#3B82C4` | Largest dies, expanded Class-A surface-light tunnel |
| B | Floors/underbody | 10-15 spm | Green `#4D8B4A` | Deep-draw tooling, heavy trim-scrap extraction |
| C | Closures | 12-18 spm | Orange `#C8782D` | Frequent mixed-model change, flexible grippers |
| D | Reinforcements/smaller panels | 15-22 spm | Purple `#75578F` | Smaller dies, faster changeovers, high variety |

Reuse the parent geometry. Variant data changes dies, transfer grippers, recipes,
inspection lighting, IDs and small accent panels; do not duplicate shared frames.

## Branding and materials

- Diegetic corporation: Cairnwell Automotive.
- Site: Moorcross Works.
- Vehicle platform: U-Series.
- `Line Boss` is prohibited on equipment, HMIs, decals and other in-world text.
- Foundry-charcoal frames, Cairnwell green equipment panels, restrained safety
  yellow on genuine hazards/edges only, worked steel, dark rubber, glass and
  supported utilities form the shared material hierarchy.
- Restored and mothballed states use layered age/wear data, not random noise.

## Construction and promotion order

1. Build and dimension-audit the shared seven-stage modular source kit locally.
2. Assemble isolated Train A with the blue variant and truthful cycle presentation.
3. Import into an isolated Unreal validation map; do not alter accepted PR-010.
4. Add native runtime/save/fault/isolation authority and component bindings.
5. Add selective collision, temporal sweeps, maintenance-robot navigation and
   crane/die-change clearances.
6. Run compile/import/runtime/collision/navigation/save/authority gates and fresh
   CCTV/drone screenshots against Pro Sheets 04 and 05.
7. Only after Train A direction passes, instantiate B-D using shared assets and
   variant data, then review against Sheets 06-08.
8. Resolve authoritative world datums before production-map placement.

No technical pass alone authorizes promotion. Visual promotion still requires
fresh fixed-camera Unreal evidence inspected against the Pro references.
