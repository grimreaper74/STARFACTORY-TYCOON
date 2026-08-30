# Station parts allocation and ordering — design v001

Status: **Planned** (direction + mined reference; no implementation yet).
Source: owner direction 2026-08-26 ("have a look at car manufacturer
assembly station system and parts allocation to station and ordering")
plus identifier mining of Car Manufacture's Assembly-CSharp.dll
(installed copy, read-only reference).

## What Car Manufacture does (mined vocabulary)

- `AssemblyStation` nodes each carry a **work scope**
  (`AssemblyNodeWorkScope`, `ChangeAssemblyNodeWorkScope`): the set of
  assembly steps that station performs. The player reassigns scopes
  between stations.
- A scope implies its **ordered-parts content**
  (`AssemblyNodeWorkScopeOrderContent`, `CanShowAllOrderedParts`): the
  parts that scope consumes are listed against the STATION, not
  against a global pool.
- A logistics service (`JobLogisticDataService`) delivers the
  allocated parts from storage to the station; `MountPart` consumes
  one at fit time. Power rides the same economy (`CityPowerSystem`,
  metered + sell-back — already implemented on our side).

## Mapping to Line Boss

1. **Work scope = stage set.** Each route station already services a
   stage class; its scope is the recipe's per-stage COMPONENT
   requirements (the shipped recipes: Hull, Electronics, Power,
   Propulsion, Navigation, Interior — internals shared across tiers).
2. **Allocation.** Each station gets a demand list derived from its
   scope x the active contract's remaining units: "HullFabricator-001
   needs 2x Component.Hull". Demand is data on the crafting/route
   seam, never a second inventory.
3. **Ordering against allocation.** The player orders parts against a
   station's demand (or imports them - the buy-until-built rule).
   Made-to-order stays law: nothing is produced or shipped without an
   order.
4. **Delivery by drone.** The heavy hauler's existing machine->store
   run gains the mirror leg: store->station for allocated parts; the
   fitting drones' Pickup mission becomes the visible MountPart.
5. **Consumption at fit.** A stage cycle at a route station consumes
   its allocated components fail-closed: missing parts stall the
   stage with the shortage named (the toast is the tutorial), which
   finally makes the import lane and the sub-assembly machines
   load-bearing.

## Order of work (next session)

a. Stage->component requirement table on the recipe (data + validator).
b. Station demand derivation + panel display (per-station parts list).
c. Store->station drone delivery leg (fleet authority).
d. Stage consumption gate in the coordinator (fail-closed, named).
e. Suite coverage at each step; the AutoShow must still deliver.
