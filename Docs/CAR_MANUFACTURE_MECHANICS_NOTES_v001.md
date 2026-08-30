# Car Manufacture (Steam) — mechanics notes from a read-only dig (v001)

Source: class/member names extracted from the installed game's Mono
Assembly-CSharp.dll (2026-08-26, read-only). No assets or code copied —
vocabulary and system-shape evidence only, same method as the ATT pass.

## What their shipped game confirms for Line Boss
- WORKERS are their headline entity (400+ classes: salary, energy,
  speed upgrades, assignment). Structural mirror of our DRONES —
  import their upgrade template as drone research items.
- SUPPLY CONTRACTS not flat prices: CarPartProvidingContract /
  ResourcesTransportLinkContract. Make-vs-buy v2: named providers with
  terms, mirroring our customer contracts on the sell side.
- BANK LOANS (100+ classes): the genre solvency valve; add alongside
  the bailout contract.
- RESEARCH DESKS/LABS as physical stations creating research JOBS —
  second independent confirmation of the research-as-production
  recommendation.
- WEEKLY UPKEEP (EntitiesUpkeepCostSystem) as the standing cost —
  matches our power/maintenance-not-rent principle.
- CLIENTS physically present with wait-time/comfort systems — contract
  personality made visible on the floor.
- CONVEYOR NODES with explicit input/output ports (incl. AirConveyors)
  — validates port-based belt routing; aerial belts are on-brand for a
  spacecraft factory someday.
- QUALITY as per-product instances with min/max bands — matches our
  FailedQualityTests per-unit model.

## Priority takes
1. Drone upgrade research items (speed/energy/capacity) — cheap, soon.
2. Loans in the finance authority — with the milestone economy pass.
3. Provider contracts for imports — when make-vs-buy v2 lands.
4. Waiting client representatives — with contract personality work.
